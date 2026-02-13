import { useState, useMemo, Fragment } from 'react';
import { formatDuration, downloadFolderTranscripts } from '../api/client';

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
  groups,
  selectedId,
  onSelect,
  isLoading,
  hasMore,
  isLoadingMore,
  onLoadMore,
}) {
  const [expandedFolders, setExpandedFolders] = useState(new Set());

  const hasFolderNodes = useMemo(() => {
    for (const group of groups) {
      if (group.group_type !== 'batch') continue;
      const tree = buildTree(group.transcripts);
      const check = (node) => {
        if (node.type === 'folder' && node.path && node.children?.length > 0) return true;
        return node.children?.some(check) || false;
      };
      if (check(tree)) return true;
    }
    return false;
  }, [groups]);

  const hasBatches = groups.some((g) => g.group_type === 'batch');

  const totalTranscripts = groups.reduce((sum, g) => sum + g.transcripts.length, 0);

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
    groups.forEach((g) => {
      if (g.group_type === 'batch') {
        const tree = buildTree(g.transcripts);
        collectPaths(tree);
      }
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

  if (groups.length === 0) {
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
        <h2>Transcripts ({totalTranscripts})</h2>
        {hasBatches && hasFolderNodes && (
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
        {groups.map((group) => {
          if (group.group_type === 'individual') {
            const t = group.transcripts[0];
            return (
              <li
                key={t.id}
                className={`transcript-item ${selectedId === t.id ? 'selected' : ''}`}
                onClick={() => onSelect(t.id)}
              >
                <div className="transcript-info">
                  <div className="transcript-filename">{t.filename}</div>
                  <div className="transcript-meta">
                    {formatDate(t.created_at)}
                    {t.duration != null && (
                      <> • {formatDuration(t.duration)}</>
                    )}
                  </div>
                </div>
                <StatusBadge status={t.status} />
              </li>
            );
          }

          // Batch group
          const batchTranscripts = group.transcripts;
          const tree = buildTree(batchTranscripts);
          const completedCount = batchTranscripts.filter((t) => t.status === 'completed').length;
          const handleDownload = async (e) => {
            e.stopPropagation();
            try {
              await downloadFolderTranscripts(group.batch_id);
            } catch (err) {
              alert(err.message || 'Download failed');
            }
          };

          return (
            <Fragment key={group.batch_id}>
              <li className="tree-batch-header">
                <span className="tree-batch-label">
                  📁 Folder upload ({batchTranscripts.length} file{batchTranscripts.length !== 1 ? 's' : ''})
                </span>
                {completedCount > 0 && (
                  <button
                    type="button"
                    className="btn-link"
                    onClick={handleDownload}
                  >
                    Download
                  </button>
                )}
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

        {hasMore && (
          <li className="load-more-item" style={{ textAlign: 'center', padding: '0.75rem' }}>
            <button
              type="button"
              className="btn-link"
              onClick={onLoadMore}
              disabled={isLoadingMore}
            >
              {isLoadingMore ? 'Loading...' : 'Load more'}
            </button>
          </li>
        )}
      </ul>
    </div>
  );
}
