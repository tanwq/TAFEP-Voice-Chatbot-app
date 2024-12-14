import streamlit as st
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

class ChatBox:
    def __init__(self):
        """Initialize the chat box component with proper state management"""
        self.logger = logging.getLogger(__name__)
        self.MAX_MESSAGES = 50
        self._initialize_session_state()

    def _initialize_session_state(self) -> None:
        """Initialize or verify session state"""
        try:
            if "messages" not in st.session_state:
                st.session_state.messages = [{
                    "role": "assistant",
                    "content": "Hello, welcome to TAFEP! How may I assist you today?",
                    "timestamp": datetime.now().isoformat(),
                    "id": "initial-message"
                }]
        except Exception as e:
            self.logger.error(f"Failed to initialize session state: {e}")
            raise

    def display_messages(self) -> None:
        """Display chat messages with error handling"""
        try:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
                    if "emotions" in message and message["emotions"]:
                        self._display_emotions(message["emotions"])
                    if "timestamp" in message:
                        st.caption(
                            f"Sent at {datetime.fromisoformat(message['timestamp']).strftime('%I:%M %p')}"
                        )
        except Exception as e:
            self.logger.error(f"Error displaying messages: {e}")
            st.error("Error displaying chat history. Please refresh the page.")

    def _display_emotions(self, emotions: List[tuple]) -> None:
        """Display emotion analysis with validation"""
        try:
            with st.expander("View emotions"):
                for emotion, score in emotions:
                    if not isinstance(score, (int, float)) or not 0 <= score <= 1:
                        self.logger.warning(f"Invalid emotion score: {score}")
                        continue
                    st.progress(
                        score,
                        text=f"{emotion.capitalize()}: {score:.2%}"
                    )
        except Exception as e:
            self.logger.error(f"Error displaying emotions: {e}")

    def add_message(self, role: str, content: str, emotions: Optional[List[tuple]] = None) -> bool:
        """Add message with validation and error handling"""
        try:
            if not self._validate_message(role, content):
                return False

            message = {
                "role": role,
                "content": content.strip(),
                "timestamp": datetime.now().isoformat(),
                "id": f"msg-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            }

            if emotions:
                message["emotions"] = self._validate_emotions(emotions)

            if len(st.session_state.messages) >= self.MAX_MESSAGES:
                st.session_state.messages.pop(0)

            st.session_state.messages.append(message)
            return True

        except Exception as e:
            self.logger.error(f"Error adding message: {e}")
            return False

    def _validate_message(self, role: str, content: str) -> bool:
        """Validate message inputs"""
        if role not in ["user", "assistant"]:
            self.logger.error(f"Invalid message role: {role}")
            return False
        if not content or not content.strip():
            self.logger.error("Empty message content")
            return False
        return True

    def _validate_emotions(self, emotions: List[tuple]) -> List[tuple]:
        """Validate emotion data"""
        return [
            (emotion, score) for emotion, score in emotions
            if isinstance(score, (int, float)) and 0 <= score <= 1
        ]

    def clear_chat(self) -> None:
        """Clear chat history safely"""
        try:
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Hello, welcome to TAFEP! How may I assist you today?",
                "timestamp": datetime.now().isoformat(),
                "id": "initial-message"
            }]
        except Exception as e:
            self.logger.error(f"Error clearing chat: {e}")
            st.error("Failed to clear chat history")

    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """Get last message safely"""
        try:
            return st.session_state.messages[-1] if st.session_state.messages else None
        except Exception as e:
            self.logger.error(f"Error retrieving last message: {e}")
            return None

    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get chat history safely"""
        try:
            return list(st.session_state.messages)
        except Exception as e:
            self.logger.error(f"Error retrieving chat history: {e}")
            return []