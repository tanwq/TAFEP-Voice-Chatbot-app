import streamlit as st

class EmotionDisplay:
    def display(self, emotions):
        if not emotions:
            return
            
        cols = st.columns(len(emotions))
        for col, (emotion, score) in zip(cols, emotions):
            with col:
                st.metric(
                    label=emotion,
                    value=f"{score:.1%}"
                )