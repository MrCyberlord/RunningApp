# Runningo

A mobile-friendly walking/jogging round-trip planner for Hacktoberfest Touch Grass. React + TypeScript + Leaflet, with FastAPI. No accounts, database, social features, live tracking, or paid infrastructure. Nothing has been deployed.

## Implementation plan / scope

1. Map click selection and optional geolocation; real pedestrian routes first.
2. Real OpenStreetMap places, time-budget search and explicit fallback states.
3. Server-side Gemma preference extraction and strict validation.
4. Responsive green interface, checks, and Render Free preparation.

This empty folder had no existing project or AGENTS.md. No API keys are needed for the default map, routing or places. A hosted Gemma account/key and verified free quota are the only optional model blockers. Local Ollama requires downloading a model and suitable local hardware. Render requires an account only when you decide to deploy.

## Local startup (PowerShell, repository root)

Current local model: **Ollama gemma3:4b**, configured server-side in the existing, ignored .env. The model is already installed; no download is needed to resume. Preserve .env. Run from D:\Downloads\Hactober Fest\Runningo.

Terminal 1, only if Ollama is not already running (the desktop app may already provide it):

    & "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve

Terminal 2:

    Set-Location 'D:\Downloads\Hactober Fest\Runningo'
    npm --prefix frontend run build
    .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

Open http://127.0.0.1:8000. Stop an existing API on that port before starting another. Leave one backend worker for process-local rate limits and caching. If Ollama is on PATH, ollama serve is equivalent. Check installed/resident models with ollama list and ollama ps.

For a fresh checkout, install Python 3.11+ (3.12 recommended), Node 22 LTS and dependencies first:

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
    if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
    npm --prefix frontend ci

The example defaults to MODEL_PROVIDER=none. To use the installed local model, set these server-only values in .env and restart FastAPI:

    MODEL_PROVIDER=ollama
    GEMMA_MODEL=gemma3:4b
    OLLAMA_URL=http://127.0.0.1:11434

On systems using the Windows Python launcher, substitute py -3.12 for python when creating the venv. For frontend development, keep the API running and use another terminal:

    npm --prefix frontend run dev

Open http://127.0.0.1:5173. Vite proxies /api to port 8000. Linux/macOS: use .venv/bin/python instead of the Windows executable. No frontend keys are needed.

## Try it

Tap a path on the map, or grant browser location permission. The initial Bengaluru view is explicitly only a viewport, not a detected location or sample route. Choose walking/jogging, 10–120 total minutes, preferences, and optional stop minutes. Click Find my fresh-air route. Change any setting to clear stale results. Optional natural-language interpretation changes form settings for review; it never creates a route.

Routes and places are always live; there are no fabricated or offline demo fixtures in the app. Tests use mocks only. Public service failure shows an error or a labeled fallback. Planning can take up to about two minutes during upstream slowdowns. Geolocation needs HTTPS or localhost. Map keyboard panning/zoom is available through Leaflet; start selection uses map tapping or geolocation.

## Routing and time calculation

Default routing uses the **FOSSGIS OSRM foot instance**, not the car demo server. Optional ORS uses foot-walking. Only returned GeoJSON geometry is drawn. Three bounded attempts target the time budget using a mapped preferred place or geographic candidate waypoints. Geographic candidates are not places; the routing engine must find pedestrian paths through them. A route is accepted only if its end returns within 20 m of its start, its mapped start is within 100 m of the selected location, and its calculated total time fits the budget. Routes can overlap or be entirely out-and-back. This is a heuristic, not an optimal loop solver.

Moving minutes = routed distance in meters / speed in meters per minute. Walking = 4.8 km/h, jogging = 8 km/h. Provider duration is retained in the API response for comparison, but never misrepresented as a jogging duration. Crossings, terrain and actual fitness can add time. Requested pause time is always added and reserved from the moving budget. A mapped stop is suggested only within 80 m of the route geometry; otherwise the pause is unassigned with a warning. POI polygon centers do not guarantee an entrance; the UI labels suggested stops accordingly. At most one preferred stop is included in this evening MVP; selecting multiple preferences does not guarantee every category. A route below 80% of the requested time gets a shorter-route warning.

