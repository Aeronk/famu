# 🌾 Famu / Murimi OS

**An AI-powered, WhatsApp-first Farm Operating System for African farmers.**

Murimi OS is a multi-tenant SaaS platform that lets smallholder & commercial
farmers, cooperatives, NGOs and extension officers manage farms, capture data
naturally over WhatsApp (English / Shona / Ndebele), and get AI advisory, yield
& disease predictions, scenario simulations, weather and market intelligence.

> Built with FastAPI · SQLAlchemy 2.0 (async) · Pydantic v2 · Alembic · Redis ·
> Celery · OpenAI + LangGraph · pgvector. Runs on **SQLite** out of the box and
> **PostgreSQL + pgvector** in production. **Boots with zero secrets** — every
> external integration falls back to a deterministic mock until you add keys.

---

## ✨ Features

- **Multi-tenancy** — single database, shared schema, `tenant_id` on every
  business object, auto-filtering repositories, optional Postgres RLS, Super Admin.
- **Auth & RBAC** — JWT access + rotating refresh tokens; roles: Super Admin,
  Tenant Admin, Farm Manager, Farmer, Extension Officer, Viewer.
- **Farm management** — farms, crops (+ activity timelines), Zimbabwe **tobacco**
  value chain (seedbed → reaping → curing → grading → deliveries + profitability),
  livestock (+ herd analytics), finance (cashflow / profitability / enterprise).
- **WhatsApp** — Meta Cloud API webhook: _"I planted 2 hectares of maize"_ →
  structured record + confirmation, with multi-turn follow-ups.
- **AI layer** — LangGraph agent (detect language → intent → entities → tool →
  reply), RAG advisory over a pgvector knowledge base, recommendation agent,
  and image analysis (`POST /ai/analyze-image`).
- **Predictions & simulations** — heuristic, ML-ready yield / disease / revenue
  models and a what-if scenario engine.
- **Analytics dashboards**, **multilingual engine**, **notifications**
  (WhatsApp / SMS / Email + scheduled Celery reminders).

See [`docs/erd.md`](docs/erd.md) for the data model.

---

## 🚀 Quickstart (SQLite — zero dependencies)

```bash
python -m venv .venv
.\.venv\Scripts\activate            # Windows  (source .venv/bin/activate on *nix)
pip install -r requirements-dev.txt

cp .env.example .env                 # defaults to SQLite; no secrets required
alembic upgrade head
python -m scripts.seed               # demo tenant, users, farm, market, RAG KB
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** (Swagger) or **/redoc**.

### Try it

```bash
# Register a tenant (returns JWT tokens)
curl -X POST localhost:8000/api/v1/auth/register-tenant -H "Content-Type: application/json" -d '{
  "tenant": {"name":"My Coop","slug":"my-coop","type":"cooperative"},
  "admin_email":"me@example.com","admin_password":"Password123","admin_full_name":"Me"
}'

# Yield prediction
curl -X POST localhost:8000/api/v1/predictions/yield -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" -d '{"crop":"maize","area":2,"rainfall_mm":650}'

# Simulate WhatsApp inbound (stub send)
curl -X POST localhost:8000/webhooks/whatsapp -H "Content-Type: application/json" -d '{
 "entry":[{"changes":[{"value":{"metadata":{"phone_number_id":"DEMO_PHONE_ID"},
 "contacts":[{"wa_id":"+263771234567","profile":{"name":"Tendai"}}],
 "messages":[{"from":"+263771234567","id":"1","type":"text","text":{"body":"I planted 2 hectares of maize"}}]}}]}]}'
```

## 🐘 PostgreSQL + pgvector (production parity)

Set in `.env`:

```
DATABASE_URL=postgresql+asyncpg://murimi:murimi@localhost:5432/murimi
```

Locally you can use the dev compose file (Postgres+pgvector & Redis only):

```bash
docker compose -f docker-compose.dev.yml up -d
alembic upgrade head && python -m scripts.seed
```

On Postgres, RAG uses native pgvector cosine search; on SQLite it falls back to
in-Python cosine similarity, so behaviour is identical for development.

---

## 🔌 Configuration

All settings come from env / `.env` (see [`.env.example`](.env.example)). Leave a
key blank to run that integration in **mock mode**:

| Variable | Effect when unset |
|----------|-------------------|
| `OPENAI_API_KEY` | Deterministic mock chat / embeddings / vision |
| `WHATSAPP_ACCESS_TOKEN` | Outbound messages are logged, not sent |
| `WEATHER_API_KEY` | Synthetic, seasonally-plausible weather |
| `SMS_API_KEY` / `EMAIL_SMTP_*` | Notifications are logged |
| `ENABLE_RLS` | Postgres row-level security (off by default) |

---

## 🧱 Architecture

Clean Architecture + DDD: **routers → services → repositories → models**, with an
in-process event bus, a tenant `contextvar`, and auto-scoping `TenantRepository`.

```
app/
├── api/            # versioned router aggregation + shared deps (auth, RBAC, pagination)
├── core/           # config, security (JWT), rbac, events, rate limiting, encryption, redis
├── database/       # async engine/session, Base, mixins, portable types (GUID/JSONB/vector)
├── tenancy/        # tenant context, middleware, auto-filtering repository
├── shared/         # base repo, schemas, exceptions, i18n (en/sn/nd)
├── modules/        # farms, crops, tobacco, livestock, finance, weather, market, auth, tenants
├── ai/             # llm client, LangGraph agent + tools, advisory, recommendation, rag, vision
├── whatsapp/       # Cloud API client, webhook, event-processing pipeline
├── predictions/    # ModelService interface + heuristic yield/disease/revenue models
├── simulations/    # scenario engine
├── analytics/      # dashboard aggregation endpoints
└── notifications/  # channels (whatsapp/sms/email) + Celery worker & beat tasks
```

---

## 🧪 Testing & quality

```bash
ruff check app tests scripts
pytest            # 32 tests: logic, auth, tenancy isolation, CRUD, WhatsApp, AI, dashboards
```

Tests run on an in-memory SQLite database (no services needed). CI also validates
the Postgres + pgvector migration path — see [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## ⚙️ Background jobs

```bash
celery -A app.notifications.celery_app worker --loglevel=info   # add -P solo on Windows
celery -A app.notifications.celery_app beat   --loglevel=info
```

Scheduled: vaccination & irrigation reminders, twice-daily weather sync, daily
disease-risk scan.

## 🚢 Deployment (Contabo + Apache, no Docker)

Gunicorn (uvicorn workers) behind Apache `mod_proxy`, with Celery worker/beat as
systemd units and GitHub Actions for CI/CD. Full guide: [`deploy/README.md`](deploy/README.md).

---

## 🗺️ Roadmap (interfaces ready, deferred from v1)

Trained ML models (heuristics today) · live provider keys · web/mobile dashboard
UI · production secrets management · additional languages (catalog structure ready).
