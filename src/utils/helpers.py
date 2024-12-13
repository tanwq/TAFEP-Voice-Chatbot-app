import re
import logging
from pathlib import Path
from datetime import datetime
import streamlit as st
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def normalize_string(input_string: str) -> str:
    """
    Remove special characters and convert to lowercase
    
    Args:
        input_string (str): Input string to normalize
        
    Returns:
        str: Normalized string
    """
    return re.sub(r'[^a-zA-Z]', '', input_string).lower()

def format_conversation_for_email(conversation_repository: List[Dict[str, Any]]) -> str:
    """
    Format conversation history for email
    
    Args:
        conversation_repository (List[Dict]): List of conversation messages
        
    Returns:
        str: Formatted conversation string
    """
    formatted = "\nConversation Details:\n"
    formatted += "-" * 50 + "\n"
    
    for entry in conversation_repository:
        role = "User" if entry["role"] == "user" else "TAFEP Advisor"
        formatted += f"{role}: {entry['content']}\n"
        if "emotions" in entry and entry["emotions"]:
            emotions_str = ", ".join([f"{e}: {s:.1%}" for e, s in entry["emotions"]])
            formatted += f"Emotions detected: {emotions_str}\n"
        formatted += "-" * 50 + "\n"
    
    return formatted

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello, welcome to TAFEP! How may I assist you today?"}
        ]
    
    if "conversation_state" not in st.session_state:
        st.session_state.conversation_state = {
            "issue_established": False,
            "discrimination_type_categorized": False,
            "probe_counter": 0,
            "probing_completed": False,
            "user_agreed_to_file_case": False
        }
    
    if "recording_state" not in st.session_state:
        st.session_state.recording_state = {
            "is_recording": False,
            "start_time": None,
            "audio_data": []
        }

def save_debug_info(data: Any, category: str) -> Path:
    """
    Save debug information to file
    
    Args:
        data: Data to save
        category (str): Debug category
        
    Returns:
        Path: Path to saved file
    """
    try:
        # Create debug directory if it doesn't exist
        debug_dir = Path("debug")
        category_dir = debug_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = category_dir / f"{category}_{timestamp}.txt"
        
        # Save data
        with open(file_path, 'w') as f:
            f.write(str(data))
            
        logger.debug(f"Saved debug info to {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error saving debug info: {e}")
        return None

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string
    
    Args:
        seconds (float): Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def clean_text(text: str) -> str:
    """
    Clean and normalize text input
    
    Args:
        text (str): Input text
        
    Returns:
        str: Cleaned text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove special characters except punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text.strip()

def get_emotion_color(emotion: str) -> str:
    """
    Get color code for emotion visualization
    
    Args:
        emotion (str): Emotion name
        
    Returns:
        str: Color hex code
    """
    emotion_colors = {
        "angry": "#FF4D4D",
        "sad": "#4D79FF",
        "happy": "#FFD700",
        "neutral": "#808080",
        "frustrated": "#FF6B6B",
        "concerned": "#9370DB"
    }
    return emotion_colors.get(emotion.lower(), "#808080")

def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def create_case_reference() -> str:
    """
    Generate unique case reference number
    
    Returns:
        str: Case reference number
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TAFEP-{timestamp}"