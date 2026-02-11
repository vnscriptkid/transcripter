import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from app.config import get_settings
from app.models.schemas import (
    TranscriptMetadata,
    TranscriptResult,
    TranscriptionStatus,
)

logger = logging.getLogger(__name__)


class StorageService:
    """
    Simple file-based storage for transcripts.
    
    Each transcript is stored as:
    - transcripts/{id}/metadata.json - Metadata about the transcript
    - transcripts/{id}/transcript.json - The actual transcript content
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.transcripts_dir = self.settings.transcripts_dir
    
    def generate_id(self) -> str:
        """Generate a unique ID for a transcript."""
        return str(uuid.uuid4())[:8]
    
    def _get_transcript_dir(self, transcript_id: str) -> Path:
        """Get the directory for a specific transcript."""
        return self.transcripts_dir / transcript_id
    
    def _get_metadata_path(self, transcript_id: str) -> Path:
        """Get the metadata file path for a transcript."""
        return self._get_transcript_dir(transcript_id) / "metadata.json"
    
    def _get_transcript_path(self, transcript_id: str) -> Path:
        """Get the transcript file path."""
        return self._get_transcript_dir(transcript_id) / "transcript.json"
    
    async def create_transcript(
        self, 
        transcript_id: str, 
        filename: str
    ) -> TranscriptMetadata:
        """
        Create a new transcript entry with pending status.
        
        Args:
            transcript_id: Unique ID for the transcript
            filename: Original filename of the uploaded video
            
        Returns:
            TranscriptMetadata for the new transcript
        """
        transcript_dir = self._get_transcript_dir(transcript_id)
        transcript_dir.mkdir(parents=True, exist_ok=True)
        
        now = datetime.utcnow()
        metadata = TranscriptMetadata(
            id=transcript_id,
            filename=filename,
            status=TranscriptionStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        
        await self._save_metadata(transcript_id, metadata)
        logger.info(f"Created transcript entry: {transcript_id}")
        
        return metadata
    
    async def update_status(
        self, 
        transcript_id: str, 
        status: TranscriptionStatus,
        error: Optional[str] = None
    ) -> TranscriptMetadata:
        """Update the status of a transcript."""
        metadata = await self.get_metadata(transcript_id)
        if metadata is None:
            raise ValueError(f"Transcript not found: {transcript_id}")
        
        metadata.status = status
        metadata.updated_at = datetime.utcnow()
        if error:
            metadata.error = error
        
        await self._save_metadata(transcript_id, metadata)
        return metadata
    
    async def save_transcript(
        self, 
        transcript_id: str, 
        result: TranscriptResult
    ) -> TranscriptMetadata:
        """
        Save a completed transcript.
        
        Args:
            transcript_id: ID of the transcript
            result: Transcription result to save
            
        Returns:
            Updated metadata
        """
        transcript_path = self._get_transcript_path(transcript_id)
        
        # Save transcript content
        with open(transcript_path, "w") as f:
            json.dump(result.model_dump(), f, indent=2)
        
        # Update metadata
        metadata = await self.get_metadata(transcript_id)
        if metadata:
            metadata.status = TranscriptionStatus.COMPLETED
            metadata.updated_at = datetime.utcnow()
            metadata.duration = result.duration
            metadata.language = result.language
            await self._save_metadata(transcript_id, metadata)
        
        logger.info(f"Saved transcript: {transcript_id}")
        return metadata
    
    async def get_metadata(self, transcript_id: str) -> Optional[TranscriptMetadata]:
        """Get metadata for a transcript."""
        metadata_path = self._get_metadata_path(transcript_id)
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, "r") as f:
            data = json.load(f)
        
        return TranscriptMetadata(**data)
    
    async def get_transcript(self, transcript_id: str) -> Optional[TranscriptResult]:
        """Get the transcript content."""
        transcript_path = self._get_transcript_path(transcript_id)
        
        if not transcript_path.exists():
            return None
        
        with open(transcript_path, "r") as f:
            data = json.load(f)
        
        return TranscriptResult(**data)
    
    async def list_transcripts(self) -> list[TranscriptMetadata]:
        """List all transcripts."""
        transcripts = []
        
        if not self.transcripts_dir.exists():
            return transcripts
        
        for transcript_dir in self.transcripts_dir.iterdir():
            if transcript_dir.is_dir():
                metadata = await self.get_metadata(transcript_dir.name)
                if metadata:
                    transcripts.append(metadata)
        
        # Sort by created_at descending (newest first)
        transcripts.sort(key=lambda x: x.created_at, reverse=True)
        return transcripts
    
    async def _save_metadata(
        self, 
        transcript_id: str, 
        metadata: TranscriptMetadata
    ) -> None:
        """Save metadata to file."""
        metadata_path = self._get_metadata_path(transcript_id)
        
        with open(metadata_path, "w") as f:
            json.dump(metadata.model_dump(mode='json'), f, indent=2, default=str)
