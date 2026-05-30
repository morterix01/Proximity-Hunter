# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Price-error ("glitch") tracker. A Python/FastAPI backend (runs on Windows) scrapes Italian
stores with Playwright, detects sudden price drops, and pushes the steep ones to a native
SwiftUI iPhone app via Firebase (FCM → APNs). The iOS app **cannot be built on Windows** — it
requires macOS / Xcode 15+; treat `ios/` as source you edit but don't compile here.

## Backend commands (run from `backend/`)

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium          # required: scrapers launch headless Chromium
Copy-Item .env.example .env          # then edit

docker compose up -d                 # Postgres (5432) + Redis (6379)

uvicorn app.main:app --reload --port 8000   # API
arq app.worker.WorkerSettings               # scheduled scraper — SEPARATE terminal
```

Trigger / inspect a cycle:
```powershell
curl -X POST http://localhost:8000/api/admin/scrape   # one cycle now
curl http://localhost:8000/api/deals
# Swagger UI: http://localhost:8000/docs
```

There is **no test suite and no linter configured** in this repo. Don't invent test commands.

## Two-process model

The API and the scraper are separate processes that share the same DB and code:

- **`uvicorn app.main:app`** — serves `/api/deals`, `/api/search`, `/api/device/register`,
  `/api/admin/scrape`. `CORSMiddleware` is wide-open (`allow_origins=["*"]`) so the SwiftUI app
  and the static `preview/index.html` (origin `null` from `file://`) can call it from a browser.
- **`arq app.worker.WorkerSettings`** — runs `scrape_all()` on a cron derived from
  `SCRAPE_INTERVAL_SECONDS` (default 900s → minutes {0,15,30,45}), plus on startup.

`/api/admin/scrape` **enqueues** a job to the arq worker if Redis is reachable; if Redis is
down it falls back to running `scrape_all()` **inline** in the request. Both processes call
`init_db()` (auto-`create_all`) on startup — there are **no Alembic migrations wired up** even
though `alembic` is in requirements. Changing `models.py` won't migrate an existing DB; drop
the volume (`docker compose down -v`) or add migrations yourself.

## Scrape → deal → push pipeline

`tasks.scrape_all()` is the heart of the system. For each scraper in
`scrapers/__init__.py::SCRAPERS`:

1. **`scraper.scrape()`** (`scrapers/base.py`) — launches headless Chromium, visits each
   `targets()` URL with a rotated UA + optional proxy, calls `parse(html, url)` → `ScrapedItem`.
   One bad page is logged and skipped, never crashes the batch. `polite_delay_s` (1.5s) between
   pages — keep request volume polite.
2. **`ingest.ingest_batch()`** → `ingest_item()` per item: upserts the `Product`, appends a
   `PriceHistory` row, computes a **reference price**, and classifies the drop.
3. **`glitch.classify()`** maps drop% to a `GlitchTier` using `.env` thresholds.
4. **`notifications.notify_error_deal()`** pushes the deal via FCM.

### Reference price (the baseline a drop is measured against)
`ingest._reference_price()` takes the **max** of: the page's struck/list price, the stored
`Product.reference_price`, and the last 20 `PriceHistory` prices. First-ever sighting of a
product returns `None` → no deal (nothing to compare against yet).

### Tiers (`glitch.py`, thresholds in `.env`)
- drop ≥ `GLITCH_ERROR_THRESHOLD` (60%) → `error` ("Errore Prezzo")
- drop ≥ `GLITCH_SUPER_THRESHOLD` (30%) → `super` ("Super Sconto")
- otherwise → `none` (no Deal row created)

### Push policy
**Only `error`-tier deals trigger a push** — `notify_error_deal()` returns early (0) for any
other tier. To also push `super`, change that guard. Pushes go to **every** registered device;
tokens FCM reports as `UnregisteredError` are pruned. If `FIREBASE_CREDENTIALS` points at a
missing file, the whole app still runs and pushes are silently skipped (logged).

### Dedup
`ingest_item()` skips creating a Deal if an `active` deal already exists for the same product at
the same `new_price`.

## `/api/search` (search vs. scrape)

