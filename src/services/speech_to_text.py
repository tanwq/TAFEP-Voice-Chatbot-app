import logging
from typing import Optional, Tuple, List
from datetime import datetime
import json
import asyncio
import base64
import wave
import io
import numpy as np
import soundfile
import websockets
from pathlib import Path
from .auth import Authenticator
from config import Config

class SpeechToText:
    def __init__(self):
        """Initialize speech-to-text service with Hume AI authentication"""
        self.logger = logging.getLogger(__name__)
        self.authenticator = Authenticator()
        
        # Audio processing parameters
        self.sample_rate = Config.SAMPLE_RATE
        self.channels = Config.CHANNELS
        self.sample_width = Config.SAMPLE_WIDTH
        
        # Response handling
        self.message_timeout = 2.0  # seconds to wait for complete response
        
        # Debug directory setup
        self.debug_dir = Path("debug_sessions") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.debug_dir.mkdir(parents=True, exist_ok=True)

    async def _send_to_hume(self, socket_url: str, encoded_audio: str) -> Optional[dict]:
        """Send audio to Hume API via WebSocket and get results"""
        try:
            async with websockets.connect(socket_url) as socket:
                # Send audio data
                json_message = json.dumps({
                    "type": "audio_input",
                    "data": encoded_audio
                })
                await socket.send(json_message)
                
                # Initialize response handling
                start_time = asyncio.get_event_loop().time()
                messages = []
                transcript = None
                emotions = None
                
                # Wait for responses with timeout
                while True:
                    try:
                        # Set a timeout for message reception
                        message = await asyncio.wait_for(
                            socket.recv(),
                            timeout=self.message_timeout
                        )
                        
                        json_message = json.loads(message)
                        messages.append(json_message)
                        
                        # Handle different message types
                        if json_message.get("type") == "transcription":
                            transcript = json_message.get("text", "").strip()
                            
                        elif json_message.get("type") == "user_message" and "models" in json_message:
                            # Get prosody scores
                            prosody_scores = json_message["models"].get("prosody", {}).get("scores", {})
                            if prosody_scores:
                                emotions = sorted(
                                    prosody_scores.items(),
                                    key=lambda x: x[1],
                                    reverse=True
                                )[:3]
                        
                        # Check if we have both transcript and emotions
                        if transcript and emotions:
                            # Construct final response
                            final_response = {
                                "type": "user_message",
                                "message": {
                                    "content": transcript
                                },
                                "models": {
                                    "prosody": {
                                        "scores": dict(emotions)
                                    }
                                }
                            }
                            return final_response
                            
                        # Check timeout
                        current_time = asyncio.get_event_loop().time()
                        if current_time - start_time > self.message_timeout:
                            self.logger.warning("Response timeout reached")
                            break
                            
                    except asyncio.TimeoutError:
                        self.logger.warning("WebSocket receive timeout")
                        break
                    except Exception as e:
                        self.logger.error(f"Error receiving message: {e}")
                        break
                
                # If we get here without returning, construct response from what we have
                return {
                    "type": "user_message",
                    "message": {
                        "content": transcript or ""
                    },
                    "models": {
                        "prosody": {
                            "scores": dict(emotions or [])
                        }
                    }
                }

        except Exception as e:
            self.logger.error(f"Error in WebSocket communication: {e}")
            return None
            
    def transcribe_audio(self, audio_bytes: bytes) -> Optional[Tuple[str, List[tuple]]]:
        """
        Synchronous wrapper for async transcription
        
        Args:
            audio_bytes (bytes): Raw audio data
            
        Returns:
            Optional[Tuple[str, List[tuple]]]: Tuple of (transcript, emotions) if successful
        """
        try:
            # Create new event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run async transcription
            result = loop.run_until_complete(self._transcribe_audio_async(audio_bytes))
            
            # Clean up
            loop.close()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in synchronous transcription wrapper: {e}")
            return None

    async def _transcribe_audio_async(self, audio_bytes: bytes) -> Optional[Tuple[str, List[tuple]]]:
        """
        Async implementation of audio transcription
        
        Args:
            audio_bytes (bytes): Raw audio data
            
        Returns:
            Optional[Tuple[str, List[tuple]]]: Tuple of (transcript, emotions) if successful
        """
        try:
            # Get fresh token
            self.logger.info("Fetching access token...")
            access_token = self.authenticator.fetch_access_token()
            self.logger.info(f"Access token received: {bool(access_token)}")
            
            if not access_token:
                self.logger.error("No access token received from authenticator")
                raise ValueError("Failed to get valid Hume access token")

            # Process audio data
            self.logger.info("Processing audio data...")
            processed_audio = await self._process_audio(audio_bytes)
            if not processed_audio:
                self.logger.error("Audio processing failed")
                raise ValueError("Failed to process audio data")

            # Log URL construction
            socket_url = (
                "wss://api.hume.ai/v0/evi/chat?"
                f"access_token={access_token}&"
                "config_id=44d4a322-684f-45b1-8261-1be941534e04"
            )
            self.logger.info(f"WebSocket URL constructed (token hidden)")

            # Send audio and get response
            self.logger.info("Sending audio to Hume API...")
            result = await self._send_to_hume(socket_url, processed_audio)
            if not result:
                self.logger.error("No response received from Hume API")
                raise ValueError("No response from Hume API")

        except Exception as e:
            self.logger.error(f"Error in async speech transcription: {e}")
            return None

    async def _process_audio(self, audio_data: bytes) -> Optional[str]:
        """Process audio data for Hume API"""
        try:
            # Convert to mono if stereo
            if self.channels == 2:
                stereo_data = np.frombuffer(audio_data, dtype=np.int16)
                mono_data = ((stereo_data[0::2] + stereo_data[1::2]) / 2).astype(np.int16)
                audio_data = mono_data.tobytes()

            # Create WAV in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(1)  # Always mono for API
                wf.setsampwidth(self.sample_width)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)

            # Encode for API
            encoded_audio = base64.b64encode(wav_buffer.getvalue()).decode('utf-8')
            return encoded_audio

        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
            return None
            
    def _extract_results(self, result: dict) -> Tuple[str, List[tuple]]:
        """Extract transcript and emotions from Hume results"""
        try:
            # Extract transcript
            transcript = result.get("message", {}).get("content", "")
            
            # Extract emotions
            prosody_scores = result.get("models", {}).get("prosody", {}).get("scores", {})
            emotions = sorted(
                prosody_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]  # Top 3 emotions

            return transcript, [(emotion, float(score)) for emotion, score in emotions]

        except Exception as e:
            self.logger.error(f"Error extracting results: {e}")
            return "", []

    async def _save_debug_data(self, audio_data: bytes, api_response: dict):
        """Save debug information"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save audio
            audio_path = self.debug_dir / f"audio_{timestamp}.wav"
            with wave.open(str(audio_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.sample_width)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)

            # Save API response
            response_path = self.debug_dir / f"response_{timestamp}.json"
            with open(response_path, "w") as f:
                json.dump(api_response, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving debug data: {e}")