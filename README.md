# GlitchHunter

Price-error ("glitch") tracker. Python/FastAPI backend scrapes stores, detects
sudden price drops, and pushes them to a native SwiftUI iPhone app via Firebase (FCM → APNs).

```
GlitchHunter/
├── backend/                 # FastAPI + Playwright + Postgres + Redis (runs on Windows)
│   └── app/
│       ├── main.py          # API: GET /api/deals, GET /api/search, POST /api/device/register, POST /api/admin/scrape
│       ├── models.py        # Product, PriceHistory, Deal, Device
│       ├── glitch.py        # drop% → tier (>=60% error, >=30% super)
│       ├── ingest.py        # scrape → price history → deal
│       ├── notifications.py # firebase-admin push
│       ├── tasks.py         # one scrape cycle
│       ├── worker.py        # arq scheduled worker
│       └── scrapers/        # base + amazon/unieuro/mediaworld + proxy rotation
└── ios/                     # SwiftUI MVVM (build on macOS / Xcode 15+)
    └── GlitchHunter/
        ├── GlitchHunterApp.swift, Notifications/AppDelegate.swift
        ├── Models/, ViewModels/, Networking/, Views/, Theme/
```

## Glitch logic

`reference_price` = max(struck price, stored baseline, recent history). Drop vs reference:

| Drop | Tier | Push |
|------|------|------|
| ≥ 60% | `error` — **Errore Prezzo** | ✅ |
| 30–59% | `super` — **Super Sconto** | ❌ (configurable) |
| < 30% | `none` | — |

Thresholds in `.env` (`GLITCH_ERROR_THRESHOLD`, `GLITCH_SUPER_THRESHOLD`).

---

## Backend (Windows)

Needs Python 3.11+, Docker (for Postgres + Redis).

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium

Copy-Item .env.example .env      # edit values

docker compose up -d             # Postgres + Redis

# API
uvicorn app.main:app --reload --port 8000
# Scheduled scraper (separate terminal)
arq app.worker.WorkerSettings
```

Test:
```powershell
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/admin/scrape   # one cycle now
curl http://localhost:8000/api/deals
curl "http://localhost:8000/api/search?q=iphone"      # search tracked products
```
Docs/UI: http://localhost:8000/docs

**Targets:** each scraper has a `*_TARGETS` list (placeholder URLs). Replace with
the products you watch, or load from DB/config. Site selectors change often —
expect to tune `parse()` per store.

**Firebase:** drop the service-account JSON at the `FIREBASE_CREDENTIALS` path.
Without it the API still runs; pushes are skipped (logged).

---

## iOS (macOS only — cannot build on Windows)

Xcode 15+, iOS 16+ target.

1. New Xcode project → SwiftUI app named `GlitchHunter`. Replace the generated
   files with everything under `ios/GlitchHunter/`.
2. **SPM:** add `https://github.com/firebase/firebase-ios-sdk` → products
   `FirebaseMessaging`, `FirebaseCore`.
3. **Firebase console:** add an iOS app, download `GoogleService-Info.plist`,
   drag it into the target. Upload your APNs key under Cloud Messaging.
4. **Signing & Capabilities:** add **Push Notifications** + **Background Modes →
   Remote notifications**.
5. **Info.plist** (let stores deep-link from a card tap):
   ```xml
   <key>LSApplicationQueriesSchemes</key>
   <array><string>com.amazon.mobile.shopping</string></array>
   ```
6. **Backend URL:** edit `APIConfig.baseURL` in `Networking/NetworkManager.swift`.
   Simulator → `http://localhost:8000`. Physical device → your Mac's LAN IP
   (and add an ATS exception for cleartext HTTP, or use HTTPS).

### Flow
- Launch → `requestAuthorization` → APNs token → FCM token →
  `POST /api/device/register`.
- `ContentView` loads `GET /api/deals`, renders a `LazyVGrid` of `DealCard`s
  (neon/glitch pulse on `error`), `.refreshable` pull-to-refresh, horizontal
  `FilterBar` with a blinking "Scraping Attivo" dot. Tap a card → opens the
  store app/web for instant purchase.
- Backend detects an `error` deal → FCM push → tapping it deep-links to the deal.

Theme (forced dark): bg `#0f0f13`, green `#00ffa3`, red `#ff3366` —
in `Theme/Theme.swift`.

---

## Deploy (free, h24) & CI

Run it 24/7 for free and build the app in CI — full walkthrough in
[`docs/DEPLOY.md`](docs/DEPLOY.md):

- **Scraping h24** → GitHub Actions cron (`.github/workflows/scrape.yml`, `python -m app.cli`),
  no always-on server.
- **DB** → Neon free Postgres. **API** → Render free Docker service (`render.yaml`, `backend/Dockerfile`).
- **iOS build** → GitHub Actions macOS + XcodeGen (`.github/workflows/ios.yml`, `ios/project.yml`),
  simulator, unsigned.
- ⚠️ **Real push to a physical iPhone and an installable signed app require a paid Apple
  Developer account** (~$99/yr). Everything else is free; without it, pushes are skipped and CI
  only proves the app compiles.

---

## Notes & caveats

- **Scraping is brittle and store ToS-sensitive.** Selectors here are best-effort
  starting points; keep request volume polite (`polite_delay_s`), respect
  robots/ToS, and prefer official APIs/affiliate feeds where available.
- Proxy/UA rotation in `scrapers/proxy.py` is a small stub — wire a real provider
  (ScraperAPI etc.) via `USE_PROXY=true` + `SCRAPER_API_KEY`.
- Schema is auto-created on startup (`init_db`). For real migrations use Alembic
  (already in requirements).
```
