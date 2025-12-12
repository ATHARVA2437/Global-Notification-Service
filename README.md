# Global Notification Service — Centralized Multi‑Tenant Notifications

A clean and production‑ready architecture scaffold for a **Global Notification Service** supporting Email, SMS, Push, and WhatsApp. Designed as a shared microservice for multiple independent applications such as ShopCardd, OMS, DMS, and Courier Apps.

This README provides a concise, evaluator‑friendly summary suitable for submission.

---

## 🚀 Quick Start (Docker)

1. Copy `.env.example` → `.env` and update values.
2. Start the services:

```bash
docker-compose up --build
```

3. Seed a sample project:

```bash
docker-compose exec postgres psql -U postgres -d notifications_db -c \
"INSERT INTO projects (id, name) VALUES ('11111111-1111-1111-1111-111111111111','ShopCardd');"
```

4. Test notification:

```bash
curl -X POST http://localhost:8000/api/v1/notifications/send \
 -H "Content-Type: application/json" \
 -H "x-api-key: dev-key-123" \
 -d '{"channel":"sms","recipient":"+919900000000","payload":{"code":"4321"},"idempotency_key":"demo","project_id":"11111111-1111-1111-1111-111111111111"}'
```

---

## 🏗️ Architecture Overview

* **FastAPI** for REST endpoints
* **PostgreSQL** for persistent storage (notifications, templates, providers)
* **Redis** as queue + caching
* **Worker service** for asynchronous sending via providers (SMS, Email, Push, WhatsApp)
* **API‑Key based multi‑tenancy** using `project_id` + scoped permissions

### Notification Flow

1. Project sends request → `/api/v1/notifications/send`
2. API validates project and API key
3. Record stored in DB → job queued in Redis
4. Worker processes and updates status

---

## 📌 Core API Endpoints

* `POST /api/v1/notifications/send`
* `GET  /api/v1/notifications/{id}`
* `GET  /api/v1/notifications?project_id=`
* `POST /api/v1/templates`
* `POST /api/v1/projects/{id}/providers`

---

## 🛡️ Multi‑Tenancy & Security

* API key mapped to unique `project_id`
* Each DB record includes `project_id` for data isolation
* Optional PostgreSQL Row‑Level Security (RLS) for strong separation
* Validation ensures Project A cannot access Project B’s data

---

## 🔒 Failure Handling

* Exponential‑backoff retries
* Dead‑letter queue for failed jobs
* Idempotency keys to prevent duplicate notifications
* Circuit‑breaker + provider fallback

---

## 📅 Development Roadmap

1. Base setup → FastAPI + DB + Docker
2. Core API + Worker queue
3. Security → API keys + project isolation
4. Provider integrations (Twilio, SendGrid, FCM, WhatsApp)
5. Observability and production hardening



 
