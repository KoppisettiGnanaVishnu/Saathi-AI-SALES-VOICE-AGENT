# Product — Autonomous AI Sales Voice Agent

## What the product does

Fortivex AI deploys autonomous voice agents that talk to leads in real time, answer questions from an approved knowledge base, qualify the opportunity, book meetings and write the outcome back to the CRM.

## Core capabilities

- **Real-time voice conversations:** speech-to-text, an LLM sales brain, and natural text-to-speech.
- **Contextual memory:** remembers the caller's name, company, need, budget, timeline and objections across the call.
- **Multilingual communication:** detects and switches between English, Hindi, Spanish, Arabic, French, German and Portuguese.
- **Lead qualification:** captures name, company, need, budget, timeline and decision role, then produces a 0–100 score.
- **Sentiment analysis:** tracks positive, neutral and negative signals turn by turn and in the final summary.
- **RAG knowledge retrieval:** answers only from approved product, pricing, security and objection-handling documents.
- **Appointment booking:** offers real calendar slots, books the meeting and prevents double booking.
- **CRM sync:** creates or updates the lead, score, stage, sentiment and booking automatically.
- **Call summarisation:** generates an executive summary, key points, objections and the next best action.
- **Human handoff:** transfers high-value or sensitive conversations to a human rep.

## Integrations

- **CRM:** HubSpot, Salesforce, Pipedrive, Zoho CRM, Microsoft Dynamics
- **Calendar:** Google Calendar, Microsoft 365, Calendly
- **Telephony:** Twilio, Exotel, Vonage, SIP trunks
- **Productivity:** Slack, Microsoft Teams, email, webhooks
- **Data:** REST API, CSV import, Snowflake/BigQuery export (Enterprise)

## Languages

English, Hindi, Spanish, Arabic, French, German and Portuguese are supported out of the box. Additional languages are available with custom voice and evaluation work.

## Deployment options

- **Cloud (multi-tenant):** fastest start, shared infrastructure, regional data residency.
- **Private VPC:** dedicated compute and storage inside the customer's cloud account.
- **On-premise:** for regulated buyers that cannot send audio off-site. Available on Enterprise.

## Performance targets

- Streaming voice response latency: under 1.2 seconds at p50.
- Intent recognition accuracy: 90–95% after knowledge-base tuning.
- Booking accuracy: 99%+ with calendar validation.
- Uptime target: 99.9% for the cloud service.

## What the MVP demonstrates

The open-source MVP in this repository demonstrates the complete workflow with a browser voice interface, a local open-source LLM, local RAG, SQLite CRM/booking, and a post-call insights report. Production telephony, managed vector search and enterprise CRM connectors are designed as swappable adapters.
