# Interview and Live-Coding Preparation

## 1. “Walk me through the architecture.”

Browser captures speech with Web Speech STT and posts text to FastAPI (`/api/chat` or `/api/chat/stream`). The backend retrieves top knowledge chunks, applies deterministic extraction and booking/grounding guardrails, and calls the configured LLM (Groq OpenAI-compatible optionally, local Ollama fallback). The response is parsed into strict JSON, merged with deterministic facts (including call volume), sentiment is fused, lead is rescored, and booking actions are validated against SQLite. The API returns reply + structured state + slots. The frontend renders transcript/CRM updates and speaks progressively via local Kokoro TTS (`/api/tts`) with browser TTS fallback.

## 2. “Why a 3B model, and how do you keep it reliable?”

The constraint is a free, local, laptop-friendly demo. A 3B model is fast enough on an M1 with 8 GB of RAM but weaker at instruction following. Reliability comes from engineering around it: JSON-only output with repair and retry, a deterministic extractor for explicit facts, explicit pricing rules in the prompt, monotonic stage advancement, retrieval source boosting, and a scripted fallback. In production I would evaluate a 7B–8B model or a small fine-tune, but the guardrails stay because they also reduce cost and latency.

## 3. “How does RAG work here?”

Markdown is chunked by heading, preserving source and heading metadata. At startup each chunk is embedded with `nomic-embed-text` and normalised. At query time the query is embedded, scored by cosine similarity, and the top three chunks are injected into the prompt. If embeddings are unavailable, or the best cosine score is below 0.2, the system falls back to keyword search with Hindi and English synonym expansion plus an intent-aware source boost. Sources are shown in the UI so answers are auditable.

## 4. “How is the lead score computed?”

A transparent additive model: need 25, budget 20, timeline 20, decision role 15, company 10, contact details 10, plus up to ±10 from sentiment, clamped to 0–100. Hot ≥ 70, Warm ≥ 40, otherwise Cold. It is deterministic and explainable, which matters for sales teams and for debugging. The LLM extracts facts but does not decide the score.

## 5. “How do you handle multilingual conversations?”

The UI sends a language code. The prompt instructs the model to reply in Hindi when the customer speaks Hindi. Retrieval expands Hindi pricing, security, booking and integration terms into English tokens so the English knowledge base is still searchable. TTS selects a Hindi voice where available. The architecture is language-agnostic; adding a language means adding glossary hints and a voice, not rewriting the agent.

## 6. “What happens if two users book the same slot?”

The appointment table has a unique constraint on the slot time. Booking validates availability inside the transaction and returns a conflict if the slot was taken. The agent then offers another slot instead of confirming. A unit test covers the double-booking case.

## 7. “How would you scale this to 1,00,000 users?”

Treat users as concurrency. Move sessions to Redis, data to Postgres, vectors to pgvector or Qdrant, make the API stateless, and put inference on an autoscaled GPU pool with continuous batching. Split STT and TTS into their own workers. At 1% peak concurrency, 1,000 simultaneous calls need roughly 20–40 GPU replicas with batching and headroom. Add caching for repeated questions, per-tenant rate limits, and queue-based backpressure.

## 8. “What about security and compliance?”

Minimise PII, encrypt in transit and at rest, scope every row by tenant, keep secrets in a managed store, add audit logs and retention/deletion workflows, and capture consent before recording. For India, DPDP; for the EU, GDPR and data residency. Retrieved text is treated as data, not instructions, to reduce prompt injection. Tool execution is restricted to the fixed booking and CRM actions.

## 9. “What are the weaknesses of this MVP?”

Browser STT can be browser/cloud-dependent; SQLite and in-memory sessions are single-node; external LLMs can be unstable/rate-limited (we fallback, but quality varies); CRM/calendar are adapters rather than real HubSpot/Salesforce/Google Calendar integrations; no telephony/barge-in/warm transfer yet. Each has a named production replacement in the architecture/report.

## 10. Live-coding tasks to rehearse

1. **Add a new knowledge document** to `data/knowledge/`, restart, ask a question, confirm the new source appears.
2. **Add a lead field** (e.g. `industry`) end to end: schema, extractor, prompt, score, UI panel, test.
3. **Change the scoring weights** and update the tests.
4. **Add a new intent boost** in `rag.py` for a competitor question and verify retrieval order.
5. **Add an API endpoint** `GET /api/calls/{session_id}` returning the stored summary.
6. **Add a language** by extending the Hindi hints pattern and the UI selector.
7. **Break the model** (stop Ollama) and demonstrate the fallback path.
8. **Force a double booking** with two sessions and show the conflict handling.

## 11. Questions to ask the interviewer

- Which channels matter first: inbound web voice, outbound dialler, or WhatsApp?
- What CRM and calendar are already in place?
- What is the target cost per qualified meeting?
- Which languages and regions are in scope for the first release?
- What does “human handoff” need to look like for their sales team?

## 12. Numbers worth remembering

- Knowledge base: markdown docs in `data/knowledge/` (chunked at startup; chunk count logged in `/api/health`).
- Lead score weights: 25 / 20 / 20 / 15 / 10 / 10, sentiment ±10.
- Hot ≥ 70, Warm ≥ 40.
- Pytest suite passing locally (24 tests after booking-flow regression added).
- Scripted English demo: lead score 90+ and a confirmed booking in four turns.
- Indicative production footprint: ~$500–$900/month for a small self-hosted deployment.
