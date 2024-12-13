import streamlit as st
from streamlit_float import float_init
from src.components.chat_box import ChatBox
from src.components.recorder import AudioRecorder
from src.components.emotion_display import EmotionDisplay
from src.utils.logger import setup_logging
from src.conversation.handler import ConversationHandler

# Initialize logging
setup_logging()

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello, welcome to TAFEP! How may I assist you today?"}
        ]

def main():
    st.set_page_config(page_title="TAFEP Voice Assistant", page_icon="🎙️")
    
    # Initialize
    float_init()
    initialize_session_state()
    
    # Custom CSS
    with open('static/css/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # Main layout
    st.title("TAFEP Voice Assistant 🎙️")
    
    # Initialize components
    chat_box = ChatBox()
    audio_recorder = AudioRecorder()
    emotion_display = EmotionDisplay()
    
    # Chat display area
    chat_container = st.container()
    with chat_container:
        chat_box.display_messages()
    
    # Recording controls
    footer = st.container()
    with footer:
        col1, col2 = st.columns([1, 9])
        with col1:
            audio_bytes = audio_recorder.record()
            
        if audio_bytes:
            audio_recorder.process_recording(audio_bytes)
    
    # Float the footer
    footer.float("bottom: 0rem;")

if __name__ == "__main__":
    main()