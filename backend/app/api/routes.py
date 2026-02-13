import json
import logging
import aiofiles
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.schemas import (
    TranscriptionStatus,
    TranscriptResponse,
    TranscriptListItem,
    UploadResponse,
    StatusResponse,
    FolderUploadResponse,
    FolderUploadAcceptedFile,
)
from app.services import (
    AudioExtractor,
    AudioExtractionError,
    WhisperAPIService,
    TranscriptionError,
    StorageService,
)
from app.database import async_session_maker

logger = logging.getLogger(__name__)
router = APIRouter()


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
    # Create a database session for background task
    async with async_session_maker() as db_session:
        storage = StorageService(db=db_session)
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
    db: AsyncSession = Depends(get_db),
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
    storage = StorageService(db=db)
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


@router.post("/upload-folder", response_model=FolderUploadResponse)
async def upload_folder(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    relative_paths: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a folder of video files for transcription.

    Accepts multiple files with their relative paths (from webkitRelativePath).
    Only video formats are processed; unsupported files are skipped.
    """
    settings = get_settings()

    try:
        paths_list = json.loads(relative_paths)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid relative_paths JSON")

    if not isinstance(paths_list, list) or len(paths_list) != len(files):
        raise HTTPException(
            status_code=400,
            detail="relative_paths must be a JSON array with same length as files"
        )

    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")

    storage = StorageService(db=db)
    batch_id = storage.generate_id()
    accepted_files_list: list[FolderUploadAcceptedFile] = []
    skipped_count = 0

    for file, rel_path in zip(files, paths_list):
        if not isinstance(rel_path, str):
            skipped_count += 1
            continue

        if not file.filename:
            skipped_count += 1
            continue

        extension = file.filename.split(".")[-1].lower()
        if extension not in settings.allowed_extensions:
            skipped_count += 1
            continue

        transcript_id = storage.generate_id()
        filename = Path(rel_path).name

        await storage.create_transcript(
            transcript_id,
            filename,
            relative_path=rel_path,
            batch_id=batch_id,
        )

        video_path = settings.uploads_dir / f"{transcript_id}.{extension}"

        try:
            content = await file.read()
            file_size_mb = len(content) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                skipped_count += 1
                continue

            async with aiofiles.open(video_path, "wb") as out_file:
                await out_file.write(content)
        except Exception as e:
            logger.error(f"Failed to save file {rel_path}: {e}")
            skipped_count += 1
            continue

        background_tasks.add_task(process_video, transcript_id, video_path)
        accepted_files_list.append(FolderUploadAcceptedFile(id=transcript_id, relative_path=rel_path))

    if len(accepted_files_list) == 0:
        raise HTTPException(
            status_code=400,
            detail=f"No video files to process. {skipped_count} file(s) skipped (unsupported format or errors)."
        )

    return FolderUploadResponse(
        batch_id=batch_id,
        message=f"Folder uploaded. {len(accepted_files_list)} video(s) queued for transcription, {skipped_count} skipped.",
        accepted_count=len(accepted_files_list),
        skipped_count=skipped_count,
        accepted_files=accepted_files_list,
    )


@router.get("/transcripts", response_model=list[TranscriptListItem])
async def list_transcripts(db: AsyncSession = Depends(get_db)):
    """List all transcripts."""
    storage = StorageService(db=db)
    transcripts = await storage.list_transcripts()
    
    return [
        TranscriptListItem(
            id=t.id,
            filename=t.filename,
            status=t.status,
            created_at=t.created_at,
            duration=t.duration,
            relative_path=t.relative_path,
            batch_id=t.batch_id,
        )
        for t in transcripts
    ]


@router.get("/transcripts/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(transcript_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific transcript with its content."""
    storage = StorageService(db=db)
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
async def get_transcript_status(transcript_id: str, db: AsyncSession = Depends(get_db)):
    """Get the status of a transcript."""
    storage = StorageService(db=db)
    metadata = await storage.get_metadata(transcript_id)
    
    if metadata is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return StatusResponse(
        id=transcript_id,
        status=metadata.status,
        error=metadata.error
    )
