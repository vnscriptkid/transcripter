# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

A full-stack video transcription platform. Users upload video files (MP4, AVI, MOV, MKV, WebM, M4V), audio is extracted via FFmpeg, and transcribed by OpenAI Whisper API. Supports Google OAuth login, batch folder uploads, and cursor-based paginated transcript management.

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 16, Alembic, PyJWT, google-auth
- **Frontend**: React 18, Vite, Google Identity Services
- **Infrastructure**: Docker, Docker Compose, Nginx (frontend), Uvicorn (backend), FFmpeg (system dep)

## Development Commands

### Makefile shortcuts (from repo root)
```bash
make pg            # Start PostgreSQL in Docker
make be_install    # Install Python deps (creates/uses venv)
make be_migrate    # Run Alembic migrations
make be            # Start backend dev server (port 8000)
make fe            # Start frontend dev server (port 5173)
make pg-shell      # Access PostgreSQL CLI
```

### Backend (manual)
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                          # Run migrations
uvicorn app.main:app --reload --port 8000     # Dev server
```

### Frontend (manual)
```bash
cd frontend
npm install
npm run dev       # Dev server at http://localhost:5173
npm run build     # Production build
```

### Full stack via Docker
```bash
docker compose up -d postgres
docker compose up --build
```

## Environment Setup

Copy `.env.example` to `backend/.env` and set:
- `DATABASE_URL` — PostgreSQL connection string
- `OPENAI_API_KEY` — required unless `USE_MOCK_TRANSCRIPTION=true`
- `USE_MOCK_TRANSCRIPTION` — set `true` to skip API calls during development
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — from Google Cloud Console (see `GOOGLE_AUTH_SETUP.md`)
- `JWT_SECRET_KEY` — random secret for signing tokens
- `ALLOWED_ORIGINS` — CORS origins
- `VITE_API_URL` — backend URL for the frontend (set in `frontend/.env`)

## Architecture

### Backend (`backend/app/`)

**Entry point**: `main.py` — creates the FastAPI app, configures CORS, mounts routers.

**Request flow for video upload**:
1. `api/routes.py` accepts file via `POST /api/upload` or `POST /api/upload-folder`
2. File saved to `uploads/`, background task kicked off
3. `services/audio.py` extracts audio via FFmpeg subprocess
4. `services/whisper_api.py` (or `mock_transcription.py`) transcribes
5. Result persisted via `services/storage.py` → PostgreSQL as JSONB

**Auth flow**:
1. Frontend sends Google ID token to `POST /api/auth/google`
2. `services/auth.py` verifies with Google, upserts user in DB, returns JWT
3. JWT attached as Bearer token; `api/deps.py` validates on protected routes

**Key abstractions**:
- `services/transcription.py` — abstract base class; implement to add new transcription providers
- `models/database.py` — ORM: `User` (google_id, email) and `Transcript` (user_id FK, batch_id for folders, status enum, transcript_content JSONB)
- `models/schemas.py` — Pydantic request/response schemas

**Database migrations** are in `alembic/versions/`. Always run `alembic upgrade head` after pulling changes.

### Frontend (`frontend/src/`)

**Entry point**: `App.jsx` — top-level state (auth, selected transcript, active view).

**API communication**: `api/client.js` — wraps fetch with JWT Bearer token injection; uses `XMLHttpRequest` for upload progress.

**Auth state**: `hooks/useAuth.js` — stores/reads JWT from localStorage, exposes user info.

**Component responsibilities**:
- `UploadForm.jsx` — single file upload with progress bar
- `FolderUploadForm.jsx` — directory picker, batch upload
- `TranscriptList.jsx` — cursor-based pagination, polls `GET /api/transcripts/status/in-progress` for live status
- `TranscriptViewer.jsx` — displays timestamped segments, triggers download

### API Routes Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/upload` | Required | Upload single video |
| POST | `/api/upload-folder` | Required | Batch upload folder |
| GET | `/api/transcripts` | Required | List (cursor pagination) |
| GET | `/api/transcripts/{id}` | Required | Get transcript |
| GET | `/api/transcripts/{id}/status` | Required | Poll status |
| GET | `/api/transcripts/status/in-progress` | Required | Bulk status poll |
| GET | `/api/transcripts/folder/{batch_id}/download` | Required | Download folder as zip |
| POST | `/api/auth/google` | None | Exchange Google token for JWT |
| GET | `/api/auth/me` | Required | Current user profile |
| GET | `/health` | None | Health check |
| GET | `/health/db` | None | DB health check |

## Adding a New Transcription Service

1. Create `backend/app/services/my_service.py` implementing the abstract class in `transcription.py`
2. Register it in `main.py` (or `config.py`) based on a new env var
3. Inject via the dependency in `api/routes.py`
