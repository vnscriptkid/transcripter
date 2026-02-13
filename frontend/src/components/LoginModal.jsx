import LoginButton from './LoginButton';

export default function LoginModal({ isOpen, onClose, onLogin }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>Sign in required</h3>
        <p style={{ color: 'var(--text-muted, #64748b)', margin: '1rem 0' }}>
          Please sign in with your Google account to upload videos for transcription.
        </p>
        <LoginButton onSuccess={onLogin} />
        <button
          className="btn-link"
          onClick={onClose}
          style={{ marginTop: '1rem', display: 'block', margin: '1rem auto 0' }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
