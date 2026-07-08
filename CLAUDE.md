# Credit Tracker — Claude Code Instructions

## What this project is
A credit card cost-transparency app (Colombia + US markets planned). Full product
context lives in `docs/prd.md` and `docs/user-journeys.md` — read these before
making product decisions, not just architectural ones.

## Current status: walking skeleton
Only the Colombia market is implemented right now, end-to-end:
create a card → add a purchase (with installments) → get the real
principal/interest amortization schedule. US market support and the
`MarketRulesProfile` abstraction described in `docs/prd.md` Section 5 are
**not yet built** — the `market` and `day_count_basis` fields exist on the
model already so this is additive later, not a migration that touches
existing rows.

## Architecture
Modular monolith (see `docs/prd.md` Section 5 for the reasoning — deliberately
not microservices yet). Module boundaries inside `backend/app/`:

- `calculations/` — pure functions, no framework/DB imports. This is the most
  important module in the codebase: it's the actual product value
  (real cost of a purchase, correctly split into principal/interest per
  installment). Never import from `api/` here. Test-first, always.
- `products/` — SQLAlchemy models + Pydantic schemas for FinancialProduct/Purchase
- `core/` — config, DB session
- `api/v1/internal/` — routes for the app's own frontend (not yet built)
- `api/v1/public/` — reserved for the future third-party API (Phase 3, not built)
- `accounts/`, `integrations/` — reserved, empty for now

## Commands
```bash
cd backend

# Install deps (editable + dev extras)
pip install -e ".[dev]" --break-system-packages   # or use a venv

# Run tests
pytest tests/ -v

# Lint
ruff check app tests

# Run locally with Postgres via Docker
cd .. && docker compose up --build

# Run migrations (once Postgres is up)
cd backend && alembic upgrade head
```

## Conventions
- All money values as `float` in the API layer, `Numeric` in the DB — never
  use raw floats for anything touching persistence-level financial precision
  beyond what's already modeled; flag if this needs revisiting for real money.
- EA (effective annual rate) is the source of truth for Colombian products;
  daily/monthly periodic rates are always derived via geometric conversion
  (`app/calculations/rates.py`), never simple/linear conversion.
- `day_count_basis` (360/365) is a per-product field, not inferred from
  market — see `docs/prd.md` Section 5 for why.
- New calculation logic goes in `calculations/`, gets unit tests first,
  before any endpoint touches it.
- Integration tests use in-memory SQLite (fast, no Docker needed for
  `pytest`); `docker-compose` with real Postgres is for manual/local runs
  and will be wired into CI once the pipeline reaches a Dev environment.

## What NOT to do without checking with the user first
- Don't add the US market rules, additional product types, or the public API —
  these are explicitly out of MVP scope (`docs/prd.md` Section 11).
- Don't change `day_count_basis` to be market-inferred — this was a deliberate
  product decision (per-bank variation in Colombia).
- Don't touch the amortization formula in `calculations/amortization.py`
  without adding/updating tests that prove it still reconciles to zero
  remaining balance.
