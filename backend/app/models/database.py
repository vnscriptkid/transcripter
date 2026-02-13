from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Float, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.schemas import TranscriptionStatus


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Transcript(Base):
    """Database model for transcript metadata and content."""
    
    __tablename__ = "transcripts"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(8), primary_key=True)
    
    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    relative_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    batch_id: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, index=True)
    
    # Status and processing
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Transcription results
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Transcript content stored as JSONB
    transcript_content: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_transcripts_batch_id", "batch_id"),
        Index("idx_transcripts_status", "status"),
        Index("idx_transcripts_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Transcript(id={self.id}, filename={self.filename}, status={self.status})>"
