import json
import logging
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import select, func, union_all, literal, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Transcript
from app.models.schemas import (
    TranscriptMetadata,
    TranscriptResult,
    TranscriptListItem,
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

    async def list_transcripts_by_batch_id_with_content(
        self, batch_id: str
    ) -> list[tuple[TranscriptMetadata, TranscriptResult]]:
        """
        List transcripts for a batch with their content (completed only).
        Returns list of (metadata, transcript_content) for building downloads.
        """
        if self.db:
            return await self._list_by_batch_with_content_in_session(
                self.db, batch_id
            )
        from app.database import async_session_maker
        async with async_session_maker() as session:
            return await self._list_by_batch_with_content_in_session(
                session, batch_id
            )

    async def _list_by_batch_with_content_in_session(
        self,
        session: AsyncSession,
        batch_id: str,
    ) -> list[tuple[TranscriptMetadata, TranscriptResult]]:
        """Internal: list batch transcripts with content in session."""
        result = await session.execute(
            select(Transcript)
            .where(Transcript.batch_id == batch_id)
            .order_by(Transcript.relative_path)
        )
        rows = result.scalars().all()
        out: list[tuple[TranscriptMetadata, TranscriptResult]] = []
        for t in rows:
            if (
                t.status == TranscriptionStatus.COMPLETED.value
                and t.transcript_content is not None
            ):
                out.append(
                    (self._db_to_metadata(t), TranscriptResult(**t.transcript_content))
                )
        return out

    async def list_transcript_groups(
        self,
        limit: int = 20,
        cursor: Optional[datetime] = None,
    ) -> tuple[list[dict], Optional[str], bool]:
        """
        Return paginated transcript groups.

        A group is either a single transcript (batch_id IS NULL) or all
        transcripts sharing the same batch_id.  Groups are ordered by
        created_at DESC (newest first) and paginated via a cursor (the
        created_at timestamp of the last group on the previous page).

        Returns (groups, next_cursor, has_more) where each group is a dict
        with keys: group_type, batch_id, created_at, transcripts.
        """
        if self.db:
            return await self._list_transcript_groups_in_session(
                self.db, limit, cursor
            )
        from app.database import async_session_maker
        async with async_session_maker() as session:
            return await self._list_transcript_groups_in_session(
                session, limit, cursor
            )

    async def _list_transcript_groups_in_session(
        self,
        session: AsyncSession,
        limit: int,
        cursor: Optional[datetime],
    ) -> tuple[list[dict], Optional[str], bool]:
        # Step 1: find distinct groups with their representative created_at
        batch_groups = (
            select(
                Transcript.batch_id.label("group_key"),
                literal("batch").label("group_type"),
                func.min(Transcript.created_at).label("group_created_at"),
            )
            .where(Transcript.batch_id.isnot(None))
            .group_by(Transcript.batch_id)
        )

        individual_groups = (
            select(
                Transcript.id.label("group_key"),
                literal("individual").label("group_type"),
                Transcript.created_at.label("group_created_at"),
            )
            .where(Transcript.batch_id.is_(None))
        )

        groups_query = union_all(batch_groups, individual_groups).subquery("groups")

        stmt = (
            select(
                groups_query.c.group_key,
                groups_query.c.group_type,
                groups_query.c.group_created_at,
            )
            .order_by(groups_query.c.group_created_at.desc())
            .limit(limit + 1)
        )

        if cursor is not None:
            stmt = stmt.where(groups_query.c.group_created_at < cursor)

        result = await session.execute(stmt)
        rows = result.all()

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        if not rows:
            return [], None, False

        # Step 2: collect keys and fetch transcript rows
        batch_ids = [r.group_key for r in rows if r.group_type == "batch"]
        individual_ids = [r.group_key for r in rows if r.group_type == "individual"]

        conditions = []
        if batch_ids:
            conditions.append(Transcript.batch_id.in_(batch_ids))
        if individual_ids:
            conditions.append(
                (Transcript.batch_id.is_(None)) & (Transcript.id.in_(individual_ids))
            )

        detail_stmt = (
            select(
                Transcript.id,
                Transcript.filename,
                Transcript.status,
                Transcript.created_at,
                Transcript.duration,
                Transcript.relative_path,
                Transcript.batch_id,
            )
            .where(or_(*conditions))
            .order_by(Transcript.created_at.desc())
        )

        detail_result = await session.execute(detail_stmt)
        detail_rows = detail_result.all()

        # Build lookup: batch_id -> list[TranscriptListItem], id -> TranscriptListItem
        batch_map: dict[str, list[TranscriptListItem]] = {}
        individual_map: dict[str, TranscriptListItem] = {}

        for row in detail_rows:
            item = TranscriptListItem(
                id=row.id,
                filename=row.filename,
                status=row.status,
                created_at=row.created_at,
                duration=row.duration,
                relative_path=row.relative_path,
                batch_id=row.batch_id,
            )
            if row.batch_id:
                batch_map.setdefault(row.batch_id, []).append(item)
            else:
                individual_map[row.id] = item

        # Assemble groups in the original sorted order
        groups = []
        for r in rows:
            if r.group_type == "batch":
                transcripts = batch_map.get(r.group_key, [])
                groups.append({
                    "group_type": "batch",
                    "batch_id": r.group_key,
                    "created_at": r.group_created_at,
                    "transcripts": transcripts,
                })
            else:
                item = individual_map.get(r.group_key)
                if item:
                    groups.append({
                        "group_type": "individual",
                        "batch_id": None,
                        "created_at": r.group_created_at,
                        "transcripts": [item],
                    })

        next_cursor = (
            rows[-1].group_created_at.isoformat() if has_more else None
        )
        return groups, next_cursor, has_more

    async def list_in_progress(self) -> list[dict]:
        """Return lightweight status info for all in-progress transcripts."""
        if self.db:
            return await self._list_in_progress_in_session(self.db)
        from app.database import async_session_maker
        async with async_session_maker() as session:
            return await self._list_in_progress_in_session(session)

    async def _list_in_progress_in_session(
        self, session: AsyncSession
    ) -> list[dict]:
        in_progress_statuses = [
            TranscriptionStatus.PENDING.value,
            TranscriptionStatus.EXTRACTING_AUDIO.value,
            TranscriptionStatus.TRANSCRIBING.value,
        ]
        result = await session.execute(
            select(Transcript.id, Transcript.status, Transcript.batch_id).where(
                Transcript.status.in_(in_progress_statuses)
            )
        )
        return [
            {"id": row.id, "status": row.status, "batch_id": row.batch_id}
            for row in result.all()
        ]

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