`routers/search.py` searches the **local `products` table** by title (`ILIKE`), enriching each
hit with its latest `PriceHistory` price and the tier of its most-recent active `Deal`. It does
**not** scrape live — it only returns products the scrapers have already populated, so on a fresh
DB it returns `[]`. Results are sorted by current drop %.

## Free 24/7 deploy & CI (see `docs/DEPLOY.md`)

The intended free hosting model avoids an always-on worker: **scraping runs as a GitHub Actions
cron** (`.github/workflows/scrape.yml`) calling `python -m app.cli` (= `app/cli.py`, a Redis-free
one-shot of `scrape_all()`), writing to **Neon Postgres**. The **read API** deploys to Render
(`render.yaml` + `backend/Dockerfile` — no Playwright/Chromium in that image; the API only reads
the DB). `database.py` normalizes free-Postgres URLs: it strips libpq `?sslmode=require` / `?ssl=`
and enables asyncpg TLS via `connect_args`. The **iOS app builds in CI** on a macOS runner via
**XcodeGen** (`ios/project.yml` → generated `GlitchHunter.xcodeproj`, gitignored), unsigned for
the simulator. Real APNs push + a signed installable build require a paid Apple Developer account.

## `preview/` — standalone HTML mockup

`preview/index.html` is a self-contained, dependency-free simulation of the iOS app inside an
iPhone 13 Pro frame (onboarding, deal grid, detail sheet with specs + image gallery, push banner,
live search). Its search tries `http://localhost:8000/api/search` first, then falls back to a
public demo catalogue (DummyJSON), then to a local list — so it's useful with or without the
backend running. It is a design/demo artifact, not wired into the build.

## Adding / fixing a scraper

Subclass `BaseScraper` (`scrapers/base.py`), set a unique `store` key, implement `targets()`
(the watchlist URLs) and `parse(html, url) -> ScrapedItem | None`, then register an instance in
`SCRAPERS` (`scrapers/__init__.py`). The `store` value must match the `Store` enum on the iOS
side and the `*_scraper.py` `store` strings (`amazon` / `unieuro` / `mediaworld`).

- **`parse()` returning `None` is the failure path** — return it whenever a required field
  (title, price, external id) is missing rather than raising.
- The `*_TARGETS` lists are **placeholder URLs**. Real use means replacing them (or loading from
  DB/config), and **site selectors drift constantly** — expect to re-tune `parse()` per store.
- Use `util.parse_euro()` for all price strings — it handles Italian formatting (`1.299,00 €`,
  `.`/space thousands, `,` decimal). Don't hand-roll price parsing.
- `scrapers/proxy.py` is a stub. Real proxying = `USE_PROXY=true` + `SCRAPER_API_KEY` (wired for
  the ScraperAPI endpoint shape).

## Conventions & cross-cutting notes

- **Async throughout**: SQLAlchemy 2.0 async (`asyncpg`), `AsyncSession` via `get_db()` FastAPI
  dependency. Routers use `select(...)` + `selectinload` for relationships, never lazy loads.
- **`ScrapedItem`** (`schemas.py`) is the normalized contract every scraper returns; **`DealOut`**
  is the API response shape. The iOS `Deal` struct (`ios/.../Models/Deal.swift`) mirrors `DealOut`
  field-for-field with snake_case `CodingKeys` — **keep them in sync** when changing either.
- Times are timezone-aware UTC (`models.utcnow`).
- Scraping is **brittle and ToS-sensitive** by nature; prefer official APIs/affiliate feeds where
  available and keep volume polite.

## iOS (edit-only on Windows)

SwiftUI MVVM under `ios/GlitchHunter/`: `ContentView` renders a `LazyVGrid` of `DealCard`s
(neon pulse on `error` tier), driven by `DealsViewModel` (`@MainActor`, calls `NetworkManager`).
Backend URL is `APIConfig.baseURL` in `Networking/NetworkManager.swift` (`localhost:8000` for the
simulator; LAN IP for a physical device). Forced-dark theme colors live in `Theme/Theme.swift`.
Setup (Xcode project creation, Firebase SPM packages, `GoogleService-Info.plist`, Push
Notifications capability, Info.plist deep-link schemes) is documented in `README.md`.