Overpass highlights parks/gardens (leisure tags), viewpoints (tourism=viewpoint), greengrocers (shop=greengrocer), and drinking-water points (amenity=drinking_water, excluding drinking_water=no). Supermarkets are not inferred to be fruit shops. Private/no-access places are excluded when tagged. Unnamed features are explicitly labeled unnamed, with source links. Nearby markers are not all on the route. Opening hours, stock, entrances, pavement quality, legal access and water quality are not inferred or invented. Unmapped places remain unknown.

## Free providers, limits and attribution

Researched 11 October 2026. Public endpoints have no availability SLA; recheck terms before inviting substantial traffic.

| Provider | Key/account | Limits and attribution |
| --- | --- | --- |
| [OSM raster tiles](https://operations.osmfoundation.org/policies/tiles/) | None | Visible OSM contributor attribution; no bulk download, prefetch, offline scraping or cache bypass. Browser handles HTTP cache and referrer. Best effort service; no guaranteed quota. |
| [FOSSGIS foot routing](https://routing.openstreetmap.de/about.html) | None | Maximum 1 request/second; valid User-Agent, attribution and Fix the map link; no heavy use or scraping. The backend serializes upstream calls and spaces starts by 1.05 s. Worldwide foot profile. |
| [Overpass public API](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html) | None | Shared capacity; load shedding and 429/504 possible. Guideline about 10,000 queries/day and 1 GB/day is not an entitlement. Intended for modest use, not a growing consumer app backend. Configurable per-attempt wall-clock deadline (15 s default, clamped 2–30 s), query timeout 2 s shorter, radius capped at 5 km, 10-minute bounded in-memory cache including successful empty results. OSM ODbL attribution/source links. |
| [openrouteservice](https://openrouteservice.org/plans/) / [restrictions](https://openrouteservice.org/restrictions/) | Free account and Standard key | Published Standard directions allowance: 2,000/day, 40/minute. Optional ORS_API_KEY stays on backend. Attribute openrouteservice/HeiGIT and OSM; result shows provider and footer links. Verify your actual dashboard limits. |

Use only one backend worker: limiter/cache are process-local. Do not scale replicas against public demo endpoints. The bounded search uses up to three routing calls per outing. Public launch at scale requires a sustainable provider arrangement; no paid resource is provisioned here. Coordinates are sent to routing/place services, which may log them. Runningo does not persist locations, but caches place responses in process memory for ten minutes. Tile requests reveal the viewed area to OSM. Google Fonts requests expose normal browser network metadata; system fonts remain the fallback.

## Gemma configuration

Default MODEL_PROVIDER=none keeps form controls functional. It explicitly returns source=form_fallback and says AI was not used. There is deliberately no keyword parser pretending to understand negation or nuanced requests. Invalid JSON, unknown keys/categories, missing fields, invalid modes, string/boolean numeric values, out-of-range minutes, impossible stop budgets, network failures and non-Gemma model configuration all fall back to unchanged form settings. The model receives only text and existing preferences, not route coordinates. No model tools execute.

For local [Ollama Gemma](https://ollama.com/library/gemma3):

    ollama pull gemma3:4b
    ollama serve

If Ollama is already running, do not start a second instance. Set in .env and restart FastAPI:

    MODEL_PROVIDER=ollama
    GEMMA_MODEL=gemma3:4b
    OLLAMA_URL=http://127.0.0.1:11434

Ollama uses /api/chat, JSON schema format and temperature zero. The output schema requires all four fields, with per-request defaults copied from the current form (including stop_minutes). A concise prompt with two examples covers synonyms, negation and stop time. Every response still passes the original strict validator; missing fields are not silently merged into model output.

The installed gemma3:270m was tested with real application calls: **1/7 semantic cases passed**, reproduced twice. One request correctly produced jogging, 30 minutes, greenery and a 5-minute stop with source=gemma. Failures included retaining fruit after “No fruit stop”, missing parks/scenic preferences, adding unrequested water and ignoring times. All seven outputs were structurally valid, so source=gemma truthfully identifies the model origin, not semantic correctness. The existing UI asks users to review settings. This model is not reliable for automatic preference extraction; use the form controls for dependable input. No model was downloaded during that original 270m evaluation, and validation was not weakened. Larger model downloads were subsequently authorized; see the preserved comparisons below.

Reproduce the opt-in live check (Ollama must already be running; no download is performed):

    .\.venv\Scripts\python.exe -m backend.check_gemma

The command exits nonzero on semantic failures and saves expected/actual application responses and timings to model-specific docs/gemma-check-<tag>.json files. The original [docs/gemma-check.json](docs/gemma-check.json) remains preserved. Ordinary pytest runs remain deterministic and do not invoke Ollama.

### Hosted demo investigation

- [Google's hosted Gemma documentation](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api) currently lists Gemma models on Gemini API and requires an AI Studio key. Availability, model identifiers, regional eligibility and [free-tier pricing](https://ai.google.dev/gemini-api/docs/pricing) must be checked in your account. Do not infer support from older Gemma 3 announcements. Its native API is not wired in this MVP; use a verified OpenAI-compatible Gemma endpoint with the implemented adapter, or keep form fallback.
- [Backboard model discovery](https://docs.backboard.io/concepts/models) exposes GET /api/models with X-API-Key. Query every page for Gemma, inspect provider and pricing, and make a small validated test before selecting a model. Discovery was researched, not authenticated or invoked here.
- The [Hacktoberfest offers page](https://hacktoberfest.com/my/promos) is the place to check participant promotions. The public page did not expose credit amount, expiry, eligibility or an account balance. **Backboard promotional credit and Gemma availability are unverified.** No credit has been claimed or spending enabled.
- [Backboard balance API](https://docs.backboard.io/concepts/billing) exposes /api/billing/balance, including auto-reload settings. Verify promotional balance, expiry and no automatic spending in the account before use. Backboard's documented X-API-Key + threads/messages API is not OpenAI-compatible and is not wired into this MVP. No assistants, threads or remote storage are created by Runningo.

For an independently verified free OpenAI-compatible **Gemma** host, the implemented server adapter supports:

    MODEL_PROVIDER=openai_compatible
    GEMMA_BASE_URL=https://your-verified-provider.example/v1
    GEMMA_MODEL=exact-gemma-model-id-from-provider
    GEMMA_API_KEY=your-server-only-key
    HOSTED_GEMMA_FREE_CONFIRMED=true

The example host is a placeholder, not a working service. Leave the confirmation false unless free access is verified; configure provider hard caps/no paid spillover. No provider key, API response secret or VITE_ credential belongs in the frontend. Ollama on your laptop is not reachable from Render through localhost. Render Free is not a practical Gemma GPU host.

## Checks

    .\.venv\Scripts\python.exe -m pytest backend -q
    npm --prefix frontend run build

57 tests passed after the end-to-end integration fixes: routed-distance time calculations, invalid distances, strict model schema, adapter success/failure, honest fallback, place classification/decoding, included stop time, closed-route contract, time-budget exclusion, outage without fabricated route, API validation. One dependency deprecation warning was observed. TypeScript and Vite production build passed. npm audit reported zero vulnerabilities at installation.

Live smoke test at Bengaluru 12.9765,77.5929: real FOSSGIS pedestrian route returned HTTP 200, 2.342 km, 29.27125 estimated walking minutes. Built homepage and health endpoint returned HTTP 200. Overpass returned HTTP 504 in a separate unsandboxed check and was unavailable in that test, correctly showing no places and explicit degraded warnings. Provider status is transient.

Untested: browser visual/mobile layout (no browser connection available), interactive map clicks/geolocation, hosted Gemma, ORS with a key, Render build/runtime. No automated test claims to verify real-world road suitability or opening hours.

## Render Free (prepared, not deployed)

render.yaml declares one Python web service with plan: free, no database or persistent disk. Build installs Python packages, runs npm ci from the committed lockfile, builds React; FastAPI serves frontend/dist and /api from the same origin. Start uses PORT and one worker. Health check is /api/health. Review the blueprint in Render before applying; keep all plans free, add secrets in its environment UI only, and leave MODEL_PROVIDER=none until a free Gemma host is verified.

[Render Free limitations](https://render.com/docs/free): idle web services sleep after 15 minutes; waking can take about a minute. The workspace gets 750 free instance hours/month shared across free services; outbound bandwidth/build limits also apply. No keep-awake pings or background tracking. In-memory caches disappear on sleep/restart. Free services can be suspended at allowance limits. Recheck current quotas in your dashboard; never upgrade automatically.

## Latest routing diagnosis and hardware recommendation

See [docs/routing-notes.md](docs/routing-notes.md) for measured RAM/disk capacity, the larger Gemma recommendation (no download), actual Overpass 504 evidence, and the verified live pedestrian round trip. [docs/routing-verification.json](docs/routing-verification.json) preserves the HTTP application result. Earlier generic 503 causes remain unknown; failures now report sanitized status/timeout/rejection reasons.

## 1b comparison and resilient Overpass lookup

Only GEMMA_MODEL in local .env was changed to gemma3:1b after the authorized Ollama download (806,067,407 installed bytes). Both models remain installed. [Seven-case comparison with latency](docs/gemma-comparison.md): 1b passed 3/7 (42.9%), versus the preserved 270m 1/7 (14.3%). No preference validation, prompt or fallback label was relaxed for the comparison.

Overpass settings (server-side; .env.example documents them):

- OVERPASS_URL: primary endpoint.
- OVERPASS_FALLBACK_URL: defaults to https://overpass.private.coffee/api/interpreter; set empty to disable. [Public instance listing and policies](https://wiki.openstreetmap.org/wiki/Overpass_API#Public_Overpass_API_instances). This is a small-demo alternative, not a guaranteed service.
- OVERPASS_TIMEOUT_SECONDS: 15 seconds per attempt by default, clamped to 2–30. Includes shared limiter wait and HTTP read; the entire lookup, including lookup-lock queue wait, is bounded at twice that plus 2 seconds (32 seconds by default).

At most two upstream requests: primary plus one distinct alternative after a transient network/server failure or incomplete response. Non-transient errors stop immediately. HTTP 429 stops failover and establishes a per-endpoint cooldown honoring Retry-After (minimum 60 seconds). Shared upstream serialization still spaces request starts by at least 1.05 seconds. Keep one process/worker. Identical concurrent lookups reuse the first successful cache result. Cache keys include provider configuration, location and radius; TTL 10 minutes, maximum 128 entries; failures are not cached as empty results.

Route API place_lookup.status is ok, empty or unavailable. The UI distinguishes a successful empty lookup from unknown places due to an unavailable service. Alternate providers, attempts, previous errors and cache hits are recorded in metadata. Opening hours, entrances, shop stock, accessibility and water quality remain unverified.

Live lookup: overpass-api.de returned HTTP 200 with 88 elements; 81 usable mapped features were retained. A repeated lookup hit the cache without another upstream request. See [place-check.json](docs/place-check.json). The alternative was not needed by this live request; bounded failover, deadlines, empty caching and cooldowns are verified with tests.

    .\.venv\Scripts\python.exe -m backend.check_places

This opt-in live command saves provider status and mapped results in docs/place-check.json. It never invents missing places.

A later check through the restarted HTTP app exercised both live endpoints: primary HTTP 504, alternative HTTP 500. It correctly returned place_lookup.status=unavailable and no invented places, while FOSSGIS pedestrian routing succeeded. [place-http-check.json](docs/place-http-check.json) preserves that result separately from the earlier successful lookup/cache test. Public provider availability is transient.

## Latest local model: gemma3:4b

After the authorized download, only GEMMA_MODEL in local .env was changed to gemma3:4b. Other resident models were unloaded before testing. The unchanged seven-case evaluation passed 7/7 with source=gemma; cold application latency was 11.485 s, warm mean 5.750 s and warm median 6.267 s. All earlier failures/results remain preserved unchanged. See [4b cold/warm comparison and defaults inspection](docs/gemma-4b-comparison.md) and [raw results](docs/gemma-check-4b.json). This fixed seven-case result is not a general reliability guarantee.

Requested pause time is always included in the total estimate and reserved from the moving-time budget. When no mapped stop can be included, the pause remains unassigned and a warning explains this. Nearby markers are not planned stops; unmatched requested place categories are reported individually.

## Checkpoint: 11 October 2026

See [docs/next-session.md](docs/next-session.md) for tomorrow's handoff. This is a local Git checkpoint only; nothing is pushed or deployed. **Free services only. Promotional credits are allowed, but no out-of-pocket spending, automatic top-ups or paid spillover.**

Latest verified functionality:

- Strict Gemma extraction: gemma3:4b passed the unchanged seven-case live evaluation (7/7); 270m and 1b failures remain preserved. Validated output reports source=gemma; failures retain the form and explicitly report form_fallback. Correct source does not guarantee semantic correctness on unseen requests.
- Real pedestrian jogging round trip at Bengaluru: 3.221 km, 24.1545 moving + 5 pause = 29.1545 minutes. FOSSGIS OSRM foot returned closed geometry; selected start snapped 6.14 m. Live Overpass data supplied a garden waypoint; the geometry came within 34.72 m of its mapped centre. Other markers are merely nearby. A physical visit, entrance and park traversal are not verified.
- Walking case: 1.272 km, 15.90375 moving + 5 pause = 20.90375 minutes. Overpass timed out / alternative HTTP 500; warnings correctly reported unavailable data, unmet greenery, an unassigned pause and a shorter route. Requested pauses now remain included even when no mapped place is available. Partial preference misses are also warned.
- Latest backend suite: 57 passed with one dependency deprecation warning. TypeScript and production builds passed after the responsive UI, prerequisite feedback, Vite CSS types and original transparent SVG favicon updates. Built favicon served HTTP 200.
- Responsive CSS source calculations cover 360, 390, 768 and 1280 px. Single column through tablet widths, desktop split, touch controls, mobile route button and Leaflet ResizeObserver are implemented. Missing start selection shows instructions rather than a disabled busy-cursor button.

Evidence: [live application verification](docs/end-to-end-4b.md), [HTTP result](docs/end-to-end-http-4b.json), [model comparison](docs/gemma-4b-comparison.md), [CSS audit](docs/responsive-layout-check.json). Historical reports are observations from their recorded runs, not current service guarantees.

Known limitations: no connected browser was available, so rendered layout, map clicks, geolocation, button interactions and actual interactive resizing still need live browser verification. Overpass and pedestrian routing are best-effort shared services; lookups may be empty or unavailable. Route search is limited to three attempts and one preferred mapped stop; routes may retrace paths or undershoot the time budget. Access, suitability, opening hours, stock and water quality remain unknown. ORS, hosted Gemma and Render runtime have not been tested. Local Ollama cannot serve a Render app via localhost. Public demo must use a verified free hosted Gemma option or honestly labeled form fallback.

Remaining work, in order:

1. Live browser verification at 360, 390, 768 and 1280 px, map selection/geolocation, missing-start feedback, both route modes and failure warnings.
2. Verify a free hosted Gemma provider/account/model/quota. Backboard promotional balance, eligibility, expiry and Gemma availability are still unverified; native Backboard integration is not implemented. Keep credentials server-side and prevent all paid spillover.
3. Review and deploy the prepared Render Free configuration only when authorized. Verify public startup/cold-start behavior, HTTPS geolocation, real routes and honest AI source labels.
4. Record the demo and prepare the DEV submission with actual provider/model use and remaining limitations.
5. Submit by **October 12, 2026 at 12:29 PM IST (UTC+05:30)**; target **11:30 AM IST**, leaving 59 minutes of buffer. This deadline is user-provided; independently confirm challenge requirements before submission.
