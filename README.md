# Saathi — A Companion for Business Conversations

**Saathi** (Hindi for *companion*) is the voice persona of this project: a warm, natural, multilingual sales companion for Fortivex AI. She runs the full first-line sales conversation locally, with no paid APIs, and speaks in a generated neural voice instead of a system robot voice.

A working, end-to-end MVP of an autonomous AI sales voice agent built entirely with free and open-source software. The agent holds a real-time voice conversation, answers questions from a company knowledge base with RAG, qualifies the lead, tracks sentiment, books a demo, writes to a CRM-style store, and produces a post-call summary with business insights.

Built for the **Fortivex AI — Round 3 Advanced AI Project Challenge**.

![stack](https://img.shields.io/badge/LLM-Ollama%20%2B%20Llama%203.2-2dd4bf) ![stack](https://img.shields.io/badge/Backend-FastAPI-38bdf8) ![stack](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-818cf8) ![stack](https://img.shields.io/badge/Cost-%240%20(fully%20local)-34d399)

---

## 1. What the demo proves

One complete business workflow runs live:

> **Inbound call → grounded product answer → qualification → objection handling → sentiment tracking → appointment booking → CRM update → call summary and insights.**

| Requirement | How this MVP implements it |
|---|---|
| Real-time STT / TTS | Browser `SpeechRecognition` for STT, local Kokoro-82M neural TTS via `/api/tts` with browser `speechSynthesis` fallback. Streaming `/api/chat/stream` delivers sentence-level speech progressively. |
| Contextual memory | In-process session history plus structured lead profile persisted in SQLite (name, company, need, budget, timeline, role, contact, call volume, stage, sentiment). |
| Multilingual | English and Hindi: language selector, multilingual prompt, Hindi query expansion for retrieval, and Hindi-aware TTS voice selection. |
| Lead qualification | LLM extraction plus deterministic regex extraction of name, company, need, budget, timeline, role, contact, and call volume. Explainable 0–100 score → Hot / Warm / Cold. |
| Sentiment analysis | LLM sentiment label fused with a transparent lexicon fallback; per-turn scores drive sentiment trend and scoring. |
| RAG | Markdown knowledge base chunked by heading, embedded locally with `nomic-embed-text` through Ollama, cosine search with keyword fallback, intent-aware source boosting, and deterministic grounded handlers for key facts/out-of-scope queries. |
| Appointment booking | Live weekday slots, identity gate before booking, clickable slot chips in chat, double-booking protection, booking through chat click or API. |
| CRM integration | SQLite-backed CRM adapter: lead upsert, score, stage, sentiment, booking, sync timestamp. Lead panel shows live CRM/booking state. Designed to swap in HubSpot/Salesforce. |
| Call summarisation | Structured summary: executive summary, need, discussion points, objections, sentiment trend, next action and follow-up. |
| Business insights | Aggregate funnel and sentiment metrics from stored calls. |

## 2. Architecture

```mermaid
flowchart LR
    U[Customer] -->|speech| MIC[Browser microphone]
    MIC --> STT[Web Speech STT]
    STT --> UI[React + Vite UI]
    UI -->|/api/chat or /api/chat/stream| API[FastAPI backend]
    API --> AGENT[Sales agent orchestrator]
    AGENT --> RAG[RAG retriever]
    RAG --> KB[(Markdown knowledge base)]
    RAG --> EMB[Ollama nomic-embed-text]
    AGENT --> LLM[LLM provider]
    LLM --> GROQ[Groq OpenAI-compatible optional]
    LLM --> OLLAMA[Ollama llama3.2:3b fallback/local]
    AGENT --> SCORE[Lead scoring + sentiment]
    AGENT --> BOOK[Booking service]
    AGENT --> CRM[CRM adapter]
    BOOK --> DB[(SQLite)]
    CRM --> DB
    AGENT --> SUM[Summary + insights]
    SUM --> DB
    API -->|reply + state + slots| UI
    UI -->|text + language| TTSAPI[/api/tts]
    TTSAPI --> KOKORO[Kokoro local TTS]
    KOKORO --> UI
    UI -->|fallback| BROWSER[Browser speechSynthesis]
    BROWSER --> U
    UI -->|audio| U
```

Full design, scaling plan and failure modes: [`docs/architecture.md`](docs/architecture.md).

## 3. Quickstart (100% local, no API keys)

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com/) running locally
- ~3 GB free disk for local models

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text   # optional; keyword RAG fallback works without it
```

Optional (better chat quality): create `backend/.env` (gitignored) with Groq/OpenAI-compatible settings:

```bash
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your_key_here
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=qwen/qwen3.2-27b
```

If the external LLM fails, Saathi falls back to local Ollama and deterministic grounded replies. Embeddings remain local via Ollama.

### One-command dev setup

```bash
make setup     # creates backend/.venv, installs Python + npm deps
make backend   # terminal 1: FastAPI on :8000
make frontend  # terminal 2: Vite on :5173
```

Or manually:

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. API docs are at **http://localhost:8000/docs**.

### Verify without a browser

```bash
make test    # pytest (booking/RAG/scoring/extraction)
make demo    # scripted English call against a running backend
backend/.venv/bin/python scripts/demo_call.py --language hi-IN
```

## 4. Demo flow

1. Start a conversation. Saathi greets you by voice/text.
2. Say: *“Hi, I’m Priya from Acme Retail. We need an AI agent to handle inbound sales calls.”*
3. Ask: *“What does it cost?”* — the answer is grounded in `data/knowledge/03-pricing.md`.
4. Say: *“We handle 10,000 calls a day.”* — Saathi captures call volume and recommends a plan based on it.
5. Say: *“Book a demo.”* — Saathi asks for name/company if missing, then shows clickable slot chips.
6. Click a slot chip (or pick a slot) — booking is confirmed, Lead/CRM panel updates, and Saathi speaks the confirmation.
7. Click **End conversation** — summary modal shows executive summary, objections, sentiment trend, next action, and insights.

Hindi: switch the language selector to **हिन्दी** and repeat the same flow.

A presenter-ready script with expected outputs: [`docs/demo-script.md`](docs/demo-script.md).

![Live call with grounded answers and a booked demo](docs/screenshots/call-transcript.jpeg)

![Post-call business insights and summary](docs/screenshots/call-summary.jpeg)

## 5. Repository layout

```text
.
├── README.md
├── PROJECT_REPORT.md              # mandatory 1-page report
├── LICENSE
├── Makefile
├── docs/
│   ├── architecture.md            # diagrams, scaling, security, failure modes
│   ├── demo-script.md             # 5-minute live demo script
│   └── interview-prep.md          # likely questions + live-coding tasks
├── data/knowledge/                # 8 RAG source documents (EN + Hindi glossary)
├── scripts/
│   ├── demo_call.py               # scripted end-to-end API call
│   └── dev.sh                     # starts backend + frontend
├── backend/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── .env.example
│   ├── tests/test_core.py
│   └── app/
│       ├── main.py                # FastAPI routes
│       ├── agent.py               # orchestration, prompt, scoring, booking, summary
│       ├── rag.py                 # chunking, embeddings, keyword fallback
│       ├── llm.py                 # Ollama client + JSON repair
│       ├── db.py                  # SQLite schema + CRM store
│       ├── slots.py               # slot generation and availability
│       ├── schemas.py             # Pydantic request models
│       └── config.py              # environment configuration
└── frontend/
    └── src/
        ├── App.jsx
        ├── components/            # Header, Transcript, Composer, LeadPanel, SummaryPanel
        ├── hooks/                 # STT + TTS hooks
        └── styles.css
