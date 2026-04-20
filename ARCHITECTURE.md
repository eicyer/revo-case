# Architecture

## What the app does

An admin signs in, submits a company (name, HQ, website), and the system uses Google Gemini to generate a short summary of that company plus five named competitors with their own summaries. Submissions are persisted; the home page shows the full history with their AI-generated content inline.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Database | Postgres 16 | Standard relational store. JSON columns let us avoid an extra table for competitors (see below). |
| Backend | FastAPI + SQLAlchemy 2 (async) + asyncpg | Async I/O matters because every request that creates a company is bottlenecked on Gemini network latency. Pydantic gives us request/response validation for free. Auto-generated Swagger at `/docs` is a free win for the spec's "API documentation" requirement. |
| AI | Google Gemini 2.5 Flash via `google-genai` SDK | Cheap, fast, supports JSON-mode (structured output) so we never have to parse free-form text. |
| Auth | JWT (HS256) via `python-jose` | Stateless — no session table, no sticky sessions. Hardcoded admin credentials in env vars per the spec. |
| Frontend | Vite + React 19 + TypeScript | Vite gives instant HMR; TypeScript catches API-shape mismatches at the call site. |
| UI | Tailwind v4 + shadcn/ui | shadcn copies component source code into the repo so the reviewer can read it. No invisible dependency lock-in. |
| Data fetching | TanStack Query | Built-in caching, deduplication, and `refetchInterval` — exactly what we need for the polling UX. |
| Routing | react-router-dom v7 | Two routes (`/login`, `/`) with an auth gate. |
| Infra | docker-compose | Three services (`db`, `api`, `ui`) brought up with one command. The reviewer needs Docker and nothing else. |

## Services

### `db`
Postgres 16 with a named volume so data persists across container restarts. Healthcheck so `api` waits for it before booting.

### `api`
FastAPI behind uvicorn. On startup, runs `Base.metadata.create_all` to materialize the schema — no Alembic migrations, since the case study has one table that never changes.

Key modules:
- `app/main.py` — app construction, CORS for `localhost:5173`, router mounting, startup lifespan.
- `app/config.py` — `pydantic-settings` reads `DATABASE_URL`, `JWT_SECRET`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `GEMINI_API_KEY` from `.env`.
- `app/db.py` — async SQLAlchemy engine + session factory.
- `app/models.py` — single `Company` SQLAlchemy model.
- `app/auth.py` — JWT encode/decode and the `get_current_admin` dependency that protects every `/companies` route.
- `app/ai.py` — `generate_company_intel(name, hq, website)` calls Gemini with a JSON-schema-constrained prompt and returns a parsed dict.
- `app/routers/auth.py` — `POST /auth/login`.
- `app/routers/companies.py` — `POST /companies`, `GET /companies`, `GET /companies/{id}`, plus the background AI task.

### `ui`
Vite dev server in a Node container, with the host `ui/` directory bind-mounted in for live editing. Vite's HMR pushes changes to the browser without a page reload.

## Data model

One table:

```sql
companies (
  id           SERIAL PRIMARY KEY,
  name         VARCHAR(255)  NOT NULL,
  hq           VARCHAR(255)  NOT NULL,
  website      VARCHAR(512)  NOT NULL,
  status       VARCHAR(20)   NOT NULL DEFAULT 'pending',  -- pending | ready | failed
  summary      JSONB,                                     -- list of bullet strings, null until ready
  competitors  JSONB,                                     -- [{name, summary:[bullet,...]}, ...] x5
  error        TEXT,                                      -- populated when status='failed'
  created_at   TIMESTAMPTZ   NOT NULL DEFAULT now()
)
```

**Why competitors live as a JSON column instead of a normalized child table:**
- We never query a competitor in isolation — every read fetches a company *with* its competitors.
- Competitors are immutable after the AI task finishes; no row-level updates to manage.
- Five competitors per company is small and bounded; no pagination concerns.
- Two columns of JSON beats two tables + a join + an N+1 risk.

The trade-off we accept: we can't easily ask "which companies list X as a competitor?" If the product evolved that way, we'd promote competitors to their own table with a foreign key.

**Cross-linking without a foreign key.** When a competitor's name matches a company you've previously submitted, the API stamps `known_company_id` on the competitor object at read time (computed in Python from a single extra query). The frontend turns that into an in-page anchor link. We avoided storing the relationship as a real FK because competitor names from Gemini are fuzzy strings, not stable identifiers — re-running the AI task could change them.

