# Shamim Styles API

FastAPI service backing the booking flow in `../frontend`. It will own bookings,
availability and M-Pesa payments.

## Stack

- **FastAPI** + **Uvicorn**
- **SQLAlchemy 2.0** (sync) with **Alembic** migrations
- **SQLite** locally, **Postgres** in production — one env var apart
- **pytest** with FastAPI's `TestClient`

Sync SQLAlchemy rather than async: FastAPI runs non-`async` path operations in a
threadpool, so sync sessions do not block the event loop, and they are markedly
easier to test and reason about at this scale.

## Getting started

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows; use source .venv/bin/activate elsewhere
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

The API listens on `http://localhost:8000`. Interactive docs are at `/docs`.

## Scripts

| Command | |
| --- | --- |
| `uvicorn app.main:app --reload` | Run with reload |
| `pytest` | Run the suite |
| `alembic upgrade head` | Apply migrations |
| `alembic revision --autogenerate -m "..."` | Create a migration from model changes |

## Layout

```
backend/
├── app/
│   ├── api/          # Routers, one module per resource
│   ├── models/       # SQLAlchemy models
│   ├── config.py     # Settings from the environment
│   ├── database.py   # Engine, session, declarative Base
│   └── main.py       # App factory, CORS, router mounting
├── alembic/          # Migrations
└── tests/
```

## Configuration

Settings come from the environment, falling back to `.env`. See
[`.env.example`](.env.example) for the full list. **Secrets are never defaulted
and never committed** — `.env` is gitignored.

Switching to Postgres is one variable:

```
DATABASE_URL=postgresql+psycopg://user:password@host:5432/shamim
```

Migrations run unchanged on both: Alembic is configured with `render_as_batch`,
so the table-rewrite SQLite needs happens automatically.

## Design rules

**The server is the price authority.** Clients send tier and addition *IDs*;
the server looks up its own catalogue and computes the total and deposit. An
amount sent by a client is never trusted. (Lands with the catalogue slice.)

**Money is stored in whole KES.** Prices in this business are whole shillings,
so amounts are integers — no floats anywhere near a total.
