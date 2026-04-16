// src/context/AuthContext.jsx
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { CONFIG } from '../config';

const AuthContext = createContext(null);

// ── helpers ──────────────────────────────────────────────
function parseJwt(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64));
  } catch { return {}; }
}

function loadFromStorage() {
  try {
    return {
      accessToken:   localStorage.getItem('am_access')  || null,
      refreshToken:  localStorage.getItem('am_refresh') || null,
      user:          JSON.parse(localStorage.getItem('am_user') || 'null'),
    };
  } catch { return { accessToken: null, refreshToken: null, user: null }; }
}

function saveToStorage({ accessToken, refreshToken, user }) {
  localStorage.setItem('am_access',  accessToken  || '');
  localStorage.setItem('am_refresh', refreshToken || '');
  localStorage.setItem('am_user',    JSON.stringify(user || null));
}

function clearStorage() {
  ['am_access', 'am_refresh', 'am_user'].forEach(k => localStorage.removeItem(k));
}

// ── provider ─────────────────────────────────────────────
export function AuthProvider({ children }) {
  const stored = loadFromStorage();
  const [accessToken,  setAccessToken]  = useState(stored.accessToken);
  const [refreshToken, setRefreshToken] = useState(stored.refreshToken);
  const [user,         setUser]         = useState(stored.user);
  const [loading,      setLoading]      = useState(false);

  const isLoggedIn = Boolean(accessToken && user?.email);

  // Persist whenever auth state changes
  useEffect(() => {
    saveToStorage({ accessToken, refreshToken, user });
  }, [accessToken, refreshToken, user]);

  /** Called by Google GIS after credential is returned */
  const loginWithGoogleToken = useCallback(async (idToken) => {
    setLoading(true);
    try {
      const res = await fetch(`${CONFIG.API_BASE}/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: idToken }),
      });
      if (!res.ok) throw new Error(`Auth failed (${res.status})`);
      const data = await res.json();

      const info = parseJwt(idToken);
      const newUser = {
        name:    info.name    || 'User',
        email:   info.email   || '',
        picture: info.picture || '',
        userId:  data.user_id,
      };

      setAccessToken(data.access_token);
      setRefreshToken(data.refresh_token);
      setUser(newUser);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    if (typeof window.google !== 'undefined') {
      window.google.accounts.id.disableAutoSelect();
    }
    clearStorage();
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
  }, []);

  /** Authenticated fetch — auto-refreshes on 401 */
  const authFetch = useCallback(async (url, options = {}) => {
    const doFetch = (token) => fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`,
      },
    });

    let res = await doFetch(accessToken);

    if (res.status === 401 && refreshToken) {
      // Try refresh
      const rRes = await fetch(`${CONFIG.API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (rRes.ok) {
        const rData = await rRes.json();
        setAccessToken(rData.access_token);
        setRefreshToken(rData.refresh_token);
        res = await doFetch(rData.access_token);
      } else {
        logout();
        throw new Error('Session expired. Please sign in again.');
      }
    }
    return res;
  }, [accessToken, refreshToken, logout]);

  /** Initiates Gmail OAuth flow */
  const authorizeGmail = useCallback(async () => {
    if (!accessToken) {
      throw new Error('Not authenticated');
    }
    try {
      const res = await authFetch(`${CONFIG.API_BASE}/auth/gmail/authorize`);
      if (!res.ok) throw new Error(`Gmail authorization failed (${res.status})`);
      const data = await res.json();
      
      // Redirect to Gmail consent screen
      if (data.auth_url) {
        window.location.href = data.auth_url;
      } else {
        throw new Error('No auth_url in response');
      }
    } catch (err) {
      throw new Error(`Gmail authorization error: ${err.message}`);
    }
  }, [accessToken, authFetch]);

  return (
    <AuthContext.Provider value={{
      user, isLoggedIn, loading,
      loginWithGoogleToken, logout, authFetch, authorizeGmail,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
