# Revo Case

A small full-stack web app built for the Revo Tech intern case study. An admin logs in, submits a company (name, HQ, website), and the backend asks Google Gemini for a short summary of that company plus five competitors with their own summaries. The frontend lists every company you've ever submitted, lets you click into competitor names that match other companies you own, and polls the backend so newly-submitted rows flip from `pending` to `ready` without a page refresh.

## Prerequisites

- **Docker Desktop** (or any Docker engine that supports `docker compose`).
- A **Google Gemini API key**. The free tier is enough for testing — get one at [aistudio.google.com](https://aistudio.google.com/app/apikey).

That's it. You do **not** need Node, Python, or Postgres installed locally — everything runs in containers.

## Setup

```bash
git clone <this repo>
cd revo-case

# Backend env
cp api/.env.example api/.env
# Open api/.env and fill in:
#   GEMINI_API_KEY  — from https://aistudio.google.com/app/apikey
#   JWT_SECRET      — generate with: python3 -c "import secrets; print(secrets.token_urlsafe(48))"
# The other defaults are fine.

# Frontend env
cp ui/.env.example ui/.env
# No edits needed — the default points at the local API.
```

## Run

```bash
docker compose up --build
```

First boot takes ~2 minutes (pulling Postgres + Node + Python images, installing deps). Subsequent starts are seconds.

When you see `Vite ready` and `Uvicorn running` in the logs, open:

- **Frontend**: <http://localhost:5173>
- **API docs (Swagger)**: <http://localhost:8000/docs>

### Default credentials

```
username: admin
password: Revo123456
```

Both are configured via `api/.env`.

## Using the app

1. Visit <http://localhost:5173>, sign in.
2. Click **Create**. Fill in name, HQ, website (e.g. `Stripe`, `San Francisco, CA`, `stripe.com`).
3. The new company appears immediately with a `pending` badge.
4. Within ~10 seconds the badge flips to `ready`, the summary bullets appear, and 5 competitor mini-cards render below.
5. If a competitor's name matches another company you've already submitted, that competitor name becomes a clickable anchor — clicking jumps to that company's card.

History persists across `docker compose restart` (Postgres data lives in a named volume).


## Troubleshooting

- **`localhost:5173` shows nothing / CORS errors in console** — the API isn't reachable. Check `docker compose ps` and confirm `api` is `Up`. If it's restarting, run `docker compose logs api` for the traceback.
- **Login fails with "Invalid username or password"** — your `api/.env` doesn't match what you're typing. Defaults are `admin` / `Revo123456`.
- **`pending` rows never go `ready`** — Gemini is failing. Run `docker compose logs api` and look for the AI task exception. Most common cause: missing or invalid `GEMINI_API_KEY`.
- **Port already in use** — something else on your machine is on 5173, 8000, or 5432. Stop the conflicting process or change the host port mapping in `docker-compose.yml`.
- **Want to wipe everything and start fresh** — `docker compose down -v` removes containers *and* the database volume.