## API surface

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/auth/login` | none | Form-encoded `username`/`password`. Returns `{access_token, token_type:"bearer"}`. |
| `POST` | `/companies` | bearer | Insert a `pending` row, schedule the background AI task, return the row. |
| `GET` | `/companies` | bearer | List all companies, newest first, with cross-link IDs stamped. |
| `GET` | `/companies/{id}` | bearer | Fetch one company. |
| `GET` | `/health` | none | Liveness check. |
| `GET` | `/docs` | none | Auto-generated Swagger UI. |

## The AI flow — async by design

Gemini takes 5–15 seconds per request. If `POST /companies` waited for it synchronously, the user would stare at a hung form. So the request flow is:

1. `POST /companies` validates the input, inserts a row with `status='pending'` and `summary=null`, schedules a FastAPI `BackgroundTasks` callback, and returns 201 immediately.
2. The background callback opens its **own** `AsyncSession` (the request session is closed by the time it runs), calls `generate_company_intel`, and on success writes `status='ready'` + the summary + competitors. On exception it writes `status='failed'` + the error string.
3. The frontend polls `GET /companies` every 2 seconds while any row is still `pending`. Once nothing is pending, polling stops automatically.

This gets us the "submit and watch it fill in" UX without standing up Redis, Celery, or websockets. The trade-off is durability: a background task lives in the API process, so an `api` container restart mid-Gemini-call drops the work. For a case study that's acceptable; for production we'd move the work to a real queue.

### Sequence

```
User              UI (React)         API (FastAPI)        Postgres        Gemini
 │                    │                   │                   │              │
 │ click "Create"     │                   │                   │              │
 ├───────────────────>│                   │                   │              │
 │                    │ POST /companies   │                   │              │
 │                    ├──────────────────>│                   │              │
 │                    │                   │ INSERT (pending)  │              │
 │                    │                   ├──────────────────>│              │
 │                    │                   │<──────────────────┤              │
 │                    │ 201 + row         │ schedule bg task  │              │
 │                    │<──────────────────┤                   │              │
 │ "pending" badge    │                   │                   │              │
 │<───────────────────┤                   │                   │              │
 │                    │                   │                   │              │
 │                    │   ── background task runs ──          │              │
 │                    │                   │                   │              │
 │                    │                   ├──────── prompt ───────────────── >│
 │                    │                   │<───────── JSON ─────────────────── ┤
 │                    │                   │ UPDATE (ready,    │              │
 │                    │                   │   summary, comps) │              │
 │                    │                   ├──────────────────>│              │
 │                    │                   │<──────────────────┤              │
 │                    │                   │                   │              │
 │                    │ GET /companies    │                   │              │
 │                    ├──────────────────>│ (every 2s while   │              │
 │                    │                   │  any pending)     │              │
 │                    │                   │ SELECT *          │              │
 │                    │                   ├──────────────────>│              │
 │                    │                   │<──────────────────┤              │
 │                    │ list w/ "ready"   │                   │              │
 │                    │<──────────────────┤                   │              │
 │ summary + 5        │ polling stops     │                   │              │
 │ competitors        │                   │                   │              │
 │<───────────────────┤                   │                   │              │
```

## Auth

The case spec hardcodes `admin` / `Revo123456`, so we keep credentials in `api/.env` and compare with `secrets.compare_digest` (constant-time, dodges timing attacks). No password hashing — there's nothing to hash, the plaintext is the spec.

On successful login the API signs a JWT (HS256, 24-hour expiry) and the frontend stashes it in `localStorage`. Every subsequent request goes through a single `apiFetch` wrapper that adds the `Authorization: Bearer <token>` header. The auth state is also mirrored in React Context so component renders react to login/logout.

The `localStorage`-vs-`httpOnly`-cookie trade-off: `localStorage` is reachable from any JavaScript on the page, so a successful XSS attack could exfiltrate the token. The "secure" alternative is httpOnly cookies + CORS-with-credentials + a CSRF token, which is overkill for a single-admin case-study app. We'd revisit this for a production system.

## Things deliberately left out

- **Migrations** — `Base.metadata.create_all` on startup is fine for one table.
- **Password hashing** — credentials are hardcoded plaintext per the spec.
- **Refresh tokens** — 24-hour access token; you log in again.
- **Rate limiting / production hardening** — the rubric is "clean and working," not "production-grade."
- **Tests** — out of scope for the case study and would multiply the file count.
- **Real job queue (Redis + Celery / Arq)** — `BackgroundTasks` is enough for a demo; the trade-off is documented above.
