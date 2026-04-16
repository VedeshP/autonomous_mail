<div align="center">

# ✉️ AetherMail

### Your Inbox. Managed by an AI That Actually Does Things.

*Not a chatbot that tells you what to do. An agent that does it for you.*

<br>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Graph-6C63FF?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash_Lite-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-Stream_Layer-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)](https://kafka.apache.org)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-Big_Data-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)](https://spark.apache.org)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC143C?style=for-the-badge)](https://qdrant.tech)
[![HDFS](https://img.shields.io/badge/HDFS-Data_Lake-66CCFF?style=for-the-badge&logo=apache&logoColor=white)](https://hadoop.apache.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br>

> *"Most AI email tools summarize your inbox. AetherMail acts on it."*

</div>

---

## 🧠 What Is AetherMail?

AetherMail is a **fully autonomous AI email management system** with an enterprise-grade backend. You connect your Gmail, describe what you want in plain English, and AetherMail's AI agent — powered by a **LangGraph state machine** — searches your emails, labels them, drafts replies, and delegates bulk operations to a **real Apache Spark cluster** — all without you touching a single email.

This isn't a wrapper around ChatGPT with a Gmail plugin. It's a purpose-built system with:

- A **Big Data pipeline** (Kafka → Spark → HDFS + PostgreSQL + Qdrant) that processes your inbox in real-time
- A **vector search engine** (Qdrant + Ollama embeddings) that lets the AI understand *what* emails mean, not just *what they say*
- A **stateful AI agent** (LangGraph) that reasons step-by-step, chooses the right tool, and executes — autonomously
- **AES encryption at rest** for every email body stored in HDFS
- **Full OAuth 2.0 + PKCE** Gmail integration with secure token management

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                   │
│                  "Label all emails from my boss as Urgent"                  │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend (REST API)                          │
│   Auth (Google OAuth 2.0 + PKCE)  │  JWT Access/Refresh Tokens              │
│   POST /api/v1/agent/execute       │  GET /api/v1/emails/                    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LangGraph Agentic State Machine                        │
│                                                                             │
│   AgentState { messages[], user_id }                                        │
│                                                                             │
│   ┌──────────────┐   tool_calls?   ┌─────────────────────────────────────┐ │
│   │  Gemini 2.5  │ ──────────────► │            Tool Router              │ │
│   │  Flash Lite  │ ◄────────────── │                                     │ │
│   │  (Brain)     │   tool_result   │  search_emails_semantic (Qdrant)    │ │
│   └──────────────┘                 │  organize_email (Gmail API)         │ │
│          │                         │  create_draft_reply (Gmail API)     │ │
│          │ END                     │  create_new_label (Gmail API)       │ │
│          ▼                         │  trigger_bulk_action_job (Kafka)    │ │
│   Final Response                   │  fetch_raw_email_from_hdfs (HDFS)   │ │
└─────────────────────────────────── └─────────────────────────────────────┘ ┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                         ▼
┌──────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
│  Gmail API       │   │  Apache Kafka         │   │  HDFS Data Lake      │
│  (Live Actions)  │   │  (Bulk Job Queue)     │   │  (Raw Email Archive) │
│                  │   │        │              │   │  AES Encrypted       │
│  • apply_label   │   │        ▼              │   │  Parquet Files       │
│  • create_draft  │   │  Apache Spark         │   └──────────────────────┘
│  • delete        │   │  Structured Streaming │
│  • archive       │   │        │              │
└──────────────────┘   │        ├──────────────┼──► PostgreSQL (metadata)
                       │        ├──────────────┼──► HDFS (encrypted body)
                       │        └──────────────┼──► Qdrant (768-dim vectors)
                       └──────────────────────-┘
```

---

## ⚙️ The Big Data Pipeline

This is the part that makes AetherMail different from every other "AI + Gmail" project.

When you trigger ingestion, the system doesn't process emails one-by-one in Python. It runs a **distributed streaming pipeline**:

### Step 1 — Ingest (Gmail → Kafka)
The FastAPI endpoint fetches raw Gmail JSON payloads in a background task and streams them into a **Kafka topic** (`raw_emails`). The response returns immediately — no blocking.

### Step 2 — Transform (Spark Structured Streaming)
An Apache Spark job listens to the Kafka topic in real-time. For each batch of emails, Spark applies three parallel operations:

**Action A — PostgreSQL:** Email metadata (sender, subject, thread_id, labels) is written via JDBC for fast structured queries.

**Action B — HDFS Data Lake:** The raw email body is **AES-encrypted** using a Fernet key via a Spark UDF, then written as Parquet files to HDFS at `hdfs://localhost:9000/aethermail/raw_emails`. The encryption happens *inside Spark* — the data never touches disk unencrypted.

**Action C — Qdrant Vector DB:** Each email snippet is converted to a **768-dimensional vector embedding** via Ollama (`nomic-embed-text`) and stored in Qdrant with metadata payload for semantic search.

```
Gmail API
   │
   ▼ (raw JSON)
Kafka Topic: raw_emails
   │
   ▼ (Spark Structured Streaming)
   ├──► PostgreSQL    → metadata (sender, subject, date, labels)
   ├──► HDFS Parquet  → AES-encrypted body_text
   └──► Qdrant        → 768-dim vector + metadata payload
```

---

## 🤖 The AI Agent (LangGraph State Machine)

The agent is built as a **compiled LangGraph graph** — not a simple loop, but a proper state machine with typed state, conditional routing, and automatic tool execution.

### Agent State
```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id: str  # injected per-request for tool authorization
```

### Agent Tools

| Tool | Backend | When the Agent Uses It |
|---|---|---|
| `search_emails_semantic` | Qdrant vector search | "Find emails about the Q3 report" |
| `organize_email` | Gmail API | "Archive all newsletters" |
| `create_new_label` | Gmail API | "Create a folder called 'Tax 2025'" |
| `create_draft_reply` | Gmail API | "Draft a reply saying I'll call back tomorrow" |
| `trigger_bulk_action_job` | Kafka producer | "Delete all emails older than 2023 from marketing@..." |
| `fetch_raw_email_from_hdfs` | Spark + HDFS | "Quote the exact text from the contract email" |

### Routing Logic
```
START → agent node
           │
           ├── has tool_calls? → tools node → back to agent
           │
           └── no tool_calls?  → END (return final response)
```

The agent's system prompt (`SYSTEM_PROMPT` in `graph.py`) enforces strict rules: if the user asks for bulk operations on hundreds of emails, the agent **must** delegate to Kafka — never attempt individual API calls. This is prompt-level architectural enforcement.

---

## 🔐 Security Architecture

AetherMail treats security as infrastructure, not an afterthought.

**OAuth 2.0 + PKCE**
Gmail authorization uses the PKCE (Proof Key for Code Exchange) flow. The `pkce_verifier` is temporarily stored in the `oauth_tokens` table during the handshake and wiped immediately after the code exchange completes.

**JWT Access + Refresh Token Pair**
Every request requires a short-lived access token (configurable expiry). Refresh tokens are typed (`"type": "refresh"`) to prevent token type confusion attacks. The refresh endpoint validates the type claim before issuing a new pair.

**AES Encryption at Rest**
Email bodies stored in HDFS are encrypted using Fernet (AES-128 in CBC mode with HMAC). The encryption key lives in `.env`, the cipher runs inside a Spark UDF, and decryption only happens when the agent's `fetch_raw_email_from_hdfs` tool is explicitly invoked.

**No Credentials in Code**
All secrets (Google OAuth, Gemini API key, DB credentials, HDFS encryption key) are loaded via `.env` with Pydantic Settings — never hardcoded.

---

## 🗃️ Database Schema

Seven tables, fully versioned with Alembic migrations:

```
users
  │
  ├── oauth_tokens (1:1)     → access_token, refresh_token, pkce_verifier, scopes
  ├── emails (1:N)           → gmail_id, thread_id, vector_id (→ Qdrant), hdfs_path (→ HDFS)
  ├── user_preferences (1:N) → key-value JSON store for user settings
  └── agent_tasks (1:N)
        └── action_logs (1:N)
              └── agent_thoughts (1:N)  → tool_used, thought_process (chain-of-thought audit)
```

Every agent action is fully auditable: task → action log → thought chain, with the tool used and the reasoning recorded at every step.

---

## 📦 Project Structure

```
autonomous_mail/
│
├── backend/
│   ├── alembic/                        # Database migration versions
│   │   └── versions/
│   │       ├── b610e434963d_*.py       # Initial schema
│   │       └── 7648cf5586b8_*.py       # Add PKCE verifier
│   │
│   ├── app/
│   │   ├── agent/
│   │   │   ├── graph.py                # LangGraph state machine + system prompt
│   │   │   ├── llm.py                  # Gemini 2.5 Flash Lite config
│   │   │   └── tools/
│   │   │       ├── email_tools.py      # Qdrant semantic search tool
│   │   │       └── action_tools.py     # Gmail + Kafka + HDFS action tools
│   │   │
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py                 # Google OAuth, JWT, PKCE flow
│   │   │   ├── emails.py               # Email CRUD + ingestion trigger
│   │   │   └── agent.py                # POST /agent/execute endpoint
│   │   │
│   │   ├── core/
│   │   │   ├── gmail_service.py        # Gmail API client + token management
│   │   │   ├── parsing.py              # Raw Gmail JSON → Pydantic parser
│   │   │   ├── security.py             # JWT creation (access + refresh)
│   │   │   └── config.py              # Pydantic Settings
│   │   │
│   │   ├── data_pipeline/
│   │   │   ├── producer.py             # Kafka producer (EmailKafkaProducer)
│   │   │   └── spark_stream.py         # Spark Structured Streaming job
│   │   │
│   │   ├── models/                     # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── email.py
│   │   │   ├── oauth_token.py
│   │   │   ├── agent.py                # AgentTask, ActionLog, ActionType
│   │   │   └── agent_thought.py        # Chain-of-thought audit trail
│   │   │
│   │   └── schemas/                    # Pydantic request/response schemas
│   │
│   └── scripts/
│       ├── test_agent.py               # CLI runner for agent testing
│       ├── test_db_insert.py           # DB insertion test with dummy user
│       └── test_parser.py              # Gmail API + parser validation
│
└── frontend/                           # React frontend (separate)
```

---

## ⚡ Setup & Installation

### Prerequisites

| Service | Purpose |
|---|---|
| Python 3.10+ | Backend runtime |
| PostgreSQL | Structured metadata storage |
| Apache Kafka | Email streaming queue |
| Apache Spark | Distributed stream processing |
| Apache Hadoop (HDFS) | Raw email data lake |
| Qdrant | Vector search database |
| Ollama (`nomic-embed-text`) | Local embedding model |
| Google Cloud Console project | OAuth 2.0 + Gmail API |
| Gemini API key | LLM for the agent |

### 1. Clone the repository
```bash
git clone https://github.com/VedeshP/autonomous_mail.git
cd autonomous_mail/backend
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in `backend/`:
```env
# PostgreSQL
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=aethermail
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# JWT
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Gemini
GEMINI_API_KEY=your_gemini_api_key

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# HDFS Encryption
HDFS_ENCRYPTION_KEY=your_fernet_key_here
```

### 5. Run database migrations
```bash
alembic upgrade head
```

### 6. Start infrastructure services
```bash
# Kafka (using Docker)
docker-compose up -d kafka zookeeper

# Qdrant
docker run -p 6333:6333 qdrant/qdrant

# HDFS (local pseudo-distributed mode)
start-dfs.sh

# Ollama (for embeddings)
ollama pull nomic-embed-text
ollama serve
```

### 7. Start the Spark streaming job
```bash
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.postgresql:postgresql:42.6.0 \
  app/data_pipeline/spark_stream.py
```

### 8. Start the FastAPI server
```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

---

## 🧪 Example Interaction

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/agent/execute" \
  -H "Authorization: Bearer <your_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Find emails from my manager about the Q3 report and label them as Urgent"}'
```

**What happens internally:**
```
[Agent] Received: "Find emails from my manager about Q3 report..."
[Agent → Tool] search_emails_semantic(query="Q3 report manager", limit=5)
[Qdrant] Returns 3 matching emails with relevance scores
[Agent → Tool] organize_email(user_id="...", gmail_id="abc123", add_label_ids=["Label_Urgent"])
[Gmail API] Label applied ✓
[Agent → Tool] organize_email(user_id="...", gmail_id="def456", add_label_ids=["Label_Urgent"])
[Gmail API] Label applied ✓
[Agent] Final response: "Done. I found 3 emails about the Q3 report and labeled 2 from your manager as Urgent."
```

**Response:**
```json
{
  "task_id": "a3f2c1d4-...",
  "agent_response": "Done. I found 3 emails related to the Q3 report. I've applied the 'Urgent' label to the 2 emails from your manager. The third email was from a shared alias and wasn't modified."
}
```

---

## 🗺️ Roadmap

- [x] Google OAuth 2.0 + PKCE authentication flow
- [x] Gmail API integration (labels, drafts, read)
- [x] Kafka producer for email ingestion
- [x] Spark Structured Streaming pipeline
- [x] HDFS data lake with AES encryption at rest
- [x] Qdrant vector store with Ollama embeddings
- [x] LangGraph agentic state machine
- [x] Full database audit trail (tasks → logs → thoughts)
- [x] Alembic schema migrations
- [ ] Gmail Push Notifications via Pub/Sub (real-time inbox watch)
- [ ] User memory / preference-aware agent responses
- [ ] Multi-account support
- [ ] Email summarization endpoint
- [ ] Bulk analytics via Spark SQL (email trends, sender stats)
- [ ] Docker Compose full-stack setup

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| Agent Orchestration | LangGraph (StateGraph) |
| LLM | Gemini 2.5 Flash Lite |
| Embeddings | Ollama (`nomic-embed-text`, 768-dim) |
| Vector Database | Qdrant |
| Stream Processing | Apache Spark Structured Streaming |
| Message Queue | Apache Kafka |
| Data Lake | HDFS (Hadoop) + Parquet |
| Relational DB | PostgreSQL |
| ORM | SQLAlchemy + Alembic |
| Auth | Google OAuth 2.0 (PKCE) + JWT (python-jose) |
| Encryption | Fernet (AES-128 CBC + HMAC) |
| Gmail Integration | Google Gmail API v1 |
| Validation | Pydantic v2 |

---

## 🤝 Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/VedeshP">
        <img src="https://github.com/VedeshP.png" width="100px;" alt=""/>
        <br />
        <sub><b>Vedesh Pandya</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/chetangadhiya5062">
        <img src="https://github.com/chetangadhiya5062.png" width="100px;" alt=""/>
        <br />
        <sub><b>Chetan Gadhiya</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/piyush-2k5">
        <img src="https://github.com/piyush-2k5.png" width="100px;" alt=""/>
        <br />
        <sub><b>Piyush Soni</b></sub>
      </a>
    </td>
  </tr>
</table>

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

*Built with obsessive attention to backend architecture.*

⭐ **Star the repo** · 🐛 **Open an issue** · 🔀 **Submit a PR**

</div>
