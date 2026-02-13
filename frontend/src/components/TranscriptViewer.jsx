import { useState } from 'react';
import { formatTimestamp, formatDuration } from '../api/client';

export default function TranscriptViewer({ transcript, metadata }) {
  const [viewMode, setViewMode] = useState('segments'); // 'segments' or 'full'
  const [copied, setCopied] = useState(false);

  if (!metadata) {
    return (
      <div className="card">
        <div className="empty-state">
          <p>Select a transcript to view</p>
        </div>
      </div>
    );
  }

  const isProcessing = ['pending', 'extracting_audio', 'transcribing'].includes(metadata.status);
  const hasFailed = metadata.status === 'failed';
  const isComplete = metadata.status === 'completed';

  const handleCopy = async () => {
    if (transcript?.text) {
      await navigator.clipboard.writeText(transcript.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const displayName = metadata.relative_path || metadata.filename;

  return (
    <div className="card transcript-viewer">
      <div className="transcript-header">
        <div>
          <h2>{displayName}</h2>
          <div className="transcript-meta">
            {metadata.language && <span>Language: {metadata.language}</span>}
            {metadata.duration && (
              <span> • Duration: {formatDuration(metadata.duration)}</span>
            )}
          </div>
        </div>
        {isComplete && transcript && (
          <button className="btn btn-secondary copy-btn" onClick={handleCopy}>
            {copied ? 'Copied!' : 'Copy Text'}
          </button>
        )}
      </div>

      {isProcessing && (
        <div className="empty-state">
          <div className="spinner"></div>
          <p style={{ marginTop: '1rem' }}>
            {metadata.status === 'pending' && 'Waiting to process...'}
            {metadata.status === 'extracting_audio' && 'Extracting audio from video...'}
            {metadata.status === 'transcribing' && 'Transcribing audio...'}
          </p>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            This may take a few minutes depending on video length.
          </p>
        </div>
      )}

      {hasFailed && (
        <div className="error-message">
          <strong>Transcription failed</strong>
          {metadata.error && <p style={{ marginTop: '0.5rem' }}>{metadata.error}</p>}
        </div>
      )}

      {isComplete && transcript && (
        <>
          <div className="tabs">
            <button
              className={`tab ${viewMode === 'segments' ? 'active' : ''}`}
              onClick={() => setViewMode('segments')}
            >
              With Timestamps
            </button>
            <button
              className={`tab ${viewMode === 'full' ? 'active' : ''}`}
              onClick={() => setViewMode('full')}
            >
              Full Text
            </button>
          </div>

          <div className="transcript-content">
            {viewMode === 'segments' && transcript.segments?.length > 0 ? (
              transcript.segments.map((segment, index) => (
                <div key={index} className="segment">
                  <div className="segment-time">
                    {formatTimestamp(segment.start, segment.end)}
                  </div>
                  <div className="segment-text">{segment.text}</div>
                </div>
              ))
            ) : (
              <div className="transcript-text">{transcript.text}</div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
