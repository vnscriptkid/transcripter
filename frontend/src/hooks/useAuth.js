import { useState, useEffect, useCallback } from 'react';
import { loginWithGoogle, getCurrentUser, setAuthToken, getAuthToken } from '../api/client';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount, check if we have a stored token and validate it
  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    getCurrentUser()
      .then(setUser)
      .catch(() => {
        setAuthToken(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  // Listen for token expiry events from the API client
  useEffect(() => {
    const handleExpired = () => setUser(null);
    window.addEventListener('auth:expired', handleExpired);
    return () => window.removeEventListener('auth:expired', handleExpired);
  }, []);

  const login = useCallback(async (googleCredentialResponse) => {
    const data = await loginWithGoogle(googleCredentialResponse.credential);
    setAuthToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(() => {
    setAuthToken(null);
    setUser(null);
  }, []);

  return { user, isLoading, login, logout };
}
