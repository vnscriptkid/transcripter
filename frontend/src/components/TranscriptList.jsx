import { formatDuration } from '../api/client';

function StatusBadge({ status }) {
  const displayStatus = status.replace('_', ' ');
  return (
    <span className={`status-badge status-${status}`}>
      {displayStatus}
    </span>
  );
}

export default function TranscriptList({ 
  transcripts, 
  selectedId, 
  onSelect,
  isLoading 
}) {
  if (isLoading) {
    return (
      <div className="card">
        <h2>Transcripts</h2>
        <div className="empty-state">
          <div className="spinner"></div>
          <p style={{ marginTop: '1rem' }}>Loading...</p>
        </div>
      </div>
    );
  }

  if (transcripts.length === 0) {
    return (
      <div className="card">
        <h2>Transcripts</h2>
        <div className="empty-state">
          <p>No transcripts yet.</p>
          <p style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
            Upload a video to get started.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>Transcripts ({transcripts.length})</h2>
      <ul className="transcript-list">
        {transcripts.map((transcript) => (
          <li
            key={transcript.id}
            className={`transcript-item ${selectedId === transcript.id ? 'selected' : ''}`}
            onClick={() => onSelect(transcript.id)}
          >
            <div className="transcript-info">
              <div className="transcript-filename">{transcript.filename}</div>
              <div className="transcript-meta">
                {formatDate(transcript.created_at)}
                {transcript.duration && (
                  <> • {formatDuration(transcript.duration)}</>
                )}
              </div>
            </div>
            <StatusBadge status={transcript.status} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  
  // Less than a minute
  if (diff < 60000) {
    return 'Just now';
  }
  
  // Less than an hour
  if (diff < 3600000) {
    const mins = Math.floor(diff / 60000);
    return `${mins} minute${mins > 1 ? 's' : ''} ago`;
  }
  
  // Less than a day
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000);
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  }
  
  // Format as date
  return date.toLocaleDateString();
}
