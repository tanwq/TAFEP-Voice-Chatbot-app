import streamlit as st

class ChatBox:
    def __init__(self):
        """Initialize the chat box component"""
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello, welcome to TAFEP! How may I assist you today?"}
            ]

    def display_messages(self):
        """Display all chat messages with emotions if available"""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if "emotions" in message and message["emotions"]:
                    self.display_emotions(message["emotions"])

    def display_emotions(self, emotions):
        """Display emotion analysis results in an expander"""
        with st.expander("View emotions"):
            for emotion, score in emotions:
                # Create a progress bar for each emotion
                st.progress(
                    score,
                    text=f"{emotion}: {score:.2%}"
                )

    def add_message(self, role, content, emotions=None):
        """Add a new message to the chat history"""
        message = {
            "role": role,
            "content": content
        }
        if emotions:
            message["emotions"] = emotions
        st.session_state.messages.append(message)

    def clear_chat(self):
        """Clear the chat history"""
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello, welcome to TAFEP! How may I assist you today?"}
        ]

    def get_last_message(self):
        """Get the last message from the chat history"""
        if st.session_state.messages:
            return st.session_state.messages[-1]
        return None

    def get_chat_history(self):
        """Get the full chat history"""
        return st.session_state.messages