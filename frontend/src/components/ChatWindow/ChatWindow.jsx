// src/components/ChatWindow/ChatWindow.jsx
import { useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useChat } from '../../context/ChatContext';
import s from './ChatWindow.module.css';

// ── helpers ──────────────────────────────────────────────
function formatText(text) {
  // Very lightweight markdown: bold, italic, inline code
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>');
}

// ── WelcomeState ─────────────────────────────────────────
const SUGGESTIONS = [
  { icon: '🔍', text: 'Find all emails from my boss this week and summarize them' },
  { icon: '🗑️', text: 'Delete all promotional emails from last month' },
  { icon: '✍️', text: 'Draft a polite reply to the last email from HR' },
  { icon: '📂', text: 'Create a label "Project Alpha" and move related emails there' },
];

function WelcomeState({ onSuggestion }) {
  return (
    <div className={s.welcome}>
      <div className={s.welcomeIcon}>
        <svg viewBox="0 0 56 56" fill="none">
          <circle cx="28" cy="28" r="26" stroke="url(#wg)" strokeWidth="2" opacity="0.6"/>
          <path d="M12 22l16 12 16-12" stroke="url(#wg)" strokeWidth="2.5" strokeLinecap="round"/>
          <path d="M12 22v16h32V22" stroke="url(#wg)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
          <circle cx="28" cy="26" r="4" fill="url(#wg)" opacity="0.9"/>
          <defs>
            <linearGradient id="wg" x1="0" y1="0" x2="56" y2="56" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#a78bfa"/>
              <stop offset="100%" stopColor="#60a5fa"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
      <h2 className={s.welcomeTitle}>How can I help with your inbox?</h2>
      <p className={s.welcomeSubtitle}>
        Ask me anything about your emails — I can search, organize, summarize, draft replies, and manage your inbox at scale.
      </p>
      <div className={s.grid}>
        {SUGGESTIONS.map((sg) => (
          <button key={sg.text} className={s.card} onClick={() => onSuggestion(sg.text)}>
            <span className={s.cardIcon}>{sg.icon}</span>
            <span>{sg.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ── ThinkingRow ───────────────────────────────────────────
function ThinkingRow() {
  return (
    <div className={s.row}>
      <div className={`${s.avatar} ${s.aiAvatar}`}>A</div>
      <div className={s.body}>
        <div className={s.sender}>AetherMail</div>
        <div className={s.thinking}>
          <span>Thinking</span>
          <div className={s.dots}>
            <span/><span/><span/>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── MessageRow ────────────────────────────────────────────
function MessageRow({ msg, user }) {
  const isUser = msg.role === 'user';
  const avatarEl = isUser
    ? <div className={s.avatar}><img src={user?.picture || ''} alt="You" onError={e => e.target.style.display='none'}/></div>
    : <div className={`${s.avatar} ${s.aiAvatar}`}>A</div>;

  return (
    <div className={s.row}>
      {avatarEl}
      <div className={s.body}>
        <div className={s.sender}>{isUser ? (user?.name || 'You') : 'AetherMail'}</div>
        <div
          className={s.text}
          dangerouslySetInnerHTML={{ __html: formatText(msg.content) }}
        />
      </div>
    </div>
  );
}

// ── ChatWindow (main export) ──────────────────────────────
export default function ChatWindow({ onSuggestion }) {
  const { user } = useAuth();
  const { activeConv, thinking } = useChat();
  const bottomRef = useRef(null);

  const messages = activeConv?.messages || [];
  const isEmpty  = messages.length === 0 && !thinking;

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, thinking]);

  return (
    <div className={s.wrapper}>
      {isEmpty ? (
        <WelcomeState onSuggestion={onSuggestion} />
      ) : (
        <div className={s.messages}>
          {messages.map(msg => (
            <MessageRow key={msg.id} msg={msg} user={user} />
          ))}
          {thinking && <ThinkingRow />}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
