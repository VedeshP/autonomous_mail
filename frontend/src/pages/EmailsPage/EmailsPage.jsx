// src/pages/EmailsPage/EmailsPage.jsx
import { useState, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { CONFIG } from '../../config';
import s from './EmailsPage.module.css';

// ── Helpers ─────────────────────────────────────────────
function formatDate(ts) {
  if (!ts) return '';
  try {
    return new Date(parseInt(ts)).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric',
    });
  } catch { return ''; }
}

function getHeader(headers = [], name) {
  return headers.find(h => h.name.toLowerCase() === name.toLowerCase())?.value || '';
}

// ── Sub-panels ───────────────────────────────────────────

/** Tab 1 — Inbox list */
function InboxTab({ authFetch }) {
  const [emails,  setEmails]  = useState([]);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');
  const [fetched, setFetched] = useState(false);

  const fetchEmails = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const res = await authFetch(`${CONFIG.API_BASE}/emails/?limit=50`);
      if (!res.ok) throw new Error(`Server error (${res.status})`);
      const data = await res.json();
      setEmails(data);
      setFetched(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  return (
    <div className={s.content}>
      <div style={{ display: 'flex', gap: 10 }}>
        <button className={`${s.btn} ${s.btnPrimary}`} onClick={fetchEmails} disabled={loading}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/>
          </svg>
          {loading ? 'Loading…' : 'Load Emails'}
        </button>
      </div>

      {error && <div className={s.ingestError}>{error}</div>}

      {loading && (
        <div className={s.empty}><div className={s.spinner}/></div>
      )}

      {!loading && fetched && emails.length === 0 && (
        <div className={s.empty}>
          <span className={s.emptyIcon}>📭</span>
          <p>No emails found in the database yet.</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Run an ingestion sync from the "Sync" tab to pull emails from Gmail.
          </p>
        </div>
      )}

      {!loading && emails.length > 0 && (
        <div className={s.emailList}>
          {emails.map((email) => {
            const headers = email.payload?.headers || [];
            const from    = getHeader(headers, 'From') || email.sender_email || 'Unknown';
            const subject = getHeader(headers, 'Subject') || email.subject || '(no subject)';
            const date    = formatDate(email.internalDate) || email.received_at || '';
            return (
              <div key={email.id || email.gmail_id} className={s.emailCard}>
                <div className={s.emailDot} />
                <div className={s.emailMeta}>
                  <div className={s.emailFrom}>{from}</div>
                  <div className={s.emailSubject}>{subject}</div>
                </div>
                <div className={s.emailDate}>{date}</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


/** Tab 2 — Labels */
function LabelsTab({ authFetch }) {
  const [labels,    setLabels]    = useState([]);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState('');
  const [newLabel,  setNewLabel]  = useState('');
  const [creating,  setCreating]  = useState(false);
  const [createMsg, setCreateMsg] = useState('');

  const fetchLabels = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const res = await authFetch(`${CONFIG.API_BASE}/emails/labels`);
      if (!res.ok) throw new Error(`Server error (${res.status})`);
      const data = await res.json();
      setLabels(data.labels || data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  const createLabel = async () => {
    const name = newLabel.trim();
    if (!name) return;
    setCreating(true); setCreateMsg('');
    try {
      const res = await authFetch(`${CONFIG.API_BASE}/emails/labels/create`, {
        method: 'POST',
        body: JSON.stringify({ name }),
      });
      if (!res.ok) throw new Error(`Failed (${res.status})`);
      const data = await res.json();
      setCreateMsg(`✅ Created label "${data.name}" (ID: ${data.id})`);
      setNewLabel('');
      fetchLabels();
    } catch (err) {
      setCreateMsg(`❌ ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  const LABEL_ICONS = {
    INBOX: '📥', SENT: '📤', DRAFT: '📝', SPAM: '🚫',
    TRASH: '🗑️', STARRED: '⭐', IMPORTANT: '❗', UNREAD: '🔵',
  };

  return (
    <div className={s.content}>
      {/* Fetch button */}
      <button className={`${s.btn} ${s.btnPrimary}`} onClick={fetchLabels} disabled={loading} style={{ alignSelf: 'flex-start' }}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/>
        </svg>
        {loading ? 'Loading…' : 'Load Labels'}
      </button>

      {error && <div className={s.ingestError}>{error}</div>}
      {createMsg && (
        <div className={createMsg.startsWith('✅') ? s.ingestResult : s.ingestError}>
          {createMsg}
        </div>
      )}

      {/* Create label */}
      <div className={s.createLabelForm}>
        <input
          className={s.input}
          placeholder="New label name…"
          value={newLabel}
          onChange={e => setNewLabel(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && createLabel()}
        />
        <button className={`${s.btn} ${s.btnPrimary}`} onClick={createLabel} disabled={creating || !newLabel.trim()}>
          {creating ? 'Creating…' : 'Create Label'}
        </button>
      </div>

      {loading && <div className={s.empty}><div className={s.spinner}/></div>}

      {!loading && labels.length === 0 && (
        <div className={s.empty}>
          <span className={s.emptyIcon}>🏷️</span>
          <p>Click "Load Labels" to fetch your Gmail labels.</p>
        </div>
      )}

      {!loading && labels.length > 0 && (
        <div className={s.labelsGrid}>
          {labels.map(label => (
            <div key={label.id} className={s.labelChip}>
              <span className={s.labelIcon}>{LABEL_ICONS[label.id] || '🏷️'}</span>
              <span className={s.labelName} title={label.name}>{label.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


/** Tab 3 — Ingestion Sync */
function SyncTab({ authFetch }) {
  const [limit,   setLimit]   = useState(10);
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState(null);
  const [error,   setError]   = useState('');

  const triggerSync = async () => {
    setLoading(true); setResult(null); setError('');
    try {
      const res = await authFetch(`${CONFIG.API_BASE}/emails/ingest/sync?limit=${limit}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error(`Server error (${res.status})`);
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={s.content}>
      <div className={s.ingestPanel}>
        <div className={s.ingestCard}>
          <div className={s.ingestTitle}>🚀 Gmail → Kafka → Spark Pipeline</div>
          <p className={s.ingestDesc}>
            This triggers the Big Data ingestion pipeline. AetherMail will fetch raw emails
            from Gmail, push them to <strong>Apache Kafka</strong>, and <strong>Spark Streaming</strong> will process,
            embed, and store them into HDFS, Milvus, and PostgreSQL.
          </p>

          <div className={s.limitRow}>
            <span>Fetch</span>
            <input
              type="number"
              className={s.limitInput}
              value={limit}
              min={1} max={500}
              onChange={e => setLimit(Number(e.target.value))}
            />
            <span>emails from Gmail</span>
          </div>

          <button
            className={`${s.btn} ${s.btnPrimary}`}
            onClick={triggerSync}
            disabled={loading}
            style={{ alignSelf: 'flex-start' }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            {loading ? 'Starting pipeline…' : 'Start Ingestion'}
          </button>

          {error  && <div className={s.ingestError}>{error}</div>}
          {result && (
            <div className={s.ingestResult}>
              <strong>{result.status}</strong><br/>
              {result.message}
            </div>
          )}
        </div>

        {/* Info card */}
        <div className={s.ingestCard}>
          <div className={s.ingestTitle}>📊 Pipeline Architecture</div>
          <p className={s.ingestDesc}>
            <strong>Speed Layer:</strong> Kafka + Spark Streaming processes emails in real-time (2s mini-batches).<br/><br/>
            <strong>Batch Layer:</strong> Historical emails are stored in HDFS as encrypted Parquet files.<br/><br/>
            <strong>Vector Index:</strong> Email text is embedded via Ollama and indexed in Milvus/Qdrant for semantic search.
          </p>
        </div>
      </div>
    </div>
  );
}


// ── Main EmailsPage ──────────────────────────────────────
const TABS = ['Inbox', 'Labels', 'Sync'];

export default function EmailsPage() {
  const { authFetch } = useAuth();
  const [activeTab, setActiveTab] = useState('Inbox');

  return (
    <div className={s.page}>
      {/* Toolbar */}
      <div className={s.toolbar}>
        <span className={s.toolbarTitle}>Emails</span>
        <div className={s.spacer}/>
      </div>

      {/* Tabs */}
      <div className={s.tabs}>
        {TABS.map(tab => (
          <button
            key={tab}
            className={`${s.tab} ${activeTab === tab ? s.active : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'Inbox' && '📥 '}
            {tab === 'Labels' && '🏷️ '}
            {tab === 'Sync' && '🔄 '}
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'Inbox'  && <InboxTab  authFetch={authFetch} />}
      {activeTab === 'Labels' && <LabelsTab authFetch={authFetch} />}
      {activeTab === 'Sync'   && <SyncTab   authFetch={authFetch} />}
    </div>
  );
}
