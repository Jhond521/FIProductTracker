# Credit Tracker — Product Requirements Document (MVP)

Status: Draft v2 — Product Framing & Scope (multi-market)
Owner: [You]
Last updated: 2026-07-07

---

## 1. Problem & Vision

Credit card statements obscure the true cost of a purchase: the interplay of interest rate, installments (where applicable), fees, and billing-cycle dates makes it hard for a consumer to know what a purchase actually costs them, or which of their debts is doing the most damage. This is true across markets, though the exact mechanics differ — Colombian cards assign installment terms per purchase; US cards typically run a single revolving balance with optional add-on installment features. Banks in neither market have much incentive to make this transparent.

**Vision**: give the individual consumer a 1-on-1 mirror of their own credit card — matching the bank's real math exactly, in their own country's terms and their own language — plus deterministic, actionable advice on what to pay down first and how to use the card in a healthier way.

**Why credit cards first**: highest-frequency pain point, most complex cost structure, and the product type where "hidden real cost" does the most damage. Other product types generalize the same engine later.

**Why Colombia and US together, from MVP**: broadens the addressable user base immediately and forces the calculation engine to be built correctly (parameterized by market) from day one rather than accreting Colombia-specific assumptions that would need to be unwound later.

---

## 2. Target User & Primary Persona

**Primary persona**: an individual consumer managing their own credit card(s) in Colombia or the US, reasonably financially literate but without visibility into daily/monthly interest math.

**Note**: a single user may hold cards from both markets (e.g. a Colombian card and a US card) — the data model treats *market* as a property of each card, not of the user account.

**Not in scope for MVP**: financial advisors managing multiple clients, businesses, third-party developers (distinct persona for a later phase — see Section 11).

---

## 3. Goals & Success Metrics

| Goal | Metric |
|---|---|
| Match the bank's real math, per market | Calculated statement total matches a real test statement within rounding tolerance, independently verified for both a Colombian and a US card |
| Make cost visible per purchase | User can see, for any single purchase, its total interest cost and real annualized cost within 2 clicks of the dashboard |
| Make advice actionable | Recommendation engine surfaces at least one concrete, specific action per active card per month |
| Work in the user's language | Full UI parity between English and Spanish — no untranslated strings |
| Reduce manual burden (Phase 2 target) | Statement OCR import reduces manual data entry to near zero |

---

## 4. MVP Scope

### In scope (MVP)
- Google sign-in
- English and Spanish UI, fully parallel (i18n from day one)
- Dashboard with aggregate stats across all the user's credit cards, regardless of market
- Manual entry of one or more credit cards, each tagged with its market (Colombia or US), with full rate/fee/date characteristics for that market (Section 8)
- Manual entry of purchases, with market-appropriate interest treatment (per-purchase installments for Colombia; revolving balance, with optional installment-plan flag, for US)
- Month-by-month statement simulation: principal vs. interest vs. fees breakdown, drill-down to the purchases feeding a given month — correct for either market's calculation method
- Editing of any card characteristic or purchase, with automatic recalculation downstream
- Deterministic recommendation engine (rule-based), working across cards regardless of market

### Explicitly out of scope for MVP (tagged for future phases — see Section 11)
- Statement OCR/PDF auto-extraction — **[Phase 2]**
- Additional product types (línea de crédito, US personal loans/HELOCs, etc.) — **[Phase 2]**
- Additional markets beyond Colombia/US — **[Phase 2]**
- Public third-party API / integrator access — **[Phase 3]**
- Notifications/reminders — **[Phase 2]**
- Multi-user/family sharing — **[Phase 3]**
- Cash advances (avances / cash advances) — **[Phase 2]**
- Rewards/points tracking — **not currently planned**

---

## 5. Internationalization & Market Rules Profile

This is the architectural core of building for two countries correctly, so it gets its own section rather than living only in the data model.

**Language (i18n)** — straightforward: every UI string lives in a translation file (English/Spanish), never hardcoded. Cheap to do right from the start, expensive to retrofit.

**Market rules (the hard part)** — Colombia and US credit cards don't just differ in field values, they differ structurally:

| Dimension | Colombia | US |
|---|---|---|
| Disclosed rate | EA (effective annual) | APR |
| Interest calculation | Per-purchase accrual against assigned installment terms | Average daily balance across the billing cycle, single revolving APR |
| Installments | Core mechanic — assigned per purchase at time of purchase | Optional add-on feature (e.g. Plan It / Flex Pay style), not universal |
| Minimum payment | Regulated formula (interest + fees + required principal %) | Not centrally regulated, but most major issuers converge on one shape: the greater of (a) a flat-dollar floor, or (b) 1% of the statement balance plus that period's interest and fees. See Section 10 for the specific reference formula and issuer examples chosen for MVP |
| Grace period | "Pago total" — paying the full statement balance typically waives interest for that period | New purchases are typically interest-free if the *previous* statement's balance was paid in full by its due date — a whole-account condition, not per-purchase |
| Recurring fee terminology | Cuota de manejo | Annual fee (if any) |
| Penalty rate | Tasa de mora | Penalty APR |

