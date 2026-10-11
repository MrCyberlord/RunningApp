# Routing diagnosis and model capacity — 11 October 2026

## Hardware snapshot (Windows CIM)

- Physical RAM: 16,597,598,208 bytes (15.46 GiB).
- Available RAM: 2,572,984,320 bytes (2.40 GiB); varies with running applications.
- C: free 297,751,650,304 bytes (277.3 GiB).
- D: free 37,159,886,848 bytes (34.6 GiB).
- Intel integrated graphics; AdapterRAM reports about 2 GiB, which is not a reliable measure of usable dedicated VRAM.

Recommend **gemma3:4b (Q4_K_M, approximately 3.4 GB download)** as the next quality-oriented local candidate for this 16 GB computer. Close memory-heavy applications first; aim for roughly 6–8 GiB available memory with a modest context. That headroom is an engineering estimate, not a measured requirement. Expect CPU/shared-memory execution and higher latency; do not assume dedicated GPU acceleration. Re-run the semantic evaluation before relying on it. If memory cannot be freed, gemma3:1b is the lighter candidate (approximately 806 MB download), with no guarantee it will solve the observed extraction failures.

Sources: [Ollama 4b](https://ollama.com/library/gemma3:4b), [Ollama 1b](https://ollama.com/library/gemma3:1b).

No models were downloaded, changed or pulled. .env remains configured for gemma3:270m. Strict preference validation and docs/gemma-check.json were preserved unchanged.

## Actual provider diagnosis

The opt-in diagnostic command uses the application's real routing code:

    .\.venv\Scripts\python.exe -m backend.diagnose_routing

It saves actual provider results in routing-diagnosis.json. The check uses the documented Bengaluru test start, not browser location.

Observed:

1. Overpass POST returned HTTP 504 in 9.25 s. Its body reported Dispatcher_Client::request_read_and_idx::timeout and said the server was probably too busy. This was a provider-side response, not a client ReadTimeout. No POIs were invented; this failure is nonfatal to routing.
2. FOSSGIS routed-foot returned HTTP 200, code Ok. First candidate: 3,237 m, about 40.46 estimated walking minutes; correctly rejected as over the 30-minute budget.
3. The adjusted candidate returned HTTP 200, code Ok: 2,341.7 m, 29.27125 estimated walking minutes; accepted.
4. After restarting FastAPI, the real POST /api/route also returned HTTP 200. Its 103-point LineString starts and ends at [77.59285,12.976526], about 6.14 m from the selected start. demo_data=false. Place lookup remained unavailable with HTTP 504. See routing-verification.json for the HTTP application result.

Provider duration was 1,873.1 seconds; the UI moving estimate uses routed distance / the documented 4.8 km/h walking pace. Geometry was returned by the foot routing endpoint, not fabricated, and no car endpoint was used.

Earlier generic HTTP 503 failures cannot retrospectively be attributed to a specific cause: the old application discarded every upstream exception. They were not reproduced in this diagnostic run. Overpass failure alone does not explain a routing 503 because route planning continues without POIs.

## Fixes and checks

- Upstream HTTP status and known OSRM response codes, client timeout types and connection errors are now distinguished in safe logs/API errors.
- Missing places explicitly include their failure reason.
- Route rejection reasons distinguish invalid geometry, start/end mismatch and exceeded time budgets.
- Authentication/permission/rate-limit responses (401/403/429) stop further routing attempts rather than hammering the same provider.
- Nonfinite routed distances are rejected.
- No secrets or raw upstream response bodies are included in normal application error messages.

42 backend tests passed, including pedestrian endpoint selection, safe error details, rate-limit handling and shrinking an over-budget route before accepting a fitting route. One existing dependency deprecation warning remains. No frontend changes were made in this task. Runningo is left serving at http://127.0.0.1:8000.
