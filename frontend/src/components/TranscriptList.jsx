import { useState, useMemo, Fragment } from 'react';
import { formatDuration } from '../api/client';

function StatusBadge({ status }) {
  const displayStatus = status.replace('_', ' ');
  return (
    <span className={`status-badge status-${status}`}>
      {displayStatus}
    </span>
  );
}

function buildTree(transcripts) {
  const root = { type: 'folder', name: '', children: [] };

  for (const t of transcripts) {
    const path = (t.relative_path || t.filename || '').replace(/\\/g, '/');
    const parts = path.split('/').filter(Boolean);
    if (parts.length === 0) continue;

    let current = root;
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      const pathSoFar = parts.slice(0, i + 1).join('/');
      let folderNode = current.children.find((c) => c.type === 'folder' && c.name === part);
      if (!folderNode) {
        folderNode = { type: 'folder', name: part, path: pathSoFar, children: [] };
        current.children.push(folderNode);
      }
      current = folderNode;
    }
    const filename = parts[parts.length - 1];
    current.children.push({ type: 'file', name: filename, transcript: t });
  }

  const sortNode = (node) => {
    if (node.type === 'folder') {
      node.children.sort((a, b) => {
        if (a.type !== b.type) return a.type === 'folder' ? -1 : 1;
        return a.name.localeCompare(b.name, undefined, { numeric: true });
      });
      node.children.forEach(sortNode);
    }
  };
  sortNode(root);
  return root;
}

function TreeNode({ node, depth, selectedId, onSelect, expanded, onToggle }) {
  if (node.type === 'folder' && node.name === '') {
    return (
      <>
        {node.children.map((child) => (
          <TreeNode
            key={child.type === 'file' ? child.transcript.id : child.path}
            node={child}
            depth={depth}
            selectedId={selectedId}
            onSelect={onSelect}
            expanded={expanded}
            onToggle={onToggle}
          />
        ))}
      </>
    );
  }

  if (node.type === 'file') {
    const t = node.transcript;
    return (
      <li
        key={t.id}
        className={`transcript-item ${selectedId === t.id ? 'selected' : ''}`}
        onClick={() => onSelect(t.id)}
        style={{ paddingLeft: `${1 + depth * 1}rem` }}
      >
        <div className="transcript-info">
          <div className="transcript-filename">{node.name}</div>
          <div className="transcript-meta">
            {formatDate(t.created_at)}
            {t.duration != null && <> • {formatDuration(t.duration)}</>}
          </div>
        </div>
        <StatusBadge status={t.status} />
      </li>
    );
  }

  const isExpanded = expanded.has(node.path);
  const hasChildren = node.children.length > 0;

  return (
    <li key={node.path || 'root'} className="tree-folder-item">
      <div
        className="tree-folder-header"
        onClick={() => hasChildren && onToggle(node.path)}
        style={{ paddingLeft: `${1 + depth * 1}rem` }}
      >
        <span className="tree-chevron">
          {hasChildren ? (isExpanded ? '▼' : '▶') : ' '}
        </span>
        <span className="tree-folder-name">📁 {node.name}</span>
      </div>
      {hasChildren && isExpanded && (
        <ul className="transcript-list tree-children">
          {node.children.map((child) => (
            <TreeNode
              key={child.type === 'file' ? child.transcript.id : child.path}
              node={child}
              depth={depth + 1}
              selectedId={selectedId}
              onSelect={onSelect}
              expanded={expanded}
              onToggle={onToggle}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return 'Just now';
  if (diff < 3600000) {
    const mins = Math.floor(diff / 60000);
    return `${mins} minute${mins > 1 ? 's' : ''} ago`;
  }
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000);
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  }
  return date.toLocaleDateString();
}

export default function TranscriptList({
  transcripts,
  selectedId,
  onSelect,
  isLoading,
}) {
  const [expandedFolders, setExpandedFolders] = useState(new Set());

  const { individual, batches, hasFolderNodes } = useMemo(() => {
    const ind = [];
    const batchMap = new Map();
    for (const t of transcripts) {
      if (t.batch_id) {
        const list = batchMap.get(t.batch_id) || [];
        list.push(t);
        batchMap.set(t.batch_id, list);
      } else {
        ind.push(t);
      }
    }
    const batches = Array.from(batchMap.entries()).map(([batchId, list]) => ({
      batchId,
      transcripts: list,
      created_at: list[0]?.created_at,
    }));
    batches.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    ind.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    let hasFolderNodes = false;
    for (const b of batches) {
      const tree = buildTree(b.transcripts);
      const check = (node) => {
        if (node.type === 'folder' && node.path && node.children?.length > 0) {
          hasFolderNodes = true;
          return;
        }
        node.children?.forEach(check);
      };
      check(tree);
    }

    return { individual: ind, batches, hasFolderNodes };
  }, [transcripts]);

  const toggleFolder = (path) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const expandAll = () => {
    const paths = new Set();
    const collectPaths = (node) => {
      if (node.type === 'folder' && node.path) paths.add(node.path);
      node.children?.forEach(collectPaths);
    };
    batches.forEach((b) => {
      const tree = buildTree(b.transcripts);
      collectPaths(tree);
    });
    setExpandedFolders(paths);
  };

  const collapseAll = () => setExpandedFolders(new Set());

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
            Upload a video or folder to get started.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="transcript-list-header">
        <h2>Transcripts ({transcripts.length})</h2>
        {batches.length > 0 && hasFolderNodes && (
          <div className="tree-actions">
            <button type="button" className="btn-link" onClick={expandAll}>
              Expand all
            </button>
            <span className="tree-actions-sep">|</span>
            <button type="button" className="btn-link" onClick={collapseAll}>
              Collapse all
            </button>
          </div>
        )}
      </div>

      <ul className="transcript-list">
        {individual.map((transcript) => (
          <li
            key={transcript.id}
            className={`transcript-item ${selectedId === transcript.id ? 'selected' : ''}`}
            onClick={() => onSelect(transcript.id)}
          >
            <div className="transcript-info">
              <div className="transcript-filename">{transcript.filename}</div>
              <div className="transcript-meta">
                {formatDate(transcript.created_at)}
                {transcript.duration != null && (
                  <> • {formatDuration(transcript.duration)}</>
                )}
              </div>
            </div>
            <StatusBadge status={transcript.status} />
          </li>
        ))}

        {batches.map(({ batchId, transcripts: batchTranscripts }) => {
          const tree = buildTree(batchTranscripts);
          return (
            <Fragment key={batchId}>
              <li className="tree-batch-header">
                <span className="tree-batch-label">
                  📁 Folder upload ({batchTranscripts.length} file{batchTranscripts.length !== 1 ? 's' : ''})
                </span>
              </li>
              <TreeNode
                node={tree}
                depth={0}
                selectedId={selectedId}
                onSelect={onSelect}
                expanded={expandedFolders}
                onToggle={toggleFolder}
              />
            </Fragment>
          );
        })}
      </ul>
    </div>
  );
}
