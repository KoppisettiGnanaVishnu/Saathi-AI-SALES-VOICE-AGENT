# Project Report — Saathi: A Companion for Business Conversations

**Author:** Koppisetti Gnana Vishnu · **Programme:** Fortivex AI, Round 3 · **Status:** working local MVP

## 1. Business problem

Sales teams lose revenue in the first minutes of an inbound enquiry. Leads arrive outside working hours, qualification varies between reps, product answers are inconsistent, and CRM notes are incomplete. Hiring linearly does not scale: a five-minute qualification call costs roughly ₹40–₹80 in loaded agent time, and slow response materially reduces conversion. The business needs a 24/7 first-line seller that answers accurately, qualifies consistently, books meetings, and hands a clean record to a human.

## 2. What was built

A working web application with a React voice UI and a FastAPI backend. The agent runs a structured sales conversation through **greeting → discovery → qualification → objection handling → booking → closing**. Each turn retrieves relevant chunks from the local markdown knowledge base, uses a strict JSON LLM contract (Groq OpenAI-compatible optional, local Ollama fallback), and applies deterministic grounding/extraction guardrails. It updates a structured lead profile (including call volume), sentiment, and explainable 0–100 Hot/Warm/Cold score, then persists state in SQLite. Booking is identity-gated, offers clickable slot chips, validates slots, prevents double booking, and writes to the CRM store. Ending the call produces a summary, objections, sentiment trend, next action, and aggregate insights. English and Hindi work end to end.

## 3. Technical implementation

- **Voice:** browser Web Speech STT; local Kokoro-82M neural TTS through `/api/tts` with browser `speechSynthesis` fallback. Streaming chat emits sentence events for progressive speech.
- **Reasoning:** configurable LLM provider: Groq/OpenAI-compatible optional, local Ollama `llama3.2:3b` fallback. Strict JSON contract, repair/retry, Groq->Ollama fallback, and deterministic grounded handlers for key sales facts and out-of-scope boundaries.
- **RAG:** heading-aware Markdown chunking, local `nomic-embed-text` embeddings, cosine similarity, Hindi/English query expansion, intent-aware source boosting, and keyword fallback.
- **State/CRM:** SQLite tables for leads, appointments, calls, and turn analytics; in-process session memory. Lead profile includes call volume, stage, sentiment, score, and booking.
- **Reliability:** Pydantic validation, identity-gated booking, clickable slot selection, slot re-validation, guarded demo reset, and pytest coverage for scoring, extraction, retrieval, slots, double-booking, and booking flow.

## 4. Commercial feasibility

Marginal cost per conversation is compute, not a per-minute API fee. On one mid-size GPU node the MVP serves early customers at a fraction of human cost per qualified meeting; a ₹8,000–₹20,000 monthly price against a few hundred rupees of inference cost gives healthy gross margin. The value is measurable: faster first response, 24/7 coverage, complete CRM capture, consistent qualification, and human handoff only for hot leads. The same agent can be sold as inbound SDR, outbound qualifier or support triage, widening the market without new core engineering.

## 5. Scaling to 1,00,000 users

The MVP is single-node; production is horizontal. Sessions move to Redis, data to Postgres with read replicas, documents to pgvector or Qdrant. The API becomes stateless behind a load balancer, inference moves to an autoscaled GPU pool with request batching, and STT/TTS move to dedicated workers. Scale is concurrency, not registrations: at 1% peak concurrency, 1,000 simultaneous calls at ~30 seconds of model work per turn need roughly 20–40 GPU replicas with headroom, while CPU nodes handle orchestration. Levers include caching repeated answers, small-model-first routing, and per-tenant rate limits.

## 6. Security, infrastructure and deployment

PII is minimised to sales-relevant fields; secrets/LLM keys live in env vars or a managed secret store (`backend/.env` is gitignored). Demo reset is guarded by config. Production adds TLS, encryption at rest, tenant-scoped row access, audit logs, retention/deletion workflows, consent before recording, and data residency controls. India’s DPDP Act and EU GDPR are governing constraints. Deployment is containerised: React static assets on CDN, FastAPI behind ingress, managed Postgres/Redis, optional GPU/local-model nodes, and CI running tests/lint/image scan before rollout. Observability should cover structured logs, per-stage latency, LLM fallback rate, booking conversion, and model/booking failures.

## 7. Operating cost (indicative, self-hosted)

A single 24 GB GPU node runs the 3B model and embeddings for early volume at roughly $0.30–$0.60/hour, or $220–$440/month. Adding Postgres, Redis, storage and monitoring brings a small production footprint to about $500–$900/month. At scale, cost is dominated by GPU hours per concurrent call; batching, caching and distilled models are the main levers. There are no licence fees: Ollama, Llama 3.2, FastAPI, React and SQLite/Postgres are all free and open source.

## 8. Limitations and next steps

Browser STT may use vendor cloud services; privacy-critical deployments should use self-hosted Whisper/faster-whisper. Kokoro local TTS improves voice quality, but production should add streaming telephony-grade audio and barge-in. The optional Groq path improves quality but adds external dependency/rate-limit risk; the local Ollama + deterministic guardrails remain the free fallback. CRM and calendar are SQLite adapters and should connect to HubSpot/Salesforce/Calendly/Google Calendar. Telephony (Twilio/Exotel/SIP), warm transfer, voicemail detection, and observability are the next product milestones.
