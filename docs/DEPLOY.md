# Deploy GlitchHunter — free & around the clock

This sets up GlitchHunter to run **24/7 for free**, with the iOS app **built in CI**.

```
GitHub Actions (cron)  --scrape-->  Neon Postgres  <--reads--  Render API  <--  iOS app / preview
   every 30 min (free)               (free)                     (free)
GitHub Actions (macOS) --builds-->  GlitchHunter.app (simulator, unsigned)
```

## What's free vs. not

| Piece | How | Free? |
|-------|-----|-------|
| Scraping h24 | GitHub Actions cron (`.github/workflows/scrape.yml`) | ✅ |
| Database | Neon serverless Postgres | ✅ |
| Read API | Render Docker web service (`render.yaml`) | ✅ (cold-starts) |
| iOS build | GitHub Actions macOS + XcodeGen (`.github/workflows/ios.yml`) | ✅ |
| **Push to a real iPhone** | APNs via Firebase | ❌ needs Apple Developer ($99/yr) |
| **Installable signed app** | code signing | ❌ needs Apple Developer ($99/yr) |

Without the Apple account: the scraper still detects deals and stores them, the API serves
them, and CI proves the app compiles — only **APNs delivery to a physical device** and
**installing a signed build** are unavailable. Pushes are auto-skipped (see `notifications.py`).

---

## 1. Put the repo on GitHub

```powershell
cd c:\Users\luis2\GlitchHunter
git init
git add .
git commit -m "GlitchHunter: backend + iOS + preview + CI"
git branch -M main
git remote add origin https://github.com/<you>/GlitchHunter.git
git push -u origin main
```

## 2. Free Postgres (Neon)

1. Create a project at https://neon.tech (free).
2. Copy the connection string and convert it for SQLAlchemy + asyncpg:
   `postgresql+asyncpg://USER:PASSWORD@HOST/DBNAME?ssl=require`
   (the app strips `ssl`/`sslmode` and enables TLS automatically — see `database.py`).

## 3. Scraping h24 (GitHub Actions)

1. Repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `DATABASE_URL` = the Neon URL above.
2. The schedule in `.github/workflows/scrape.yml` runs every 30 min. Trigger a first run
   manually: **Actions → Scrape (h24) → Run workflow**.
3. Edit the `*_TARGETS` lists in `backend/app/scrapers/*.py` to the products you actually watch
   (the defaults are placeholders) and tune `parse()` selectors per store.

> Tables are auto-created on first run (`init_db`). On an empty DB, `/api/search` returns `[]`
> until the scraper has populated products.

## 4. Deploy the read API (Render)

1. https://render.com → **New → Blueprint** → pick this repo (it reads `render.yaml`).
2. Set the `DATABASE_URL` env var (same Neon URL).
3. Deploy. Your API is at `https://glitchhunter-api.onrender.com` (verify `/health`).

> The free API image has **no browser**, so `/api/admin/scrape` can't scrape there — that's
> what the Actions cron is for. The API only reads the DB.

## 5. Point the clients at the API

- **Preview:** open `preview/index.html?api=https://glitchhunter-api.onrender.com`, or click the
  **⚙ gear** in the header to set/persist the backend URL.
- **iOS app:** set `APIConfig.baseURL` in `ios/GlitchHunter/Networking/NetworkManager.swift`.

## 5b. Choosing what to monitor (watchlist)

The scrapers read their targets from a **watchlist table** (`/api/watch`), not hard-coded URLs:

- `GET /api/watch` · `POST /api/watch {url[,store]}` · `DELETE /api/watch/{id}`
- Store is auto-detected from the URL domain (amazon/unieuro/mediaworld).

In the preview: the **⭐ I miei** chip shows your watchlist; tap **+** on any card (or **➕ Monitora**
in the detail sheet) to add it, or **➕ Aggiungi da URL** to paste a store link. The list lives in
the browser (`localStorage`) and is mirrored to `POST /api/watch` when the backend is reachable, so
the next scrape cycle starts tracking it. The home also shows the curated deals feed.

## 5c. Publish the preview on GitHub Pages (free public URL)

`.github/workflows/pages.yml` deploys `preview/` to Pages on every push to `main`.
One-time: repo → **Settings → Pages → Source = GitHub Actions**. Then open the published URL and
set your API via the **⚙ gear** (or `?api=` query param).

## 6. Build the iOS app in CI

`.github/workflows/ios.yml` runs on every push touching `ios/**`. It installs XcodeGen,
generates `GlitchHunter.xcodeproj` from `ios/project.yml`, and builds for the iOS Simulator
**unsigned**. To build locally:

```bash
brew install xcodegen
cd ios && xcodegen generate && open GlitchHunter.xcodeproj
```

## 7. (Optional, paid) Real push notifications

Needs an Apple Developer account. Then: create the Firebase iOS app, upload your APNs key,
download `GoogleService-Info.plist` into the Xcode target, and add the service-account JSON as
the GitHub secret `FIREBASE_CREDENTIALS_JSON` (the scrape workflow writes it to disk and enables
pushes).

---

### Tuning the cadence
`schedule: "*/30 * * * *"` = every 30 min. GitHub's cron is best-effort (can lag during peak)
and the minimum interval is ~5 min. For tighter, more reliable timing you'd need a paid
always-on worker (the original `arq app.worker.WorkerSettings`).
