# Project Report — Mira, Autonomous AI Sales Voice Agent

**Author:** Koppisetti Gnana Vishnu · **Programme:** Fortivex AI, Round 3 · **Status:** working local MVP

## 1. Business problem

Sales teams lose revenue in the first minutes of an inbound enquiry. Leads arrive outside working hours, qualification varies between reps, product answers are inconsistent, and CRM notes are incomplete. Hiring linearly does not scale: a five-minute qualification call costs roughly ₹40–₹80 in loaded agent time, and slow response materially reduces conversion. The business needs a 24/7 first-line seller that answers accurately, qualifies consistently, books meetings, and hands a clean record to a human.

## 2. What was built

A working web application with a React voice UI and a FastAPI backend. The agent runs a structured sales conversation through **greeting → discovery → qualification → objection handling → booking → closing**. Each turn retrieves the three most relevant chunks from an eight-document knowledge base, calls local Llama 3.2 3B through Ollama with a strict JSON contract, updates a structured lead profile and sentiment, and persists the result in SQLite. A deterministic layer extracts explicit facts (name, company, contact, budget, timeline, role) so the small model cannot lose them, and an explainable 0–100 score maps the lead to Hot/Warm/Cold. Qualified leads are offered live weekday slots; booking is double-booking-safe and written to the CRM store. Ending the call produces a summary, objections, sentiment trend, next action and aggregate insights. English and Hindi both work end to end.

## 3. Technical implementation

- **Voice:** browser Web Speech API for free STT/TTS, isolated behind hooks so Whisper/Piper can replace it.
- **Reasoning:** Ollama + `llama3.2:3b`, low temperature, JSON-only output with repair and retry, plus a deterministic fallback so a demo never dies.
- **RAG:** heading-aware Markdown chunking, `nomic-embed-text` embeddings, cosine similarity, Hindi/English query expansion, intent-aware source boosting, and keyword fallback when embeddings are unavailable.
- **State:** SQLite tables for leads, appointments, calls and turn analytics; in-process session memory for context.
- **Reliability:** Pydantic validation, typed tool actions, slot re-validation at booking, guarded demo reset, and 13 unit tests covering scoring, extraction, retrieval, slots and concurrency.

## 4. Commercial feasibility

Marginal cost per conversation is compute, not a per-minute API fee. On one mid-size GPU node the MVP serves early customers at a fraction of human cost per qualified meeting; a ₹8,000–₹20,000 monthly price against a few hundred rupees of inference cost gives healthy gross margin. The value is measurable: faster first response, 24/7 coverage, complete CRM capture, consistent qualification, and human handoff only for hot leads. The same agent can be sold as inbound SDR, outbound qualifier or support triage, widening the market without new core engineering.

## 5. Scaling to 1,00,000 users

The MVP is single-node; production is horizontal. Sessions move to Redis, data to Postgres with read replicas, documents to pgvector or Qdrant. The API becomes stateless behind a load balancer, inference moves to an autoscaled GPU pool with request batching, and STT/TTS move to dedicated workers. Scale is concurrency, not registrations: at 1% peak concurrency, 1,000 simultaneous calls at ~30 seconds of model work per turn need roughly 20–40 GPU replicas with headroom, while CPU nodes handle orchestration. Levers include caching repeated answers, small-model-first routing, and per-tenant rate limits.

## 6. Security, infrastructure and deployment

PII is minimised to sales-relevant fields; secrets live in environment variables or a managed store; demo reset is disabled outside demos. Production adds TLS, encryption at rest, tenant-scoped row access, audit logs, retention and deletion workflows, and consent before recording. India’s DPDP Act and EU GDPR/data residency are the governing constraints. Deployment is containerised: React static assets on a CDN, FastAPI in Docker behind an ingress, managed Postgres and Redis, GPU inference in a private subnet, and CI running tests, linting and image scanning before rollout. Observability covers structured logs, per-stage latency, conversion metrics and alerts on model or booking failures.

## 7. Operating cost (indicative, self-hosted)

A single 24 GB GPU node runs the 3B model and embeddings for early volume at roughly $0.30–$0.60/hour, or $220–$440/month. Adding Postgres, Redis, storage and monitoring brings a small production footprint to about $500–$900/month. At scale, cost is dominated by GPU hours per concurrent call; batching, caching and distilled models are the main levers. There are no licence fees: Ollama, Llama 3.2, FastAPI, React and SQLite/Postgres are all free and open source.

## 8. Limitations and next steps

Browser STT may use vendor cloud services, so a privacy-critical deployment must switch to self-hosted Whisper/Piper. The 3B model needs the deterministic guardrails already in place; a 7B–8B model or fine-tune is the next quality step. CRM and calendar are adapters over SQLite and should connect to HubSpot/Salesforce and Calendly/Google Calendar. Telephony, barge-in, voicemail detection and warm transfer are the next product milestones.
