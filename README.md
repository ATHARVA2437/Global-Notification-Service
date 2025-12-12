# Global Microservices — Notification MVP (Dev Scaffold)

This repository contains a minimal **Global Notification Service** MVP (FastAPI + Postgres + Redis + worker)
and an architecture document for the Full Global Microservices assignment.

## Quickstart (requires Docker)
1. Copy `.env.example` to `.env` and edit if needed.
2. Start the stack:
   ```bash
   docker-compose up --build
   ```
3. Seed DB (in another terminal):
   ```bash
   docker-compose exec postgres psql -U postgres -d notifications_db -c "INSERT INTO projects (id, name) VALUES ('11111111-1111-1111-1111-111111111111','ShopCardd');"
   ```
4. Send a test notification:
   ```bash
   curl -X POST http://localhost:8000/api/v1/notifications/send \
     -H "Content-Type: application/json" \
     -H "x-api-key: dev-key-123" \
     -d '{"channel":"sms","recipient":"+919900000000","payload":{"code":"4321"}, "idempotency_key":"test-1"}'
   ```
5. Check worker logs — it will process and mark notification `sent`.

## What is included
- `docs/ARCHITECTURE.md` — architecture & implementation plan to submit
- Working API and worker to demonstrate notification flow
- VS Code tasks and launch configs for in-editor development


## Additional included files
- `docs/ARCHITECTURE.md` — completed architecture and implementation plan
- `docs/diagram.mmd` — mermaid diagram for architecture (importable to draw.io)
- `docs/sql/rls_example.sql` — RLS example
- `docs/openapi.yaml` — basic OpenAPI subset
