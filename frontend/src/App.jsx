import { useState, useEffect, useCallback } from 'react';
import UploadForm from './components/UploadForm';
import FolderUploadForm from './components/FolderUploadForm';
import TranscriptList from './components/TranscriptList';
import TranscriptViewer from './components/TranscriptViewer';
import LoginButton from './components/LoginButton';
import LoginModal from './components/LoginModal';
import { useAuth } from './hooks/useAuth';
import { listTranscriptGroups, getTranscript, getInProgressStatuses } from './api/client';

function App() {
  const { user, isLoading: isAuthLoading, login, logout } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);

  const [groups, setGroups] = useState([]);
  const [nextCursor, setNextCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedTranscript, setSelectedTranscript] = useState(null);
  const [selectedMetadata, setSelectedMetadata] = useState(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isLoadingTranscript, setIsLoadingTranscript] = useState(false);

  // Fetch initial page of groups (only when logged in)
  const fetchInitialGroups = useCallback(async () => {
    if (!user) {
      setGroups([]);
      setIsLoadingList(false);
      return;
    }
    try {
      const data = await listTranscriptGroups({ limit: 20 });
      setGroups(data.groups);
      setNextCursor(data.next_cursor);
      setHasMore(data.has_more);
    } catch (err) {
      console.error('Failed to fetch transcripts:', err);
      setGroups([]);
    } finally {
      setIsLoadingList(false);
    }
  }, [user]);

  // Re-fetch when auth state changes
  useEffect(() => {
    if (!isAuthLoading) {
      setIsLoadingList(true);
      setSelectedId(null);
      setSelectedTranscript(null);
      setSelectedMetadata(null);
      fetchInitialGroups();
    }
  }, [user, isAuthLoading, fetchInitialGroups]);

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
    if (!user) return;

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

        let changed = false;
        for (const id of inProgressIds) {
          const newStatus = statusMap.get(id);
          if (!newStatus) { changed = true; break; }
          for (const group of groups) {
            const t = group.transcripts.find(tr => tr.id === id);
            if (t && t.status !== newStatus) { changed = true; break; }
          }
          if (changed) break;
        }

        if (changed) {
          const data = await listTranscriptGroups({ limit: 20 });
          setGroups(data.groups);
          setNextCursor(data.next_cursor);
          setHasMore(data.has_more);

          if (selectedId && inProgressIds.has(selectedId)) {
            loadTranscript(selectedId);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [groups, selectedId, user]);

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

  const handleUploadComplete = (result) => {
    fetchInitialGroups();
    loadTranscript(result.id);
  };

  const handleFolderUploadComplete = (result) => {
    fetchInitialGroups();
    const firstId = result.accepted_files?.[0]?.id;
    if (firstId) loadTranscript(firstId);
  };

  const handleRequestLogin = () => setShowLoginModal(true);

  const handleModalLogin = async (credentialResponse) => {
    await login(credentialResponse);
    setShowLoginModal(false);
  };

  if (isAuthLoading) {
    return (
      <div className="container">
        <div className="card">
          <div className="empty-state">
            <div className="spinner"></div>
            <p style={{ marginTop: '1rem' }}>Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <header>
        <div className="header-row">
          <div>
            <h1>Video Transcriber</h1>
            <p className="subtitle">Upload a video and get an AI-powered transcript</p>
          </div>
          {user ? (
            <div className="user-menu">
              {user.picture && (
                <img
                  src={user.picture}
                  alt=""
                  className="user-avatar"
                  referrerPolicy="no-referrer"
                />
              )}
              <span className="user-name">{user.name}</span>
              <button
                className="btn btn-secondary"
                onClick={logout}
                style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}
              >
                Sign out
              </button>
            </div>
          ) : (
            <LoginButton onSuccess={login} />
          )}
        </div>
      </header>

      <UploadForm
        onUploadComplete={handleUploadComplete}
        user={user}
        onRequestLogin={handleRequestLogin}
      />
      <FolderUploadForm
        onUploadComplete={handleFolderUploadComplete}
        user={user}
        onRequestLogin={handleRequestLogin}
      />

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

      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onLogin={handleModalLogin}
      />
    </div>
  );
}

export default App;
