import json
import asyncio
import websockets
import numpy as np
import soundfile
import io
import wave
import base64
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

class WebSocketConnection:
    def __init__(self):
        """Initialize WebSocket connection handler"""
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.is_tts_speaking = False
        self.is_processing_response = False
        
        # Create debug directories
        self.debug_base_dir = Path("debug_sessions")
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.debug_base_dir / f"session_{self.session_timestamp}"
        self.audio_dir = self.session_dir / "audio"
        self.hume_dir = self.session_dir / "hume_responses"
        
        # Create directories
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.hume_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize counter
        self.recording_counter = 0

    def on_tts_state_change(self, is_speaking: bool):
        """Callback for TTS speaking state changes"""
        self.is_tts_speaking = is_speaking
        if is_speaking:
            self.logger.info("TTS started speaking")
        else:
            self.logger.info("TTS finished speaking")

    async def connect(self, socket_url: str):
        """
        Establish WebSocket connection
        
        Args:
            socket_url (str): WebSocket URL with authentication token
        """
        self.logger.info("Starting WebSocket connection")
        while True:
            try:
                async with websockets.connect(socket_url) as socket:
                    self.logger.info("Connected to WebSocket successfully")
                    await self._handle_connection(socket)
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("WebSocket connection closed. Attempting reconnection...")
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Connection error: {str(e)}. Attempting reconnection...")
                await asyncio.sleep(5)

    async def process_audio(self, audio_file: str, socket_url: str) -> dict:
        """
        Process audio file through Hume AI
        
        Args:
            audio_file (str): Path to audio file
            socket_url (str): WebSocket URL with authentication token
            
        Returns:
            dict: Processed response with text and emotions
        """
        try:
            # Read audio file
            with wave.open(audio_file, 'rb') as wf:
                audio_data = wf.readframes(wf.getnframes())
                
            # Save debug recording
            timestamp, counter = await self._save_debug_recording(
                audio_data,
                len(audio_data) / (wf.getframerate() * wf.getsampwidth())
            )
            
            # Process audio through WebSocket
            async with websockets.connect(socket_url) as socket:
                # Prepare audio data
                wav_content = await self._prepare_audio_data(audio_data)
                
                # Send audio
                json_message = json.dumps({
                    "type": "audio_input",
                    "data": base64.b64encode(wav_content).decode('utf-8')
                })
                await socket.send(json_message)
                
                # Wait for response
                response = await self._receive_response(socket)
                
                # Save Hume response
                if response:
                    await self._save_hume_response(
                        response,
                        timestamp,
                        counter
                    )
                
                return response
                
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
            return None

    async def _handle_connection(self, socket):
        """Handle active WebSocket connection"""
        try:
            async for message in socket:
                try:
                    response = json.loads(message)
                    
                    # Save Hume response
                    await self._save_hume_response(
                        response,
                        getattr(self, 'last_audio_timestamp', None),
                        getattr(self, 'last_audio_counter', None)
                    )
                    
                    # Process different response types
                    if response.get("type") == "transcription":
                        transcript = response.get("text", "").strip()
                        if transcript:
                            return {
                                "type": "transcript",
                                "text": transcript,
                                "emotions": []
                            }
                            
                    elif response.get("type") == "user_message" and "models" in response:
                        user_message = response.get("message", {}).get("content", "")
                        prosody_scores = response["models"].get("prosody", {}).get("scores", {})
                        
                        emotions = await self._process_emotion_data(prosody_scores)
                        return {
                            "type": "transcript",
                            "text": user_message,
                            "emotions": emotions
                        }
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON parsing error: {e}")
                    
        except Exception as e:
            self.logger.error(f"WebSocket handling error: {e}")

    async def _prepare_audio_data(self, audio_data: bytes) -> bytes:
        """Prepare audio data for transmission"""
        try:
            # Convert to mono if needed
            np_array = np.frombuffer(audio_data, dtype=np.int16)
            if len(np_array.shape) > 1:
                np_array = np_array.mean(axis=1).astype(np.int16)
            
            # Create WAV in memory
            wav_buffer = io.BytesIO()
            soundfile.write(
                wav_buffer,
                np_array,
                samplerate=16000,  # Hume AI expects 16kHz
                subtype="PCM_16",
                format="WAV"
            )
            
            return wav_buffer.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error preparing audio: {e}")
            raise

    async def _process_emotion_data(self, prosody_scores: dict) -> list:
        """Process emotion scores from Hume AI response"""
        try:
            # Sort emotions by score
            emotions = sorted(
                prosody_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]  # Get top 3 emotions
            
            return [(emotion, float(score)) for emotion, score in emotions]
            
        except Exception as e:
            self.logger.error(f"Error processing emotions: {e}")
            return []

    def _save_debug_recording(self, audio_data: bytes, duration: float) -> tuple:
        """Save audio recording for debugging"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.recording_counter += 1
            
            # Save WAV file
            wav_path = self.audio_dir / f"recording_{timestamp}_{self.recording_counter}.wav"
            with wave.open(str(wav_path), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_data)
            
            # Save metadata
            metadata_path = self.audio_dir / f"recording_{timestamp}_{self.recording_counter}.json"
            metadata = {
                "timestamp": timestamp,
                "duration_seconds": duration,
                "file_size_bytes": len(audio_data)
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
            
            return timestamp, self.recording_counter
            
        except Exception as e:
            self.logger.error(f"Error saving debug recording: {e}")
            return None, None

    async def _save_hume_response(self, response: dict, audio_timestamp: str, audio_counter: int):
        """Save Hume AI response for debugging"""
        try:
            if audio_timestamp and audio_counter:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                response_type = response.get('type', 'unknown')
                
                response_path = self.hume_dir / f"{response_type}_{timestamp}_{audio_counter}.json"
                
                response["debug_info"] = {
                    "corresponding_audio": f"recording_{audio_timestamp}_{audio_counter}.wav",
                    "response_timestamp": timestamp,
                    "message_type": response_type
                }
                
                with open(response_path, 'w') as f:
                    json.dump(response, f, indent=4)
                
        except Exception as e:
            self.logger.error(f"Error saving Hume response: {e}")

    async def _receive_response(self, socket) -> dict:
        """Wait for and process response from WebSocket"""
        try:
            while True:
                message = await socket.recv()
                response = json.loads(message)
                
                if response.get("type") == "user_message" and "models" in response:
                    user_message = response.get("message", {}).get("content", "")
                    prosody_scores = response["models"].get("prosody", {}).get("scores", {})
                    
                    emotions = await self._process_emotion_data(prosody_scores)
                    return {
                        "text": user_message,
                        "emotions": emotions
                    }
                    
        except Exception as e:
            self.logger.error(f"Error receiving response: {e}")
            return None