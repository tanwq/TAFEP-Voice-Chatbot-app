import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables at config initialization
load_dotenv(override=True)

class Config:
    """Application configuration"""
    
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent
    DEBUG_DIR = BASE_DIR / "debug"
    LOGS_DIR = BASE_DIR / "logs"
    TEMP_DIR = BASE_DIR / "temp"
    
    # API Keys and Authentication
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    
    # Hume AI Settings
    HUME_API_KEY = os.getenv('HUME_API_KEY')
    HUME_SECRET_KEY = os.getenv('HUME_SECRET_KEY')
    HUME_CONFIG_ID = os.getenv('HUME_CONFIG_ID')
    HUME_API_HOST = os.getenv('HUME_API_HOST')
    
    # Google Cloud Settings
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    # AI Model Settings
    AI_MODEL = os.getenv('AI_MODEL')
    AI_MODEL_VERSION = os.getenv('AI_MODEL_VERSION')
    
    # Audio Settings
    SAMPLE_RATE = int(os.getenv('SAMPLE_RATE')) if os.getenv('SAMPLE_RATE') else None
    SAMPLE_WIDTH = int(os.getenv('SAMPLE_WIDTH')) if os.getenv('SAMPLE_WIDTH') else None
    CHANNELS = int(os.getenv('CHANNELS')) if os.getenv('CHANNELS') else None
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE')) if os.getenv('CHUNK_SIZE') else None
    FORMAT = 'paInt16'  # PyAudio format constant
    SILENCE_THRESHOLD = int(os.getenv('SILENCE_THRESHOLD')) if os.getenv('SILENCE_THRESHOLD') else None
    MIN_AUDIO_LENGTH = float(os.getenv('MIN_AUDIO_LENGTH')) if os.getenv('MIN_AUDIO_LENGTH') else None
    MAX_SILENCE_DURATION = float(os.getenv('MAX_SILENCE_DURATION')) if os.getenv('MAX_SILENCE_DURATION') else None
    
    # TTS Settings
    TTS_VOICE = os.getenv('TTS_VOICE')
    TTS_MODEL = os.getenv('TTS_MODEL')
    
    # Development Settings
    DEBUG = os.getenv('DEBUG')
    LOG_LEVEL = os.getenv('LOG_LEVEL')
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else None
    ENVIRONMENT = os.getenv('ENVIRONMENT')
    
    # Application Settings
    PROBE_LIMIT = int(os.getenv('PROBE_LIMIT')) if os.getenv('PROBE_LIMIT') else None
    MAX_CONVERSATION_HISTORY = int(os.getenv('MAX_CONVERSATION_HISTORY')) if os.getenv('MAX_CONVERSATION_HISTORY') else None
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration settings"""
        required_vars = {
            'ANTHROPIC_API_KEY': 'Anthropic API key',
            'OPENAI_API_KEY': 'OpenAI API key',
            'ELEVENLABS_API_KEY': 'ElevenLabs API key',
            'HUME_API_KEY': 'Hume API key',
            'HUME_SECRET_KEY': 'Hume secret key',
            'HUME_CONFIG_ID': 'Hume config ID',
            'HUME_API_HOST': 'Hume API host',
            'GOOGLE_APPLICATION_CREDENTIALS': 'Google Cloud credentials path',
            'GOOGLE_CLOUD_PROJECT': 'Google Cloud project ID',
            'AI_MODEL': 'AI model selection',
            'AI_MODEL_VERSION': 'AI model version',
            'SAMPLE_RATE': 'Sample rate',
            'SAMPLE_WIDTH': 'Sample width',
            'CHANNELS': 'Audio channels',
            'CHUNK_SIZE': 'Chunk size',
            'SILENCE_THRESHOLD': 'Silence threshold',
            'MIN_AUDIO_LENGTH': 'Minimum audio length',
            'MAX_SILENCE_DURATION': 'Maximum silence duration',
            'TTS_VOICE': 'Text-to-speech voice',
            'TTS_MODEL': 'Text-to-speech model',
            'DEBUG': 'Debug mode',
            'LOG_LEVEL': 'Logging level',
            'PORT': 'Application port',
            'ENVIRONMENT': 'Environment type',
            'PROBE_LIMIT': 'Probe limit',
            'MAX_CONVERSATION_HISTORY': 'Maximum conversation history'
        }
        
        missing_vars = []
        for var, description in required_vars.items():
            if getattr(cls, var) is None:
                missing_vars.append(f"{description} ({var})")
        
        if missing_vars:
            raise ValueError(
                "Missing required environment variables:\n" +
                "\n".join(f"- {var}" for var in missing_vars) +
                "\nPlease check your .env file."
            )

        # Validate value constraints
        if cls.AI_MODEL not in ['AnthropicAI', 'OpenAI']:
            raise ValueError("AI_MODEL must be either 'AnthropicAI' or 'OpenAI'")
            
        if cls.DEBUG.lower() not in ['true', 'false']:
            raise ValueError("DEBUG must be either 'True' or 'False'")
            
        if not os.path.exists(cls.GOOGLE_APPLICATION_CREDENTIALS):
            raise ValueError(f"Google credentials file not found at: {cls.GOOGLE_APPLICATION_CREDENTIALS}")
    
    @classmethod
    def get_websocket_url(cls, access_token: str) -> str:
        """Generate WebSocket URL with access token"""
        return (
            f"wss://{cls.HUME_API_HOST}/v0/evi/chat?"
            f"access_token={access_token}&config_id={cls.HUME_CONFIG_ID}"
        )
    
    @classmethod
    def setup_directories(cls):
        """Create necessary application directories"""
        directories = [cls.DEBUG_DIR, cls.LOGS_DIR, cls.TEMP_DIR]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

# Initialize important settings on import
Config.validate_config()
Config.setup_directories()