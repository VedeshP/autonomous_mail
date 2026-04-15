// src/components/ChatInput/ChatInput.jsx
import { useState, useRef, useCallback } from 'react';
import { useChat } from '../../context/ChatContext';
import s from './ChatInput.module.css';

export default function ChatInput({ prefill, onPrefillConsumed }) {
  const { sendMessage, thinking } = useChat();
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  // When parent passes a suggestion, fill in the input
  if (prefill && prefill !== value) {
    setValue(prefill);
    onPrefillConsumed?.();
    setTimeout(() => textareaRef.current?.focus(), 50);
  }

  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  }, []);

  const handleChange = (e) => {
    setValue(e.target.value);
    autoResize();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || thinking) return;
    sendMessage(trimmed);
    setValue('');
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const isReady = value.trim().length > 0 && !thinking;

  return (
    <div className={s.area}>
      <div className={s.wrapper}>
        <textarea
          ref={textareaRef}
          id="prompt-input"
          className={s.textarea}
          placeholder="Ask AetherMail anything about your inbox…"
          rows={1}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
        />
        <div className={s.actions}>
          {value.length > 200 && (
            <span className={s.charCount}>{value.length}</span>
          )}
          <button
            id="send-btn"
            className={`${s.sendBtn} ${isReady ? s.ready : ''}`}
            onClick={submit}
            disabled={!isReady}
            title="Send message"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
      </div>
      <p className={s.disclaimer}>
        AetherMail may make mistakes. Review important actions before they execute.
      </p>
    </div>
  );
}
