"""Opt-in live application check: python -m backend.check_gemma (no downloads)."""
import json
import os
import time
import statistics
from pathlib import Path
from fastapi.testclient import TestClient
from .main import app
from .models import Preferences

CASES = [
    ('ordinary walk', 'A 30 minute walk through parks.',
     Preferences(), Preferences(minutes=30, preferences=['greenery'])),
    ('ordinary jog', 'Jog for 40 minutes.',
     Preferences(), Preferences(mode='jogging', minutes=40)),
    ('preserve defaults', 'Add scenic views.',
     Preferences(mode='jogging', minutes=45, preferences=['water'], stop_minutes=7),
     Preferences(mode='jogging', minutes=45, preferences=['water','scenic'], stop_minutes=7)),
    ('negated fruit', 'No fruit stop.',
     Preferences(preferences=['greenery','fruit','water'], stop_minutes=5),
     Preferences(preferences=['greenery','water'], stop_minutes=5)),
    ('stop time', 'A 30 minute jog with greenery and a 5 minute stop.',
     Preferences(), Preferences(mode='jogging', minutes=30, preferences=['greenery'], stop_minutes=5)),
    ('fruit and stop', 'Walk for 45 minutes, visit a fruit shop, and take a 10 minute break.',
     Preferences(), Preferences(minutes=45, preferences=['fruit'], stop_minutes=10)),
    ('no stops', 'No stops, just walk for 20 minutes.',
     Preferences(stop_minutes=5), Preferences(minutes=20, stop_minutes=0)),
]


def main():
    results = []
    with TestClient(app) as client:
        for name, text, current, expected in CASES:
            started = time.perf_counter()
            response = client.post('/api/preferences', json={'text': text, 'current': current.model_dump()})
            latency = time.perf_counter() - started
            body = response.json()
            actual = body.get('preferences', {})
            wanted = expected.model_dump()
            matches = all(actual.get(k) == v for k,v in wanted.items() if k != 'preferences')
            matches = matches and set(actual.get('preferences', [])) == set(wanted['preferences'])
            passed = response.status_code == 200 and body.get('source') == 'gemma' and matches
            row = {'name': name, 'request': text, 'current': current.model_dump(),
                   'expected': wanted, 'actual': body, 'passed': passed,
                   'latency_seconds': round(latency, 3)}
            results.append(row)
            print(json.dumps(row), flush=True)
    passed = sum(r['passed'] for r in results)
    timings = [r['latency_seconds'] for r in results]
    report = {'model': os.getenv('GEMMA_MODEL'), 'provider': os.getenv('MODEL_PROVIDER'),
              'passed': passed, 'total':len(results), 'accuracy':passed/len(results),
              'latency_mean_seconds':statistics.mean(timings),
              'latency_median_seconds':statistics.median(timings),
              'timing_note':'End-to-end application latency; first case includes model loading if cold.',
              'cases': results}
    tag = os.getenv('GEMMA_MODEL', 'unknown').split(':')[-1]
    if not tag.isalnum():
        raise ValueError('Use an alphanumeric model tag for report filenames')
    report_path = Path(__file__).resolve().parents[1] / 'docs' / f'gemma-check-{tag}.json'
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    passed = sum(r['passed'] for r in results)
    print(f'{passed}/{len(results)} live application cases passed')
    return 0 if passed == len(results) else 1

if __name__ == '__main__':
    raise SystemExit(main())
