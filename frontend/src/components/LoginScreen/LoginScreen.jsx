// src/components/LoginScreen/LoginScreen.jsx
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { CONFIG } from '../../config';
import s from './LoginScreen.module.css';

// Brand SVG (envelope with gradient)
function BrandIcon() {
  return (
    <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="20" cy="20" r="18" stroke="url(#lg)" strokeWidth="2"/>
      <path d="M8 14l12 9 12-9" stroke="url(#lg)" strokeWidth="2" strokeLinecap="round"/>
      <path d="M8 14v14h24V14" stroke="url(#lg)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="20" cy="19" r="3" fill="url(#lg)" opacity="0.9"/>
      <defs>
        <linearGradient id="lg" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#a78bfa"/>
          <stop offset="100%" stopColor="#60a5fa"/>
        </linearGradient>
      </defs>
    </svg>
  );
}

function GoogleIcon() {
  return (
    <svg className={s.googleIcon} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
  );
}

export default function LoginScreen() {
  const { loginWithGoogleToken, loading } = useAuth();
  const [error, setError] = useState('');

  useEffect(() => {
    // Initialize Google GIS when available
    const initGoogle = () => {
      if (typeof window.google === 'undefined') return;
      window.google.accounts.id.initialize({
        client_id: CONFIG.GOOGLE_CLIENT_ID,
        callback: handleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true,
      });
    };
    // Retry until GIS script loads
    const id = setInterval(() => {
      if (typeof window.google !== 'undefined') {
        initGoogle();
        clearInterval(id);
      }
    }, 300);
    return () => clearInterval(id);
  }, []); // eslint-disable-line

  const handleCredentialResponse = async (response) => {
    setError('');
    try {
      await loginWithGoogleToken(response.credential);
    } catch (err) {
      setError(err.message || 'Sign-in failed. Please try again.');
    }
  };

  const handleSignIn = () => {
    setError('');
    if (typeof window.google === 'undefined') {
      setError('Google Sign-In library not loaded. Check your internet connection.');
      return;
    }
    window.google.accounts.id.prompt((notification) => {
      if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
        // Render a hidden button and click it as fallback
        const container = document.getElementById('gsi-fallback');
        window.google.accounts.id.renderButton(container, {
          theme: 'filled_black', size: 'large',
        });
        setTimeout(() => {
          const btn = container?.querySelector('div[role=button]');
          if (btn) btn.click();
        }, 200);
      }
    });
  };

  return (
    <div className={s.screen}>
      <div className={s.aura} />

      <div className={s.container}>
        {/* Brand */}
        <div className={s.brand}>
          <div className={s.brandIcon}><BrandIcon /></div>
          <h1 className={s.brandName}>AetherMail</h1>
          <p className={s.brandTagline}>Your AI-Powered Email Assistant</p>
        </div>

        {/* Card */}
        <div className={s.card}>
          <h2 className={s.cardTitle}>Welcome back</h2>
          <p className={s.cardSubtitle}>Sign in to access your AI‑powered inbox</p>

          {error && <div className={s.errorMsg}>{error}</div>}

          <button
            id="google-signin-btn"
            className={s.googleBtn}
            onClick={handleSignIn}
            disabled={loading}
          >
            <GoogleIcon />
            <span>{loading ? 'Signing in…' : 'Continue with Google'}</span>
          </button>

          {/* Hidden fallback container for GIS button */}
          <div id="gsi-fallback" style={{ display: 'none' }} />

          <div className={s.divider}><span>Secured by OAuth 2.0</span></div>

        </div>

        <p className={s.footer}>
          By continuing, you agree to AetherMail's Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
}
