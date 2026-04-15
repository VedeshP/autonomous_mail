// src/App.jsx
import { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ChatProvider } from './context/ChatContext';
import LoginScreen from './components/LoginScreen/LoginScreen';
import Sidebar     from './components/Sidebar/Sidebar';
import Topbar      from './components/Topbar/Topbar';
import ChatWindow  from './components/ChatWindow/ChatWindow';
import ChatInput   from './components/ChatInput/ChatInput';
import EmailsPage  from './pages/EmailsPage/EmailsPage';
import './App.css';

// ── Inner app (needs auth context) ───────────────────────
function AppShell() {
  const { isLoggedIn } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [suggestionPrefill, setSuggestionPrefill] = useState('');
  const [activePage, setActivePage] = useState('chat'); // 'chat' | 'emails'

  if (!isLoggedIn) return <LoginScreen />;

  const toggleSidebar = () => setSidebarCollapsed(prev => !prev);

  const handleSuggestion = (text) => {
    setSuggestionPrefill(text);
  };

  return (
    <ChatProvider>
      <div className="app">
        <Sidebar 
          collapsed={sidebarCollapsed} 
          onToggle={toggleSidebar} 
          activePage={activePage}
          onNavChange={setActivePage}
        />

        <div className="main">
          <Topbar onToggleSidebar={toggleSidebar} />

          {activePage === 'chat' && (
            <div className="chatArea">
              <ChatWindow onSuggestion={handleSuggestion} />
              <ChatInput
                prefill={suggestionPrefill}
                onPrefillConsumed={() => setSuggestionPrefill('')}
              />
            </div>
          )}

          {activePage === 'emails' && (
            <EmailsPage />
          )}
        </div>
      </div>
    </ChatProvider>
  );
}

// ── Root with providers ───────────────────────────────────
export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
