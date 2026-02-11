# Video Transcriber

A cost-effective video transcription application using OpenAI Whisper API. Upload video files and get AI-powered transcripts with timestamps.

## Features

- Upload video files (MP4, AVI, MOV, MKV, WebM, M4V)
- Automatic audio extraction using FFmpeg
- Transcription using OpenAI Whisper API
- View transcripts with timestamps
- Copy transcript text to clipboard
- Real-time status updates

## Cost

- OpenAI Whisper API: **$0.006 per minute** of audio
- Example: 1 hour video = $0.36

## Prerequisites

- Python 3.10+
- Node.js 18+
- FFmpeg installed on system
- OpenAI API key

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH.

## Setup

### Backend

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with your OpenAI API key:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

5. Start the server:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000

### Frontend

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at http://localhost:5173

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload a video file for transcription |
| GET | `/api/transcripts` | List all transcripts |
| GET | `/api/transcripts/{id}` | Get a specific transcript |
| GET | `/api/transcripts/{id}/status` | Check transcription status |
| GET | `/health` | Health check |

## Project Structure

```
transcripter/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings
│   │   ├── api/
│   │   │   └── routes.py        # API endpoints
│   │   ├── services/
│   │   │   ├── transcription.py # Abstract interface
│   │   │   ├── whisper_api.py   # OpenAI implementation
│   │   │   ├── audio.py         # FFmpeg extraction
│   │   │   └── storage.py       # File storage
│   │   └── models/
│   │       └── schemas.py       # Pydantic models
│   ├── uploads/                 # Uploaded videos
│   ├── transcripts/             # Saved transcripts
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── UploadForm.jsx
│   │   │   ├── TranscriptList.jsx
│   │   │   └── TranscriptViewer.jsx
│   │   └── api/
│   │       └── client.js
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Extending the Application

### Adding a New Transcription Service

1. Create a new service in `backend/app/services/`:

```python
from app.services.transcription import TranscriptionService, TranscriptionError
from app.models.schemas import TranscriptResult

class NewTranscriptionService(TranscriptionService):
    async def transcribe(self, audio_path: Path) -> TranscriptResult:
        # Implement transcription logic
        pass
    
    def get_name(self) -> str:
        return "New Service"
```

2. Update `backend/app/api/routes.py` to use the new service.

### Adding YouTube Support (Future)

The application is designed to support multiple video sources. To add YouTube:

1. Install `yt-dlp`: `pip install yt-dlp`
2. Create a `YouTubeSource` class that downloads videos to a temp file
3. Add a new API endpoint for YouTube URLs

## License

MIT
