# Recruiter Test Questions and Grounded Answers

Use this document as the primary source for recruiter/evaluator questions. Answers must stay grounded in Fortivex knowledge.

## Company and Product

**Q: What does Fortivex AI do?**  
A: Fortivex AI builds autonomous AI voice agents for inbound and outbound sales calls. Saathi can answer product questions, qualify leads, handle objections, book demos, update CRM records, and generate call summaries and business insights.

**Q: Who is this product for?**  
A: It is for B2B sales teams, SDR teams, founders, and businesses that want to automate repetitive sales conversations while keeping humans focused on closing high-value deals.

**Q: What makes Saathi different from a normal chatbot?**  
A: Saathi is voice-first and built for sales conversations. It uses real-time speech, contextual memory, RAG-grounded answers, lead qualification, sentiment analysis, appointment booking, CRM updates, and post-call summaries. Unlike a generic chatbot, it is designed to move a sales conversation toward qualification and booking.

**Q: Can it handle both inbound and outbound calls?**  
A: Yes. Fortivex AI supports both inbound and outbound sales calls, including lead qualification, FAQs, follow-ups, and demo booking.

**Q: Does it support multilingual conversations?**  
A: Yes. The product supports multilingual communication. The MVP demo supports English and Hindi, and the knowledge base includes a Hindi glossary for common sales terms.

## Pricing

**Q: What plans do you offer and how much do they cost?**  
A: Fortivex AI offers three plans: Starter at $199 per month, Growth at $499 per month, and Enterprise with custom pricing based on volume and integrations.

**Q: What is included in Starter?**  
A: Starter is $199 per month and includes 300 call minutes, 1 phone number, English voice agent, email support, and basic CRM export.

**Q: What is included in Growth?**  
A: Growth is $499 per month and includes 1,000 call minutes, 3 phone numbers, multilingual agents (English + Hindi + one additional language), CRM and calendar integrations, lead scoring, sentiment analysis, call summaries, and priority email and chat support.

**Q: What is included in Enterprise?**  
A: Enterprise has custom pricing. It includes volume-based minutes, unlimited numbers and languages, SSO/SAML, audit logs, role-based access, private VPC or on-premise deployment, custom integrations, dedicated solution architect, and SLA.

**Q: Are there overage charges?**  
A: Yes. Starter overage is $0.35 per additional minute. Growth overage is $0.29 per additional minute. Enterprise uses committed-volume rates agreed in contract.

**Q: Is there a discount or pilot?**  
A: There is a 15% discount on annual prepayment. Startup and nonprofit discounts are available on request. A 14-day paid pilot with 100 minutes is available.

## Security and Privacy

**Q: How secure is our data?**  
A: Data in transit is protected with TLS 1.3. Recordings, transcripts, and CRM data at rest are encrypted with AES-256. Customer data is logically isolated per workspace. Role-based access controls and audit logs are available, especially for Enterprise.

**Q: Do you support GDPR/DPDP/HIPAA?**  
A: The security documentation describes compliance-oriented controls such as encryption, access controls, auditability, retention controls, and deployment options. For specific GDPR, DPDP, HIPAA, or contractual compliance requirements, Saathi should confirm the exact requirement with the Fortivex team.

**Q: Can it be deployed securely for enterprise?**  
A: Yes. Enterprise supports private VPC or on-premise deployment, SSO/SAML, audit logs, RBAC, and custom security reviews.

## Integrations and Setup

**Q: Which CRMs do you support?**  
A: Prebuilt connectors include HubSpot, Salesforce, Pipedrive, Zoho CRM, and Microsoft Dynamics. Other CRMs can be integrated through REST API or webhooks.

**Q: Which calendars/telephony systems are supported?**  
A: Calendar integrations are supported for booking workflows. Telephony supports Twilio, Exotel, Vonage, and SIP trunks. The MVP demonstrates the same workflow in browser voice; production telephony is a transport swap.

**Q: How long does setup take?**  
A: A standard pilot goes live in 2 to 4 weeks. Week one covers knowledge-base ingestion and voice selection, week two covers CRM/calendar integration and testing, and weeks three to four cover a controlled pilot with live traffic.

**Q: Can we use our own documents?**  
A: Yes. You can upload product docs, pricing, FAQs, objection-handling guides, and security policies. The RAG pipeline indexes them and Saathi answers from approved content.

## Sales Behaviour

**Q: Can you qualify my lead?**  
A: Yes. Saathi qualifies leads by capturing name, company, need, budget, timeline, decision role, and contact details, then scores the lead and updates CRM state.

**Q: Can you book a demo?**  
A: Yes. Saathi can show available demo slots and book one after you clearly confirm a specific slot.

**Q: How do you handle objections?**  
A: Saathi responds consultatively using approved knowledge. For price objections, it explains value and pilot options. For security objections, it explains documented controls and offers security review. For timing objections, it offers a pilot or follow-up.

**Q: Are you an AI or human?**  
A: I am Saathi, an AI sales assistant from Fortivex AI.

## Boundaries

**Q: If you don't know something, what do you do?**  
A: I will clearly say I don't have that information in the current Fortivex knowledge base and offer to confirm with the Fortivex team. I should not guess or invent facts.

**Q: Can you answer unrelated questions like weather/news/coding homework?**  
A: I can politely explain that I'm focused on Fortivex AI sales and product questions. I should not answer unrelated questions as if they are part of Fortivex knowledge.
