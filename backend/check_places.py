"""Opt-in real Overpass lookup plus cache verification. No synthetic places."""
import asyncio
import json
import time
from pathlib import Path
from urllib.parse import urlparse
import httpx
from .main import app
from . import routing
from .models import Point

async def main():
    events=[]
    original=routing.fetch
    async def observe(method,url,**kwargs):
        event={'provider':urlparse(url).hostname}
        started=time.perf_counter()
        try:
            result=await original(method,url,**kwargs)
            event.update({'http_status':200,'element_count':len(result.get('elements',[])),'remark':result.get('remark')})
            return result
        except httpx.HTTPStatusError as exc:
            event.update({'http_status':exc.response.status_code,'reason':routing.failure_reason(exc)})
            raise
        except BaseException as exc:
            event['exception']=type(exc).__name__
            raise
        finally:
            event['latency_seconds']=round(time.perf_counter()-started,3)
            events.append(event)
    routing.fetch=observe
    report={'start':{'lat':12.9765,'lon':77.5929},'radius_m':1200}
    started=time.perf_counter()
    try:
        first=await routing.places(Point(**report['start']),report['radius_m'])
        report.update({'metadata':first.metadata,'places':list(first),'status':first.metadata['status'],
                       'latency_seconds':round(time.perf_counter()-started,3)})
        cached=await routing.places(Point(**report['start']),report['radius_m'])
        report['second_lookup']=cached.metadata
    except routing.PlaceLookupError as exc:
        report.update({'status':'unavailable','reason':str(exc),'latency_seconds':round(time.perf_counter()-started,3)})
    report['events']=events
    path=Path(__file__).resolve().parents[1]/'docs'/'place-check.json'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 1 if report['status']=='unavailable' else 0

if __name__=='__main__': raise SystemExit(asyncio.run(main()))
