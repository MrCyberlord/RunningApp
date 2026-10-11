# Gemma live extraction comparison

Same seven requests, current values, expected values, prompt, schema and strict validator. Only the configured local model changed. No repairs or keyword overrides were applied to model output. All 1b responses returned source=gemma and passed structural validation; semantic failures remain failures.

| Case | 270m correctness | 1b correctness | 1b latency (s) | 1b semantic issue |
| --- | --- | --- | --- | --- |
| ordinary walk | Fail | Pass | 3.789 | — |
| ordinary jog | Fail | Fail | 2.637 | Added unrequested greenery |
| preserve defaults | Fail | Fail | 2.707 | Dropped existing water preference |
| negated fruit | Fail | Pass | 2.716 | — |
| stop time | Pass | Pass | 2.711 | — |
| fruit and stop | Fail | Fail | 2.779 | Returned stop_minutes=0 instead of 10 |
| no stops | Fail | Fail | 3.580 | Kept stop_minutes=5 instead of 0 |

270m: 1/7 = 14.3%. 1b: 3/7 = 42.9%.

1b mean latency: 2.988 s; median: 2.716 s. These are end-to-end local application request durations, one sequential run on this computer. First request includes cold loading if needed; other applications and memory pressure affect timings. Original 270m latencies were not recorded and are not invented.

Raw artifacts: [270m original](gemma-check-270m.json), [1b timed run](gemma-check-1b.json). The original gemma-check.json is also preserved unchanged. The command python -m backend.check_gemma now writes a model-specific report.

The 1b model remains insufficient for unattended extraction; users must review form values. Invalid schema output or unavailable inference still produces source=form_fallback and unchanged form values. Neither validation nor source labels were weakened.
