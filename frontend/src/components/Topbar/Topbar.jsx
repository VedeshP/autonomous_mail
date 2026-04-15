// src/components/Topbar/Topbar.jsx
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { CONFIG } from '../../config';
import s from './Topbar.module.css';

export default function Topbar({ onToggleSidebar }) {
  const { user, authFetch } = useAuth();
  const [gmailStatus, setGmailStatus] = useState('checking'); // 'checking' | 'connected' | 'disconnected'

  useEffect(() => {
    async function checkGmail() {
      try {
        // Probe Gmail connectivity by fetching labels — only works if Gmail is connected
        const res = await authFetch(`${CONFIG.API_BASE}/emails/labels`);
        setGmailStatus(res.ok ? 'connected' : 'disconnected');
      } catch {
        setGmailStatus('disconnected');
      }
    }
    checkGmail();
  }, [authFetch]);

  const statusLabel = {
    checking:     'Checking…',
    connected:    'Gmail connected',
    disconnected: 'Gmail not linked',
  }[gmailStatus];

  return (
    <header className={s.topbar}>
      {/* Sidebar toggle */}
      <button className={s.iconBtn} onClick={onToggleSidebar} title="Toggle sidebar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="3" y1="6"  x2="21" y2="6"/>
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>

      <span className={s.title}>AetherMail</span>

      <div className={s.spacer} />

      <div className={s.actions}>
        {/* Gmail status badge */}
        <div className={s.badge} title={statusLabel}>
          <span className={`${s.dot} ${gmailStatus !== 'checking' ? s[gmailStatus] : ''}`} />
          <span>{statusLabel}</span>
        </div>

        {/* User avatar */}
        {user?.picture && (
          <img
            className={s.avatar}
            src={user.picture}
            alt={user.name}
            onError={e => { e.target.style.display = 'none'; }}
          />
        )}
      </div>
    </header>
  );
}
