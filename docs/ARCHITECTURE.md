# Global Microservices — Architecture & Implementation Plan (Complete)

**Author:** Atharva Rathi
**Date:** 2025-12-12

---
## Executive summary
This document describes a Global Microservices platform offering centralized services (Notifications, Auth, Payments, Billing, Customer Support) that multiple client projects (ShopCardd, OMS, DMS, Courier App) can integrate with. Design goals: multi-tenancy, strong isolation, observability, scalability, and secure integrations with external providers.

---
## 1. High-Level Architecture
See `docs/diagram.mmd` (Mermaid) for the system diagram that you can paste into draw.io or markdown that supports Mermaid rendering.

Components:
- Clients: ShopCardd, OMS, DMS, Courier App
- API Gateway: authentication, rate-limiting, routing, JWT verification
- Global Services: Auth, Notifications, Payments, Billing, Support
- Internal: Postgres (primary), Kafka (event bus) or Redis Streams (smaller scale), Redis (cache & rate-limiter), S3 (object storage)
- Workers: per-service workers (notification delivery, billing scheduler, reconciliation)
- External Providers: Twilio (SMS/WhatsApp), SES/SendGrid (Email), FCM/OneSignal (Push), Stripe/PayPal/Bank APIs (Payments)
- Monitoring: Prometheus/Grafana, Jaeger, ELK/Loki

High-level flow (example: Project A sends notification):
1. Client -> API Gateway (x-api-key or Authorization: Bearer <JWT>)
2. Gateway authenticates, authorizes and forwards to Notification Service with authenticated `project_id` in headers.
3. Notification Service validates request, writes notification row (project_id scoped), emits event to `notifications.outbound` topic.
4. Notification Worker consumes event, resolves template, calls provider adapter (Twilio/SES/FCM), writes `notification_logs` and updates status.
5. If provider fails, worker retries (exponential backoff) and on final failure pushes to DLQ and notifies support/admins.

---
## 2. Global Notification Service (detailed)
**Responsibilities**: send Email/SMS/Push/WhatsApp, templating, user preferences, rate-limiting, retries, DLQ, audit logs.

**Core Components**:
- API layer (REST/gRPC) for clients
- Template store (DB/S3)
- Orchestrator for channel selection and fallback
- Async pub/sub (Kafka) and Workers (consumer groups)
- Provider adapters (Twilio, SES, FCM)
- Rate-limiting (Redis token bucket)
- Audit logs & metrics

**Important tables** (SQL):
- `templates(id, project_id, name, channel, body, is_active, created_at)`
- `notifications(id, project_id, channel, recipient, payload jsonb, template_id, status, idempotency_key, created_at)`
- `notification_logs(id, notification_id, attempt_no, provider, provider_response, status, created_at)`

**Key endpoints**:
- `POST /api/v1/notifications/send`
- `GET /api/v1/notifications/{id}`
- `POST /api/v1/templates`
- `GET /api/v1/templates`

**Idempotency & Dedup**: client-provided `idempotency_key` per `project_id`. Server stores and returns existing record if duplicate.

**Rate limiting**: per-project and per-recipient token bucket in Redis.

**Retry**: exponential backoff with jitter; DLQ after N attempts; create support ticket automatically for critical failures.

---
## 3. Global Auth Service (detailed)
**Responsibilities**: centralized user management, SSO (OIDC/SAML), issuing JWTs, API keys for M2M, RBAC, session management, SCIM for provisioning.

**Core tables**:
- `users(id, email, hashed_password, status, created_at)`
- `projects(id, name, org_id)`
- `roles(id, name, permissions)`
- `user_roles(user_id, role_id, project_id)`
- `api_keys(id, project_id, key_hash, scopes, expires_at)`

**Flows**:
- User login (Auth service) -> JWT with claims {user_id, project_id(s), roles}
- API call with `x-api-key` -> Gateway validates API key tied to project_id

**SSO**: enterprise customers => add SAML/OIDC connectors, mapping external identity attributes to internal users.

---
## 4. Global Payment Service (detailed)
**Responsibilities**: unified payments API, gateway adapters, transaction ledger, idempotency, reconciliation, payouts (vendors).

**Core tables**:
- `transactions(id, project_id, order_id, amount_cents, currency, status, provider, provider_txn_id, created_at)`
- `payouts(id, project_id, recipient_account, amount_cents, status, provider_payout_id, scheduled_at)`
- `reconciliation_entries(id, transaction_id, provider_report, matched_at)`

