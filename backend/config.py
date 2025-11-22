from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # Database Configuration
    database_url: str = "postgresql://user:password@localhost:5432/audiobot"

    # ElevenLabs API Configuration
    elevenlabs_api_key: str
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default Rachel voice

    # FastAPI Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True


settings = Settings()
