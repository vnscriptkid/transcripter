import { useState, useRef } from 'react';
import { uploadVideo } from '../api/client';

const ALLOWED_EXTENSIONS = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v'];

export default function UploadForm({ onUploadComplete }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    const extension = file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      return `Invalid file type. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`;
    }
    return null;
  };

  const handleFile = async (file) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    setSelectedFile(file);
    setIsUploading(true);
    setProgress(0);

    try {
      const result = await uploadVideo(file, setProgress);
      setIsUploading(false);
      setSelectedFile(null);
      setProgress(0);
      onUploadComplete(result);
    } catch (err) {
      setError(err.message);
      setIsUploading(false);
      setProgress(0);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleClick = () => {
    if (!isUploading) {
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  return (
    <div className="card">
      <h2>Upload Video</h2>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div
        className={`upload-zone ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept={ALLOWED_EXTENSIONS.map(ext => `.${ext}`).join(',')}
          style={{ display: 'none' }}
        />
        
        {isUploading ? (
          <>
            <div className="spinner" style={{ marginBottom: '1rem' }}></div>
            <p>Uploading {selectedFile?.name}...</p>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p className="upload-hint" style={{ marginTop: '0.5rem' }}>
              {progress}% complete
            </p>
          </>
        ) : (
          <>
            <div className="upload-icon">📹</div>
            <p className="upload-text">
              Drag and drop a video file here, or click to browse
            </p>
            <p className="upload-hint">
              Supported formats: {ALLOWED_EXTENSIONS.join(', ')}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