**Endpoints**:
- `POST /api/v1/payments/initiate`
- `POST /api/v1/payments/capture`
- `POST /api/v1/payments/refund`
- `POST /api/v1/payments/webhook` (provider -> our webhook)

**Idempotency**: idempotency_key per transaction to avoid duplicate charges.

**Reconciliation**: background job to match provider statements to local ledger; create exceptions for manual review.

---
## 5. Subscription & Billing Service (detailed)
**Responsibilities**: plan management, recurring billing, invoices, proration, trial handling.

**Tables**:
- `plans(id, project_id, name, price_cents, interval, features,jsonb)`
- `subscriptions(id, project_id, customer_id, plan_id, status, next_billing_date, trial_end_at)`
- `invoices(id, subscription_id, amount_cents, pdf_url, status, issued_at)`
- `payment_attempts(id, invoice_id, attempt_no, status, provider_response)`

**Billing engine**: scheduled worker that creates invoices, charges payment methods, retries failed payments, and triggers dunning flows.

---
## 6. Global Customer Support Service (detailed)
**Responsibilities**: ticketing, chat integration, SLA routing, attachments, auditability.

**Tables**:
- `tickets(id, project_id, customer_id, subject, description, status, priority, assignee_id, created_at)`
- `ticket_comments(id, ticket_id, author_id, body, created_at)`
- `attachments(id, ticket_id, url, uploaded_by)`

**Integrations**: Slack, Zendesk, Intercom adapters if customers already use those.

---
## 7. Multi-tenancy & Security
**Strategy**: project-scoped multi-tenancy enforced at three layers:
1. **API layer**: require JWT or `x-api-key` that carries `project_id`. Gateway injects `x-project-id` to services.
2. **DB layer**: Postgres Row-Level Security (RLS). Services set `SET LOCAL app.current_project = '<project_id>'` for DB session. RLS policies ensure rows must match `project_id`.
3. **Operational**: optional DB-per-tenant for very large tenants.

**RLS example**: see `docs/sql/rls_example.sql`

**Encryption & secrets**: use KMS/Vault for secrets; TLS in transit; field-level encryption for PII as required.

---
## 8. Observability & Monitoring
- Metrics: Prometheus metrics for request rates, latencies, queue lag, worker errors.
- Tracing: OpenTelemetry + Jaeger for distributed tracing.
- Logs: Structured JSON logs to Loki/ELK.
- Alerts: SLO based alerts on error rates and queue lag.

---
## 9. Failure handling & resilience
- **Provider failures**: retry with exponential backoff, then DLQ and admin notification.
- **DB outage**: if DB is down, accept requests into durable queue (Kafka) and process when DB recovers; fail fast for operations that must be atomic (payments).
- **Idempotency**: required for payments and notifications.
- **Circuit-breakers**: limit calls to misbehaving provider and fallback to alternate provider (e.g., SMS provider fallback).

---
## 10. Development Phases (concrete)
Phase 0: Doc + infra (1 week)
Phase 1: Notification MVP (2 weeks)
Phase 2: Auth + RLS (2 weeks)
Phase 3: Payments MVP (2-3 weeks)
Phase 4: Billing & Invoicing (2 weeks)
Phase 5: Support & admin UI (2 weeks)
Phase 6: Hardening & rollout (2 weeks)

Each phase includes tests, CI, infra as code, and monitoring setup.

---
## 11. Deliverables for submission
- `docs/ARCHITECTURE.md` (this file)
- `docs/diagram.mmd` (Mermaid diagram)
- `docs/sql/` (schemas & RLS examples)
- `services/` working Notification MVP code (for demonstration)
- README with quickstart and test calls

---
## 12. Appendix — quick cURL examples
Send notification sample:
```bash
curl -X POST http://localhost:8000/api/v1/notifications/send \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key-123" \
  -d '{"channel":"sms","recipient":"+919900000000","payload":{"code":"4321"}, "idempotency_key":"test-1"}'
```

Payment initiate sample (placeholder):
```bash
curl -X POST https://global-api.example.com/api/v1/payments/initiate -H 'Content-Type: application/json' -d '{"project_id":"proj_1","amount":1999,"currency":"INR","order_id":"ord_123","idempotency_key":"abc"}'
```

---
