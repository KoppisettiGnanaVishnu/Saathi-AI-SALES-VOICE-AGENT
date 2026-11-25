# System Architecture

## 1. Context

The agent is the first-line seller for inbound and outbound sales calls. It must answer product questions accurately, qualify the lead, handle objections, book a meeting, update the CRM and produce a summary a human can act on. The MVP runs entirely on a laptop with free software; every component has a documented production replacement.

## 2. Component diagram

```mermaid
flowchart TB
    subgraph Client["Browser (React + Vite)"]
        MIC[Microphone] --> STT[SpeechRecognition]
        STT --> APP[App state]
        APP --> UI[Transcript, Lead CRM, Summary]
        APP --> AUDIO[Audio player]
    end

    subgraph API["FastAPI backend"]
        ROUTES[REST + SSE chat stream]
        AGENT[Sales agent orchestrator]
        PROMPT[Prompt builder / grounding]
        EXTRACT[Deterministic extractor]
        SCORE[Lead scorer]
        SENT[Sentiment fusion]
        TOOLS[Booking / CRM tools]
        TTSAPI[/api/tts]
    end

    subgraph Intelligence["AI providers"]
        GROQ[Groq OpenAI-compatible, optional]
        OLLAMA[Ollama llama3.2:3b fallback/local]
        EMB[Ollama nomic-embed-text]
        KOKORO[Kokoro local TTS]
    end

    subgraph Data["Persistence"]
        KB[(Markdown knowledge base)]
        SQL[(SQLite: leads, appointments, calls, turns)]
    end

    APP -->|POST /api/chat or /stream| ROUTES
    ROUTES --> AGENT
    AGENT --> PROMPT
    PROMPT --> GROQ
    PROMPT --> OLLAMA
    AGENT -->|embed query| EMB
    AGENT -->|top-k chunks| KB
    AGENT --> EXTRACT
    EXTRACT --> SCORE
    AGENT --> SENT
    AGENT --> TOOLS
    TOOLS --> SQL
    SCORE --> SQL
    SENT --> SQL
    AGENT -->|JSON reply + slots + state| ROUTES
    ROUTES --> APP
    APP -->|POST /api/tts| TTSAPI
    TTSAPI --> KOKORO
    KOKORO --> AUDIO
    AUDIO -->|fallback| BROWSER[Browser speechSynthesis]
```

## 3. Turn lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant U as Customer
    participant B as Browser
    participant A as FastAPI
    participant R as Retriever
    participant L as LLM (Groq/Ollama)
    participant D as SQLite
    participant T as Kokoro TTS

    U->>B: speaks/types a question
    B->>B: STT transcript (browser)
    B->>A: POST /api/chat/stream {session_id, message, language}
    A->>R: search(message, k=3)
    R-->>A: chunks + sources
    A->>A: deterministic fact extract + booking gate
    A->>L: chat_json / stream (if not deterministic)
    L-->>A: reply/JSON
    A->>A: grounding/fallback checks, sentiment fusion, score
    alt explicit slot booking
        A->>D: validate slot + insert appointment
    end
    A->>D: upsert lead, append turn analytics
    A-->>B: sentence events + final state (slots/booking/lead)
    B->>T: POST /api/tts per sentence
    T-->>B: audio (or browser TTS fallback)
    B->>U: progressive speech + updated transcript/CRM panel
