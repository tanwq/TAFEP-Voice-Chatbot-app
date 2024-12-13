import os
import platform
import asyncio
import requests
import logging
from google.cloud import texttospeech
from typing import Callable
import subprocess
import wave
# Import winsound for Windows
if platform.system() == "Windows":
    import winsound

class TextToSpeech:
    def __init__(self):
        """Initialize TTS service with Google Cloud client"""
        self.tts_client = texttospeech.TextToSpeechClient()
        self.logger = logging.getLogger(__name__)
        self.speaking_callback: Callable[[bool], None] = None
        self._speaking_event = asyncio.Event()
        self._speaking_event.set()  # Initially not speaking
        self._speaking_lock = asyncio.Lock()  # Lock for thread safety
        
    def register_speaking_callback(self, callback: Callable[[bool], None]):
        """Register callback for speaking state changes"""
        self.speaking_callback = callback
    
    async def _notify_speaking_state(self, is_speaking: bool):
        """Safely notify callback of speaking state change"""
        try:
            if self.speaking_callback:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.speaking_callback,
                    is_speaking
                )
        except Exception as e:
            self.logger.error(f"Error in speaking callback: {e}")

    async def speak_with_elevenlabs(self, text: str):
        """
        Generate and play audio using ElevenLabs API
        
        Args:
            text (str): Text to convert to speech
        """
        if not text or len(text.strip()) == 0:
            self.logger.error("Empty or invalid input for text-to-speech.")
            return
            
        async with self._speaking_lock:
            try:
                # Wait for any previous speech to complete
                await self._speaking_event.wait()
                self._speaking_event.clear()
                
                # Notify that TTS is starting
                await self._notify_speaking_state(True)
                
                url = "https://api.elevenlabs.io/v1/text-to-speech/dFsPk3Np2rLsQ5viBQeB"
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": os.getenv("ELEVENLABS_API_KEY")
                }
                data = {
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.3,
                        "similarity_boost": 0.8,
                        "style": 0.01,
                        "use_speaker_boost": True
                    }
                }

                # Make API request
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.post(url, json=data, headers=headers, stream=True)
                )
                response.raise_for_status()

                # Write audio file
                with open("output.mp3", 'wb') as f:
                    async for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)

                # Play the audio
                await self._play_audio("output.mp3")

            except Exception as e:
                self.logger.error(f"ElevenLabs TTS Error: {e}")
                await self._notify_speaking_state(False)
            finally:
                self._speaking_event.set()

    async def speak_with_wavenet(self, text: str, pitch: str = "-10%", rate: str = "medium"):
        """
        Generate and play audio using Google Cloud Wavenet
        
        Args:
            text (str): Text to convert to speech
            pitch (str): Voice pitch adjustment
            rate (str): Speech rate
        """
        if not text or len(text.strip()) == 0:
            self.logger.error("Empty or invalid input for text-to-speech.")
            return

        async with self._speaking_lock:
            try:
                # Wait for previous speech to complete
                await self._speaking_event.wait()
                self._speaking_event.clear()
                
                # Notify that TTS is starting
                await self._notify_speaking_state(True)
                    
                # Prepare SSML
                ssml_text = f"""
                <speak>
                    <prosody pitch="{pitch}" rate="{rate}">
                        {text}
                    </prosody>
                </speak>
                """
                
                # Configure synthesis input
                input_text = texttospeech.SynthesisInput(ssml=ssml_text)
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    name="en-US-Wavenet-D",
                    ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.LINEAR16
                )

                # Generate speech
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.tts_client.synthesize_speech(
                        input=input_text,
                        voice=voice,
                        audio_config=audio_config
                    )
                )

                # Save audio file
                with open("output.wav", "wb") as out:
                    out.write(response.audio_content)

                # Play audio
                await self._play_audio("output.wav")

            except Exception as e:
                self.logger.error(f"WaveNet TTS Error: {e}")
                await self._notify_speaking_state(False)
            finally:
                self._speaking_event.set()

    async def _play_audio(self, file_path: str):
        """
        Play audio file using appropriate system player
        
        Args:
            file_path (str): Path to audio file
        """
        try:
            # Get audio duration before playing
            with wave.open(file_path, 'rb') as wave_file:
                duration_seconds = wave_file.getnframes() / wave_file.getframerate()
                
            # Play audio based on operating system
            if platform.system() == "Darwin":  # macOS
                process = await asyncio.create_subprocess_exec("afplay", file_path)
                await process.wait()
            elif platform.system() == "Windows":
                winsound.PlaySound(file_path, winsound.SND_FILENAME)
            else:  # Linux
                process = await asyncio.create_subprocess_exec("aplay", file_path)
                await process.wait()

            # Notify that speaking has finished
            await self._notify_speaking_state(False)

        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
            await self._notify_speaking_state(False)
            raise