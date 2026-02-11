from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class TranscriptionStatus(str, Enum):
    """Status of a transcription job."""
    PENDING = "pending"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptSegment(BaseModel):
    """A segment of transcribed text with timing."""
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str


class TranscriptResult(BaseModel):
    """Result from transcription service."""
    text: str
    segments: list[TranscriptSegment] = []
    language: Optional[str] = None
    duration: Optional[float] = None


class TranscriptMetadata(BaseModel):
    """Metadata for a transcript."""
    id: str
    filename: str
    status: TranscriptionStatus
    created_at: datetime
    updated_at: datetime
    duration: Optional[float] = None
    language: Optional[str] = None
    error: Optional[str] = None


class TranscriptResponse(BaseModel):
    """Full transcript response."""
    metadata: TranscriptMetadata
    transcript: Optional[TranscriptResult] = None


class UploadResponse(BaseModel):
    """Response after uploading a video."""
    id: str
    message: str
    status: TranscriptionStatus


class StatusResponse(BaseModel):
    """Response for status check."""
    id: str
    status: TranscriptionStatus
    error: Optional[str] = None


class TranscriptListItem(BaseModel):
    """Item in transcript list."""
    id: str
    filename: str
    status: TranscriptionStatus
    created_at: datetime
    duration: Optional[float] = None
