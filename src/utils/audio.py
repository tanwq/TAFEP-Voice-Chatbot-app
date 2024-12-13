import pyaudio
import wave
import numpy as np
import logging
import os
from pathlib import Path
import soundfile as sf
from datetime import datetime
import tempfile
from typing import Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, 
                 channels: int = 1,
                 rate: int = 44100,
                 chunk: int = 1024,
                 format: int = pyaudio.paInt16,
                 silence_threshold: int = 150,
                 min_silence_duration: float = 0.5):
        """
        Initialize audio processor with given parameters
        
        Args:
            channels (int): Number of audio channels
            rate (int): Sample rate
            chunk (int): Buffer size
            format (int): Audio format (from pyaudio)
            silence_threshold (int): RMS threshold for silence detection
            min_silence_duration (float): Minimum silence duration to stop recording
        """
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.format = format
        self.silence_threshold = silence_threshold
        self.min_silence_duration = min_silence_duration
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Debug directory setup
        self.debug_dir = Path("debug_audio")
        self.debug_dir.mkdir(exist_ok=True)

    def convert_wav_to_mp3(self, wav_path: str, mp3_path: str) -> bool:
        """
        Convert WAV file to MP3 format
        
        Args:
            wav_path (str): Path to input WAV file
            mp3_path (str): Path to output MP3 file
            
        Returns:
            bool: True if conversion successful, False otherwise
        """
        try:
            import pydub
            audio = pydub.AudioSegment.from_wav(wav_path)
            audio.export(mp3_path, format="mp3")
            return True
        except Exception as e:
            logger.error(f"Error converting WAV to MP3: {e}")
            return False

    def convert_to_mono(self, audio_data: bytes) -> bytes:
        """
        Convert stereo audio data to mono
        
        Args:
            audio_data (bytes): Input audio data
            
        Returns:
            bytes: Mono audio data
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Reshape if stereo
            if len(audio_array) % 2 == 0:
                audio_array = audio_array.reshape(-1, 2)
                mono_array = audio_array.mean(axis=1, dtype=np.int16)
                return mono_array.tobytes()
            return audio_data
        except Exception as e:
            logger.error(f"Error converting to mono: {e}")
            return audio_data

    def normalize_audio(self, audio_data: bytes) -> bytes:
        """
        Normalize audio volume
        
        Args:
            audio_data (bytes): Input audio data
            
        Returns:
            bytes: Normalized audio data
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Normalize
            normalized = np.int16(audio_array * (32767/max(abs(audio_array))))
            return normalized.tobytes()
        except Exception as e:
            logger.error(f"Error normalizing audio: {e}")
            return audio_data

    def prepare_audio_for_api(self, audio_data: bytes) -> Tuple[bytes, str]:
        """
        Prepare audio data for API submission
        
        Args:
            audio_data (bytes): Raw audio data
            
        Returns:
            Tuple[bytes, str]: Processed audio data and temporary file path
        """
        try:
            # Convert to mono if needed
            mono_data = self.convert_to_mono(audio_data)
            
            # Normalize volume
            normalized_data = self.normalize_audio(mono_data)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(normalized_data)
            
            return normalized_data, temp_file.name
        except Exception as e:
            logger.error(f"Error preparing audio: {e}")
            return None, None

    def save_debug_audio(self, audio_data: bytes, prefix: str = "debug") -> Optional[str]:
        """
        Save audio data for debugging purposes
        
        Args:
            audio_data (bytes): Audio data to save
            prefix (str): Filename prefix
            
        Returns:
            Optional[str]: Path to saved file if successful
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.wav"
            filepath = self.debug_dir / filename
            
            with wave.open(str(filepath), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(audio_data)
            
            logger.info(f"Saved debug audio: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving debug audio: {e}")
            return None

    def cleanup_old_files(self, max_files: int = 100) -> None:
        """
        Clean up old debug audio files
        
        Args:
            max_files (int): Maximum number of files to keep
        """
        try:
            files = sorted(self.debug_dir.glob("*.wav"), key=os.path.getctime)
            if len(files) > max_files:
                for file in files[:-max_files]:
                    file.unlink()
                logger.info(f"Cleaned up {len(files) - max_files} old audio files")
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")

    def __del__(self):
        """Cleanup when object is deleted"""
        try:
            self.audio.terminate()
        except Exception as e:
            logger.error(f"Error terminating PyAudio: {e}")