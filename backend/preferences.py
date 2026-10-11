import json
import os
import httpx
from .models import Preferences


def validate_model_output(raw: str) -> Preferences:
    # Accept one JSON object only: no markdown, commentary or extra fields.
    data = json.loads(raw)
    if not isinstance(data, dict) or set(data) != set(Preferences.model_fields):
        raise ValueError('Expected every preference field and no extra fields')
    return Preferences.model_validate(data)


def fallback(text: str, current: Preferences) -> Preferences:
    # Deliberately does not guess nuanced intent (including negation).
    # Existing form choices remain authoritative when Gemma is unavailable.
    return current.model_copy(deep=True)


async def parse_preferences(text: str, current: Preferences):
    provider = os.getenv('MODEL_PROVIDER', 'none')
    unavailable = {'preferences': fallback(text, current).model_dump(), 'source': 'form_fallback',
                   'message': 'AI was not used. Your form settings were kept; adjust them below.'}
    if provider == 'none':
        return unavailable
    model = os.getenv('GEMMA_MODEL', 'gemma3:4b')
    if 'gemma' not in model.lower():
        return unavailable
    schema = Preferences.model_json_schema()
    # Defaults in the form schema made every property optional. Require every
    # output field without weakening the independent Pydantic validation.
    schema['required'] = list(Preferences.model_fields)
    for name, value in current.model_dump().items():
        schema['properties'][name]['default'] = value
    prompt = (
        'Convert the request to JSON. Keep current values for unspecified fields. '
        'walk=walking; jog/run=jogging; parks/gardens=greenery; views=scenic. '
        'Add requested preferences; remove negated preferences. '
        'minutes=total time; stop_minutes=pause time. No stops means 0. '
        'No fruit stop removes fruit but preserves other stop time.\n'
        'Example current: {"mode":"walking","minutes":25,"preferences":[],"stop_minutes":0}\n'
        'Request: Run for 50 minutes, see a garden, rest for 3 minutes.\n'
        'JSON: {"mode":"jogging","minutes":50,"preferences":["greenery"],"stop_minutes":3}\n'
        'Example current: {"mode":"jogging","minutes":35,"preferences":["fruit","water"],"stop_minutes":4}\n'
        'Request: No fruit stop.\n'
        'JSON: {"mode":"jogging","minutes":35,"preferences":["water"],"stop_minutes":4}\n'
        'Current: ' + current.model_dump_json() + '\nRequest: ' + json.dumps(text) + '\nJSON:'
    )
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            if provider == 'ollama':
                r = await client.post(os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/') + '/api/chat',
                    json={'model': model, 'stream': False, 'format': schema,
                          'messages': [{'role': 'user', 'content': prompt}], 'options': {'temperature': 0}})
                r.raise_for_status()
                raw = r.json()['message']['content']
            elif provider == 'openai_compatible' and os.getenv('HOSTED_GEMMA_FREE_CONFIRMED') == 'true':
                base = os.environ['GEMMA_BASE_URL'].rstrip('/')
                if not base.startswith('https://'):
                    return unavailable
                r = await client.post(base + '/chat/completions',
                    headers={'Authorization': 'Bearer ' + os.environ['GEMMA_API_KEY']},
                    json={'model': model, 'messages': [{'role': 'user', 'content': prompt}],
                          'temperature': 0, 'max_tokens': 300})
                r.raise_for_status()
                raw = r.json()['choices'][0]['message']['content']
            else:
                return unavailable
        result = validate_model_output(raw)
        return {'preferences': result.model_dump(), 'source': 'gemma',
                'message': 'Gemma interpreted your request. Review the settings before planning.'}
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return unavailable
