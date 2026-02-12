FROM python:3.11-slim

# Install FFmpeg (required for audio extraction)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for uploads and transcripts
RUN mkdir -p uploads transcripts

# Expose port (Railway/Render will set PORT env var)
EXPOSE 8000

# Use PORT environment variable if set, otherwise default to 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