```

## 6. API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Model/provider, RAG mode, TTS status |
| `POST` | `/api/session` | Start a call, returns greeting + state |
| `POST` | `/api/chat` | Send a turn; returns reply, lead, score, sentiment, stage, sources, booking, slots |
| `POST` | `/api/chat/stream` | Streaming chat; sentence events for progressive speech + final state event |
| `POST` | `/api/tts` | Synthesize text via local Kokoro; browser fallback used if unavailable |
| `POST` | `/api/session/{id}/book` | Book a specific slot (used by clickable chat slots/UI) |
| `POST` | `/api/session/{id}/end` | End call and generate summary |
| `GET` | `/api/leads` | CRM-style lead list |
| `GET` | `/api/appointments` | Booked appointments |
| `GET` | `/api/insights` | Aggregate business insights |
| `POST` | `/api/demo/reset` | Clear demo data (guarded by `ALLOW_DEMO_RESET`) |

## 7. Configuration

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai_compatible` (Groq/OpenRouter/any OpenAI-style API) |
| `LLM_API_KEY` | empty | API key for OpenAI-compatible provider; keep in gitignored `backend/.env` |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | OpenAI-compatible base URL |
| `LLM_MODEL` | `openai/gpt-oss-20b` | External chat model when `LLM_PROVIDER=openai_compatible` (Groq) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `llama3.2:3b` | Local chat fallback/model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Local embedding model |
| `USE_EMBEDDINGS` | `true` | Falls back to keyword search automatically |
| `TTS_URL` | `http://127.0.0.1:8100` | Local Kokoro TTS service |
| `TTS_ENABLED` | `true` | Enables neural TTS; browser fallback still works |
| `DB_PATH` | `backend/data/sales_agent.db` | SQLite database |
| `KNOWLEDGE_DIR` | `data/knowledge` | RAG documents |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origins |
| `ALLOW_DEMO_RESET` | `true` | Enables the reset endpoint |

## 8. Design decisions and honest limitations

- **Local-first:** no paid API keys and no cloud dependency for reasoning. The same code can point at a hosted OpenAI-compatible endpoint in production.
- **Deterministic guardrails around a small model:** structured JSON prompting, JSON repair, deterministic lead extraction, scripted fallback, and explicit slot buttons make the demo reliable on a 3B model.
- **Browser STT is browser-dependent.** Chrome’s Web Speech STT may use a vendor cloud service. For a privacy-critical deployment, replace it with self-hosted Whisper/faster-whisper; UI speech is isolated behind hooks.
- **Neural TTS is optional/local.** Kokoro runs locally when available; browser speech synthesis is the fallback.
- **External LLM is optional.** Groq/OpenAI-compatible mode can improve quality, but keys/cost/quotas apply; local Ollama + deterministic grounding remain the free fallback path.
- **SQLite and in-memory sessions are MVP choices**, not production choices. The scaling path is Postgres + Redis + queue.
- **CRM and calendar are adapters**, currently backed by SQLite and generated slots. HubSpot/Salesforce/Calendly/Google Calendar are production extension points.

## 9. Tests

```bash
cd backend && .venv/bin/python -m pytest -q
```

Covers lead scoring, placeholder filtering, affirmative detection, lead extraction, stage advancement, JSON repair, keyword RAG in English and Hindi, slot uniqueness, double-booking protection, and booking-flow identity/slot-selection behavior. Latest local run: **24 passed**.

## 10. Business case

See [`PROJECT_REPORT.md`](PROJECT_REPORT.md) for the 1-page report covering the business problem, implementation, commercial feasibility, scaling to 1,00,000 users, data security, infrastructure, deployment and operating costs.

## License

MIT — see [`LICENSE`](LICENSE).
