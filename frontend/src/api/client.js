// Use environment variable for API URL in production, fallback to relative path
const API_BASE = import.meta.env.VITE_API_URL || '/api';

// --- Auth token management ---

let authToken = localStorage.getItem('auth_token');

export function setAuthToken(token) {
  authToken = token;
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
}

export function getAuthToken() {
  return authToken;
}

function authHeaders() {
  if (!authToken) return {};
  return { 'Authorization': `Bearer ${authToken}` };
}

/**
 * Wrapper around fetch that attaches auth headers and handles 401 expiry.
 */
async function authenticatedFetch(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { ...options.headers, ...authHeaders() },
  });
  if (response.status === 401 && authToken) {
    setAuthToken(null);
    window.dispatchEvent(new Event('auth:expired'));
  }
  return response;
}

// --- Auth API calls ---

export async function loginWithGoogle(googleToken) {
  const response = await fetch(`${API_BASE}/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: googleToken }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed');
  }
  return response.json();
}

export async function getCurrentUser() {
  const response = await authenticatedFetch(`${API_BASE}/auth/me`);
  if (!response.ok) {
    throw new Error('Not authenticated');
  }
  return response.json();
}

// --- Existing API calls (updated with auth) ---

/**
 * Upload a video file for transcription
 * @param {File} file - The video file to upload
 * @param {function} onProgress - Progress callback (0-100)
 * @returns {Promise<{id: string, message: string, status: string}>}
 */
export async function uploadVideo(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const progress = Math.round((event.loaded / event.total) * 100);
        onProgress(progress);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || 'Upload failed'));
        } catch {
          reject(new Error('Upload failed'));
        }
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Network error'));
    });

    xhr.open('POST', `${API_BASE}/upload`);
    if (authToken) {
      xhr.setRequestHeader('Authorization', `Bearer ${authToken}`);
    }
    xhr.send(formData);
  });
}

/**
 * Upload a folder of video files for transcription
 * @param {File[]} files - Video files from folder selection (with webkitRelativePath)
 * @param {string[]} relativePaths - Paths from file.webkitRelativePath, same order as files
 * @param {function} onProgress - Progress callback (0-100), approximate
 * @returns {Promise<{batch_id: string, accepted_count: number, skipped_count: number, accepted_files: Array}>}
 */
export async function uploadFolder(files, relativePaths, onProgress) {
  const formData = new FormData();
  formData.append('relative_paths', JSON.stringify(relativePaths));
  for (const file of files) {
    formData.append('files', file);
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const progress = Math.round((event.loaded / event.total) * 100);
        onProgress(progress);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || 'Folder upload failed'));
        } catch {
          reject(new Error('Folder upload failed'));
        }
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Network error'));
    });

    xhr.open('POST', `${API_BASE}/upload-folder`);
    if (authToken) {
      xhr.setRequestHeader('Authorization', `Bearer ${authToken}`);
    }
    xhr.send(formData);
  });
}

/**
 * Get paginated transcript groups
 * @param {Object} options
 * @param {number} options.limit - Max groups per page (default 20)
 * @param {string|null} options.cursor - ISO timestamp cursor for next page
 * @returns {Promise<{groups: Array, next_cursor: string|null, has_more: boolean}>}
 */
export async function listTranscriptGroups({ limit = 20, cursor = null } = {}) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set('cursor', cursor);

  const response = await authenticatedFetch(`${API_BASE}/transcripts?${params}`);

  if (!response.ok) {
    throw new Error('Failed to fetch transcripts');
  }

  return response.json();
}

/**
 * Get a specific transcript
 * @param {string} id - Transcript ID
 * @returns {Promise<{metadata: object, transcript: object|null}>}
 */
export async function getTranscript(id) {
  const response = await authenticatedFetch(`${API_BASE}/transcripts/${id}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Transcript not found');
    }
    throw new Error('Failed to fetch transcript');
  }

  return response.json();
}

/**
 * Download all transcripts of a folder upload as a zip file.
 * Preserves original folder structure; each transcript is a .txt file.
 * @param {string} batchId - Batch ID from folder upload
 */
export async function downloadFolderTranscripts(batchId) {
  const response = await authenticatedFetch(
    `${API_BASE}/transcripts/folder/${batchId}/download`
  );

  if (!response.ok) {
    let message = 'Download failed';
    try {
      const body = await response.json();
      if (body.detail) {
        message = typeof body.detail === 'string' ? body.detail : body.detail[0]?.msg || message;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(message);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `transcripts-${batchId}.zip`;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * Get the status of a transcript
 * @param {string} id - Transcript ID
 * @returns {Promise<{id: string, status: string, error: string|null}>}
 */
export async function getTranscriptStatus(id) {
  const response = await authenticatedFetch(`${API_BASE}/transcripts/${id}/status`);

  if (!response.ok) {
    throw new Error('Failed to fetch status');
  }

  return response.json();
}

/**
 * Get statuses of all in-progress transcripts (bulk polling)
 * @returns {Promise<{transcripts: Array<{id: string, status: string, batch_id: string|null}>}>}
 */
export async function getInProgressStatuses() {
  const response = await authenticatedFetch(`${API_BASE}/transcripts/status/in-progress`);

  if (!response.ok) {
    throw new Error('Failed to fetch in-progress statuses');
  }

  return response.json();
}

/**
 * Format duration in seconds to MM:SS
 * @param {number} seconds
 * @returns {string}
 */
export function formatDuration(seconds) {
  if (!seconds) return '--:--';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format timestamp for segment
 * @param {number} start - Start time in seconds
 * @param {number} end - End time in seconds
 * @returns {string}
 */
export function formatTimestamp(start, end) {
  return `${formatDuration(start)} - ${formatDuration(end)}`;
}
