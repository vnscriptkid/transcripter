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
    relative_path: Optional[str] = None  # Path relative to folder root (folder uploads)
    batch_id: Optional[str] = None  # Groups transcripts from same folder upload


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
    relative_path: Optional[str] = None
    batch_id: Optional[str] = None


class FolderUploadAcceptedFile(BaseModel):
    """Accepted file in folder upload response."""
    id: str
    relative_path: str


class FolderUploadResponse(BaseModel):
    """Response after uploading a folder."""
    batch_id: str
    message: str
    accepted_count: int
    skipped_count: int
    accepted_files: list[FolderUploadAcceptedFile]


class TranscriptGroup(BaseModel):
    """A logical group: either a single transcript or a batch."""
    group_type: str  # "individual" or "batch"
    batch_id: Optional[str] = None
    created_at: datetime
    transcripts: list[TranscriptListItem]


class PaginatedTranscriptGroupsResponse(BaseModel):
    """Paginated response of transcript groups."""
    groups: list[TranscriptGroup]
    next_cursor: Optional[str] = None
    has_more: bool


class InProgressStatusItem(BaseModel):
    """Lightweight status for an in-progress transcript."""
    id: str
    status: TranscriptionStatus
    batch_id: Optional[str] = None


class InProgressResponse(BaseModel):
    """Response for bulk in-progress status check."""
    transcripts: list[InProgressStatusItem]
