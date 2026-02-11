import asyncio
import logging
import aiofiles
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks

from app.config import get_settings
from app.models.schemas import (
    TranscriptionStatus,
    TranscriptResponse,
    TranscriptListItem,
    UploadResponse,
    StatusResponse,
)
from app.services import (
    AudioExtractor,
    AudioExtractionError,
    WhisperAPIService,
    TranscriptionError,
    StorageService,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Service instances
storage = StorageService()


def get_transcription_service() -> WhisperAPIService:
    """Get the transcription service instance."""
    return WhisperAPIService()


async def process_video(
    transcript_id: str,
    video_path: Path,
) -> None:
    """
    Background task to process a video file.
    
    1. Extract audio from video
    2. Transcribe audio
    3. Save transcript
    """
    audio_extractor = AudioExtractor()
    
    try:
        # Update status to extracting audio
        await storage.update_status(transcript_id, TranscriptionStatus.EXTRACTING_AUDIO)
        
        # Extract audio
        audio_path = await audio_extractor.extract_audio(video_path)
        
        # Update status to transcribing
        await storage.update_status(transcript_id, TranscriptionStatus.TRANSCRIBING)
        
        # Transcribe
        transcription_service = get_transcription_service()
        result = await transcription_service.transcribe(audio_path)
        
        # Save transcript
        await storage.save_transcript(transcript_id, result)
        
        # Cleanup audio file
        if audio_path.exists():
            audio_path.unlink()
        
        logger.info(f"Successfully processed video: {transcript_id}")
        
    except AudioExtractionError as e:
        logger.error(f"Audio extraction failed for {transcript_id}: {e}")
        await storage.update_status(
            transcript_id, 
            TranscriptionStatus.FAILED,
            error=str(e)
        )
    except TranscriptionError as e:
        logger.error(f"Transcription failed for {transcript_id}: {e}")
        await storage.update_status(
            transcript_id,
            TranscriptionStatus.FAILED,
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error processing {transcript_id}: {e}")
        await storage.update_status(
            transcript_id,
            TranscriptionStatus.FAILED,
            error=f"Unexpected error: {e}"
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload a video file for transcription.
    
    The video will be processed in the background:
    1. Audio is extracted using FFmpeg
    2. Audio is sent to OpenAI Whisper API for transcription
    3. Transcript is saved and can be retrieved via /transcripts/{id}
    """
    settings = get_settings()
    
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    extension = file.filename.split(".")[-1].lower()
    if extension not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{extension}' not allowed. Allowed: {settings.allowed_extensions}"
        )
    
    # Generate ID and create transcript entry
    transcript_id = storage.generate_id()
    await storage.create_transcript(transcript_id, file.filename)
    
    # Save uploaded file
    video_path = settings.uploads_dir / f"{transcript_id}.{extension}"
    
    try:
        async with aiofiles.open(video_path, "wb") as out_file:
            content = await file.read()
            
            # Check file size
            file_size_mb = len(content) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large ({file_size_mb:.1f} MB). Max size: {settings.max_file_size_mb} MB"
                )
            
            await out_file.write(content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    # Start background processing
    background_tasks.add_task(process_video, transcript_id, video_path)
    
    return UploadResponse(
        id=transcript_id,
        message="Video uploaded successfully. Transcription in progress.",
        status=TranscriptionStatus.PENDING
    )


@router.get("/transcripts", response_model=list[TranscriptListItem])
async def list_transcripts():
    """List all transcripts."""
    transcripts = await storage.list_transcripts()
    
    return [
        TranscriptListItem(
            id=t.id,
            filename=t.filename,
            status=t.status,
            created_at=t.created_at,
            duration=t.duration
        )
        for t in transcripts
    ]


@router.get("/transcripts/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(transcript_id: str):
    """Get a specific transcript with its content."""
    metadata = await storage.get_metadata(transcript_id)
    
    if metadata is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    transcript = None
    if metadata.status == TranscriptionStatus.COMPLETED:
        transcript = await storage.get_transcript(transcript_id)
    
    return TranscriptResponse(
        metadata=metadata,
        transcript=transcript
    )


@router.get("/transcripts/{transcript_id}/status", response_model=StatusResponse)
async def get_transcript_status(transcript_id: str):
    """Get the status of a transcript."""
    metadata = await storage.get_metadata(transcript_id)
    
    if metadata is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return StatusResponse(
        id=transcript_id,
        status=metadata.status,
        error=metadata.error
    )
