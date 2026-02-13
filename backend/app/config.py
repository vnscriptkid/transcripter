import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # OpenAI API
    openai_api_key: str = ""
    
    # Development: Use mock transcription service to avoid API costs
    # Set USE_MOCK_TRANSCRIPTION=true in .env for local development
    use_mock_transcription: bool = False
    
    # Database - defaults to local PostgreSQL, can be overridden with DATABASE_URL env var
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/transcripter"
    
    # File storage paths
    base_dir: Path = Path(__file__).parent.parent
    uploads_dir: Path = base_dir / "uploads"
    transcripts_dir: Path = base_dir / "transcripts"
    
    # Audio extraction settings
    audio_format: str = "mp3"
    audio_bitrate: str = "128k"
    
    # API settings
    max_file_size_mb: int = 500
    allowed_extensions: list[str] = ["mp4", "avi", "mov", "mkv", "webm", "m4v"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @field_validator("database_url", mode="before")
    @classmethod
    def convert_database_url(cls, v):
        """Convert postgresql:// to postgresql+asyncpg:// for asyncpg driver."""
        if isinstance(v, str) and v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    
    # Create directories if they don't exist
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.transcripts_dir.mkdir(parents=True, exist_ok=True)
    
    return settings
