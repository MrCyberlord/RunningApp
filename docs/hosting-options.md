# Hosted Gemma investigation — October 12, 2026

Time-box complete. Recommendation for this submission: retain verified local Ollama gemma3:4b and make an honest local demo. No hosted inference has been verified; no credentials are configured, no credits claimed, and no partner integration is implemented. No paid inference, tunnel, resource provisioning or account mutation was performed.

## OpenRouter: catalog confirmed, execution blocked

A live unauthenticated GET https://openrouter.ai/api/v1/models returned HTTP 200. It listed google/gemma-4-26b-a4b-it:free and google/gemma-4-31b-it:free with prompt/completion prices of zero. The catalog did not list google/gemma-3-4b-it:free; do not configure that old identifier based on a stale model page. Raw filtered evidence: hosted-gemma-catalog-2026-10-12.json. Listing is not a successful inference or guaranteed capacity. These hosted models differ from local Gemma 3 4B.

Account/key is required to proceed. Keep the account without purchased credit, payment method or auto top-up; restrict the exact free model and use a zero paid-spend key cap if the dashboard supports it. Verify these controls in the account, including what a zero limit actually enforces, before inference. GET /api/v1/key exposes applicable limits/budgets. Do not buy credits to increase free quotas. Avoid model fallback lists or automatic routers that could select paid models. The current adapter supplies one exact model but cannot enforce provider billing itself.

Candidate base URL is https://openrouter.ai/api/v1 with the existing OpenAI-compatible adapter. Authenticated availability, quota, spending controls and strict extraction behavior remain unverified. This is a candidate to test, not a ready hosted recommendation. [Public catalog](https://openrouter.ai/api/v1/models), [free variants](https://openrouter.ai/docs/guides/routing/model-variants/free), [key budgets and limits](https://openrouter.ai/docs/api/reference/limits).

## Backboard: account verification blocked

Official documentation advertises $5 new-account credits valid for 30 days; this does not prove a Hacktoberfest promotional entitlement or the owner's balance. The participant [offers page](https://hacktoberfest.com/my/promos) did not expose authenticated eligibility/credit details. No Backboard key is configured.

Owner must verify promotion eligibility, credited amount and expiry in the dashboard. Before any inference, inspect GET /api/billing/balance with X-API-Key: confirm balance_usd covers the test and auto_reload_enabled=false. The billing endpoints are read-only; disable reload in the dashboard, verify no payment/spillover, and confirm zero-balance behavior. If controls cannot be verified, stop.

Authenticated GET /api/models supports skip/limit pagination (limit at most 500). Search every page for Gemma and inspect exact name/provider, pricing and JSON capability. No actual Gemma model availability is established here. Backboard's native messages API is not wired to Runningo's adapter; do not claim integration or assume OpenAI compatibility. [Model discovery](https://docs.backboard.io/concepts/models), [billing controls](https://docs.backboard.io/concepts/billing).

## Google: documented Gemma support, not connected

Google's current hosted Gemma page lists gemma-4-31b-it and gemma-4-26b-a4b-it and requires an AI Studio key. This is not proof of account eligibility or the old Gemma 3 identifier. Native Gemini API support is not wired into Runningo. Free-tier applicability and no-billing settings require authenticated verification; no request was made. [Supported models](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api), [pricing](https://ai.google.dev/gemini-api/docs/pricing).

## Decision gate

Do not set HOSTED_GEMMA_FREE_CONFIRMED=true until exact model availability, spending controls and a valid preference response are verified under approved free access. If blocked, Render can eventually run with MODEL_PROVIDER=none and explicit form_fallback, while the recorded local demo demonstrates actual Gemma. Do not imply those are the same deployment. Never expose port 11434, create a public Ollama tunnel or provision a paid GPU.