**Design implication**: the calculation engine must be built around a `MarketRulesProfile` abstraction — each `FinancialProduct` (card) is tagged with a market, which selects the correct interest-calculation strategy, minimum-payment formula, and grace-period rule. `calculations/` should never contain an "if Colombia" branch scattered through generic code — instead, two (or more, later) strategy implementations behind one interface, selected by the product's market. This is what makes adding a third country later additive rather than another round of untangling assumptions.

**Locale-aware formatting**: number formatting differs (Colombia uses period as thousands separator, comma as decimal — the reverse of US convention) — this needs to be handled at the display layer based on locale, independent of the underlying stored values.

**Day-count convention is a per-product setting, not a per-market default**: in Colombia, each bank independently decides whether to compute daily interest on a 360- or 365-day basis — it isn't standardized nationally, so it can't be hardcoded as "Colombia = X." The same field applies to US cards for consistency, even though US issuers converge much more consistently on actual/365. Concretely: every `FinancialProduct`, regardless of market, has a `day_count_basis` field (360 or 365), defaulting to 365, editable per card. The daily periodic rate is always computed as `disclosed_annual_rate / day_count_basis` — this one parameter, not a market check, is what the accrual engine reads.

---

## 6. Domain Glossary (by Market)

### Common
| Term | Meaning |
|---|---|
| Credit limit / Cupo | Maximum balance the card allows |
| Statement / Billing cycle | The period over which purchases and interest are grouped into one due amount |
| Grace period / float | Condition under which a purchase or balance avoids interest entirely |

### Colombia-specific
| Term | Meaning |
|---|---|
| Cupo | Credit limit |
| Fecha de corte | Statement cutoff date — purchases after this land in the *next* statement |
| Fecha de pago | Payment due date |
| Cuota de manejo | Monthly/annual handling fee |
| Tasa de mora | Penalty rate on overdue balances |
| EA (efectiva anual) | Effective annual rate — standard disclosure format |
| Diferido sin intereses | "Deferred without interest" — interest-free installment promo |
| Pago mínimo | Minimum payment — regulated formula |

### US-specific
| Term | Meaning |
|---|---|
| APR | Annual Percentage Rate — standard disclosure format |
| Billing cycle | Typically ~30 days, ending on a statement closing date |
| Average daily balance | The method most US issuers use to compute interest across the cycle |
| Minimum payment | Issuer-specific, but most converge on: greater of a flat-dollar floor or 1% of balance plus that period's interest and fees (Section 10) |
| Penalty APR | Elevated rate applied after late payment, per card agreement |
| Installment plan (e.g. Plan It, Flex Pay) | Optional, issuer-specific feature to split a purchase or balance into fixed payments — not universal |

---

## 7. Functional Requirements

### 7.1 Authentication & Onboarding
- Sign in / sign up via Google OAuth
- First-run experience lands directly in "add your first card" if the user has no products yet, otherwise the dashboard
- Language selectable at any time (default from browser locale, override in settings)

### 7.2 Dashboard
- Aggregate view across all cards, regardless of market: total balance, total monthly interest, total fees, highest-cost product flagged
- Entry point to add a new product
- Per-card summary cards linking into the detailed month-by-month view

### 7.3 Add / Edit Credit Card Product
- Market selection (Colombia / US) at creation time — determines which fields and calculation rules apply
- Captures market-appropriate characteristics (Section 8)
- Editable after creation, with all downstream calculations recalculating automatically

### 7.4 Add / Edit Purchases
- Captures amount, currency, date, and market-appropriate interest treatment: installment count and per-purchase terms for Colombian cards; standard revolving treatment, with an optional installment-plan flag, for US cards
- Editable after creation with automatic recalculation

### 7.5 Month-by-Month Statement View
- Shows each statement period's total due, split into principal / interest / fees, using the correct calculation method for that card's market
- Drill-down to contributing purchases
- Correctly assigns purchases to a statement period based on cutoff/cycle date, not purchase date

### 7.6 Recommendations Engine (deterministic, rule-based)
Works across all of a user's cards regardless of market. Example rules:
- Flag purchases whose real annualized cost exceeds the card's disclosed rate
- Show the interest-cost delta between minimum payment and a higher payment amount
- Flag installment promos nearing expiration (Colombia) or issuer installment-plan terms nearing completion (US)
- Suggest a cross-card payoff order by real cost (avalanche method)
- Flag utilization above a threshold as a stability risk
- Flag when paying the full statement balance would eliminate interest for that period

---

## 8. Data Model Considerations — Fields to Capture

