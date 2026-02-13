import { useState, useEffect, useCallback } from 'react';
import UploadForm from './components/UploadForm';
import FolderUploadForm from './components/FolderUploadForm';
import TranscriptList from './components/TranscriptList';
import TranscriptViewer from './components/TranscriptViewer';
import { listTranscriptGroups, getTranscript, getInProgressStatuses } from './api/client';

function App() {
  const [groups, setGroups] = useState([]);
  const [nextCursor, setNextCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedTranscript, setSelectedTranscript] = useState(null);
  const [selectedMetadata, setSelectedMetadata] = useState(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isLoadingTranscript, setIsLoadingTranscript] = useState(false);

  // Fetch initial page of groups
  const fetchInitialGroups = useCallback(async () => {
    try {
      const data = await listTranscriptGroups({ limit: 20 });
      setGroups(data.groups);
      setNextCursor(data.next_cursor);
      setHasMore(data.has_more);
    } catch (err) {
      console.error('Failed to fetch transcripts:', err);
    } finally {
      setIsLoadingList(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchInitialGroups();
  }, [fetchInitialGroups]);

  // Load more groups (next page)
  const loadMore = useCallback(async () => {
    if (!hasMore || isLoadingMore) return;
    setIsLoadingMore(true);
    try {
      const data = await listTranscriptGroups({ limit: 20, cursor: nextCursor });
      setGroups(prev => [...prev, ...data.groups]);
      setNextCursor(data.next_cursor);
      setHasMore(data.has_more);
    } catch (err) {
      console.error('Failed to load more transcripts:', err);
    } finally {
      setIsLoadingMore(false);
    }
  }, [hasMore, isLoadingMore, nextCursor]);

  // Poll for status updates on in-progress transcripts
  useEffect(() => {
    // Collect in-progress transcript ids from current groups
    const inProgressIds = new Set();
    for (const group of groups) {
      for (const t of group.transcripts) {
        if (['pending', 'extracting_audio', 'transcribing'].includes(t.status)) {
          inProgressIds.add(t.id);
        }
      }
    }

    if (inProgressIds.size === 0) return;

    const interval = setInterval(async () => {
      try {
        const { transcripts: statuses } = await getInProgressStatuses();
        const statusMap = new Map(statuses.map(s => [s.id, s.status]));

        // Check if any tracked transcript changed status
        let changed = false;
        for (const id of inProgressIds) {
          const newStatus = statusMap.get(id);
          // If missing from in-progress list, it completed or failed
          if (!newStatus) {
            changed = true;
            break;
          }
          // Check against current state
          for (const group of groups) {
            const t = group.transcripts.find(tr => tr.id === id);
            if (t && t.status !== newStatus) {
              changed = true;
              break;
            }
          }
          if (changed) break;
        }

        if (changed) {
          // Re-fetch initial page to pick up updated statuses
          const data = await listTranscriptGroups({ limit: 20 });
          setGroups(data.groups);
          setNextCursor(data.next_cursor);
          setHasMore(data.has_more);

          // Refresh selected transcript if it was processing
          if (selectedId && inProgressIds.has(selectedId)) {
            loadTranscript(selectedId);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [groups, selectedId]);

  // Load a specific transcript
  const loadTranscript = async (id) => {
    setSelectedId(id);
    setIsLoadingTranscript(true);

    try {
      const data = await getTranscript(id);
      setSelectedMetadata(data.metadata);
      setSelectedTranscript(data.transcript);
    } catch (err) {
      console.error('Failed to load transcript:', err);
    } finally {
      setIsLoadingTranscript(false);
    }
  };

  // Handle upload completion (single file)
  const handleUploadComplete = (result) => {
    fetchInitialGroups();
    loadTranscript(result.id);
  };

  // Handle folder upload completion
  const handleFolderUploadComplete = (result) => {
    fetchInitialGroups();
    const firstId = result.accepted_files?.[0]?.id;
    if (firstId) loadTranscript(firstId);
  };

  return (
    <div className="container">
      <header>
        <h1>Video Transcriber</h1>
        <p className="subtitle">Upload a video and get an AI-powered transcript</p>
      </header>

      <UploadForm onUploadComplete={handleUploadComplete} />
      <FolderUploadForm onUploadComplete={handleFolderUploadComplete} />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '1.5rem' }}>
        <TranscriptList
          groups={groups}
          selectedId={selectedId}
          onSelect={loadTranscript}
          isLoading={isLoadingList}
          hasMore={hasMore}
          isLoadingMore={isLoadingMore}
          onLoadMore={loadMore}
        />

        {isLoadingTranscript ? (
          <div className="card">
            <div className="empty-state">
              <div className="spinner"></div>
              <p style={{ marginTop: '1rem' }}>Loading transcript...</p>
            </div>
          </div>
        ) : (
          <TranscriptViewer
            transcript={selectedTranscript}
            metadata={selectedMetadata}
          />
        )}
      </div>
    </div>
  );
}

export default App;
