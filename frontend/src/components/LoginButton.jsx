import { useEffect, useRef } from 'react';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

export default function LoginButton({ onSuccess }) {
  const buttonRef = useRef(null);
  const initializedRef = useRef(false);

  useEffect(() => {
    if (initializedRef.current || !GOOGLE_CLIENT_ID) return;

    function tryInit() {
      if (!window.google?.accounts?.id) return false;
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: onSuccess,
      });
      window.google.accounts.id.renderButton(buttonRef.current, {
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        shape: 'rectangular',
      });
      initializedRef.current = true;
      return true;
    }

    // Try immediately, then retry if GIS script hasn't loaded yet
    if (!tryInit()) {
      const interval = setInterval(() => {
        if (tryInit()) clearInterval(interval);
      }, 200);
      return () => clearInterval(interval);
    }
  }, [onSuccess]);

  if (!GOOGLE_CLIENT_ID) {
    return (
      <p style={{ color: 'var(--error, #ef4444)', fontSize: '0.85rem' }}>
        Google Client ID not configured
      </p>
    );
  }

  return <div ref={buttonRef}></div>;
}
