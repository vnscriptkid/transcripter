import { useState, useRef } from 'react';
import { uploadFolder } from '../api/client';

const ALLOWED_EXTENSIONS = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v'];

function getExtension(filename) {
  const parts = filename.split('.');
  return parts.length > 1 ? parts.pop().toLowerCase() : '';
}

export default function FolderUploadForm({ onUploadComplete, user, onRequestLogin }) {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [folderName, setFolderName] = useState(null);
  const folderInputRef = useRef(null);

  const handleFolderChange = async (e) => {
    const files = Array.from(e.target.files || []);
    e.target.value = '';

    if (!user) {
      onRequestLogin?.();
      return;
    }

    if (files.length === 0) {
      setError('No files found in folder');
      return;
    }

    const rootName = files[0].webkitRelativePath?.split('/')[0] || 'Folder';
    const videoFiles = files.filter((f) =>
      ALLOWED_EXTENSIONS.includes(getExtension(f.name))
    );
    const skippedCount = files.length - videoFiles.length;

    if (videoFiles.length === 0) {
      setError(`No video files found. ${skippedCount} file(s) skipped (unsupported format).`);
      return;
    }

    const relativePaths = videoFiles.map((f) => {
      const path = f.webkitRelativePath || f.name;
      const parts = path.split('/');
      return parts.slice(1).join('/') || f.name;
    });

    setError(null);
    setFolderName(rootName);
    setIsUploading(true);
    setProgress(0);

    try {
      const result = await uploadFolder(videoFiles, relativePaths, setProgress);
      setIsUploading(false);
      setFolderName(null);
      setProgress(0);
      onUploadComplete(result);
    } catch (err) {
      setError(err.message);
      setIsUploading(false);
      setProgress(0);
    }
  };

  const handleClick = () => {
    if (!isUploading) {
      folderInputRef.current?.click();
    }
  };

  const supportsFolderUpload = 'webkitdirectory' in document.createElement('input');

  if (!supportsFolderUpload) {
    return (
      <div className="card">
        <h2>Upload Folder</h2>
        <p className="upload-hint" style={{ color: 'var(--text-muted)' }}>
          Folder upload is not supported in your browser. Please use a modern browser (Chrome, Firefox, Safari, Edge).
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>Upload Folder</h2>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div
        className="upload-zone"
        onClick={handleClick}
      >
        <input
          type="file"
          ref={folderInputRef}
          onChange={handleFolderChange}
          webkitdirectory=""
          directory=""
          multiple
          style={{ display: 'none' }}
        />

        {isUploading ? (
          <>
            <div className="upload-icon">📁</div>
            <p>Uploading {folderName}...</p>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="upload-hint" style={{ marginTop: '0.5rem' }}>
              {progress}% complete
            </p>
          </>
        ) : (
          <>
            <div className="upload-icon">📁</div>
            <p className="upload-text">
              Click to select a folder
            </p>
            <p className="upload-hint">
              Only video files ({ALLOWED_EXTENSIONS.join(', ')}) will be processed. Other files are skipped.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