### Common (all cards, regardless of market)
| Field | MVP? | Notes |
|---|---|---|
| Market (Colombia / US) | Yes | Selects the rules profile |
| Institution / issuer name | Yes | |
| Credit limit | Yes | For utilization-based recommendations |
| Disclosed rate (EA or APR, per market) | Yes | Store in the market's native format; convert internally as needed |
| Day-count basis (360 / 365) | Yes | Per-product, not per-market — defaults to 365, editable per card. Colombian banks each decide independently; not standardized nationally |
| Penalty rate (tasa de mora / penalty APR) | Yes | |
| Statement cycle dates (cutoff/closing, due date) | Yes | Drives period assignment |
| Recurring fee (cuota de manejo / annual fee) | Yes | |
| Insurance opt-in + cost | Yes | Common in Colombia; optional add-on in US |
| Minimum payment rule | Yes | Market-specific formula (Section 5) |
| Grace period rule | Yes | Market-specific condition (Section 5) |
| FX/international transaction fee (%) | Yes | Applies to foreign-currency purchases in either market |

### Colombia-specific
| Field | MVP? | Notes |
|---|---|---|
| Whether 1-installment purchases carry interest | Yes | Varies by card |

### US-specific
| Field | MVP? | Notes |
|---|---|---|
| Whether an installment-plan feature (Plan It/Flex Pay style) is enabled, and its terms | Yes | Optional per purchase, not universal |
| Penalty APR trigger conditions | Nice to have | Some issuers apply after a specific number of late payments |

### Purchase-level (common)
| Field | MVP? | Notes |
|---|---|---|
| Amount | Yes | |
| Currency | Yes | For FX fee logic |
| Purchase date | Yes | |
| Number of installments (Colombia) / installment-plan opt-in (US) | Yes | Market-dependent shape, same underlying concept |
| Whether interest-free (promo) | Yes | |
| Promo/plan expiration terms | Yes, if applicable | |
| Merchant/description | Nice to have | |

---

## 9. Non-Functional Requirements
- **Accuracy over speed**, independently for each market — the calculation engine must be exactly right before anything else, and "right for Colombia" and "right for the US" are two separate correctness bars, not one
- **Data sensitivity**: real financial data — treat auth and storage with real care from day one
- Performance, scale, and uptime are non-priorities for MVP

---

## 10. Assumptions & Open Questions

### Resolved

**US minimum-payment reference formula (chosen for MVP)**: research across major issuers shows most converge on the same shape — the greater of a flat-dollar floor or 1% of the statement balance plus that period's interest and fees, plus any past-due amount. Reference formula to implement first:

> `minimum_payment = past_due_amount + max(flat_floor, 0.01 × statement_balance + period_interest + period_fees)`

Issuers using this exact shape (as of current published terms): **Chase** (floor $40), **Wells Fargo** (floor $25), **Bank of America** (same 1%-plus-fees-and-interest shape), **Barclaycard** (floor $25). **Capital One** uses the same shape with a floor around $25. Treat `flat_floor` as a per-card configurable field (not hardcoded), since it varies by issuer and product line, but default new US cards to this formula.

**Notable variants, deliberately not the MVP default but worth knowing about**: **Citi** anchors around $25–$20 plus 1% depending on the specific card; **Discover** and **American Express** use a higher base percentage (2–3%) and, in some cases, exclude interest from the percentage-based leg — these are real enough that they may need to become alternate presets in Phase 2 if a user's actual card doesn't match the MVP default, but the MVP ships with the Chase/Wells Fargo/Bank of America/Capital One shape as the single implemented formula.

**Day-count convention**: resolved — configurable per product (`day_count_basis`, 360/365, default 365), not inferred from market. See Section 5.

### Still open
- Assuming manual "as-of" entry rather than full historical reconstruction from account opening — confirm during journey mapping
- Need to confirm Colombia's exact minimum-payment formula against a real statement when one becomes available; until then, model it per the regulated shape described in Section 6 with placeholder parameters clearly marked as estimated
- Need to decide how far back historical statements can/should be entered for a card added mid-life

---

## 11. Future Phases (Out of MVP, Explicitly Tagged)

**Phase 2**
- Statement OCR/PDF auto-extraction
- Additional product types: línea de crédito (CO), personal loans/HELOCs (US)
- Additional markets beyond Colombia/US
- Cash advances
- Notifications/reminders

**Phase 3**
- Public third-party API (versioned, API-key authenticated)
- Multi-user/family account sharing
- Usury-rate (tasa de usura) comparison feature (Colombia-specific regulatory benchmark)

---

## 12. MVP Prioritization (MoSCoW)

- **Must have**: Google auth, English/Spanish UI, add/edit card with market selection, add/edit purchase, month-by-month breakdown with drill-down (correct per market), core recommendation rules, both markets' calculation engines independently verified
- **Should have**: utilization warnings, promo/installment-plan expiration warnings
- **Could have**: merchant/description field, annual fee tracking
- **Won't have (this release)**: everything in Section 11
