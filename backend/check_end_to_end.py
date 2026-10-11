"""Opt-in live Gemma + Overpass + pedestrian routing application verification."""
import json, time, os
from pathlib import Path
from fastapi.testclient import TestClient
from . import main, routing
from .models import Point, Preferences

original_plan, original_routed, original_fetch = main.plan, routing.routed, routing.fetch
trace = {}
async def traced_plan(req):
    trace['planner_received'] = req.model_dump()
    return await original_plan(req)
async def traced_routed(points):
    attempt = {'requested_waypoints':[p.model_dump() for p in points]}
    trace.setdefault('routing_attempts', []).append(attempt)
    try:
        result = await original_routed(points)
        attempt.update(provider=result[3], distance_m=result[1], provider_waypoints=result[4])
        return result
    except Exception as exc:
        attempt['error'] = routing.failure_reason(exc)
        raise
async def traced_fetch(method, url, **kwargs):
    entry = {'method':method, 'url':url.split('?')[0]}
    trace.setdefault('upstream', []).append(entry)
    started=time.perf_counter()
    try:
        data=await original_fetch(method,url,**kwargs)
        entry.update(status=200, code=data.get('code'), elements=len(data.get('elements',[])))
        return data
    except Exception as exc:
        entry['error']=routing.failure_reason(exc)
        raise
    finally: entry['latency_seconds']=round(time.perf_counter()-started,3)
main.plan, routing.routed, routing.fetch = traced_plan, traced_routed, traced_fetch
report={'model':os.getenv('GEMMA_MODEL'),'start':{'lat':12.9765,'lon':77.5929},'cases':[]}
with TestClient(main.app) as client:
    for mode, word in [('jogging','jog'),('walking','walk')]:
        trace={}
        text=f'A 30-minute {word} with greenery and a 5-minute stop.'
        started=time.perf_counter()
        parsed=client.post('/api/preferences',json={'text':text,'current':Preferences().model_dump()}).json()
        row={'request':text,'interpretation':parsed}
        expected=Preferences(mode=mode,minutes=30,preferences=['greenery'],stop_minutes=5).model_dump()
        row['interpretation_correct']=parsed.get('source')=='gemma' and parsed.get('preferences')==expected
        payload={**parsed['preferences'],'start':report['start']}
        response=client.post('/api/route',json=payload)
        row.update(route_status=response.status_code,route=response.json(),trace=trace,latency_seconds=round(time.perf_counter()-started,3))
        row['planner_received_interpreted_values']=trace.get('planner_received')==payload
        if response.status_code==200:
            route=response.json(); coords=route['geometry']['coordinates']
            first=Point(lon=coords[0][0],lat=coords[0][1]); last=Point(lon=coords[-1][0],lat=coords[-1][1])
            row['evidence']={'geometry_points':len(coords),'closure_m':routing.distance(first,last),'start_offset_m':routing.distance(first,Point(**report['start'])),'time_sum_correct':abs(route['total_minutes']-route['moving_minutes']-route['stop_minutes'])<1e-9,'requested_stop_preserved':route['stop_minutes']==5,'selected_places':[{'id':p['id'],'name':p['name'],'kind':p['kind'],'nearest_geometry_vertex_m':min(routing.distance(Point(lat=p['lat'],lon=p['lon']),Point(lon=c[0],lat=c[1])) for c in coords)} for p in route['stops']]}
        report['cases'].append(row)
        Path('docs/end-to-end-4b.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print(json.dumps({k:v for k,v in row.items() if k not in ('route','trace')}),flush=True)
        if response.status_code==200: print(json.dumps({k:v for k,v in response.json().items() if k not in ('geometry','places')}),flush=True)
