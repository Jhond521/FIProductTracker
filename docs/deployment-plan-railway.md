# Credit Tracker — Deployment Plan (Railway, Dev → QA → UAT → Prod)

This is the plan to hand to Claude Code. Read it once here so you know what
"done" looks like at each stage; Claude Code executes the actual commands.

---

## 1. Platform decision: Railway

Railway is the right fit here specifically because its **Environments**
feature maps directly onto Dev/QA/UAT/Prod without extra tooling: one
Railway *project* can contain multiple named *environments*, each with its
own Postgres instance, its own environment variables, and its own deploy
history — but sharing the same GitHub repo and the same Docker build.
That's precisely the "build once, promote the same image" principle from
the original pipeline plan.

**Sequencing**: build and prove Dev first. Don't create QA/UAT/Prod until
Dev is genuinely working end-to-end (health check reachable, migration
applied, the same create-card → add-purchase → get-schedule flow working
against a public URL instead of localhost). Adding all four environments
before any of them work just multiplies the places something can be wrong.

---

## 2. What "Dev environment done" looks like

- A Railway project exists, connected to `https://github.com/Jhond521/FIProductTracker`
- A Postgres instance is provisioned inside the Dev environment
- The backend service builds from `backend/Dockerfile` and deploys automatically on every push to `main`
- `DATABASE_URL` is supplied automatically by Railway's Postgres plugin (it injects this as a reference variable — you don't hand-type connection strings)
- The Alembic migration has been applied against that Postgres instance
- Visiting the Railway-generated public URL's `/health` endpoint returns `{"status": "ok"}`
- The full create-card → add-purchase → get-schedule flow works against that public URL, not just localhost

---

## 3. Environment variable matrix

| Variable | Dev | QA | UAT | Prod | Notes |
|---|---|---|---|---|---|
| `DATABASE_URL` | auto (Railway Postgres ref) | auto | auto | auto | Never hand-typed — Railway injects this per-environment automatically when you add a Postgres plugin to that environment |
| `ENVIRONMENT` | `dev` | `qa` | `uat` | `prod` | Plain string, used for logging/behavior flags later, not for market rules (those are per-product, not per-environment) |

That's genuinely the whole list right now — this app has no third-party API keys, no auth secrets yet (Google OAuth is still a future phase per the PRD), so the matrix stays this small until those land. Resist the urge to add speculative config now; add variables when a real feature needs them.

---

## 4. Running the migration in each environment

Railway lets you set a **Deploy Command** (or a post-deploy hook) per
service. For this app:

```
alembic upgrade head
```

Run this once manually the first time (via `railway run alembic upgrade head`
against that environment, from your local machine with the Railway CLI
linked to that environment) to confirm it works, then wire it as an
automatic pre-start step so every future deploy applies any new migrations
before the app starts serving traffic. Getting the ordering right (migrate
*before* the new app code starts handling requests) matters once there are
real schema changes to coordinate — worth doing properly even at this
early stage rather than retrofitting later.

---

## 5. Networking

Railway assigns each environment's service a URL like
`fiproducttracker-dev.up.railway.app` automatically — no domain
purchase or DNS configuration needed for Dev/QA/UAT. A custom domain only
becomes relevant for Prod, and even then, that's a later decision (Section
8), not a blocker for anything right now.

---

## 6. Promotion flow (once Dev is proven — not yet)

