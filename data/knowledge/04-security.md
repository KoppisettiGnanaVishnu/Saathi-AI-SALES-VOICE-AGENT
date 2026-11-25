# Security, Privacy and Compliance

## Data protection

- TLS 1.3 encryption for all data in transit.
- AES-256 encryption at rest for recordings, transcripts and CRM data.
- Customer data is logically isolated per workspace.
- Secrets are stored in a managed secret manager and rotated regularly.
- No customer data is used to train shared foundation models.

## Access control

- Role-based access control (admin, manager, rep, analyst).
- SSO/SAML and SCIM provisioning on Enterprise.
- Mandatory MFA for administrative accounts.
- Full audit logs for logins, exports, configuration changes and tool calls.

## PII and retention

- Automatic PII redaction for card numbers, account numbers and other sensitive fields.
- Configurable recording and transcript retention from 7 to 90 days.
- Customer-initiated deletion via API or support ticket.
- Data residency options in the US, EU and India.

## Compliance

- GDPR-aligned data processing agreements.
- India DPDP Act readiness.
- SOC 2 Type II program in progress (target: Q3 2026).
- HIPAA support with a Business Associate Agreement on Enterprise.
- Configurable call-recording consent announcements by region.

## AI safety and guardrails

- Answers are grounded in an approved knowledge base; the agent is instructed not to invent pricing or security claims.
- Tool allowlist: the agent can only book slots, update CRM fields and request human handoff.
- Prompt-injection defenses: retrieved documents and caller text are treated as untrusted data.
- Human handoff for high-value, regulated or emotionally sensitive conversations.
- Every tool call and booking is logged for audit.

## Reliability and operations

- 99.9% uptime target for the cloud service.
- Multi-zone deployment with automated failover.
- Daily backups with point-in-time recovery for CRM data.
- Incident response runbooks and 24/7 on-call for Enterprise.
- Continuous evaluation of answer quality, hallucination rate and booking accuracy.
