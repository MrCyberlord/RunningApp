"""Live, opt-in diagnosis against pedestrian providers; no model calls."""
import asyncio
import json
from pathlib import Path
import time
import httpx
from .main import app
from . import routing
from .models import RouteRequest, Point

async def main():
    events = []
    original_fetch = routing.fetch
    async def observed(method, url, **kwargs):
        event = {'method': method, 'provider': 'Overpass' if 'overpass' in url else 'FOSSGIS foot', 'params': kwargs.get('params')}
        started = time.monotonic()
        try:
            data = await original_fetch(method, url, **kwargs)
            event.update({'status': 200, 'code': data.get('code'), 'message': data.get('message'),
                          'remark': data.get('remark'), 'elements': len(data.get('elements', []))})
            if data.get('routes'):
                r = data['routes'][0]
                event.update({'distance_m': r['distance'], 'duration_seconds':r['duration'],
                              'geometry_points':len(r.get('geometry',{}).get('coordinates',[])),
                              'waypoints': data.get('waypoints')})
            return data
        except httpx.HTTPStatusError as exc:
            event.update({'status':exc.response.status_code, 'body':exc.response.text[:1500]})
            raise
        except Exception as exc:
            event.update({'exception':type(exc).__name__, 'message':str(exc)})
            raise
        finally:
            event['elapsed_seconds'] = round(time.monotonic()-started,3)
            events.append(event)
            print(json.dumps(event),flush=True)
    routing.fetch = observed
    result = None
    try:
        result = await routing.plan(RouteRequest(start=Point(lat=12.9765,lon=77.5929),minutes=30,preferences=['greenery']))
        print(json.dumps({'result':'success','provider':result['provider'],'distance_m':result['distance_m'],'moving_minutes':result['moving_minutes']}))
    except Exception as exc:
        print(json.dumps({'result':'failure','exception':type(exc).__name__,'detail':getattr(exc,'detail',str(exc))}))
    path = Path(__file__).resolve().parents[1]/'docs'/'routing-diagnosis.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({'events':events,'route':result},indent=2)+'\n',encoding='utf-8')

if __name__ == '__main__':
    asyncio.run(main())
