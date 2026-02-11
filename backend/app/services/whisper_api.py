import logging
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI

from app.config import get_settings
from app.models.schemas import TranscriptResult, TranscriptSegment
from app.services.transcription import TranscriptionService, TranscriptionError

logger = logging.getLogger(__name__)


class WhisperAPIService(TranscriptionService):
    """
    Transcription service using OpenAI Whisper API.
    
    Cost: $0.006 per minute of audio
    Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm
    Max file size: 25 MB
    """
    
    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )
        
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    def get_name(self) -> str:
        return "OpenAI Whisper API"
    
    async def transcribe(self, audio_path: Path) -> TranscriptResult:
        """
        Transcribe audio using OpenAI Whisper API.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            TranscriptResult with text and segments
            
        Raises:
            TranscriptionError: If transcription fails
        """
        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_path}")
        
        # Check file size (25 MB limit for Whisper API)
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 25:
            raise TranscriptionError(
                f"Audio file too large ({file_size_mb:.1f} MB). "
                "Whisper API has a 25 MB limit."
            )
        
        logger.info(f"Transcribing {audio_path} using Whisper API")
        
        try:
            with open(audio_path, "rb") as audio_file:
                # Use verbose_json to get timestamps
                response = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            # Parse segments from response (OpenAI returns TranscriptionSegment objects, not dicts)
            segments = []
            if hasattr(response, 'segments') and response.segments:
                for seg in response.segments:
                    segments.append(TranscriptSegment(
                        start=getattr(seg, 'start', 0) or 0,
                        end=getattr(seg, 'end', 0) or 0,
                        text=(getattr(seg, 'text', None) or '').strip()
                    ))
            
            result = TranscriptResult(
                text=response.text,
                segments=segments,
                language=getattr(response, 'language', None),
                duration=getattr(response, 'duration', None)
            )
            
            logger.info(f"Successfully transcribed {audio_path}")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            if "api_key" in str(e).lower():
                raise TranscriptionError("Invalid OpenAI API key")
            raise TranscriptionError(f"Transcription failed: {e}")
