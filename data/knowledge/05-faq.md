# Frequently Asked Questions

## How long does setup take?

A standard pilot goes live in 2–4 weeks. Week one covers knowledge-base ingestion and voice selection, week two covers CRM/calendar integration and testing, and weeks three to four cover a controlled pilot with live traffic.

## How accurate is the agent?

Intent recognition is typically 90–95% after knowledge-base tuning. Booking accuracy is 99%+ because every slot is validated against the calendar. The agent escalates to a human whenever confidence is low or the caller asks for one.

## Which CRMs do you support?

HubSpot, Salesforce, Pipedrive, Zoho CRM and Microsoft Dynamics have prebuilt connectors. Any other CRM can be integrated through the REST API or webhooks. The MVP uses an adapter interface with a SQLite implementation so a real CRM can be swapped in without changing the agent logic.

## Can it book meetings automatically?

Yes. The agent offers real availability, confirms the caller's choice, books the slot and writes the meeting to the CRM. Double bookings are prevented at the database level.

## Does it work with our phone system?

Yes. We support Twilio, Exotel, Vonage and SIP trunks. The MVP demonstrates the same workflow through a browser microphone; production telephony is a transport swap, not an agent rewrite.

## Which languages are supported?

English, Hindi, Spanish, Arabic, French, German and Portuguese out of the box. Additional languages can be added with custom voice and evaluation work.

## Can we use our own documents?

Yes. You upload product docs, pricing, FAQs, objection-handling guides and security policies. The RAG pipeline chunks and indexes them, and the agent answers only from approved content.

## How do you prevent hallucinations?

The agent is instructed to answer only from retrieved knowledge. If the answer is not present, it says it will confirm with the team. Every response can include source citations, and evaluation suites measure groundedness and hallucination rate.

## What happens when the agent cannot help?

It offers a human handoff, creates a callback task, or transfers the call depending on configuration. High-value accounts can be routed to a human immediately.

## Is there a free trial?

We offer a 14-day paid pilot with 100 minutes. It includes onboarding, a knowledge base and a quality report. This lets teams validate accuracy and ROI before a longer commitment.

## How is pricing calculated?

Pricing is per workspace with included call minutes. Overage is billed per minute. Enterprise pricing is custom based on volume, integrations and deployment model. See the pricing document for details.

## How do you measure success?

Typical metrics are speed to first response, qualified meetings booked, cost per qualified meeting, CRM completeness, caller satisfaction and human-handoff rate. The MVP generates these insights after every call.
