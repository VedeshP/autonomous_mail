// src/components/Sidebar/Sidebar.jsx
import { useAuth } from '../../context/AuthContext';
import { useChat } from '../../context/ChatContext';
import s from './Sidebar.module.css';

const NAV_ITEMS = [
  {
    id: 'chat',
    label: 'Chat',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
      </svg>
    ),
  },
  {
    id: 'emails',
    label: 'Emails',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
        <polyline points="22,6 12,13 2,6"/>
      </svg>
    ),
  },
];

function BrandMiniIcon() {
  return (
    <svg viewBox="0 0 40 40" fill="none">
      <circle cx="20" cy="20" r="18" stroke="url(#sm)" strokeWidth="2"/>
      <path d="M8 14l12 9 12-9" stroke="url(#sm)" strokeWidth="2" strokeLinecap="round"/>
      <path d="M8 14v14h24V14" stroke="url(#sm)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="20" cy="19" r="3" fill="url(#sm)" opacity="0.9"/>
      <defs>
        <linearGradient id="sm" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#a78bfa"/>
          <stop offset="100%" stopColor="#60a5fa"/>
        </linearGradient>
      </defs>
    </svg>
  );
}

export default function Sidebar({ collapsed, onToggle, activePage, onNavChange }) {
  const { user, logout } = useAuth();
  const { conversations, activeId, startNewChat, switchConv } = useChat();

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to sign out?')) logout();
  };

  return (
    <aside className={`${s.sidebar} ${collapsed ? s.collapsed : ''}`}>
      {/* Header */}
      <div className={s.header}>
        <div className={s.brandMini}>
          <div className={s.brandMiniIcon}><BrandMiniIcon /></div>
          <span className={s.brandMiniName}>AetherMail</span>
        </div>
        <button className={s.iconBtn} onClick={onToggle} title="Toggle sidebar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
      </div>

      {/* Navigation */}
      <div className={s.navSection}>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={`${s.navItem} ${activePage === item.id ? s.activeNav : ''}`}
            onClick={() => onNavChange(item.id)}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </div>

      {/* New Chat */}
      <button className={s.newChatBtn} onClick={() => { onNavChange('chat'); startNewChat(); }} id="new-chat-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        <span>New Chat</span>
      </button>

      {/* History */}
      {conversations.length > 0 && (
        <div className={s.sectionLabel}>Recent</div>
      )}
      <div className={s.history}>
        {conversations.map(conv => (
          <button
            key={conv.id}
            className={`${s.historyItem} ${conv.id === activeId ? s.active : ''}`}
            onClick={() => { onNavChange('chat'); switchConv(conv.id); }}
            title={conv.title}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
            </svg>
            {conv.title}
          </button>
        ))}
      </div>

      {/* Bottom — user + logout */}
      <div className={s.bottom}>
        <div className={s.userProfile}>
          <img
            className={s.avatar}
            src={user?.picture || ''}
            alt={user?.name || 'User'}
            onError={e => { e.target.style.display = 'none'; }}
          />
          <div className={s.userInfo}>
            <span className={s.userName}>{user?.name || 'User'}</span>
            <span className={s.userEmail}>{user?.email || ''}</span>
          </div>
        </div>

        <button className={s.logoutBtn} onClick={handleLogout} id="logout-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          Sign out
        </button>
      </div>
    </aside>
  );
}
