from audio_recorder_streamlit import audio_recorder
import streamlit as st
import logging
from typing import Optional
from datetime import datetime
from typing import List, Optional, Tuple

class AudioRecorder:
    def __init__(self, chat_box, conversation_handler, speech_to_text):
        """
        Initialize with required dependencies
        
        Args:
            chat_box: ChatBox instance for displaying messages
            conversation_handler: ConversationHandler for generating responses
            speech_to_text: SpeechToText for audio transcription
        """
        self.logger = logging.getLogger(__name__)
        self.chat_box = chat_box
        self.conversation_handler = conversation_handler
        self.speech_to_text = speech_to_text
        self.is_processing = False

    def record(self) -> Optional[bytes]:
        """Record audio with error handling"""
        try:
            return audio_recorder(
                pause_threshold=2.0,
                icon_size="2x",
                recording_color="#e21e1e",
                neutral_color="#0096db"
            )
        except Exception as e:
            self.logger.error(f"Recording error: {e}")
            st.error("Error initializing audio recorder")
            return None

    def process_recording(self, audio_bytes: bytes) -> None:
        if not audio_bytes or self.is_processing:
            return

        try:
            self.is_processing = True
            with st.spinner("Processing your message..."):
                # Get transcript and emotions from speech service
                result = self.speech_to_text.transcribe_audio(audio_bytes)
                
                if result:
                    transcript, emotions = result
                    
                    # Add user message
                    self.chat_box.add_message(
                        role="user",
                        content=transcript,
                        emotions=emotions
                    )

                    # Generate and add bot response with emotions
                    bot_response = self.conversation_handler.generate_response(
                        transcript,
                        emotions
                    )
                    if bot_response:
                        self.chat_box.add_message(
                            role="assistant",
                            content=bot_response
                        )

        except Exception as e:
            self.logger.error(f"Error processing recording: {e}")
            st.error("Error processing your message. Please try again.")
        finally:
            self.is_processing = False