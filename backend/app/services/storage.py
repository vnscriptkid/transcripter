import json
import logging
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Transcript
from app.models.schemas import (
    TranscriptMetadata,
    TranscriptResult,
    TranscriptionStatus,
)

logger = logging.getLogger(__name__)


class StorageService:
    """
    Database-based storage for transcripts using PostgreSQL.
    
    Stores transcript metadata and content in PostgreSQL database.
    Transcript content is stored as JSONB for efficient querying.
    """
    
    def __init__(self, db: Optional[AsyncSession] = None):
        """
        Initialize storage service.
        
        Args:
            db: Optional database session. If provided, will use this session
                and won't commit/close it. If None, will create a new session
                for each operation.
        """
        self.db = db
    
    def generate_id(self) -> str:
        """Generate a unique ID for a transcript."""
        return str(uuid.uuid4())[:8]
    
    async def create_transcript(
        self,
        transcript_id: str,
        filename: str,
        relative_path: Optional[str] = None,
        batch_id: Optional[str] = None,
    ) -> TranscriptMetadata:
        """
        Create a new transcript entry with pending status.

        Args:
            transcript_id: Unique ID for the transcript
            filename: Original filename of the uploaded video
            relative_path: Path relative to folder root (for folder uploads)
            batch_id: Groups transcripts from same folder upload

        Returns:
            TranscriptMetadata for the new transcript
        """
        if self.db:
            # Use provided session
            return await self._create_transcript_in_session(
                self.db, transcript_id, filename, relative_path, batch_id
            )
        else:
            # Create new session
            from app.database import async_session_maker
            async with async_session_maker() as session:
                return await self._create_transcript_in_session(
                    session, transcript_id, filename, relative_path, batch_id
                )
    
    async def _create_transcript_in_session(
        self,
        session: AsyncSession,
        transcript_id: str,
        filename: str,
        relative_path: Optional[str] = None,
        batch_id: Optional[str] = None,
    ) -> TranscriptMetadata:
        """Internal method to create transcript within a session."""
        now = datetime.utcnow()
        
        transcript = Transcript(
            id=transcript_id,
            filename=filename,
            status=TranscriptionStatus.PENDING.value,
            relative_path=relative_path,
            batch_id=batch_id,
            created_at=now,
            updated_at=now,
        )
        
        session.add(transcript)
        await session.commit()
        await session.refresh(transcript)
        
        logger.info(f"Created transcript entry: {transcript_id}")
        
        return self._db_to_metadata(transcript)
    
    async def update_status(
        self, 
        transcript_id: str, 
        status: TranscriptionStatus,
        error: Optional[str] = None
    ) -> TranscriptMetadata:
        """Update the status of a transcript."""
        if self.db:
            return await self._update_status_in_session(self.db, transcript_id, status, error)
        else:
            from app.database import async_session_maker
            async with async_session_maker() as session:
                return await self._update_status_in_session(session, transcript_id, status, error)
    
    async def _update_status_in_session(
        self,
        session: AsyncSession,
        transcript_id: str,
        status: TranscriptionStatus,
        error: Optional[str] = None,
    ) -> TranscriptMetadata:
        """Internal method to update status within a session."""
        result = await session.execute(
            select(Transcript).where(Transcript.id == transcript_id)
        )
        transcript = result.scalar_one_or_none()
        
        if transcript is None:
            raise ValueError(f"Transcript not found: {transcript_id}")
        
        transcript.status = status.value
        transcript.updated_at = datetime.utcnow()
        if error:
            transcript.error = error
        
        await session.commit()
        await session.refresh(transcript)
        
        return self._db_to_metadata(transcript)
    
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
        if self.db:
            return await self._save_transcript_in_session(self.db, transcript_id, result)
        else:
            from app.database import async_session_maker
            async with async_session_maker() as session:
                return await self._save_transcript_in_session(session, transcript_id, result)
    
    async def _save_transcript_in_session(
        self,
        session: AsyncSession,
        transcript_id: str,
        result: TranscriptResult,
    ) -> TranscriptMetadata:
        """Internal method to save transcript within a session."""
        db_result = await session.execute(
            select(Transcript).where(Transcript.id == transcript_id)
        )
        transcript = db_result.scalar_one_or_none()
        
        if transcript is None:
            raise ValueError(f"Transcript not found: {transcript_id}")
        
        # Save transcript content as JSONB
        transcript.transcript_content = result.model_dump()
        transcript.status = TranscriptionStatus.COMPLETED.value
        transcript.updated_at = datetime.utcnow()
        transcript.duration = result.duration
        transcript.language = result.language
        
        await session.commit()
        await session.refresh(transcript)
        
        logger.info(f"Saved transcript: {transcript_id}")
        return self._db_to_metadata(transcript)
    
    async def get_metadata(self, transcript_id: str) -> Optional[TranscriptMetadata]:
        """Get metadata for a transcript."""
        if self.db:
            return await self._get_metadata_in_session(self.db, transcript_id)
        else:
            from app.database import async_session_maker
            async with async_session_maker() as session:
                return await self._get_metadata_in_session(session, transcript_id)
    
    async def _get_metadata_in_session(
        self,
        session: AsyncSession,
        transcript_id: str,
    ) -> Optional[TranscriptMetadata]:
        """Internal method to get metadata within a session."""
        result = await session.execute(
            select(Transcript).where(Transcript.id == transcript_id)
        )
        transcript = result.scalar_one_or_none()
        
        if transcript is None:
            return None
        
        return self._db_to_metadata(transcript)
    
    async def get_transcript(self, transcript_id: str) -> Optional[TranscriptResult]:
        """Get the transcript content."""
        if self.db:
            return await self._get_transcript_in_session(self.db, transcript_id)
        else:
            from app.database import async_session_maker
            async with async_session_maker() as session:
                return await self._get_transcript_in_session(session, transcript_id)
    
    async def _get_transcript_in_session(
        self,
        session: AsyncSession,
        transcript_id: str,
    ) -> Optional[TranscriptResult]:
        """Internal method to get transcript within a session."""
        result = await session.execute(
            select(Transcript).where(Transcript.id == transcript_id)
        )
        transcript = result.scalar_one_or_none()
        
        if transcript is None or transcript.transcript_content is None:
            return None
        
        return TranscriptResult(**transcript.transcript_content)
    
    async def list_transcripts(self) -> list[TranscriptMetadata]:
        """List all transcripts, sorted by created_at descending (newest first)."""
        if self.db:
            return await self._list_transcripts_in_session(self.db)
        else:
            from app.database import async_session_maker
            async with async_session_maker() as session:
                return await self._list_transcripts_in_session(session)
    
    async def _list_transcripts_in_session(
        self,
        session: AsyncSession,
    ) -> list[TranscriptMetadata]:
        """Internal method to list transcripts within a session."""
        result = await session.execute(
            select(Transcript).order_by(Transcript.created_at.desc())
        )
        transcripts = result.scalars().all()
        
        return [self._db_to_metadata(t) for t in transcripts]
    
    def _db_to_metadata(self, transcript: Transcript) -> TranscriptMetadata:
        """Convert database model to Pydantic metadata model."""
        return TranscriptMetadata(
            id=transcript.id,
            filename=transcript.filename,
            status=TranscriptionStatus(transcript.status),
            created_at=transcript.created_at,
            updated_at=transcript.updated_at,
            duration=transcript.duration,
            language=transcript.language,
            error=transcript.error,
            relative_path=transcript.relative_path,
            batch_id=transcript.batch_id,
        )
