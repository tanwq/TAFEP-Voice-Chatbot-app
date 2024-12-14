import streamlit as st
import logging
from typing import List, Tuple
from datetime import datetime

class EmotionDisplay:
    def __init__(self):
        """Initialize emotion display component"""
        self.logger = logging.getLogger(__name__)
        self.MAX_EMOTIONS = 5

    def display(self, emotions: List[tuple]) -> None:
        """Display emotions with proper validation and error handling"""
        if not emotions:
            return

        try:
            # Validate and limit emotions
            valid_emotions = self._validate_emotions(emotions)
            display_emotions = valid_emotions[:self.MAX_EMOTIONS]

            # Create columns and display emotions
            cols = st.columns(len(display_emotions))
            for col, (emotion, score) in zip(cols, display_emotions):
                with col:
                    self._display_emotion_metric(emotion, score)

        except Exception as e:
            self.logger.error(f"Error displaying emotions: {e}")

    def _validate_emotions(self, emotions: List[tuple]) -> List[tuple]:
        """Validate emotion data"""
        valid_emotions = []
        for emotion, score in emotions:
            try:
                if isinstance(score, (int, float)) and 0 <= score <= 1:
                    valid_emotions.append((emotion.lower(), float(score)))
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid emotion data: {emotion}, {score}")
        return valid_emotions

    def _display_emotion_metric(self, emotion: str, score: float) -> None:
        """Display single emotion metric"""
        try:
            st.metric(
                label=emotion.capitalize(),
                value=f"{score:.1%}",
                delta=None,
            )
        except Exception as e:
            self.logger.error(f"Error displaying emotion metric: {e}")