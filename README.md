## 🧠 Mnemosyne — AI Memory Platform

*Persistent memory layer for Large Language Models.*

Mnemosyne remembers your projects so you never have to rebuild context again.

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](#) 
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](#) 
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688)](#) 
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---
## 🌐 Live Web Dashboard & Demo

* **Web Dashboard:** [Mnemosyne Live Dashboard](https://mnemosyne-fyv5.onrender.com/dashboard)
* **Video Demo Link:** [Watch Video Demo](https://youtu.be/YwkY_AjPkGQ)
---

## 📸 Interface & Workflow Screenshots

| Knowledge & Context Retrieval |
| :---: |
| ![Retrieval Screenshot](./Screenshot%202026-08-09%20065728.png) |

| Dashboard & Settings | Memory Graph & Analytics |
| :---: | :---: |
| ![Dashboard Screenshot](./Screenshot%202026-08-09%20065736.png) | ![Analytics Screenshot](./Screenshot%202026-08-09%20065801.png) |

| Project Overview |
| :---: |
| ![Project Overview](./Screenshot%202026-08-09%20065817.png) |
---

## 📖 Overview

### The What: What is Mnemosyne?

Mnemosyne is a persistent memory and knowledge-synthesis layer designed for Large Language Models. By connecting a browser extension directly to a FastAPI backend and structured vector stores, it ensures that your AI assistant retains context, specifications, and project choices across separate conversations.

### The Why: The Real-World Problem It Solves

Current LLM assistants (ChatGPT, Claude, Gemini, etc.) are *stateless*. The moment you close a tab or click "New Chat", all project history, resolved bugs, coding standards, database schemas, and architectural choices are completely forgotten.

When you start a new conversation, you are hit with high cognitive load and manual overhead:
1. You have to explain your project goals and architecture again.
2. You must copy-paste dependency files, configurations, and API keys.
3. You have to re-verify resolved bugs so the model doesn't re-propose broken solutions.

*Mnemosyne resolves this by acting as your project's digital hippocampus.* It continuously observes developer chats, distills unstructured conversation threads into clear facts, code intents, decisions, and bugs, and stores them in a dense vector index. The next time you start a new chat, the extension queries the vector index for relevant past context and automatically injects it, ensuring the AI is instantly aligned.

---

## 🏗️ Architecture

How the client extension, memory ingestion flow, structured extraction pipelines, and storage engines cooperate:

```mermaid
graph TD
    subgraph Client ["Client Side (Browser)"]
        A[Chrome Extension - Popup UI] -->|Save Settings & Projects| B[(Local Extension Storage)]
        C[Content Script - content.js] -->|Auto-Inject Retrieved Context| D[ChatGPT / Gemini / Claude UI]
        C -->|Capture Chat Messages| E[Service Worker - background.js]
        E -->|Secure REST Requests| F[FastAPI Backend Server]
    end

    subgraph Service ["Backend Core Service Layer"]
        F --> G[Auth & JWT Verification]
        F --> H[Memory Router]
        F --> I[Retrieval Router]
        F --> J[Projects Router]
        
        H -->|1. Queue Raw Conversation| K[Memory Ingestion Worker]
        K -->|2. Fragment Sentences| L[Chunking Engine]
        L -->|3. Extract Intent/Bugs| M[LLM Fact Extractor]
        M -->|4. Assess Fact Quality| N[Importance Scorer]
        N -->|5. Compute Embedding| O[Vector Embeddings Service]
        N -->|6. Relate Entities| P[Knowledge Graph Engine]
        
        P -->|7. Synthesize Facts| Q[Project DNA Builder]
        
        I -->|1. Semantic Query| R[Hybrid Retrieval Service]
        R -->|2. Rerank & Assemble| S[Context Builder]
        S -->|3. Context Optimization| T[Prompt Optimizer]
        T -->|4. Return Injected Context| C
    end

    subgraph Storage ["Persistent & Cache Databases"]
        G -->|Validate Profiles| DB_PG[(PostgreSQL Database)]
        J -->|Manage Workspace Projects| DB_PG
        O -->|Store Dense Embeddings| DB_QD[(Qdrant Vector Database)]
        R -->|Vector Similarity Query| DB_QD
        K -->|Async Queue & Cache| DB_RD[(Redis Memory Cache)]
    end
    
    subgraph Providers ["AI Model Providers"]
        M -->|LLM Context Extraction| PR_RT[Provider Router]
        PR_RT -->|Adapter| PR_GP[Google Gemini API]
        PR_RT -->|Adapter| PR_GR[Groq Cloud API]
        PR_RT -->|Adapter| PR_OL[Ollama Local API]
        PR_RT -->|Adapter| PR_HF[Hugging Face Spaces]
    end
```

---

## 🛠️ Chrome Web Store Publishing Status

> [!NOTE]
> **Why this extension is loaded locally:**
> Mnemosyne is fully functional and designed to run locally. It has not been published to the public Chrome Web Store because of upfront store registration fees and ongoing developer verification costs. To run the extension, load the `extension/` directory directly into Chrome using **Developer mode** ("Load unpacked") as outlined in the Quick Start below.

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local dev)

### 1. Clone the repository

```bash
git clone https://github.com/your-org/mnemosyne.git
cd mnemosyne
```

### 2. Configure environment

```bash
cd backend
cp .env.example .env
# Edit .env and set at minimum:
#   SECRET_KEY=<a long random string>
#   GROQ_API_KEY=<your Groq key>   (or GEMINI_API_KEY / leave blank for local)
```

### 3. Start all services

```bash
docker compose up -d
```

This starts:
| Service | URL |
|---------|-----|
| Mnemosyne API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| Qdrant UI | http://localhost:6333/dashboard |

### 4. Run database migrations

```bash
docker compose exec api alembic -c alembic.ini upgrade head
```

### 5. Load the Chrome extension

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** → select `mnemosyne/extension/`
4. Click the 🧠 icon in your toolbar
5. Enter your API URL (`http://localhost:8000/api/v1`) and sign in

---

## 📡 API Reference

Full interactive docs available at **`/docs`** (development mode).

### Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/register` | Create an account |
| `POST` | `/api/v1/auth/login` | Obtain a JWT token |
| `GET`  | `/api/v1/auth/me` | Current user profile |
| `POST` | `/api/v1/projects` | Create a project |
| `GET`  | `/api/v1/projects` | List your projects |
| `POST` | `/api/v1/memory/ingest` | Process a conversation |
| `POST` | `/api/v1/retrieval` | Semantic context retrieval |
| `GET`  | `/api/v1/health/live` | Liveness check |
| `GET`  | `/api/v1/health/ready` | Readiness check |

---

## 🔧 Development

### Install dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run locally (without Docker)

Ensure PostgreSQL, Redis, and Qdrant are running (or use `docker compose up postgres redis qdrant -d`), then:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Run tests

```bash
pytest                                 # all unit tests
pytest -m "not integration"            # skip integration tests
pytest --cov=. --cov-report=term       # with coverage
```

### Lint & format

```bash
ruff check .
ruff format .
```

---

## 🧪 Provider Configuration

Set API keys in `.env`:

```env
GROQ_API_KEY=gsk_...          # https://console.groq.com
GEMINI_API_KEY=AIza...        # https://ai.google.dev
# OpenRouter, Ollama, HuggingFace also supported
```

Configure providers via the API (`/api/v1/providers`) or use the `local` provider (no API key required — uses deterministic hashing embeddings for development).

---

## 📁 Project Structure

```
mnemosyne/
├── backend/
│   ├── api/              # FastAPI routers (v1/)
│   ├── core/             # Config, security, auth, logger, lifespan
│   ├── database/         # SQLAlchemy base, session, migrations
│   ├── memory_engine/    # Chunking, extraction, embeddings, retrieval, graph, DNA
│   ├── models/           # SQLAlchemy ORM models
│   ├── providers/        # AI provider adapters (Groq, Gemini, Ollama, etc.)
│   ├── repositories/     # Data access layer
│   ├── schemas/          # Pydantic request/response models
│   ├── services/         # Business logic layer
│   ├── tests/            # Unit and integration tests
│   ├── workers/          # Background task functions
│   ├── main.py           # FastAPI app entry point
│   ├── Dockerfile        # Multi-stage production image
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── extension/            # Chrome Extension (Manifest V3)
│   ├── manifest.json
│   ├── background.js     # Service worker
│   ├── content.js        # Page observer & injector
│   ├── popup.html
│   ├── popup.js
│   └── styles.css
│
├── .github/
│   └── workflows/ci.yml  # GitHub Actions CI/CD
│
└── README.md
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit with clear messages
4. Ensure tests pass (`pytest`)
5. Open a Pull Request

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

*Mnemosyne is named after the Greek goddess of memory and the mother of the Muses.*
