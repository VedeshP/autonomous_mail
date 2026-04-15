import React, { useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Mail, MessageSquare, Plus, Menu, Search, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  // Sidebar state
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const toggleSidebar = () => {
    setIsSidebarOpen(prev => !prev);
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${isSidebarOpen ? '' : 'sidebar-hidden'}`}>
        <div className="sidebar-header">
          <div className="brand">
            {/* Custom AetherMail SVG Logo */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24" height="24" viewBox="0 0 24 24"
              fill="none" stroke="var(--color-primary)"
              strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M7 10v5h10v-5l-5 4-5-4z"></path>
              <circle cx="12" cy="8" r="1.5" fill="var(--color-primary)" stroke="none"></circle>
            </svg>
            <span style={{ color: 'var(--color-text-main)' }}>AetherMail</span>
          </div>
          <Menu
            size={20}
            color="var(--color-text-muted)"
            style={{ cursor: 'pointer' }}
            onClick={toggleSidebar}
          />
        </div>

        <div className="sidebar-content-wrapper">
          <div className="nav-links">
            <div
              className={`nav-item ${location.pathname === '/' ? 'active' : ''}`}
              onClick={() => navigate('/')}
            >
              <MessageSquare size={18} />
              <span>Chat</span>
            </div>
            <div
              className={`nav-item ${location.pathname === '/emails' ? 'active' : ''}`}
              onClick={() => navigate('/emails')}
            >
              <Mail size={18} />
              <span>Emails</span>
            </div>
          </div>

          <button className="new-chat-btn" onClick={() => navigate('/')}>
            <Plus size={18} style={{ color: 'var(--color-primary)' }} />
            <span>New Chat</span>
          </button>

          <div className="recent-section">
            <div className="recent-title">RECENT</div>
            <div className="nav-item">
              <MessageSquare size={16} color="var(--color-text-muted)" />
              <span style={{ fontSize: '0.85rem' }}>New conversation</span>
            </div>
            <div className="nav-item">
              <MessageSquare size={16} color="var(--color-text-muted)" />
              <span style={{ fontSize: '0.85rem' }}>New conversation</span>
            </div>
            <div className="nav-item">
              <MessageSquare size={16} color="var(--color-text-muted)" />
              <span style={{ fontSize: '0.85rem' }}>New conversation</span>
            </div>
            <div className="nav-item">
              <MessageSquare size={16} color="var(--color-text-muted)" />
              <span style={{ fontSize: '0.85rem' }}>New conversation</span>
            </div>
          </div>

          <div className="sidebar-footer">
            <div className="user-profile">
              <div className="avatar"></div>
              <span style={{ fontSize: '0.9rem' }}>User</span>
            </div>
            <div className="sign-out" onClick={logout}>
              <LogOut size={16} />
              <span>Sign out</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        <header className="topbar">
          <div className="topbar-left">
            <Menu
              size={20}
              color="var(--color-primary)"
              style={{ cursor: 'pointer' }}
              onClick={toggleSidebar}
            />
            <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>AetherMail</span>
          </div>
          <div className="status-badge">
            <div className="status-dot"></div>
            Gmail connected
          </div>
        </header>

        <main className="content-area">
          {children}
        </main>
      </div>
    </div>
  );
}
