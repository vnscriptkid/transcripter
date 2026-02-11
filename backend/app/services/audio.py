import asyncio
import subprocess
import shutil
from pathlib import Path
from typing import Optional
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


class AudioExtractionError(Exception):
    """Exception raised when audio extraction fails."""
    pass


class AudioExtractor:
    """Extracts audio from video files using FFmpeg."""
    
    def __init__(self):
        self.settings = get_settings()
        self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> None:
        """Check if FFmpeg is installed."""
        if not shutil.which("ffmpeg"):
            raise RuntimeError(
                "FFmpeg is not installed or not in PATH. "
                "Please install FFmpeg to use this application."
            )
    
    async def extract_audio(
        self, 
        video_path: Path, 
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Extract audio from a video file.
        
        Args:
            video_path: Path to the video file
            output_path: Optional output path. If not provided, uses same name with audio extension.
            
        Returns:
            Path to the extracted audio file
            
        Raises:
            AudioExtractionError: If extraction fails
        """
        if not video_path.exists():
            raise AudioExtractionError(f"Video file not found: {video_path}")
        
        if output_path is None:
            output_path = video_path.with_suffix(f".{self.settings.audio_format}")
        
        # FFmpeg command to extract audio
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "libmp3lame" if self.settings.audio_format == "mp3" else "aac",
            "-ab", self.settings.audio_bitrate,
            "-y",  # Overwrite output file
            str(output_path)
        ]
        
        logger.info(f"Extracting audio from {video_path} to {output_path}")
        
        try:
            # Run FFmpeg asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"FFmpeg error: {error_msg}")
                raise AudioExtractionError(f"FFmpeg failed: {error_msg}")
            
            if not output_path.exists():
                raise AudioExtractionError("Audio file was not created")
            
            logger.info(f"Successfully extracted audio to {output_path}")
            return output_path
            
        except asyncio.CancelledError:
            logger.warning("Audio extraction was cancelled")
            raise
        except Exception as e:
            if isinstance(e, AudioExtractionError):
                raise
            logger.error(f"Unexpected error during audio extraction: {e}")
            raise AudioExtractionError(f"Audio extraction failed: {e}")
    
    async def get_duration(self, file_path: Path) -> Optional[float]:
        """
        Get the duration of a media file in seconds.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            Duration in seconds, or None if it cannot be determined
        """
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(file_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await process.communicate()
            
            if process.returncode == 0 and stdout:
                duration_str = stdout.decode().strip()
                return float(duration_str)
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not determine duration: {e}")
            return None
