import { useState, useEffect, useCallback } from 'react';
import UploadForm from './components/UploadForm';
import TranscriptList from './components/TranscriptList';
import TranscriptViewer from './components/TranscriptViewer';
import { listTranscripts, getTranscript, getTranscriptStatus } from './api/client';

function App() {
  const [transcripts, setTranscripts] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedTranscript, setSelectedTranscript] = useState(null);
  const [selectedMetadata, setSelectedMetadata] = useState(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingTranscript, setIsLoadingTranscript] = useState(false);

  // Fetch transcripts list
  const fetchTranscripts = useCallback(async () => {
    try {
      const data = await listTranscripts();
      setTranscripts(data);
    } catch (err) {
      console.error('Failed to fetch transcripts:', err);
    } finally {
      setIsLoadingList(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchTranscripts();
  }, [fetchTranscripts]);

  // Poll for updates when there are processing transcripts
  useEffect(() => {
    const processingTranscripts = transcripts.filter(t => 
      ['pending', 'extracting_audio', 'transcribing'].includes(t.status)
    );

    if (processingTranscripts.length === 0) return;

    const interval = setInterval(async () => {
      // Check status of processing transcripts
      const updates = await Promise.all(
        processingTranscripts.map(t => getTranscriptStatus(t.id).catch(() => null))
      );

      let needsRefresh = false;
      updates.forEach((update, index) => {
        if (update && update.status !== processingTranscripts[index].status) {
          needsRefresh = true;
        }
      });

      if (needsRefresh) {
        fetchTranscripts();
        // Also refresh selected transcript if it was processing
        if (selectedId && processingTranscripts.some(t => t.id === selectedId)) {
          loadTranscript(selectedId);
        }
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
  }, [transcripts, selectedId, fetchTranscripts]);

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

  // Handle upload completion
  const handleUploadComplete = (result) => {
    // Refresh the list and select the new transcript
    fetchTranscripts();
    loadTranscript(result.id);
  };

  return (
    <div className="container">
      <header>
        <h1>Video Transcriber</h1>
        <p className="subtitle">Upload a video and get an AI-powered transcript</p>
      </header>

      <UploadForm onUploadComplete={handleUploadComplete} />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '1.5rem' }}>
        <TranscriptList
          transcripts={transcripts}
          selectedId={selectedId}
          onSelect={loadTranscript}
          isLoading={isLoadingList}
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
