import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AI
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4-turbo-preview")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_AI_API_KEY: str = os.getenv("GOOGLE_AI_API_KEY", "")

    # Voice
    STT_PROVIDER: str = os.getenv("STT_PROVIDER", "openai_whisper")
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "elevenlabs")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "")
    WAKE_WORD: str = os.getenv("WAKE_WORD", "nexa")
    PORCUPINE_KEY: str = os.getenv("PORCUPINE_ACCESS_KEY", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/nexa.db")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/memory")

    # Server
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "localhost")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key")
    ALLOW_TERMINAL: bool = os.getenv("ALLOW_TERMINAL_EXECUTION", "true").lower() == "true"
    ALLOW_FILE_DELETE: bool = os.getenv("ALLOW_FILE_DELETION", "false").lower() == "true"
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

    # Features
    ENABLE_PROACTIVE: bool = os.getenv("ENABLE_PROACTIVE_ASSISTANT", "true").lower() == "true"
    ENABLE_SCREEN_ANALYSIS: bool = os.getenv("ENABLE_SCREEN_ANALYSIS", "true").lower() == "true"
    ENABLE_PHONE_CONTROL: bool = os.getenv("ENABLE_PHONE_CONTROL", "true").lower() == "true"

    # Paths
    PLUGINS_PATH: str = os.getenv("PLUGINS_PATH", "./plugins")
    LOGS_PATH: str = os.getenv("LOGS_PATH", "./logs")
    TEMP_PATH: str = "./temp"

    # Smart Home
    HOME_ASSISTANT_URL: str = os.getenv("HOME_ASSISTANT_URL", "")
    HOME_ASSISTANT_TOKEN: str = os.getenv("HOME_ASSISTANT_TOKEN", "")

    # Integrations
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")

    def validate(self):
        errors = []
        if not self.AI_API_KEY and not self.OPENAI_API_KEY:
            errors.append("AI_API_KEY or OPENAI_API_KEY required")
        return errors
