This document outlines the technical design for **Project Mail**: an autonomous, agentic email management ecosystem designed to handle Big Data scales (1TB+) while providing a personalized, human-like interface for email orchestration.

---

# Project Document: Mail Autonomous Intelligence

## 1. Problem Statement
The modern professional receives an average of 120 emails per day, leading to "Information Fragmentation." Existing filters are rule-based and cannot handle complex, context-dependent intent.

**Mathematical Definition:**
Let $E = \{e_1, e_2, ..., e_n\}$ be a high-velocity stream of unstructured email objects. Each $e_i$ is a multi-modal tuple $(H, B, A)$, where $H$ is metadata (headers), $B$ is body text, and $A$ is the set of attachments.

Given a user natural language prompt $P$, we seek an Autonomous Mapping Function $F$:
$$F(E, P, S_t) \rightarrow \{A, R\}$$
Where:
*   $S_t$ is the **Semantic State** (history and user preferences extracted from 1TB of historical data).
*   $A$ is a sequence of **Atomic Actions** (Delete, Label, Draft, Schedule).
*   $R$ is the **Reasoning Trace** (The "Why" behind the action).

**Objective:** Maximize the precision of action $A$ while maintaining a latency $\lambda < 5s$ for incoming stream processing.

---

## 2. Big Data Characteristics (The 5 Vs)
To justify the **1TB storage** and the use of the Hadoop ecosystem:

*   **Volume:** 1TB of data is achieved by storing 10 years of historical email archives for a mid-sized organization, including raw MIME files, large attachments (PDFs/Images), and high-dimensional vector embeddings (which often triple the size of raw text).
*   **Velocity:** Real-time ingestion via Gmail Webhooks/Pub-Sub requires a system that handles "Burstiness" (e.g., morning email surges).
*   **Variety:** Data includes unstructured Text (Body), Semi-structured JSON (Metadata), and Binary Blobs (Attachments).
*   **Veracity:** Distinguishing between automated marketing, phishing, and high-value human communication.
*   **Value:** Converting 1TB of "dark data" into a searchable, actionable personal knowledge base.

---

## 3. Architecture & Data Pipeline
The architecture follows a **Lambda Architecture** pattern to handle both historical context (Batch) and real-time actions (Speed).

### The Workflow:
1.  **Ingestion Layer:** Python workers use OAuth2 to listen to Gmail via Google Pub/Sub.
2.  **Transport Layer:** **Apache Kafka** acts as the buffer. Every new email is a message in the `incoming_mail` topic.
3.  **Speed Layer (Spark Streaming):** 
    *   Spark consumes Kafka messages.
    *   Tasks: PII Masking, Language detection, and immediate "Urgency" scoring.
4.  **Batch Layer (Hadoop/HDFS):** 
    *   Raw emails are saved in **HDFS** in **Parquet format** for efficient analytical querying.
    *   Historical "cleanup" jobs run here using **MapReduce** or **Spark SQL**.
5.  **Intelligence Layer (Vector DB):** 
    *   Text is passed to a local embedding model.
    *   Vectors are stored in **Milvus** or **Qdrant** to allow the agent to "remember" past conversations.
6.  **Serving Layer (Agentic Framework):** 
    *   The User interface (Web/CLI) accepts prompts.
    *   The Agent queries the Vector DB and HDFS to generate context.

---

## 4. Tech Stack & Justification

| Technology | Role | Reason for Choice |
| :--- | :--- | :--- |
| **HDFS** | Primary Storage | To store the 1TB of raw attachments and MIME data with fault tolerance. |
| **Apache Spark** | Processing Engine | Used for complex ETL (cleaning HTML) and Batch processing of years of history. |
| **Apache Kafka** | Message Broker | Ensures no emails are lost during high-velocity bursts. |
| **Milvus / Qdrant** | Vector Database | Essential for "Semantic Search"—finding emails by meaning rather than keywords. |
| **Ollama (Local)** | Local LLM Runner | Runs **Llama 3 (8B)** or **Phi-3** on your machine for privacy and low-cost classification. |
| **CrewAI / LangGraph**| Agent Orchestration | Manages the "Multi-Agent" logic (Delegation and Tools). |
| **PostgreSQL** | Metadata Store | To store user settings, labels, and the state of the agent's tasks. |

### Example Use Case:
*   **User Prompt:** "Find the invoice for the cloud server I bought last year and tell me if it's more expensive than the one from two years ago."
*   **Process:** 
    1.  **Agent** queries **Milvus** to find "Cloud Server Invoice" across the 1TB dataset.
    2.  **Spark SQL** fetches the specific raw data from **HDFS**.
    3.  **Local LLM** parses the numbers from the two PDFs.
    4.  **Agent** performs the comparison and replies to the user.

---

## 5. The Agentic Workflow (The "Human Assistant" Logic)

The system doesn't use one LLM; it uses a **"Crew"** of specialized agents:

### Agent 1: The Triage Officer (Small Local Model - Phi-3)
*   **Task:** Constantly monitors the Kafka stream.
*   **Logic:** Classifies emails into: `Junk`, `Personal`, `Work`, `Urgent`.
*   **Action:** If `Junk`, it moves it to HDFS and stops. If `Urgent`, it triggers a notification.

### Agent 2: The Librarian (RAG Specialist)
*   **Task:** Context Retrieval.
*   **Logic:** When the user asks a question, this agent writes the search queries for the Vector DB and the Spark SQL engine.
*   **Tool Usage:** Uses a "Search_HDFS" tool and a "Search_VectorDB" tool.

### Agent 3: The Executive Assistant (Large Model - Llama 3 70B on Server)
*   **Task:** Decision Making & Action.
*   **Logic:** Takes the filtered context from the Librarian and the user's prompt.
*   **Action:** Formulates the final response or the Gmail API call (e.g., `create_draft` or `update_label`).

### The Feedback Loop:
1.  **Reasoning:** The agent generates a "Thought" (e.g., *"I see this is a flight confirmation; I should check for hotel emails in the same date range."*).
2.  **Observation:** It looks at the data retrieved from the Big Data layer.
3.  **Final Act:** It executes the Gmail command and logs the result back into HDFS for future training.

---

## 6. Storage Definition (Breaking down the 1TB)
To hit the **1TB goal**, your storage strategy is:
1.  **Raw Data (400GB):** JSON dumps of every email and original base64 encoded attachments.
2.  **Processed Data (200GB):** Cleaned text, extracted entities (names, dates, prices) in Parquet format.
3.  **Embedding Index (300GB):** High-dimensional vectors of email chunks for semantic recall.
4.  **Audit Logs (100GB):** Every "Thought" and "Action" taken by the agents, stored for performance tuning and MapReduce analysis.



-----

**Mail is an autonomous agentic system that treats an inbox not as a list of messages, but as a high-velocity Big Data stream. By leveraging a Big Data architecture (Hadoop/Spark) for historical recall and Local LLM Agents for real-time reasoning, the system will act as a "Digital Chief of Staff." It will process incoming mail with high velocity, store and index TB-scale archives for perfect memory, and execute complex operations through natural language prompts—providing the user with a fully curated, self-organizing communication ecosystem.**

------------
**Consider making the system secure before storing or sending stuff ot AI Agents - Encrytption should be done**
-------------------