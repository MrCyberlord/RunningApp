# 60–90 second local demo recording

Target: about 80 seconds. Record actual behavior at http://127.0.0.1:8000; say clearly that it is local. No deployment or partner claim. Hide .env, API keys, account pages and personal location. Use the fixed Bengaluru start rather than revealing home coordinates.

## Before recording

- Follow README startup. Confirm /api/health and Ollama gemma3:4b. Keep only the needed model resident if memory is tight; no new download.
- Rehearse map taps, mode controls and geolocation once. Check narrow and desktop layouts. Browser interactions remain unverified until you do this.
- Use start 12.9765,77.5929, 30 total minutes, 5 pause minutes, greenery. Confirm a real route completes before recording. Do not spam shared endpoints.
- Keep browser DevTools Network ready, filter /api/preferences, hide unrelated requests and credentials. Interpretation's response can prove source=gemma; the UI's message alone is less explicit.
- If public routing fails, retry later within rate limits or record the honest warning and show prior evidence clearly labeled as an earlier run. Never replace live geometry with invented or unlabeled fixtures. Do not claim the rehearsal is the current recording.

## Timeline

- **0–10 s:** “Runningo helps me turn a short break into a real walk or jog. This demo runs locally with Gemma through Ollama.” Show the map and form.
- **10–20 s:** Point out missing-start guidance, then tap the map to select a starting point. Show the coordinates changing. Geolocation is optional; demonstrate only if permission is intentionally granted.
- **20–40 s:** Enter “A 30-minute jog with greenery and a 5-minute stop.” Click Interpret. Show jogging, 30 minutes, greenery and 5 pause minutes. Briefly show the real /api/preferences response source=gemma. Let genuine loading be visible; label any cuts.
- **40–60 s:** Click the route button. Show the returned line and start/end. Read the actual distance, moving estimate, pause and total from this run; do not pre-script yesterday's numbers as today's output.
- **60–72 s:** Open a garden marker. Explain whether it is a planned near-point stop or nearby-only marker. Entrances and access are unverified. If lookup failed, show the missing-data/unmet-preference warning instead.
- **72–82 s:** Switch to walking and generate if time permits; otherwise show the setting and note the separately recorded walking evidence. Never imply a route was generated if only the setting changed.
- **82–90 s:** “7/7 on a small fixed extraction set, not a general accuracy claim. Public services can fail; the app labels fallback. No public deployment yet.” Show repository/README locally if useful.

## Submission checks

- Video is 60–90 s, legible, audible and shows no secrets. Save a local copy; upload only when authorized.
- Review docs/dev-draft.md against the actual recording. Add actual video/repository links only after they exist and are accessible.
- Confirm official challenge template, eligibility, category and tags before publishing. User-provided deadline: October 12, 2026 at 12:29 PM IST; target 11:30 AM IST. No automatic publish/push is authorized.
