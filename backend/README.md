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
python -m app.seed
uvicorn app.main:app --reload
```

The API listens on `http://localhost:8000`. Interactive docs are at `/docs`.

## Scripts

| Command | |
| --- | --- |
| `uvicorn app.main:app --reload` | Run with reload |
| `pytest` | Run the suite |
| `alembic upgrade head` | Apply migrations |
| `python -m app.seed` | Seed the catalogue (idempotent) |
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

Percent-encode special characters in the password — `@` becomes `%40`, since a
bare `@` would be read as the host delimiter.

Set `ENVIRONMENT=production` when deployed: it refuses to start on a wildcard
`CORS_ORIGINS`, which paired with credentialed CORS would let any site call the
API on a user's behalf.

Migrations run unchanged on both: Alembic is configured with `render_as_batch`,
so the table-rewrite SQLite needs happens automatically.

## Endpoints

| | |
| --- | --- |
| `GET /api/health` | Liveness, including a database round trip |
| `GET /api/catalogue` | The menu, in display order |
| `GET /api/availability?date=YYYY-MM-DD` | Every slot for a day, free or taken |
| `POST /api/bookings` | Create a booking |

## Design rules

**The server is the price authority.** Clients send tier and addition *IDs*;
the server looks up its own catalogue and computes the total and deposit. An
amount sent by a client is never trusted.

The catalogue lives in the database and is seeded from `app/seed.py`, whose
values mirror `frontend/src/data/services.ts`. Seeding is idempotent and
merges rather than replaces, so bookings keep referencing a live tier.

**Money is stored in whole KES.** Prices in this business are whole shillings,
so amounts are integers — no floats anywhere near a total. The deposit rule is
half the total to the nearest 50, floored at 100, computed with integer
arithmetic so it matches the frontend exactly: Python rounds half-to-even and
JavaScript rounds half-up, which would otherwise disagree by 50 on some totals.

**Amounts are frozen onto a booking.** A booking records what it cost when it
was made, so a later price change cannot rewrite what someone agreed to pay.

**A slot holds one live booking.** The uniqueness index is partial, covering
only pending and confirmed bookings, so cancelling or expiring one frees the
time rather than blocking it forever. Unpaid M-Pesa holds lapse after
`HOLD_MINUTES` and are released lazily whenever availability is read or a
booking is made — there is no background worker yet.

**Times belong to the salon, not the server.** Whether a slot has passed is
judged against `SALON_TIMEZONE`, and per slot rather than per day — comparing
whole dates would leave the morning's appointments on offer all afternoon.
Bookings are bounded by `MAX_BOOKING_LEAD_DAYS` so a slot cannot be held years
out where nobody would see it.

**Timestamps are UTC and timezone-aware**, via the `UtcDateTime` type. SQLite
has no aware type and would otherwise hand back naive values that crash on
comparison, while Postgres would not — the same code failing in only one
environment.
