# Runningo next session

Resume Monday, October 12, 2026. Submission deadline: **12:29 PM IST (UTC+05:30)**. Target submission: **11:30 AM IST** (59-minute buffer). Deadline is user-provided; confirm challenge requirements.

## State

Local MVP only; no deployment or push. React/TypeScript/Leaflet frontend, FastAPI backend, no database/accounts. **Free-only: promotional credits are allowed; no out-of-pocket spending, top-ups or paid spillover.** Local .env is preserved and ignored. Current model is **Ollama gemma3:4b**, already installed; 270m and 1b comparison results retained. Do not download another model to resume.

## Start from repository root in PowerShell

    Set-Location 'D:\Downloads\Hactober Fest\Runningo'

If Ollama is not already running, in a separate terminal:

    & "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve

Then:

    npm --prefix frontend run build
    .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

Open http://127.0.0.1:8000. Existing processes may still occupy ports 8000/11434; reuse or stop them before starting duplicates. Read README for fresh dependency setup; do not overwrite .env.

## Evidence and relevant paths

- frontend/src/main.tsx: preferences-to-planner flow, map, resize observer, prerequisite/loading feedback.
- frontend/src/style.css: green mobile-first CSS, tap targets and desktop split. frontend/src/vite-env.d.ts + frontend/tsconfig.json: Vite CSS types and strict side-effect import checking.
- frontend/public/favicon.svg + frontend/index.html: original bright-green runner favicon, mirrored direction. dist/ is generated and ignored.
- backend/preferences.py + backend/models.py: unchanged prompt, strict schema and honest fallback. backend/routing.py: pedestrian provider, bounded Overpass failover/cache, time budget and place warnings.
- backend/test_core.py + backend/test_overpass.py: 57 passing tests; one dependency deprecation warning. TypeScript/Vite production build passed.
- docs/gemma-check-270m.json, gemma-check-1b.json, gemma-check-4b.json; gemma-4b-comparison.md: unchanged seven cases scored 1/7, 3/7, 7/7. 4b cold 11.485 s; warm mean 5.750 s. Finite evaluation is not a general accuracy guarantee.
- docs/end-to-end-4b.json + end-to-end-http-4b.json + end-to-end-4b.md: real Gemma jogging/walking flow; exact interpreted values reached planner. Jogging 3.221 km / 29.1545 min including 5-min pause, FOSSGIS OSRM foot, garden waypoint within 34.72 m of returned geometry. Walking 1.272 km / 20.90375 min including pause, explicit lookup-failure/unmet greenery warning. Closure 0 m, start offset 6.14 m. before-fix report preserves the corrected pause-loss bug.
- docs/responsive-layout-check.json: CSS/source checks at requested widths, not screenshots. No browser connection was available; actual rendered overflow, geolocation/clicks and resize remain unverified.
- .env.example: safe server-side configuration template. render.yaml: single-worker Render Free preparation, MODEL_PROVIDER=none by default, not deployed.

## Morning priorities

1. Verify actual browser behavior: 360/390/768/1280 px, start selection, geolocation permission/error, missing-start message, Gemma review, walk/jog, route/time/stop accounting, nearby versus routed places, empty/unavailable states. Never claim road suitability or entrances are verified.
2. Check a free hosted Gemma account and discover exact available model; Backboard promo credit/model availability are unverified and its native API is not wired. Verify balance/expiry and disable paid spillover. Existing OpenAI-compatible adapter is configurable only after free access confirmation. Local Ollama localhost is inaccessible from Render.
3. With authorization, deploy Render Free, keep one worker, configure secrets only in backend environment, test HTTPS/cold starts/routing/model source. Honest form_fallback is the only fallback; never imply AI use when it failed.
4. Record a short real demo and finish DEV submission; aim for 11:30 AM IST, hard deadline 12:29 PM. Recheck submission rules. Do not spend money.

## Useful checks

    .\.venv\Scripts\python.exe -m pytest backend -q -p no:cacheprovider
    .\frontend\node_modules\.bin\tsc.cmd --project frontend/tsconfig.json --noEmit
    npm --prefix frontend run build

Opt-in live checks call free public services/local Ollama and overwrite their latest evidence files; preserve existing reports first if needed:

    .\.venv\Scripts\python.exe -m backend.check_end_to_end
    .\.venv\Scripts\python.exe -m backend.check_gemma
    .\.venv\Scripts\python.exe -m backend.check_places

Blockers: hosted account/key/free quota and exact Gemma availability; Render account/authorization; unavailable browser connection for visual checks; transient Overpass errors. No paid resource has been provisioned. Git checkpoint is local only; get its hash with git log -1 --oneline.
