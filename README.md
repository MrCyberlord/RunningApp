# Runningo

Runningo turns a short break into a walking or jogging route that returns to your starting point. Built for a Hacktoberfest Touch Grass challenge, it combines real pedestrian routing with optional natural-language preference extraction.

> A 30-minute jog with greenery and a 5-minute stop.

**Local Gemma integration works. There is no public deployment.**

## Features

- Interactive map with start selection and optional browser geolocation.
- Walking and jogging routes based on available time, with distance, moving time, pause time and total estimates.
- Parks, gardens, viewpoints, greengrocers and drinking-water markers from OpenStreetMap where data exists.
- Preferred-place waypoints, distinct nearby-only markers, and warnings for unmet preferences or unavailable data.
- Optional Gemma interpretation with strict validation and explicit fallback labels.
- Green mobile-first interface with loading/error states and responsive Leaflet sizing.

**Stack:** React, TypeScript, Vite and Leaflet; Python, FastAPI, Pydantic and HTTPX; Ollama with gemma3:4b; FOSSGIS OSRM foot routing and Overpass place lookup. No accounts, database or live tracking.

## Quick start

Requires Git, Python 3.11+ (3.12 recommended), Node.js 22 LTS and npm. Ollama is optional for AI interpretation. Default routing and place lookup require internet access but no API key.

```sh
git clone https://github.com/MrCyberlord/RunningApp.git
cd RunningApp
python -m venv .venv
```

Activate the environment:

| Platform | Command |
| --- | --- |
| macOS/Linux | `source .venv/bin/activate` |
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |

If your Python command is python3 or py, use that to create the environment. If PowerShell activation is restricted, use Command Prompt or invoke the virtual environment’s Python executable directly.

From the repository root, with the environment activated:

```sh
python -m pip install -r backend/requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. FastAPI serves the built frontend and API; health is available at /api/health. The default configuration works with form controls and explicitly reports AI as unused.

### Enable local Gemma

Install [Ollama](https://ollama.com/), then download the evaluated model:

```sh
ollama pull gemma3:4b
ollama serve
```

Skip ollama serve if Ollama is already running. Copy .env.example to .env in the repository root if it does not exist, preserving any existing settings. Set:

```dotenv
MODEL_PROVIDER=ollama
GEMMA_MODEL=gemma3:4b
OLLAMA_URL=http://127.0.0.1:11434
```

Restart FastAPI after changing configuration. Keep model settings and credentials server-side; .env is ignored by Git. No frontend key is required. Local inference speed depends on hardware and available memory.

For frontend development, keep FastAPI running and start Vite in another terminal:

```sh
npm --prefix frontend run dev
```

Open http://127.0.0.1:5173. Vite proxies /api requests to port 8000.

## Architecture

The React form sends text and current settings to FastAPI. Ollama runs Gemma with a JSON schema and temperature zero; Pydantic validates preference fields, types, categories and time bounds. Successful interpretation reports `source: gemma`. Invalid or unavailable output preserves current form values and reports `source: form_fallback`. Users review interpreted settings before planning.

The planner queries Overpass for mapped places and requests geometry from FOSSGIS OSRM’s pedestrian endpoint. Gemma supplies neither geometry nor time calculations. Code estimates moving time from routed distance at **4.8 km/h walking** or **8 km/h jogging**, reserves the requested pause, and checks that total time fits the available time. A pause remains included when no mapped place can be assigned, with a warning.

Place lookup uses bounded timeouts, at most one alternative endpoint and a ten-minute in-memory cache. Successful empty results are distinguished from unavailable service. Run one backend worker because caching and upstream rate limiting are process-local.

## Validation

- **Automated:** 57 backend tests passed; TypeScript and the production build passed.
- **Live local API:** Gemma preferences reached the planner, and real pedestrian round trips returned successfully. One jogging case produced 3.221 km with 24.15 moving minutes plus a 5-minute pause. See the [end-to-end report](docs/end-to-end-4b.md) and [latest HTTP evidence](docs/resume-verification-2026-10-12.json).
- **Manual UI checks:** the developer verified time changes, longer jogging routes, and reduced route distance when adding stop time. Other browser interactions and rendered layouts remain unverified.

The same **small fixed set of seven extraction cases** produced:

| Local model | Semantically correct cases |
| --- | --- |
| gemma3:270m | 1/7 |
| gemma3:1b | 3/7 |
| gemma3:4b | 7/7 |

These development results do not establish general accuracy. The prompt, expectations and strict validation were preserved across comparisons. See [evaluation details and timings](docs/gemma-4b-comparison.md).

Run checks with the Python environment activated:

```sh
python -m pytest backend -q -p no:cacheprovider
npm --prefix frontend run build
```

The build includes TypeScript checking. Optional live checks are `python -m backend.check_end_to_end`, `python -m backend.check_gemma` and `python -m backend.check_places`; they call external services/local Ollama and replace their latest evidence files.

## Limitations

- Route search tries at most three candidates and includes at most one preferred mapped stop. Paths may overlap, retrace or undershoot the requested time; a suitable route may not be found.
- Fixed pace estimates do not account for terrain, crossings or individual fitness.
- Mapped centres are not verified entrances. Nearby markers do not imply visits. Opening hours, legal access, route suitability, fruit stock and water quality are unverified.
- Shared public services may time out or rate-limit requests. Schema validation cannot guarantee that a model interpreted intent correctly.
- Geolocation requires browser permission and HTTPS or localhost. Mobile layout, geolocation and browser behavior beyond the manual checks above still need interactive verification.
- [Render Free configuration](render.yaml) is prepared, but deployment and hosted Gemma inference have not been verified. Local Ollama should remain private. See [deployment details](docs/render-deployment.md) and [hosted-model research](docs/hosting-options.md).

## Data, attribution and privacy

Maps and places use [OpenStreetMap contributors’ data](https://www.openstreetmap.org/copyright). Pedestrian routes use [FOSSGIS routing](https://routing.openstreetmap.de/about.html); place queries use [Overpass](https://overpass-api.de/). Optional [openrouteservice](https://openrouteservice.org/) routing requires a server-side key and has not been tested here. Respect each provider’s usage and attribution policies; these public endpoints are intended for modest traffic.

Planning sends coordinates to route/place providers, and map tiles reveal the viewed area to the tile service. Interpretation sends text and current preferences to the configured model. Runningo has no location database; place responses are temporarily cached in memory. The interface also requests Google Fonts, with system-font fallbacks. Third-party services may retain request logs.
