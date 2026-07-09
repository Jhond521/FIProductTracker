# Credit Tracker — Design Brief (Layout Phase)

Companion to `docs/prd.md` and `docs/user-journeys.md`. This brief scopes
the layout/visual design pass for the screens that already have working
backend logic behind them — read the PRD and journeys docs for full
product context before designing; this file only covers what to design
right now and the real data to ground it in.

---

## 1. What's in scope for this pass

Four screens, corresponding to journeys J1 and J2 (see
`docs/user-journeys.md`) — the only two journeys with working backend
logic behind them so far:

1. **Dashboard** — aggregate view across the user's cards, entry point to add a new card
2. **Add card** — form to register a credit card (Colombia market only, for now)
3. **Add purchase** — form to log a purchase against a card, deferred into installments
4. **Statement / schedule view** — the actual product value: real principal/interest breakdown per installment, total interest cost, real annualized cost

A rough functional click-through of these four screens already exists (built
during the layout-planning conversation) — it proves the navigation flow
and uses real verified numbers, but is intentionally unpolished. Treat it
as a reference for *what connects to what*, not for visual style.

---

## 2. What's explicitly NOT in scope (don't design yet)

- **Recommendations screen** — the recommendation engine isn't built yet (PRD Section 11, Phase-adjacent). Designing this screen now means designing against logic that doesn't exist, and it will need to be redone once the engine's actual output shape is known.
- **Multi-purchase month-by-month aggregation** — the Statement screen in scope here shows one purchase's schedule. The fuller "which purchases feed this month's total" aggregation (J2's full scope) isn't built on the backend yet — don't design that drill-down until it is.
- **US market fields** — only Colombia's calculation path is implemented. The Add Card form should not surface APR, installment-plan opt-in, or other US-specific fields yet.
- **Language toggle / i18n** — bilingual English/Spanish support is a real MVP requirement (PRD Section 4), but implementing an actual language switch is a build-phase concern, not a layout-phase one. Design in one language (English is fine) and leave a visible affordance (e.g. a language selector in the header) so the layout has room for it later, without needing working translation now.

---

## 3. Real data to design against (don't use placeholder/lorem ipsum)

Use these actual verified numbers so the design reflects real content
shapes (currency formatting, number lengths, table density) rather than
guessed-at placeholder data:

**Card**: Banco Demo, Colombia, credit limit 5,000,000 COP, EA rate 36%, day-count basis 365

**Purchase**: "Electrodomestico", 600,000 COP, 6 installments, purchase date 2026-07-01

**Resulting schedule** (principal/interest split, all six installments):

| Installment | Payment | Principal | Interest | Balance |
|---|---|---|---|---|
| 1 | 109,278 | 93,705 | 15,573 | 506,295 |
| 2 | 109,278 | 96,137 | 13,141 | 410,158 |
| 3 | 109,278 | 98,633 | 10,646 | 311,525 |
| 4 | 109,278 | 101,193 | 8,086 | 210,332 |
| 5 | 109,278 | 103,819 | 5,459 | 106,514 |
| 6 | 109,278 | 106,514 | 2,765 | 0 |

**Headline figures**: total interest cost $55,669 COP, real annualized cost ~18.6%

Colombian number formatting convention: period as thousands separator, comma as decimal (the reverse of US convention) — worth reflecting in the design even though the mockup above used plain digit grouping for simplicity.

---

## 4. Design goals

- **Modern, clean fintech aesthetic** — the user's own words for the product were "a modern UI." Nothing more specific was prescribed, so use good design judgment; avoid anything that reads as a generic admin-panel template.
- **Easy navigation between the four screens** — the rough mockup's flat button-row navigation was flagged as hard to navigate; solve this properly (clear hierarchy, obvious way back to the dashboard, clear indication of which card/purchase you're looking at).
- **The Statement screen is the actual product value** — the principal/interest breakdown per installment is what makes this app different from just looking at a bank statement. It deserves the most design attention of the four screens, not the least.
- **Numbers must be scannable** — this is a financial product; users will scan for specific figures (total interest, real cost) more than read prose. Design for that.

---

## 5. What happens after this design pass

Once layout is approved, implementation moves to a real React frontend
(Vite), per the architecture already decided in `docs/prd.md` and the
repo's structure. This brief is for the design conversation only — no
code expected as output of this phase.
