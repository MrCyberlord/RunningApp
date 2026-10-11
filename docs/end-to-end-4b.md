# Live application verification with gemma3:4b

Both exact hyphenated requests returned source=gemma and the expected mode, 30 total minutes, greenery and 5 pause minutes. Instrumentation at the actual FastAPI planner boundary confirmed its validated input equals the interpretation plus the selected start (12.9765,77.5929). No upstream data was mocked. See end-to-end-4b.json for full requests, provider traces, geometry and responses; end-to-end-4b-before-fix.json preserves the discovered pause-loss failure.

Jogging: FOSSGIS OSRM foot, 3221 m (rounded), 24.1545 moving + 5 pause = 29.1545 minutes. 162 geometry vertices, closure 0 m, start snap 6.14 m. Overpass primary succeeded. The selected garden way/1258159464 was explicitly passed as a routing waypoint; nearest returned vertex is 34.72 m from its mapped centre. Other returned places are nearby markers only. Entrance, actual park traversal and access remain unverified.

Walking: FOSSGIS OSRM foot, 1272 m (rounded), 15.90375 moving + 5 pause = 20.90375 minutes. 71 vertices, closure 0 m, start snap 6.14 m. Overpass hit its deadline and the alternative returned HTTP 500. Response distinguishes unavailable from empty, warns greenery is unmet, identifies the pause as unassigned, and warns the limited search found a shorter route.

Fixes: pause is reserved and added whether a mapped place is available or not; partially unmet preference categories now produce warnings; map popups distinguish nearby-only markers from suggested stops. Model prompt and strict validation are unchanged. Prior model comparisons are retained.

This exercises real API handlers and live upstream services, with source tracing for React interpretation-to-form-to-route wiring. No connected in-app browser was available, so clicks, map tiles and browser geolocation were not interactively verified in this run. No deployment was performed.

Reproduce: .venv\Scripts\python.exe -m backend.check_end_to_end (makes live upstream calls and replaces the latest evidence file).