Railway supports duplicating an environment's configuration to create a
new one (QA from Dev's config, etc.), which is the mechanism for "the same
image, promoted forward" rather than separately configuring each
environment from scratch. Concretely, once Dev works:

1. Duplicate the Dev environment's config to create QA, with its own
   Postgres (Railway does not let environments share a database — this is
   correct behavior, not a limitation to work around)
2. Deploys to QA are triggered manually (a specific commit/tag), not
   automatically on every push to `main` — this is the actual "promotion"
   step, distinct from Dev's continuous auto-deploy
3. Repeat for UAT, then Prod, each requiring a deliberate promotion action
   rather than happening automatically

This step is explicitly **out of scope for today** — flagged here so the
plan is visible, not because it's next.

---

## 7. Later: wiring this into GitHub Actions

Once the manual Railway promotion flow above is well understood by hand,
the natural evolution is to let the existing `.github/workflows/ci.yml`
also handle deployment — auto-deploy to Dev on merge to `main`, then a
manual `workflow_dispatch` trigger (or GitHub Environments' required-
reviewer protection rules) gating promotion to QA/UAT/Prod. This is a
Phase 2 infrastructure task, not something to build before Dev itself is
proven — sequence matters here.

---

## 8. Explicitly not today
- Custom domain for Prod
- GitHub Actions-driven deploy automation (Section 7)
- QA/UAT/Prod environments themselves (Section 6)
- Any secrets beyond `DATABASE_URL`/`ENVIRONMENT` (nothing else exists yet to protect)

---

## 9. Concrete task list for Claude Code today

1. Install/verify the Railway CLI, log in
2. Create a new Railway project, connect it to the GitHub repo
3. Add a Postgres plugin to the (default/Dev) environment
4. Configure the backend service to build from `backend/Dockerfile`
5. Set `ENVIRONMENT=dev`
6. Deploy, then run `alembic upgrade head` against it via `railway run`
7. Confirm `/health` responds on the public URL
8. Run through the create-card → add-purchase → get-schedule flow against
   that public URL (same manual test as the localhost one, just pointed at
   the new URL) and confirm the numbers match

**Status: done, verified.** Dev is live, health check confirmed, full flow
matches the local calculation exactly.

---

## 10. Lessons from the Dev deployment (apply directly to QA/UAT/Prod)

These were discovered the hard way on Dev — feed them to Claude Code
up front for every subsequent environment so they aren't rediscovered
each time:

- **Root Directory isn't CLI-exposed, but *does* carry over when duplicating an environment**: Railway's CLI has no command to set a service's build Root Directory directly. It must be set via the dashboard (Settings → Source → Root Directory) the first time a service is created fresh (`railway add --repo` or the initial project setup) — as happened for Dev. **Correction, verified during QA setup**: when creating a new environment by duplicating an existing one (`railway environment new qa --duplicate dev`), Root Directory *does* carry over automatically along with `DATABASE_URL`, targetPort, and domain config — no manual re-set needed in that path. Only the fresh-service path requires the manual dashboard step.
- **`DATABASE_URL` scheme must be rewritten**: Railway's Postgres reference
  variable defaults to `postgresql://`, but this app's SQLAlchemy async
  engine requires `postgresql+asyncpg://`. Set this explicitly for every
  environment's `DATABASE_URL` — don't assume the default reference works.
- **`targetPort` must be set explicitly**: defaults to null, causing a 502
  even once the container is running. Must be set to `8000` to match the
  Dockerfile's `EXPOSE 8000`.
- **Migrations run via SSH into the deployed container**: `alembic upgrade
  head` needs real access to that environment's actual database, so it's
  run via `railway ssh` against the deployed service, not from a local
  connection string. This needs an SSH keypair registered with Railway
  (already done for Dev — reuse it, don't regenerate per environment).
- **Don't trust the deployment record in the first few seconds after
  duplicating an environment**: right after running `railway environment
  new ... --duplicate ...`, querying the new deployment's record can show
  a transient/incomplete API state — e.g. builder showing `RAILPACK` with
  no Root Directory, or the Source panel showing "GitHub Repo not found"
  — before the record finishes populating. This is not a real reconnect
  issue; recheck once it settles (a few seconds) rather than treating the
  first read as ground truth or trying to "fix" a connection that isn't
  actually broken.
- **SSH host-key mismatches can happen against `ssh.railway.com`**:
  Railway's SSH gateway rotates keys across backend hosts, so a prior
  successful `railway ssh` connection doesn't guarantee the next one
  won't hit a host-key mismatch warning. Fix by removing/refreshing just
  that host's entry in your local `known_hosts` file (don't disable host-
  key checking wholesale) and reconnecting. Expect this can recur on
  Prod — it's a one-time-per-occurrence fix, not a sign of a broken setup.

---

## 11. QA environment — task list for Claude Code

Building on the Dev environment already proven (Section 9) and the
lessons above (Section 10). The key difference from Dev: **QA does not
auto-deploy on every push to `main`.** Deploys to QA are a deliberate
promotion step — pick a specific commit (typically one already verified
working in Dev) and deploy that, rather than continuous deployment.

1. In the existing `FIProductTracker` Railway project, create a new
   environment named `qa` (Railway supports duplicating an existing
   environment's config as a starting point — reuse Dev's service
   config, then adjust per below)
2. Add a **separate** Postgres plugin scoped to the `qa` environment —
   never share Dev's database
3. ~~Set the backend service's Root Directory to `backend` again~~ —
   **not needed**: verified during QA setup that Root Directory carries
   over automatically when duplicating an environment (Section 10 update)
4. Set `DATABASE_URL` to reference QA's own Postgres plugin, rewritten to
   the `postgresql+asyncpg://` scheme (Section 10)
5. Set `targetPort` to `8000` (Section 10)
6. Set `ENVIRONMENT=qa`
7. **Turn off auto-deploy** for this service in the `qa` environment —
   confirm with Claude Code exactly how Railway exposes this (dashboard
   toggle or CLI flag) before assuming it's on by default
8. Deploy the current `main` commit manually (the same one already
   verified in Dev) — this is the actual "promotion," not a fresh build
9. Run `alembic upgrade head` against QA via `railway ssh` (reuse the
   existing SSH keypair from Dev)
10. Confirm `/health` responds on QA's public URL
11. Run the same create-card → add-purchase → get-schedule flow against
    QA's URL and confirm the numbers match Dev's

**Status: done, verified.** QA is live at its own Railway-generated URL,
own Postgres confirmed isolated (queried directly, no shared data),
auto-deploy confirmed disabled for `qa` while remaining enabled for `dev`,
migration applied, health check and full calculation flow match Dev
exactly.

**Explicitly not part of this task**: UAT, Prod, or wiring GitHub Actions
to automate this promotion step (Section 7) — those remain later phases.

---

## 12. UAT environment — task list for Claude Code

Same pattern as QA (Section 11), one more repetition to confirm it's
reliable rather than a fluke. UAT shares QA's core behavior — deploys are
a deliberate promotion, not continuous — but exists as a distinct stage so
a specific commit can sit in UAT for review independent of whatever QA is
currently testing.

1. In the existing `FIProductTracker` Railway project, create a new
   environment named `uat` by duplicating `qa`'s config (`railway
   environment new uat --duplicate qa`) — Root Directory, `targetPort`,
   and domain config should carry over automatically per the Section 10
   correction; verify this rather than assuming it holds a third time
2. Add a **separate** Postgres plugin scoped to the `uat` environment
3. Set `DATABASE_URL` to reference UAT's own Postgres plugin, rewritten to
   the `postgresql+asyncpg://` scheme (Section 10)
4. Confirm `targetPort` is `8000` (should carry over, but verify)
5. Set `ENVIRONMENT=uat`
6. **Turn off auto-deploy** for this service in the `uat` environment —
   verify directly in the dashboard, same as QA
7. **Don't panic if the deployment record looks wrong immediately after
   duplication** (builder/Root Directory/Source panel) — recheck once it
   settles rather than trying to reconnect something that isn't actually
   broken (Section 10)
8. Deploy the same commit already verified in QA (not necessarily
   whatever is newest in `main` — UAT should reflect what QA actually
   tested)
9. Run `alembic upgrade head` against UAT via `railway ssh` — if you hit a
   host-key mismatch for `ssh.railway.com`, refresh that host's entry in
   `known_hosts` and reconnect (Section 10), don't disable host-key
   checking
10. Confirm `/health` responds on UAT's public URL
11. Run the same create-card → add-purchase → get-schedule flow against
    UAT's URL and confirm the numbers match Dev/QA
12. Empirically verify UAT's Postgres is isolated from both Dev's and
    QA's (query directly, same method used to verify QA's isolation) —
    don't just trust the environment config

