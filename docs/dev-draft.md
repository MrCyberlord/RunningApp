---
title: "Runningo: a little fresh air, planned with Gemma"
published: false
tags: [hacktoberfest, gemma, python, react]
---

Source: [MrCyberlord/RunningApp](https://github.com/MrCyberlord/RunningApp).

I built Runningo for a Touch Grass challenge: choose a starting point, walk or jog, set your available time, and find a real route back. It is a small local MVP built with React, TypeScript, Leaflet and FastAPI, using free services only.

## What I built

The map supports tap-to-select starts and optional browser geolocation. You can request parks/gardens, scenic viewpoints, a greengrocer or drinking water where OpenStreetMap has data. Nearby markers are distinguished from suggested routed stops. Missing place data and unmet preferences produce warnings.

Natural-language requests go to local Ollama gemma3:4b. For “A 30-minute jog with greenery and a 5-minute stop,” Gemma returned the expected structured settings with source=gemma. Those settings were passed to the route endpoint. The model never draws paths or calculates time: FOSSGIS OSRM foot supplies pedestrian geometry, and code calculates moving time from routed distance plus the requested pause.

## What I verified locally

On October 12, my local HTTP app returned a real 3.221 km pedestrian round trip near Bengaluru's Cubbon Park area: 24.15 moving minutes at the configured jogging pace, plus a 5-minute pause, for 29.15 minutes total. Place data was reused from a successful Overpass cache entry. A mapped garden influenced routing as a waypoint; earlier geometry checks measured the route within about 35 m of its mapped centre. That does not verify its entrance or a visit inside the garden.

A separate walking case returned a real loop while Overpass was unavailable. The app warned that greenery was unmet and the pause had no mapped place assigned. I fixed a bug that had previously dropped pause time during lookup failures.

Gemma 3 4B passed **7/7 cases on one small, fixed evaluation set**, compared with 1/7 for 270m and 3/7 for 1b using the same prompt and expectations. These are preserved development results, not general accuracy or a statistical benchmark. Strict schema validation rejects malformed outputs, but a valid schema alone cannot guarantee semantic correctness. Form controls remain authoritative, and model failure explicitly reports source=form_fallback rather than claiming AI was used.

The latest deterministic suite has 57 passing tests; TypeScript and the Vite build pass. Rendered mobile layouts, map clicks and browser geolocation still need interactive verification; CSS/source checks alone are not visual testing.

## Scope and limitations

This is **tested locally, not deployed**. There is no public demo URL and no Backboard or hosted Gemma integration. Render Free configuration is prepared only. Hosted model listings and promotional offers require account, quota and spending-control verification before use.

Routes may retrace paths or undershoot the budget; the search tries at most three routes and includes at most one preferred place. Public services can time out. Walking/jogging times use fixed 4.8/8 km/h estimates. Opening hours, entrances, access, road suitability, fruit stock and water quality are unverified. No accounts, database, social features or live tracking are included.

My next steps are live browser checks, a short local recording, and a free public deployment only after hosting is verified. Promotional credits are acceptable; out-of-pocket spending is not.

Data and attribution: [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), [FOSSGIS pedestrian routing](https://routing.openstreetmap.de/about.html), and [Overpass](https://overpass-api.de/). Gemma runs locally through [Ollama](https://ollama.com/library/gemma3).

<!-- Before publishing: insert the actual repository link and recorded demo, confirm the challenge's official template/tags/eligibility and deadline, and replace any statements only if newly verified. No public URL or partner integration is implied. -->
