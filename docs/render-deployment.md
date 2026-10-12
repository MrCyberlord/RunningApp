# Render Free readiness — prepared, not deployed

Reviewed October 12, 2026. GitHub repository: https://github.com/MrCyberlord/RunningApp; local branch is master. The owner authorized connecting and pushing source on October 12. No service creation or deployment was performed. Code/configuration is ready for a first build attempt, not proven on Render. A local Python + Vite build is not proof of Render runtime compatibility.

## Account and GitHub steps for the owner

1. Sign into/create a GitHub account. Create an empty Runningo repository (no generated README, license or .gitignore to avoid initial history conflicts). Choose visibility according to challenge rules. Review the local changes and commit them when ready. The existing checkpoint is 4dd24b609f2da0e9252ce599db40613409f87b6c.
2. Only after authorizing a push, connect the actual GitHub repository as origin and push master. The owner has now authorized connecting and pushing this repository; verify the resulting remote commit before proceeding to Render. Verify .env, node_modules, .venv and dist are absent from GitHub. Commit the npm lockfile and .env.example.
3. Create/sign into Render, choose a workspace, connect the GitHub integration and grant access to this repository only. Use a workspace without a payment method where available; otherwise establish a verified zero-spend policy before creating anything. Do not upgrade or enable paid add-ons.
4. New > Web Service > select repository. Branch master; root directory blank (repository root); runtime Python; compute Free. Set auto-deploy off for controlled review. Do not choose Static Site: the app needs FastAPI. A Blueprint using render.yaml is an alternative, not an extra service; review it before applying.
5. Review the fields below. Do not press Deploy until authorized. Service creation can start a build immediately. Never add a disk, database, worker or paid model host.

[Render deployment instructions](https://render.com/docs/your-first-deploy) describe Git-provider authorization, service fields and Free compute selection.

## Exact service configuration

- Build: pip install -r backend/requirements.txt && npm --prefix frontend ci && npm --prefix frontend run build
- Start: uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1
- Health path: /api/health
- PYTHON_VERSION=3.12.10; NODE_VERSION=22.16.0 (from render.yaml; first Render build remains untested).
- MODEL_PROVIDER=none initially. This is an honest form-only public configuration, not hosted AI.
- OVERPASS_URL=https://overpass-api.de/api/interpreter
- OVERPASS_FALLBACK_URL=https://overpass.private.coffee/api/interpreter
- OVERPASS_TIMEOUT_SECONDS=15
- USER_AGENT=Runningo/0.1 (small Hacktoberfest demo)
- Leave ORS_API_KEY unset to use FOSSGIS foot. No frontend secrets or VITE_ credentials. Render supplies PORT; do not hard-code 8000.

Only after authenticated free-host verification, replace MODEL_PROVIDER with openai_compatible and set GEMMA_BASE_URL, the exact GEMMA_MODEL, secret GEMMA_API_KEY and HOSTED_GEMMA_FREE_CONFIRMED=true in Render's server environment. This flag is a configuration gate, not a billing safeguard. Keep it false/unset while access or spending controls are uncertain. Do not copy local MODEL_PROVIDER=ollama or OLLAMA_URL to Render. Never tunnel or bind local Ollama publicly.

## Free limits and post-deployment acceptance

Render documents free-service sleep after 15 idle minutes, shared monthly free hours, and usage caps. Bandwidth overages can be billed when a payment method exists; without one, Free services are suspended instead. Exhausted build minutes can block builds. Free compute alone is not an unconditional zero-spend guarantee. Check the actual workspace settings before deployment. [Free-service policy](https://render.com/docs/free).

After an authorized deploy, record only the actual URL Render assigns. Verify HTTPS home/favicon, /api/health, real pedestrian loop, stop sum, place status/warnings and missing-start feedback. With MODEL_PROVIDER=none, confirm source=form_fallback. With an approved host, verify source=gemma and rerun the fixed semantic cases; local gemma3:4b results do not transfer to a different hosted model. Check cold-start and 360/390/768/1280 px browser behavior. Preserve logs without keys or personal locations. No deployment URL exists yet.
