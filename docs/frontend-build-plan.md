# Credit Tracker — Frontend Build Plan

Companion to `docs/prd.md`, `docs/user-journeys.md`, and `docs/design-brief.md`.
Hand this to Claude Code once the design from Claude Design is approved.

---

## 1. Scope of this build

Implement the four screens covered in `docs/design-brief.md` (Dashboard,
Add Card, Add Purchase, Statement view) as real, working React components,
wired to the actual backend API — not mock data. This covers journeys J1
and J2 only (`docs/user-journeys.md`), matching what the backend actually
supports right now.

**Explicitly not in scope**: Recommendations screen, multi-purchase
month aggregation, US market fields, working language toggle — same
exclusions as the design brief, for the same reason (no backend logic
behind them yet).

---

## 2. Source of truth for the API contract

Don't re-derive field names or request shapes from the design mockup or
from memory of this conversation — use the live, deployed API's own
generated contract instead:

- Dev environment's `/openapi.json` (or `/docs` for the interactive version)
- The three endpoints already live and verified in all four environments:
  - `POST /api/v1/internal/products`
  - `POST /api/v1/internal/products/{id}/purchases`
  - `GET /api/v1/internal/products/{id}/purchases/{id}/schedule`

If the design brief's field names differ from what the API actually
expects, the API is correct — it's already deployed and tested — and the
component should conform to it, not the other way around.

---

## 3. Project structure

Add a `frontend/` folder alongside `backend/`, at the repo root:

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── AddCard.tsx
│   │   ├── AddPurchase.tsx
│   │   └── Statement.tsx
│   ├── api/           # typed API client functions, one per endpoint
│   └── components/    # shared UI pieces
├── Dockerfile
├── package.json
└── vite.config.ts
```

Vite + React, matching the stack already decided in `docs/prd.md`.

---

## 4. Build order — one journey at a time, tested against the real API

Same "walking skeleton" discipline that made the backend phase go
smoothly: build and manually verify one thing before starting the next,
rather than building all four screens and testing at the end.

1. Scaffold the Vite project, get a blank page rendering
2. Build **Add Card** first — simplest form, and every other screen needs
   at least one card to exist. Wire it to `POST /api/v1/internal/products`
   against the local Dev backend (via `docker compose`) and confirm a real
   card gets created (check via `/docs` or a direct API call) before
   moving on
3. Build **Dashboard** — even with just one card, confirm it correctly
   fetches and displays real data from the API, not the mock numbers used
   in the design phase
4. Build **Add Purchase** — wire to `POST .../purchases`, confirm a real
   purchase appears against the card created in step 2
5. Build **Statement view** — wire to `GET .../schedule`, confirm the
   displayed numbers match what a direct API call returns (this is the
   easiest step to sanity-check, since the exact expected numbers are
   already known from prior verification)

Only after all four work locally against the local Dev backend should
containerization/deployment be considered (Section 5).

---

## 5. Containerization and deployment (later, not first)

Once all four screens work locally:

1. Add a `Dockerfile` for the frontend (multi-stage: build the static
   assets, serve via a lightweight server)
2. Add `frontend` as a third service in `docker-compose.yml`, alongside
   `backend` and `postgres`
3. Confirm the full stack (frontend + backend + postgres) works together
   locally via `docker compose up` before touching Railway
4. Only then repeat the same Railway pattern already proven for the
   backend: Dev first, verify end-to-end, then duplicate forward to
   QA/UAT/Prod — same lessons apply (Root Directory, `targetPort`,
   environment variable scheme, the transient-deployment-record caveat)

This section is explicitly a later step — don't jump to deployment before
the frontend works cleanly against the local Dev backend first.

---

## 6. What to tell Claude Code

A reasonable first prompt, once the design is ready:

> "Read `docs/prd.md`, `docs/user-journeys.md`, `docs/design-brief.md`,
> and `docs/frontend-build-plan.md`. Build the frontend per Section 4 of
> the build plan, one journey at a time, verifying each against the local
> Dev backend via `docker compose` before moving to the next. Use the
> live `/openapi.json` as the API contract, not assumptions from the
> design mockup. Stop after each numbered step and show me it working
> before continuing to the next."

That last instruction matters — the same "confirm before proceeding"
discipline that mattered for the Prod deploy applies here too, just at
a smaller scale: better to catch a wiring mistake after step 2 than
after all four screens are built.
