"""Opt-in cold/warm checks; imports the unchanged seven cases and production adapter."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import statistics
import time
import httpx
from fastapi.testclient import TestClient
from .check_gemma import CASES
from .main import app

ROOT = Path(__file__).resolve().parents[1]

async def unload_all():
    base = os.getenv('OLLAMA_URL','http://127.0.0.1:11434').rstrip('/')
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(base+'/api/ps')
        response.raise_for_status()
        before=response.json()['models']
        for model in before:
            response=await client.post(base+'/api/generate',json={'model':model['name'],'stream':False,'keep_alive':0})
            response.raise_for_status()
        response=await client.get(base+'/api/ps')
        response.raise_for_status()
        after=response.json()['models']
        if after:
            raise RuntimeError('Models still loaded before cold test')
        return [m['name'] for m in before]


def evaluate(client, phase, name, text, current, expected, traces):
    before=len(traces)
    started=time.perf_counter()
    response=client.post('/api/preferences',json={'text':text,'current':current.model_dump()})
    latency=time.perf_counter()-started
    body=response.json()
    actual=body.get('preferences',{})
    wanted=expected.model_dump()
    correct=all(actual.get(k)==v for k,v in wanted.items() if k!='preferences')
    correct=correct and set(actual.get('preferences',[]))==set(wanted['preferences'])
    trace=traces[before:] or [{'error':'No Ollama request recorded'}]
    row={'name':name,'phase':phase,'request':text,'current':current.model_dump(),
         'expected':wanted,'actual':body,'http_status':response.status_code,
         'passed':response.status_code==200 and body.get('source')=='gemma' and correct,
         'latency_seconds':round(latency,3),'ollama':trace[-1]}
    print(json.dumps(row),flush=True)
    return row


def main():
    model=os.getenv('GEMMA_MODEL')
    if model!='gemma3:4b' or os.getenv('MODEL_PROVIDER')!='ollama':
        raise RuntimeError('Benchmark requires local gemma3:4b through Ollama')
    # No changes to prompt, model settings, request defaults or expected results.
    unloaded=asyncio.run(unload_all())
    traces=[]
    original=httpx.AsyncClient.post
    async def observed(self,url,*args,**kwargs):
        if not str(url).endswith('/api/chat'):
            return await original(self,url,*args,**kwargs)
        payload=kwargs['json']
        row={'model':payload['model'],'temperature':payload['options']['temperature'],
             'schema_required':payload['format']['required'],
             'schema_defaults':{k:v.get('default') for k,v in payload['format']['properties'].items()}}
        try:
            response=await original(self,url,*args,**kwargs)
            row['http_status']=response.status_code
            data=response.json()
            row['raw_content']=data.get('message',{}).get('content')
            for field in ('load_duration','total_duration','prompt_eval_duration','eval_duration','prompt_eval_count','eval_count'):
                if field in data: row[field]=data[field]
            return response
        except Exception as exc:
            row['error']=type(exc).__name__
            raise
        finally:
            traces.append(row)
    httpx.AsyncClient.post=observed
    try:
        with TestClient(app) as client:
            cold=evaluate(client,'cold',*CASES[0],traces)
            resident=httpx.get(os.getenv('OLLAMA_URL','http://127.0.0.1:11434').rstrip('/')+'/api/ps',timeout=10).json()['models']
            if not any(m['name']==model for m in resident):
                (ROOT/'docs'/'gemma-check-4b.json').write_text(json.dumps({'model':model,'cold_start':cold,'warm_status':'not run: model not resident after cold request'},indent=2)+'\n',encoding='utf-8')
                return 1
            # All seven cases now run against a resident model, including the
            # same first input, to separate cold load from warm response latency.
            warm=[evaluate(client,'warm',*case,traces) for case in CASES]
    finally:
        httpx.AsyncClient.post=original
    timings=[r['latency_seconds'] for r in warm]
    report={'model':model,'unloaded_before_test':unloaded,'cold_start_verified_empty':True,
            'adapter_sha256':hashlib.sha256((ROOT/'backend'/'preferences.py').read_bytes()).hexdigest(),
            'case_runner_sha256':hashlib.sha256((ROOT/'backend'/'check_gemma.py').read_bytes()).hexdigest(),
            'cold_start':cold,'cases':warm,'passed':sum(r['passed'] for r in warm),'total':len(warm),
            'accuracy':sum(r['passed'] for r in warm)/len(warm),
            'warm_mean_seconds':statistics.mean(timings),'warm_median_seconds':statistics.median(timings),
            'note':'End-to-end application latency. Ollama durations are nanoseconds. No prompt/schema/default repair changes.'}
    path=ROOT/'docs'/'gemma-check-4b.json'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'summary':{k:v for k,v in report.items() if k not in ('cases','cold_start')},'cold_latency_seconds':cold['latency_seconds']}),flush=True)
    return 0 if all(r['passed'] for r in warm) else 1

if __name__=='__main__': raise SystemExit(main())
