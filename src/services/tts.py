import os
import platform
import requests
import logging
from google.cloud import texttospeech
from typing import Callable
import subprocess
import wave
from config import Config
from pathlib import Path

# Import winsound for Windows
if platform.system() == "Windows":
    import winsound

class TextToSpeech:
    def __init__(self):
        """Initialize TTS service with Google Cloud client"""
        # Set Google Cloud credentials
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = Config.GOOGLE_APPLICATION_CREDENTIALS
        self.tts_client = texttospeech.TextToSpeechClient()
        self.logger = logging.getLogger(__name__)
        self.speaking_callback = None
        self._is_speaking = False
        
    def register_speaking_callback(self, callback: Callable[[bool], None]):
        """Register callback for speaking state changes"""
        self.speaking_callback = callback
    
    def _notify_speaking_state(self, is_speaking: bool):
        """Safely notify callback of speaking state change"""
        try:
            if self.speaking_callback:
                self.speaking_callback(is_speaking)
        except Exception as e:
            self.logger.error(f"Error in speaking callback: {e}")

    def speak_with_elevenlabs(self, text: str):
        """
        Generate and play audio using ElevenLabs API
        
        Args:
            text (str): Text to convert to speech
        """
        if not text or len(text.strip()) == 0:
            self.logger.error("Empty or invalid input for text-to-speech.")
            return
            
        try:
            # Notify that TTS is starting
            self._is_speaking = True
            self._notify_speaking_state(True)
            
            url = "https://api.elevenlabs.io/v1/text-to-speech/dFsPk3Np2rLsQ5viBQeB"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": Config.ELEVENLABS_API_KEY
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
            response = requests.post(url, json=data, headers=headers, stream=True)
            response.raise_for_status()

            # Write audio file
            output_path = Path(Config.TEMP_DIR) / "output.mp3"
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            # Play the audio
            self._play_audio(str(output_path))

        except Exception as e:
            self.logger.error(f"ElevenLabs TTS Error: {e}")
        finally:
            self._is_speaking = False
            self._notify_speaking_state(False)

    def speak_with_wavenet(self, text: str, pitch: str = "-10%", rate: str = "medium"):
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

        try:
            # Notify that TTS is starting
            self._is_speaking = True
            self._notify_speaking_state(True)
                
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
            response = self.tts_client.synthesize_speech(
                input=input_text,
                voice=voice,
                audio_config=audio_config
            )

            # Save audio file
            output_path = Path(Config.TEMP_DIR) / "output.wav"
            with open(output_path, "wb") as out:
                out.write(response.audio_content)

            # Play audio
            self._play_audio(str(output_path))

        except Exception as e:
            self.logger.error(f"WaveNet TTS Error: {e}")
        finally:
            self._is_speaking = False
            self._notify_speaking_state(False)

    def _play_audio(self, file_path: str):
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
                subprocess.run(["afplay", file_path], check=True)
            elif platform.system() == "Windows":
                winsound.PlaySound(file_path, winsound.SND_FILENAME)
            else:  # Linux
                subprocess.run(["aplay", file_path], check=True)

            # Notify that speaking has finished
            self._notify_speaking_state(False)

        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
            self._notify_speaking_state(False)
            raise