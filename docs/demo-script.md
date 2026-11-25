# 5-Minute Live Demo Script

## Pre-flight (before the reviewer joins)

```bash
ollama list                     # llama3.2:3b and nomic-embed-text present
make backend                    # terminal 1
make frontend                   # terminal 2
curl -s localhost:8000/api/health | python -m json.tool
```

Expected health: `status: ok`, `llm.reachable: true`, `rag.mode: embeddings` (or `keyword` if the embedding model is absent — both are valid), `chunks: 69`.

Open **http://localhost:5173**, allow microphone access, and keep the text composer visible as a fallback. Click **Reset demo** if the database has old rows.

## Minute 0–1 — Frame the problem

> “Inbound sales teams lose leads in the first five minutes. Qualification is inconsistent and CRM notes are incomplete. This is a working MVP of an AI voice agent that answers from the company knowledge base, qualifies the lead, books the demo and writes the CRM record — all locally, with zero paid APIs.”

Point at the header badges: model, RAG mode, backend status.

## Minute 1–2 — Start the call

Click **Start call**. Mira greets you by voice.

Say or type:

> “Hi, I’m Priya from Acme Retail. We need an AI agent to handle inbound sales calls.”

Point out:
- Transcript shows the turn with a source chip.
- Lead panel captures **Priya** and **Acme Retail**.
- Stage moves from greeting to discovery.

## Minute 2–3 — Grounded answer (RAG)

> “What does it cost?”

Expected reply: Starter **$199/month**, Growth **$499/month**, Enterprise custom.

Point out the source chip `03-pricing.md` and say:

> “The answer is retrieved, not generated from memory. The prompt forbids pricing outside the knowledge base.”

Optional objection:

> “That’s more than we budgeted.”

Expected behaviour: acknowledge, reframe against cost per qualified meeting, offer a smaller plan or pilot.

## Minute 3–4 — Qualification and booking

> “We have a budget of around $2,000 per month and want to launch in 3 weeks. I’m the head of sales.”

Point out:
- Score jumps to **Hot** (90+).
- Budget, timeline and role appear in the lead panel.
- Stage advances to qualification.

> “Yes, book the first slot.”

Expected behaviour: agent books **Fri, 27 Nov · 11:00 AM**, the booking card appears, and the CRM indicator turns on.

Alternative: click a **Book** button on any slot to show deterministic tool execution.

## Minute 4–5 — Summary and insights

Click **End call**.

Walk through the modal:
- executive summary,
- customer need,
- discussion points,
- objections,
- sentiment trend,
- lead score and status,
- next action and follow-up.

Then close the modal and point at the insights bar: calls handled, hot leads, meetings booked, average sentiment.

## Multilingual proof (30 seconds)

Switch the language selector to **हिन्दी**, start a new call, and say:

> “नमस्ते, मैं प्रिया हूँ। हमें इनबाउंड सेल्स कॉल्स के लिए AI एजेंट चाहिए।”

Then:

> “आपकी कीमत क्या है?”

Expected: Hindi reply grounded in `03-pricing.md`.

## If something fails

| Symptom | Recovery |
|---|---|
| No microphone permission | Use the text composer; the workflow is identical |
| Model slow / times out | Wait once, then use the quick-prompt chips; fallback still responds |
| Backend not reachable | Check `make backend` terminal and `/api/health` |
| RAG mode is keyword | Still valid; say embeddings are optional and keyword fallback is intentional |
| Slot already booked | Pick another slot from the panel |

## Closing statement

> “The MVP demonstrates the full loop: voice, retrieval, qualification, sentiment, booking, CRM and insights. The production path replaces browser speech with Whisper/Piper, SQLite with Postgres, and the single Ollama process with an autoscaled GPU pool — without changing the agent contract.”
