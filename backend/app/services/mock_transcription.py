import logging
import asyncio
from pathlib import Path

from app.models.schemas import TranscriptResult, TranscriptSegment
from app.services.transcription import TranscriptionService, TranscriptionError

logger = logging.getLogger(__name__)


class MockTranscriptionService(TranscriptionService):
    """
    Mock transcription service for local development.
    
    Returns realistic mock transcript data without making actual API calls.
    Useful for development to avoid API costs.
    """
    
    def __init__(self):
        logger.info("Using MockTranscriptionService - no API calls will be made")
    
    def get_name(self) -> str:
        return "Mock Transcription Service (Development)"
    
    async def transcribe(self, audio_path: Path) -> TranscriptResult:
        """
        Mock transcription that simulates API behavior.
        
        Args:
            audio_path: Path to the audio file (not actually used, but validated)
            
        Returns:
            TranscriptResult with mock transcription data
            
        Raises:
            TranscriptionError: If file doesn't exist (to match real behavior)
        """
        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_path}")
        
        # Simulate processing time (like a real API call)
        await asyncio.sleep(0.5)
        
        # Get filename for context
        filename = audio_path.name
        
        # Generate realistic mock transcript with segments
        # You can customize this to return different mock data
        mock_text = (
            f"This is a mock transcription for {filename}. "
            "In a real scenario, this would be the actual transcribed text from the audio file. "
            "The mock service allows you to develop and test without making actual API calls to OpenAI. "
            "This helps avoid costs during local development."
        )
        
        # Create realistic segments with timestamps
        segments = [
            TranscriptSegment(
                start=0.0,
                end=5.2,
                text="This is a mock transcription for the audio file."
            ),
            TranscriptSegment(
                start=5.2,
                end=12.8,
                text="In a real scenario, this would be the actual transcribed text from the audio file."
            ),
            TranscriptSegment(
                start=12.8,
                end=20.5,
                text="The mock service allows you to develop and test without making actual API calls to OpenAI."
            ),
            TranscriptSegment(
                start=20.5,
                end=25.0,
                text="This helps avoid costs during local development."
            ),
        ]
        
        # Estimate duration based on file size or use a default
        try:
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            # Rough estimate: ~1MB per minute of audio (varies by format)
            estimated_duration = max(25.0, file_size_mb * 60)
        except:
            estimated_duration = 25.0
        
        result = TranscriptResult(
            text=mock_text,
            segments=segments,
            language="en",
            duration=estimated_duration
        )
        
        logger.info(f"Mock transcription completed for {audio_path}")
        return result
