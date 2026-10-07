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
| `python -m app.sync_calendar` | Add any confirmed bookings the calendar is missing (idempotent) |
| `alembic revision --autogenerate -m "..."` | Create a migration from model changes |

## Layout

```
backend/
├── app/
│   ├── api/          # Routers, one module per resource
│   ├── models/       # SQLAlchemy models
│   ├── services/     # Booking, pricing, payments; M-Pesa and calendar providers
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
| `POST /api/bookings` | Create a booking; sends an M-Pesa prompt when the deposit is by M-Pesa |
| `GET /api/bookings/{reference}` | Look a booking up, to poll for payment |
| `POST /api/mpesa/callback/{secret}` | Safaricom's verdict on a prompt |

## M-Pesa

Payment is asynchronous: the prompt is accepted at once, and whether the client
entered their PIN arrives later on a callback. A booking therefore holds its
slot as `pending_payment` until the callback settles it.

`MPESA_PROVIDER=fake` records prompts in memory rather than sending them, so the
whole flow runs without credentials or a public URL. Production refuses to start
on the fake, and refuses to start without the credentials and callback secret.

### Running against the real sandbox

1. Create an app at [developer.safaricom.co.ke](https://developer.safaricom.co.ke)
   and copy its Consumer Key and Secret.
2. Expose the API: `ngrok http 8000`, and copy the https URL.
3. Generate a callback secret:
   `python -c "import secrets; print(secrets.token_urlsafe(32))"`
4. Put all four in `.env`, and set `MPESA_PROVIDER=daraja`.
5. Book with `payment_method: "mpesa"` and a real Safaricom number. The prompt
   arrives on the handset; answering it confirms the booking.

The callback URL is built for you as
`<MPESA_CALLBACK_BASE_URL>/api/mpesa/callback/<MPESA_CALLBACK_SECRET>`.

Three things the callback handler does not take on trust:

- **The URL carries an unguessable secret.** Safaricom does not sign callbacks,
  so without it anyone who found the endpoint could confirm a booking nobody
  paid for.
- **The amount is checked against what we asked for**, not read from the
  payload.
- **It is idempotent**, keyed on `CheckoutRequestID`. Safaricom retries until it
  gets a 200, so the same confirmation arrives more than once.

A failed or cancelled payment leaves the hold running rather than tearing it
down, so the client can answer a fresh prompt without losing the slot; if they
do nothing it lapses on its own.

## Google Calendar

Shamim has no admin screen; her view of bookings is her Google Calendar. Each
booking is added as an event the moment it is confirmed — straight away when
paying at the studio, on the callback when the deposit is by M-Pesa. A held
slot that is never paid for never appears.

The event carries the client's name and phone, the set and additions, the total,
the deposit and its M-Pesa receipt, the balance due, and any notes.

`CALENDAR_PROVIDER=fake` records events in memory rather than sending them.
Production refuses to start on the fake, and refuses a missing or malformed key.

Two rules shape how it runs:

- **A calendar outage never undoes a booking.** The event is added after the
  response is sent, so the client and Safaricom never wait on Google, and a
  failure cannot fail a payment that already settled.
- **A miss is retried.** Each run adds *every* confirmed upcoming booking the
  calendar is missing, so the next confirmation catches up whatever an outage
  left behind. `python -m app.sync_calendar` does the same on demand, or from
  cron. Event ids derive from the booking reference, so nothing lands twice.

### Setting it up

1. In the [Google Cloud console](https://console.cloud.google.com), create a
   project and enable the **Google Calendar API**.
2. Under **IAM & Admin → Service Accounts**, create a service account, then
   **Keys → Add key → JSON**. Keep the downloaded file out of the repo.
3. In Google Calendar on a computer, create a calendar for bookings — say
   "Shamim Styles bookings". A separate calendar gets its own colour and
   notification settings, and the service account can touch nothing else.
4. In that calendar's settings, **Share with specific people** → add the key's
   `client_email` with **Make changes to events**.
5. Copy the **Calendar ID** from **Integrate calendar** into
   `GOOGLE_CALENDAR_ID`.
6. Put the key on one line in `GOOGLE_SERVICE_ACCOUNT_JSON`:
   `python -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))))" key.json`
7. Set `CALENDAR_PROVIDER=google`, make a studio booking, and check it appears.

Set **Event notifications** on the bookings calendar too — for example a day
before and an hour before. Events added by the service account use that
calendar's defaults, and Google does not reliably alert her when one is added,
so these reminders are how she hears about a booking without opening the
calendar.

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
