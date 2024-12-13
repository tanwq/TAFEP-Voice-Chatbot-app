from audio_recorder_streamlit import audio_recorder
import streamlit as st
from ..services.websocket import WebSocketConnection
from ..conversation.handler import ConversationHandler

class AudioRecorder:
    def record(self):
        return audio_recorder(
            pause_threshold=2.0,
            icon_size="2x",
            recording_color="#e21e1e",
            neutral_color="#0096db"
        )
    
    def process_recording(self, audio_bytes):
        with st.spinner("Processing your message..."):
            # Process audio through WebSocket
            websocket = WebSocketConnection()
            response = websocket.process_audio(audio_bytes)
            
            if response:
                # Update chat with user message and emotions
                st.session_state.messages.append({
                    "role": "user",
                    "content": response["text"],
                    "emotions": response["emotions"]
                })
                
                # Generate bot response
                conversation = ConversationHandler()
                bot_response = conversation.generate_response(response["text"])
                
                # Add bot response to chat
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": bot_response
                })
