import streamlit as st
from streamlit_float import float_init
import logging
from pathlib import Path
from typing import Tuple
import os

from src.components.chat_box import ChatBox
from src.components.recorder import AudioRecorder
from src.components.emotion_display import EmotionDisplay
from src.utils.logger import setup_logging
from src.conversation.handler import ConversationHandler
from src.services.tts import TextToSpeech
from src.services.speech_to_text import SpeechToText
from src.utils.helpers import initialize_session_state
from config import Config

class TAFEPApp:
    def __init__(self):
        """Initialize TAFEP application"""
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        
        # Initialize services
        self._initialize_services()

    def _initialize_services(self):
        """Initialize core services with error handling"""
        try:
            self.tts_service = TextToSpeech()
            self.conversation_handler = ConversationHandler(self.tts_service)
            self.speech_to_text = SpeechToText()
            self.logger.debug(f"Initialize Services Completed")
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise

    def setup_page_config(self):
        """Configure Streamlit page settings"""
        try:
            st.set_page_config(
                page_title="TAFEP Voice Assistant",
                page_icon="🎙️",
                layout="wide",
                initial_sidebar_state="collapsed"
            )
            float_init()
            self.logger.debug(f"Setup Page Config Completed")
        except Exception as e:
            self.logger.error(f"Failed to setup page config: {e}")
            st.error("Error initializing application. Please refresh the page.")

    def load_custom_css(self):
        """Load custom CSS styles"""
        try:
            css_path = Path('static/css/style.css')
            if css_path.exists():
                with open(css_path) as f:
                    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
                    self.logger.debug(f"Load Custom CSS Completed")
            else:
                self.logger.warning("CSS file not found")
        except Exception as e:
            self.logger.error(f"Failed to load CSS: {e}")

    def initialize_components(self) -> Tuple[ChatBox, AudioRecorder, EmotionDisplay]:
        """Initialize UI components with proper dependency injection"""
        try:
            # Initialize chat box
            chat_box = ChatBox()

            # Initialize audio recorder with dependencies
            audio_recorder = AudioRecorder(
                chat_box=chat_box,
                conversation_handler=self.conversation_handler,
                speech_to_text=self.speech_to_text
            )
            
            # Initialize emotion display
            emotion_display = EmotionDisplay()

            self.logger.debug(f"Initialize Components Completed")
            
            return chat_box, audio_recorder, emotion_display
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            st.error("Error initializing application components. Please refresh the page.")
            raise

    def handle_audio_recording(self, audio_recorder: AudioRecorder):
        """Handle audio recording and processing"""
        try:
            footer = st.container()
            with footer:
                col1, col2 = st.columns([1, 9])
                with col1:
                    audio_bytes = audio_recorder.record()
                    
                if audio_bytes and not audio_recorder.is_processing:
                    with st.spinner("Processing your message..."):
                        audio_recorder.process_recording(audio_bytes)
            
            # Float the footer
            footer.float("bottom: 0rem;")
            
        except Exception as e:
            self.logger.error(f"Error in audio recording: {e}")
            st.error("Error processing audio. Please try again.")

    def run(self):
        """Main application entry point"""
        try:       
            # Setup page
            self.setup_page_config()
            self.load_custom_css()
            
            # Initialize session state
            initialize_session_state()
            
            # Initialize components with dependencies
            chat_box, audio_recorder, emotion_display = self.initialize_components()
            
            # Main title
            st.title("TAFEP Voice Assistant 🎙️")
            
            # Chat display area
            chat_container = st.container()
            with chat_container:
                chat_box.display_messages()
            
            # Handle audio recording
            self.handle_audio_recording(audio_recorder)
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            st.error("An unexpected error occurred. Please refresh the page.")

def main():
    """Application entry point"""
    try:
        setup_logging()
        app = TAFEPApp()
        app.run()
    except Exception as e:
        logging.error(f"Fatal application error: {e}")
        st.error("Fatal error occurred. Please contact support.")

if __name__ == "__main__":
    main()