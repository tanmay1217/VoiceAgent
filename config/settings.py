"""Configuration settings for the voice assistant."""
from pydantic_settings import BaseSettings
from pathlib import Path
import os
from dotenv import load_dotenv

# Project root directory
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
CONFIG_DIR = ROOT_DIR / "config"
env_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Auto Dealership Voice Assistant"
    VERSION: str = "1.0.0"
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Default to gpt-4o-mini (faster & cheaper)
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    AZURE_SPEECH_KEY: str = os.getenv("AZURE_SPEECH_KEY", "")
    AZURE_SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "eastus")
    
    SPEECH_LANGUAGE: str = os.getenv("SPEECH_LANGUAGE", "en-US")
    SPEECH_SAMPLE_RATE: int = 16000
    
    TTS_VOICE_NAME: str = os.getenv("TTS_VOICE_NAME", "en-US-JennyNeural")
    TTS_SPEAKING_RATE: str = os.getenv("TTS_SPEAKING_RATE", "1.0")
    TTS_PITCH: str = os.getenv("TTS_PITCH", "0%")
    
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'bookings.db'}"
    
    KNOWLEDGE_BASE_PATH: str = str(DATA_DIR / "knowledge_base.json")
    
    MAX_CONVERSATION_TURNS: int = 10
    AGENT_TIMEOUT_SECONDS: int = 30
    AUDIO_CHUNK_SIZE: int = 1024
    AUDIO_FORMAT: int = 8  # pyaudio.paInt16
    AUDIO_CHANNELS: int = 1
    RECORD_SECONDS: int = 5
    
    class Config:
        case_sensitive = True

settings = Settings()

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)