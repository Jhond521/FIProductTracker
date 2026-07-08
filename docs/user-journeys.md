# Credit Tracker — User Journeys (MVP)

Companion to the PRD. Each journey includes the user's intent, what the system must do, and edge cases — now covering both the Colombia and US market rules where they diverge. Future-phase journeys are listed at the end, tagged.

---

## J1 — First-Time Onboarding & First Card Setup

**Intent**: a new user wants to see their credit card's real cost for the first time, in their own language and their own country's terms.

1. User lands on the app (English or Spanish, based on browser locale, overridable)
2. Clicks "Sign in with Google"
3. First-time login → no products exist → routed straight into "Add your first card"
4. User selects the card's **market** (Colombia / US) — this determines which fields appear next
5. **If Colombia**: user enters cupo, EA rate, tasa de mora, fecha de corte, fecha de pago, cuota de manejo, seguros, 1-installment interest rule, minimum payment rule, grace period rule, FX fee
6. **If US**: user enters credit limit, APR, penalty APR, billing cycle closing/due dates, annual fee (if any), whether an installment-plan feature is available and its terms, minimum payment rule, grace period rule, FX fee
7. User enters current purchases against that card, with market-appropriate fields (installment count for Colombia; standard purchase, with optional installment-plan opt-in, for US)
8. System computes the current/upcoming statement using the correct market's method and shows it
9. User is routed to the dashboard

**Edge cases**:
- User doesn't know their exact rate or minimum-payment formula — need a reasonable default path, clearly marked as estimated, per market
- User is mid-cycle when adding the card — historical data depth is an open product decision (PRD Section 10)
- A user with one Colombian and one US card should see both correctly represented on one dashboard, with no market-specific field bleeding into the wrong card's display

---

## J2 — Reviewing the Monthly Statement Breakdown (Core Loop)

**Intent**: a returning user wants to understand what they're being charged this month and why — regardless of which market their card belongs to.

1. User signs in, lands on dashboard showing aggregate stats across all cards
2. Selects one card
3. System shows the month-by-month view, computed via the correct method for that card's market (per-purchase accrual for Colombia; average daily balance for US)
4. Drills into a specific month → sees contributing purchases and each one's share
5. Drills into a specific purchase → sees its full lifecycle: total cost, interest paid to date, remaining installments/plan terms (if any), real annualized cost

**Edge cases**:
- A US purchase with no installment plan simply contributes to the revolving balance — the drill-down should present this clearly rather than forcing an "installments" framing that doesn't apply
- Purchases after the cutoff/closing date land in the next period, for either market
- Grace period logic differs by market (per-period "pago total" vs. previous-balance-paid-in-full condition) — the UI explanation of *why* interest was or wasn't charged should reflect the correct rule for that card

---

## J3 — Adding a New Purchase to an Existing Card

**Intent**: user made a new purchase and wants it reflected accurately.

1. From the card's detail view, selects "add purchase"
2. Enters amount, currency, date, and market-appropriate terms (installments for Colombia; standard purchase or optional installment-plan opt-in for US)
3. System recalculates: assigned statement period, updated month-by-month view, updated recommendations
4. User sees the update reflected immediately

**Edge cases**:
- Foreign-currency purchase — FX fee applies automatically in either market
- US installment-plan opt-in after the fact (some issuers allow converting an existing purchase into a plan later) — worth deciding if this is MVP or Phase 2 during build

---

## J4 — Editing a Card or Purchase, with Recalculation

**Intent**: correcting a rate, fixing an entry error, or updating promo/plan terms.

1. User navigates to the card or purchase, selects edit
2. Updates the relevant field(s)
3. System recalculates every downstream figure using the correct market rules profile
4. User sees updated state everywhere, no stale numbers

**Edge cases**:
- Editing a *past* purchase's terms — retroactive vs. forward-only recalculation is a product decision, not a technical one (PRD Section 10), and applies identically regardless of market
- Changing a card's market after creation should not be allowed silently — this would invalidate the whole calculation history; if ever needed, treat it as effectively creating a new product

---

## J5 — Viewing Recommendations

**Intent**: user wants to know what to actually do next.

1. From the dashboard or a specific card, views "recommendations"
2. System surfaces deterministic, specific recommendations, correctly reasoned for that card's market (e.g. minimum-payment delta uses the right formula; grace-period advice reflects the right condition)
3. User can drill into the numbers behind a recommendation

**Edge cases**:
- Cross-market payoff ranking (a Colombian card and a US card competing for "pay this first") — needs a common comparable metric (real annualized cost) even though the underlying calculation methods differ
- No actionable recommendation exists — system says so clearly

---

## Future-Phase Journeys (Tagged, Not MVP)

**J6 — Statement OCR Upload [Phase 2]**: parse a PDF statement (format differs meaningfully between Colombian and US issuers) and reconcile against existing data.

**J7 — Third-Party API Integration [Phase 3]**: external developer integrates via the versioned public API.

**J8 — Adding a Non-Credit-Card Product [Phase 2]**: línea de crédito (CO) or personal loan/HELOC (US), reusing the amortization-schedule path of the engine.

**J9 — Notifications [Phase 2]**: reminders ahead of cutoff/closing, due date, or promo/plan expiration.

**J10 — Adding a Third Market [Phase 2]**: validates that the `MarketRulesProfile` abstraction actually holds up under a new country's rules, without touching existing Colombia/US logic.
