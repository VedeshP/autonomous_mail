// src/context/ChatContext.jsx
import { createContext, useContext, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { CONFIG } from '../config';

const ChatContext = createContext(null);

function genId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

const STORAGE_KEY = 'am_convs';

function loadConvs() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
  catch { return []; }
}
function saveConvs(convs) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(convs));
}

export function ChatProvider({ children }) {
  const { authFetch } = useAuth();
  const [conversations, setConversations] = useState(loadConvs);
  const [activeId,      setActiveId]      = useState(null);
  const [thinking,      setThinking]      = useState(false);

  const activeConv = conversations.find(c => c.id === activeId) || null;

  const persistConvs = useCallback((convs) => {
    setConversations(convs);
    saveConvs(convs);
  }, []);

  const startNewChat = useCallback(() => {
    const id = genId();
    const conv = { id, title: 'New conversation', messages: [] };
    persistConvs([conv, ...conversations]);
    setActiveId(id);
    return id;
  }, [conversations, persistConvs]);

  const switchConv = useCallback((id) => {
    setActiveId(id);
  }, []);

  const sendMessage = useCallback(async (prompt) => {
    if (!prompt.trim() || thinking) return;

    // Ensure there's an active conversation
    let convId = activeId;
    let updatedConvs = [...conversations];

    if (!convId || !updatedConvs.find(c => c.id === convId)) {
      const id = genId();
      const newConv = { id, title: prompt.slice(0, 48), messages: [] };
      updatedConvs = [newConv, ...updatedConvs];
      convId = id;
      setActiveId(id);
    }

    // Add user message
    const userMsg = { id: genId(), role: 'user', content: prompt };
    updatedConvs = updatedConvs.map(c => {
      if (c.id !== convId) return c;
      const updated = { ...c, messages: [...c.messages, userMsg] };
      // Set title from first message
      if (c.messages.length === 0) {
        updated.title = prompt.slice(0, 52) + (prompt.length > 52 ? '…' : '');
      }
      return updated;
    });
    persistConvs(updatedConvs);
    setThinking(true);

    try {
      const res = await authFetch(`${CONFIG.API_BASE}/agent/execute`, {
        method: 'POST',
        body: JSON.stringify({ prompt }),
      });

      let aiContent;
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error (${res.status})`);
      }
      const data = await res.json();
      aiContent = data.agent_response || 'No response received.';

      const aiMsg = { id: genId(), role: 'ai', content: aiContent };
      updatedConvs = updatedConvs.map(c =>
        c.id === convId
          ? { ...c, messages: [...c.messages, aiMsg] }
          : c
      );
    } catch (err) {
      const errMsg = {
        id: genId(),
        role: 'ai',
        content: `⚠️ **Error:** ${err.message}\n\nMake sure the backend server is running at \`${CONFIG.API_BASE}\`.`,
        isError: true,
      };
      updatedConvs = updatedConvs.map(c =>
        c.id === convId
          ? { ...c, messages: [...c.messages, errMsg] }
          : c
      );
    } finally {
      persistConvs(updatedConvs);
      setThinking(false);
    }
  }, [activeId, conversations, authFetch, thinking, persistConvs]);

  return (
    <ChatContext.Provider value={{
      conversations, activeConv, activeId,
      thinking, startNewChat, switchConv, sendMessage,
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = () => useContext(ChatContext);
