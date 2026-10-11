# Gemma 4b cold/warm comparison

Downloaded gemma3:4b through Ollama (3,350,272,403 installed bytes) and changed only GEMMA_MODEL in local .env. Other Ollama models were unloaded using keep_alive=0, not deleted. /api/ps was empty immediately before the cold test. The production adapter, prompt, JSON schema behavior, strict validator, fallback labels and seven requests/expected answers were unchanged. Original 270m and 1b results and comparison were preserved byte-for-byte.

| Case | 270m correctness | 1b correctness | 4b correctness | 4b warm latency (s) |
| --- | --- | --- | --- | --- |
| ordinary walk | Fail | Pass | Pass | 1.967 |
| ordinary jog | Fail | Fail | Pass | 5.752 |
| preserve defaults | Fail | Fail | Pass | 6.239 |
| negated fruit | Fail | Pass | Pass | 6.669 |
| stop time | Pass | Pass | Pass | 6.666 |
| fruit and stop | Fail | Fail | Pass | 6.690 |
| no stops | Fail | Fail | Pass | 6.267 |

Overall: 270m 1/7 (14.3%), 1b 3/7 (42.9%), 4b 7/7 (100%) on this fixed test set. Every 4b cold/warm application response returned HTTP 200 and source=gemma with exactly the expected preferences. This small evaluation is not a general accuracy guarantee.

Cold-start ordinary-walk application latency: 11.485 s. Ollama reported 5.623 s of model loading within that request. The same first input took 1.967 s warm, benefiting from cached prompt evaluation. All seven warm requests averaged 5.750 s (median 6.267 s). Timings include local application and HTTP inference overhead, not browser rendering. Each warm request started with the model resident; different input/schema defaults still require prompt evaluation. Prior 1b latency was recorded; original 270m latency was not.

## Defaults and ambiguity inspection

No failures remained in this run. Inspection of the unchanged production code confirms that current form values are supplied in the prompt and as JSON-schema defaults; there is no post-response merging of missing fields. All four output fields are required. Missing fields cause form_fallback, not silent default insertion. Strict validation then parses the complete model response; only duplicate preference removal is applied by the pre-existing Pydantic validator. Captured raw Ollama content agrees with application output in every 4b case.

The prompt explicitly defines additions as preserving existing preferences, and defines “No fruit stop” as removing fruit while preserving other stop time. This resolves that potentially ambiguous phrase for this evaluation; an unstated user intent might differ. “No stops” explicitly sets stop_minutes to zero. Both definitions matched the existing expected values without changes. There is no evidence of default-merging logic causing the smaller-model errors. The 4b model was able to follow the same policy. No further model is recommended from these results.

## Reproduction and evidence

    .\.venv\Scripts\python.exe -m backend.benchmark_gemma

This opt-in benchmark unloads resident models, performs the first case cold, confirms gemma3:4b is resident, then runs the unchanged seven cases warm. It does not download models or change configuration. It captures raw model output, schema defaults/required fields and Ollama load/evaluation timings. Production inference keeps its original 45-second timeout and temperature 0.

[Raw cold/warm results](gemma-check-4b.json), [preserved 1b results](gemma-check-1b.json), [preserved 270m results](gemma-check-270m.json), [previous comparison](gemma-comparison.md).
