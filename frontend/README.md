# Shamim Styles

Marketing site and booking flow for Shamim Styles, a lash salon in Nairobi.
Built from the high-fidelity design prototypes in the handoff.

## Stack

- **Next.js 15** (App Router) + **React 19**
- **TypeScript** (strict)
- **CSS Modules** over a CSS-custom-property token layer — chosen over a utility
  framework because the design is built almost entirely on fluid `clamp()` scales,
  which read far better as named tokens than as arbitrary utility values.
- **next/font** for Merriweather + Rubik (self-hosted, no render-blocking request)

## Getting started

This app lives in `frontend/`, alongside the FastAPI service in `backend/`.

```bash
cd frontend
npm install
npm run dev
```

Other scripts: `npm run build`, `npm run start`, `npm run lint`, `npm run typecheck`.

## Folder structure

```
src/
├── app/                 # App Router routes + root layout
├── components/
│   ├── layout/          # Shell furniture shared by every page (nav, footer)
│   ├── ui/              # Design-system primitives (Button, …)
│   └── home/            # Route-specific composition
├── data/                # Content and configuration, kept out of components
└── styles/
    ├── tokens.css       # Design tokens — the single source of truth
    └── globals.css      # Reset, base elements, shared keyframes
```

Route-specific components live in a folder named after the route. Anything used by
two or more routes graduates to `ui/` or `layout/`.

## Design tokens

All colour, type, spacing, radii and motion values live in
[`src/styles/tokens.css`](src/styles/tokens.css). Component CSS reads tokens only —
no raw hex values. The fluid type and spacing scales mirror the prototype `clamp()`
values exactly, so the rendered output matches the design at every viewport rather
than only at breakpoints.

| Token | Value | Role |
| --- | --- | --- |
| `--color-deep-brown` | `#14100c` | Page background |
| `--color-dark-brown` | `#432818` | Card surfaces |
| `--color-maroon` | `#6F1D1B` | Accent, primary-button text |
| `--color-tan` | `#BB9457` | Selected states, borders, labels |
| `--color-cream` | `#FFE6A7` | Primary text and filled buttons |

## Backend

`../backend/` holds the FastAPI service that will own bookings and M-Pesa payments.
The front end currently models the booking flow client-side only.
