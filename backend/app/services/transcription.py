from abc import ABC, abstractmethod
from pathlib import Path

from app.models.schemas import TranscriptResult


class TranscriptionService(ABC):
    """
    Abstract base class for transcription services.
    
    This interface allows easy switching between different transcription
    providers (OpenAI Whisper API, Google Speech-to-Text, AWS Transcribe, 
    local Whisper, etc.) without changing the rest of the application.
    """
    
    @abstractmethod
    async def transcribe(self, audio_path: Path) -> TranscriptResult:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to the audio file to transcribe
            
        Returns:
            TranscriptResult containing the transcription text and segments
            
        Raises:
            TranscriptionError: If transcription fails
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the transcription service."""
        pass


class TranscriptionError(Exception):
    """Exception raised when transcription fails."""
    pass
