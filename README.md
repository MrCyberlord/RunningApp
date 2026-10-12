# Runningo

Repository: [MrCyberlord/RunningApp](https://github.com/MrCyberlord/RunningApp).

A mobile-friendly walking and jogging route planner for a Hacktoberfest Touch Grass project. Pick a start, choose your time and preferences, and get a real pedestrian route back. React + TypeScript + Leaflet, with FastAPI and optional server-side Gemma interpretation.

**Status, October 12, 2026: verified locally; not deployed or published. No public demo URL or partner integration exists.** Free services only; promotional credits are allowed, but no out-of-pocket spending, top-ups or paid spillover. No accounts, database, social features or live tracking.

## Run locally

PowerShell from this workstation's repository root. Existing .env and installed models must be preserved:

    Set-Location 'D:\Downloads\Hactober Fest\Runningo'

If Ollama is not already running, start it in a separate terminal:

    & "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve

Current model: **Ollama gemma3:4b**, already installed locally. Existing server-only .env settings:

    MODEL_PROVIDER=ollama
    GEMMA_MODEL=gemma3:4b
    OLLAMA_URL=http://127.0.0.1:11434

Build and start the app in another terminal:

    npm --prefix frontend run build
    .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

Open http://127.0.0.1:8000. Health: http://127.0.0.1:8000/api/health. Reuse running services instead of starting duplicates. Keep Ollama private on loopback; do not tunnel it or expose port 11434. No frontend API key is required.

Fresh checkout prerequisites: Python 3.11+ (3.12 recommended), Node 22 LTS and npm. Install dependencies:

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
    if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
    npm --prefix frontend ci

The example defaults to MODEL_PROVIDER=none and honest form fallback. Local AI additionally requires Ollama and the gemma3:4b model; on a new machine install that model separately with ollama pull gemma3:4b, then set the three local values above. No download is necessary on this workstation. Never overwrite an existing .env. Python launcher alternative: py -3.12 -m venv .venv. Linux/macOS: substitute .venv/bin/python for the Windows venv executable.

For frontend development, keep FastAPI running and use a third terminal:

    npm --prefix frontend run dev

Open http://127.0.0.1:5173; Vite proxies /api to FastAPI. For the recording, prefer the built app on port 8000.

## Use it

1. Tap the map to select a start, or use browser geolocation (permission and HTTPS/localhost required). The initial Bengaluru viewport is not a detected location. Missing start selection shows instructions.
2. Choose walking/jogging, total minutes, optional pause and place categories. Or interpret “A 30-minute jog with greenery and a 5-minute stop,” then review the resulting form values.
3. Generate a route. Read distance, moving estimate, pause and total. Inspect suggested stops versus nearby-only markers and any warnings.

Gemma extracts preferences only. Strict Pydantic validation requires all fields, correct types, supported categories and valid time bounds. Malformed or unavailable model responses preserve form values and explicitly report source=form_fallback; successful model output reports source=gemma. This identifies origin, not semantic certainty. Natural-language interpretation does not generate route geometry.

## Routes, places and time

FOSSGIS OSRM's **foot** endpoint supplies real pedestrian GeoJSON; optional openrouteservice uses foot-walking. No driving substitution or fabricated route is used. Code tries at most three mapped waypoint routes, accepts closure within 20 m, start snapping within 100 m and total time within the requested budget. Geographic candidate waypoints are not invented places.

Moving minutes derive from routed distance at 4.8 km/h walking or 8 km/h jogging. Requested pause time is reserved from the moving budget and added even without a mapped place; in that case it is explicitly unassigned. Provider duration is retained separately. At most one preferred mapped stop is included; each unmet category is warned. Routes may retrace paths, undershoot the budget or fail.

Overpass supplies OSM parks/gardens, viewpoints, greengrocers and drinking-water points, excluding explicit private/no-access places and drinking_water=no. Polygon centres are not entrances; suggested stops require a returned route vertex within 80 m of the mapped point. Other markers are nearby only. Opening hours, legal access, route suitability, stock and water quality are unknown, not inferred.

Lookup uses a bounded 15-second default per-attempt deadline, at most one alternative public endpoint, a bounded ten-minute cache including successful empty results, and explicit unavailable versus empty status. HTTP 429 stops failover and establishes a cooldown. Routing/place requests share serialization with at least 1.05 seconds between starts. Use one backend worker; no shared limiter exists across processes.

## Verified local evidence

- **October 12 resumed HTTP check:** health OK; installed gemma3:4b returned correct jogging/30/greenery/5 preferences with source=gemma. Those values were sent to /api/route, which returned HTTP 200, FOSSGIS OSRM foot, 3.221 km and **24.1545 moving + 5 pause = 29.1545 minutes**. Place results were reused from a successful Overpass cache entry. [Raw evidence](docs/resume-verification-2026-10-12.json).
- Prior instrumented checks confirmed interpreted values reach the validated planner input. Jogging geometry closed exactly, snapped 6.14 m from the selected start, and passed within 34.72 m of a garden waypoint. A separate walking case returned 1.272 km / 20.90375 minutes including pause, with honest warnings when lookup failed. [End-to-end report](docs/end-to-end-4b.md), [raw local HTTP result](docs/end-to-end-http-4b.json).
- **Small fixed evaluation, not general accuracy:** unchanged seven extraction cases scored 1/7 for 270m, 3/7 for 1b and 7/7 for 4b. Strict validation and the prompt were not relaxed. 4b cold application latency was 11.485 s; warm mean 5.750 s. These development cases do not establish reliability on unseen requests. [Comparison](docs/gemma-4b-comparison.md), [preserved results](docs/gemma-check-4b.json).
- 57 deterministic backend tests pass, with one dependency deprecation warning. TypeScript and the production build pass. CSS/source calculations cover 360, 390, 768 and 1280 px; **rendered layouts and actual browser clicks/geolocation/resizing remain unverified because no browser connection was available**. The original transparent runner favicon is bundled; missing-start feedback and Leaflet resize observation are implemented.

Checks from repository root:

    .\.venv\Scripts\python.exe -m pytest backend -q -p no:cacheprovider
    .\frontend\node_modules\.bin\tsc.cmd --project frontend/tsconfig.json --noEmit
    npm --prefix frontend run build

Optional live checks call local Ollama/free public services and overwrite their latest evidence files; preserve prior reports if needed:

    .\.venv\Scripts\python.exe -m backend.check_end_to_end
    .\.venv\Scripts\python.exe -m backend.check_gemma
    .\.venv\Scripts\python.exe -m backend.check_places

## Free services, attribution and privacy

| Service | Account/key | Policy and constraints |
| --- | --- | --- |
| [OpenStreetMap tiles](https://operations.osmfoundation.org/policies/tiles/) | None | Visible contributor attribution; no bulk/offline prefetching; best-effort shared service. |
| [FOSSGIS foot routing](https://routing.openstreetmap.de/about.html) | None | One request/second limit, valid User-Agent and attribution; limited search, no heavy traffic. |
| [Overpass](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html) | None | Shared capacity, rate limits/timeouts; modest use only; cache, bounded retry and OSM source links. |
| [Optional openrouteservice](https://openrouteservice.org/plans/) | Free account/key | Not tested with a key here; confirm current dashboard quota and attribution before use. |
| Local [Ollama Gemma](https://ollama.com/library/gemma3) | Installed locally | gemma3:4b, server-side; no paid host. |

OSM data attribution and source links remain visible. Coordinates go to routing/place providers; map views go to tile providers. Optional interpretation sends text and current settings to the configured model, not coordinates. No location database exists; place results are cached in memory. Browser Google Fonts requests expose ordinary network metadata; system fonts are the fallback. Public providers may log requests and offer no availability guarantee. Keep .env, credentials, dependencies and dist out of Git; .env.example is safe configuration only.

## Hosting readiness and limits

[Exact Render account/GitHub/environment steps](docs/render-deployment.md). render.yaml prepares one Free Python web service, no database/disk, one worker, built React served by FastAPI. Render build/runtime is **not tested**; the GitHub repository is https://github.com/MrCyberlord/RunningApp, using branch master. MODEL_PROVIDER=none is the honest initial hosted configuration. Render's idle sleep and usage allowances affect demos; paid overages can apply with a payment method, so verify zero-spend controls before creating anything. [Render Free policy](https://render.com/docs/free).

[Time-boxed hosted Gemma investigation](docs/hosting-options.md): OpenRouter's live public catalog listed two zero-priced Gemma 4 variants; authenticated inference and account controls are unverified. Backboard promotional entitlement/balance, Gemma availability and integration are unverified. Google documents hosted Gemma, but its native API is not wired here. No hosted option is recommended as verified. Do not expose local Ollama to make a public demo.

Existing adapter supports an independently verified free OpenAI-compatible host with server-only MODEL_PROVIDER=openai_compatible, GEMMA_BASE_URL, GEMMA_MODEL, GEMMA_API_KEY and HOSTED_GEMMA_FREE_CONFIRMED=true. The confirmation flag is not a spending cap. Do not enable it until availability, hard spending controls and actual extraction have been verified. Otherwise keep explicit form_fallback. Local model evaluation does not transfer to different hosted models.

## Submission materials and remaining work

[DEV draft](docs/dev-draft.md) · [60–90 second recording checklist](docs/demo-checklist.md) · [handoff](docs/next-session.md).

Priorities: live browser verification, a real local demo recording, then free hosted Gemma/Render only if account access and authorization are available. Confirm official challenge template, eligibility and category, add actual repository/video links when they exist, then obtain authorization before deployment or publishing the DEV post. No URL or partner claim should be invented.

User-provided deadline: **October 12, 2026 at 12:29 PM IST (UTC+05:30)**; target **11:30 AM IST**. Hosting is time-boxed; a reproducible local project and honest write-up take priority when blocked.