**Explicitly not part of this task**: Prod, or wiring GitHub Actions to
automate promotion (Section 7) — those remain later phases.

---

## 13. Prod environment — task list for Claude Code

Same mechanical pattern as QA/UAT (Sections 11–12), but Prod carries two
real differences worth pausing on rather than rushing through as "just
one more repetition":

- **Only promote a commit that has actually passed through UAT** — not
  whatever is newest on `main`, and not directly from QA. The whole point
  of the Dev→QA→UAT→Prod chain is that each stage is a real checkpoint;
  skipping UAT's verification to deploy something "similar enough"
  defeats the purpose of having built this pipeline at all.
- **Confirm explicitly before deploying** — this is the one environment
  where "it worked" isn't just a learning-exercise outcome; treat the
  deploy step itself as something to pause on and confirm with you
  directly, not something Claude Code should do the instant it's ready to.
  **Correction, learned the hard way**: `railway environment new --duplicate`
  triggers an immediate deploy as a side effect of *creating* the
  environment — the confirmation has to happen *before* running that
  command, not after. Asking "is this the right commit?" once the
  environment already exists is too late; the deploy has already
  happened by then. This mattered less the first time (only one commit
  existed in this repo's history to deploy), but won't be true once
  there's a real choice between multiple commits and a real rollback
  cost if the wrong one ships.

1. In the existing `FIProductTracker` Railway project, create a new
   environment named `prod` by duplicating `uat`'s config (`railway
   environment new prod --duplicate uat`) — expect the same transient
   deployment-record state right after duplication (Section 10); recheck
   once it settles rather than reacting to the first read
2. Add a **separate** Postgres plugin scoped to the `prod` environment
3. Set `DATABASE_URL` to reference Prod's own Postgres plugin, rewritten
   to the `postgresql+asyncpg://` scheme (Section 10)
4. Confirm `targetPort` is `8000` (should carry over, but verify)
5. Set `ENVIRONMENT=prod`
6. Confirm auto-deploy is off for this service in the `prod` environment
7. **Custom domain — open decision, not a blocker**: Prod can either stay
   on Railway's generated `*.up.railway.app` URL for now, or a custom
   domain can be configured later. Don't set one up unless explicitly
   asked — this is a deliberate later decision (Section 5), not something
   to default into while setting up Prod for the first time.
8. **Confirm with the user which exact commit to deploy** — the one
   already verified in UAT — before running the deploy command
9. Deploy that confirmed commit
10. Run `alembic upgrade head` against Prod via `railway ssh` — same
    host-key-mismatch caveat as before (Section 10)
11. Confirm `/health` responds on Prod's public URL
12. Run the same create-card → add-purchase → get-schedule flow against
    Prod's URL and confirm the numbers match Dev/QA/UAT
13. Empirically verify Prod's Postgres is isolated from Dev/QA/UAT (query
    directly, same method used for QA and UAT) — don't just trust config

**Explicitly not part of this task**: wiring GitHub Actions to automate
promotion (Section 7) — that remains a later phase, and the four
environments now existing side by side is itself a good enough stopping
point to pause and confirm everything is genuinely solid before adding
automation on top.

**Status: done, verified.** Prod is live at its own Railway-generated URL,
own Postgres confirmed isolated from Dev/QA/UAT (queried directly), auto-
deploy confirmed disabled, migration applied, health check and full
calculation flow match all three prior environments exactly. All four
environments (Dev → QA → UAT → Prod) are now live, isolated, and verified
end-to-end. Custom domain and GitHub Actions-driven promotion (Section 7)
remain explicitly out of scope going forward.