```

## 4. Retrieval design

1. Documents in `data/knowledge/` are split on Markdown headings into ~69 chunks with source and heading metadata.
2. If embeddings are enabled, each chunk is embedded once with `nomic-embed-text` at startup and normalised into a matrix.
3. A query is embedded and compared by cosine similarity. If the best score is below `0.2`, the keyword path runs instead.
4. Keyword search tokenises the query, expands Hindi terms and English synonyms (`cost → pricing price plan`, `integrate → crm calendar`), scores overlap with a heading bonus, and applies an intent-aware source boost so pricing questions prefer `03-pricing.md` and security questions prefer `04-security.md`.
5. Retrieved sources are returned to the UI and injected into the prompt; the prompt forbids inventing facts outside them.

## 5. Reliability and grounding

| Risk | Mitigation |
|---|---|
| Malformed/empty LLM JSON | JSON extraction/repair, Groq->Ollama fallback, deterministic grounded fallback replies |
| Hallucinated/out-of-scope answers | KB-grounded handlers for pricing/security/product/integration/timeline; safe KB-boundary response for out-of-scope questions |
| Missed lead facts | Deterministic regex extraction for name, company, email, phone, budget, timeline, role, call volume |
| Premature/wrong booking | Identity gate before showing slots, clickable slot selection, slot re-validation, DB unique constraint on slot time |
| Streaming/final mismatch | Stream discards bad/partial model output; final state is authoritative; booking confirmations kept consistent |
| Model/provider outage | Groq optional; local Ollama fallback; deterministic scripted replies keep demo usable |
| TTS unavailable | Local Kokoro preferred; browser speech synthesis fallback |

## 6. Data model

```mermaid
erDiagram
    LEADS ||--o{ APPOINTMENTS : books
    LEADS ||--o{ CALLS : has
    CALLS ||--o{ TURNS : records

    LEADS {
        text session_id PK
        text name
        text company
        text email
        text phone
        text need
        text budget
        text timeline
        text decision_role
        int score
        text status
        text sentiment
        text stage
        text crm_synced_at
    }
    APPOINTMENTS {
        text slot_id PK
        text session_id
        text slot_iso
        text label
        text created_at
    }
    CALLS {
        text session_id PK
        text summary_json
        int duration_seconds
        text ended_at
    }
    TURNS {
        int id PK
        text session_id
        text role
        text content
        text sentiment
        real sentiment_score
        text stage
        text created_at
    }
```

## 7. Scaling to 1,00,000 users

```mermaid
flowchart LR
    LB[Global load balancer] --> API1[FastAPI pod]
    LB --> API2[FastAPI pod]
    LB --> APIN[FastAPI pod ...]
    API1 --> REDIS[(Redis sessions + rate limits)]
    API1 --> PG[(Postgres primary)]
    PG --> REPL[(Read replicas)]
    API1 --> Q[Job queue]
    Q --> INF[GPU inference pool<br/>vLLM / Ollama]
    Q --> STT[Whisper workers]
    Q --> TTS[Piper workers]
    API1 --> VDB[(pgvector / Qdrant)]
    INF --> OBS[Logs, metrics, traces]
    STT --> OBS
    TTS --> OBS
```

- **Stateless API:** sessions in Redis; any pod can serve any turn.
- **Inference pool:** separate GPU workers with continuous batching; autoscale on queue depth and p95 latency.
- **Voice workers:** Whisper and Piper scale independently of the LLM.
- **Data:** Postgres with read replicas for CRM reads; vector store partitioned by tenant.
- **Capacity model:** 1,00,000 registered users ≈ 1% peak concurrency = 1,000 simultaneous calls. At ~30 seconds of model work per turn and batching across replicas, 20–40 GPU replicas cover peak with headroom; off-peak scales down.
- **Cost levers:** cache frequent answers, route simple intents to a smaller model, cap turn length, and batch embedding jobs.

## 8. Security and privacy

- **Data minimisation:** only sales-relevant fields; no raw audio stored by the MVP.
- **Transport and storage:** TLS in production; encryption at rest for Postgres, object storage and backups.
- **Tenancy:** tenant ID on every row, enforced at the query layer, with per-tenant API keys.
- **Secrets:** environment variables locally, managed secret store in production; never committed.
- **Compliance:** consent before recording, configurable retention, deletion workflow, audit logs; DPDP (India) and GDPR (EU) considerations documented in the report.
- **Model safety:** prompt-injection defence by treating retrieved text as data, not instructions; output constrained to JSON; no tool execution outside the fixed booking/CRM set.
- **Abuse:** rate limits, payload size limits, and a kill switch for demo reset.

## 9. Deployment

| Environment | Topology |
|---|---|
| Local demo | `uvicorn` + Vite dev server + local Ollama |
| Staging | Docker Compose: API, Postgres, Redis, Ollama, reverse proxy |
| Production | CDN for React build, containers on Kubernetes/ECS, managed Postgres + Redis, private GPU subnet, autoscaling inference, centralised observability |

CI runs backend tests, a frontend build, dependency and image scanning, and a smoke test of `/api/health` before deployment. Blue/green rollout with health checks avoids dropping live calls.

## 10. Failure modes

| Failure | Behaviour |
|---|---|
| Ollama unreachable | Health shows `reachable: false`; chat uses scripted fallback |
| Embedding model missing | RAG automatically degrades to keyword search |
| Slot taken during call | Booking rejected, agent offers another slot |
| LLM returns invalid JSON | Repair, retry, then fallback |
| Frontend cannot reach API | Inline error banner with retry guidance |
| Browser lacks speech support | Text composer remains fully functional |
