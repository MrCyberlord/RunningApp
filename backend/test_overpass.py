import asyncio
import httpx
import pytest
from . import routing
from .models import Point

START = Point(lat=12.9765, lon=77.5929)

@pytest.fixture(autouse=True)
def clean_lookup(monkeypatch):
    monkeypatch.setenv('OVERPASS_URL','https://primary.example/api/interpreter')
    monkeypatch.setenv('OVERPASS_FALLBACK_URL','https://alternative.example/api/interpreter')
    monkeypatch.setenv('OVERPASS_TIMEOUT_SECONDS','15')
    monkeypatch.setattr(routing,'_cache',{})
    monkeypatch.setattr(routing,'_overpass_cooldowns',{})
    monkeypatch.setattr(routing,'_place_gate',asyncio.Lock())


def status_error(status,headers=None):
    response = httpx.Response(status,request=httpx.Request('POST','https://primary.example'),headers=headers)
    return httpx.HTTPStatusError('upstream',request=response.request,response=response)


def test_one_alternative_attempt_and_success_cache(monkeypatch):
    calls = []
    async def fetch(method,url,**kwargs):
        calls.append(url)
        assert kwargs['timeout'] == 15
        assert '[timeout:13]' in kwargs['data']['data']
        if len(calls)==1: raise status_error(504)
        return {'elements':[{'type':'node','id':9,'lat':12.9765,'lon':77.5929,'tags':{'amenity':'drinking_water'}}]}
    monkeypatch.setattr(routing,'fetch',fetch)
    async def check():
        first = await routing.places(START,1200)
        second = await routing.places(START,1200)
        assert first.metadata['status']=='ok'
        assert first.metadata['attempts']==2
        assert first.metadata['provider']=='alternative.example'
        assert second.metadata['cache_hit'] is True
        assert second.metadata['attempts']==0
        assert first[0]['osm_url']=='https://www.openstreetmap.org/node/9'
    asyncio.run(check())
    assert len(calls)==2


def test_successful_empty_result_is_cached_not_unavailable(monkeypatch):
    calls = []
    async def fetch(*args,**kwargs):
        calls.append(1)
        return {'elements':[]}
    monkeypatch.setattr(routing,'fetch',fetch)
    async def check():
        first=await routing.places(START,1200)
        second=await routing.places(START,1200)
        assert first==[] and first.metadata['status']=='empty'
        assert second.metadata['status']=='empty' and second.metadata['cache_hit']
    asyncio.run(check())
    assert len(calls)==1


def test_unavailable_is_not_cached_and_at_most_one_retry(monkeypatch):
    calls = []
    async def fetch(*args,**kwargs):
        calls.append(1)
        raise status_error(503)
    monkeypatch.setattr(routing,'fetch',fetch)
    with pytest.raises(routing.PlaceLookupError): asyncio.run(routing.places(START,1200))
    assert len(calls)==2 and not routing._cache


def test_rate_limit_stops_failover_and_respects_retry_after(monkeypatch):
    calls=[]
    async def fetch(*args,**kwargs):
        calls.append(1)
        raise status_error(429,{'Retry-After':'120'})
    monkeypatch.setattr(routing,'fetch',fetch)
    async def check():
        before=routing.time.monotonic()
        for _ in range(2):
            with pytest.raises(routing.PlaceLookupError): await routing.places(START,1200)
        assert routing._overpass_cooldowns['https://primary.example/api/interpreter']>=before+120
    asyncio.run(check())
    assert len(calls)==1


def test_disabled_or_duplicate_alternative_never_repeats(monkeypatch):
    monkeypatch.setenv('OVERPASS_FALLBACK_URL','https://primary.example/api/interpreter')
    calls=[]
    async def fetch(*args,**kwargs):
        calls.append(1)
        raise httpx.ReadTimeout('timeout')
    monkeypatch.setattr(routing,'fetch',fetch)
    with pytest.raises(routing.PlaceLookupError): asyncio.run(routing.places(START,1200))
    assert len(calls)==1
    monkeypatch.setenv('OVERPASS_FALLBACK_URL','')
    assert len(routing.overpass_endpoints())==1


def test_incomplete_success_is_not_mislabeled_empty(monkeypatch):
    async def fetch(*args,**kwargs): return {'elements':[], 'remark':'runtime timeout'}
    monkeypatch.setattr(routing,'fetch',fetch)
    with pytest.raises(routing.PlaceLookupError): asyncio.run(routing.places(START,1200))
    assert not routing._cache


def test_wall_clock_deadline_bounds_hanging_attempts(monkeypatch):
    calls=[]
    monkeypatch.setattr(routing,'overpass_timeout',lambda:0.02)
    async def fetch(*args,**kwargs):
        calls.append(1)
        await asyncio.sleep(10)
    monkeypatch.setattr(routing,'fetch',fetch)
    async def check():
        async with asyncio.timeout(0.5):
            with pytest.raises(routing.PlaceLookupError,match='DeadlineExceeded'):
                await routing.places(START,1200)
    asyncio.run(check())
    assert len(calls)==2


def test_concurrent_identical_requests_share_successful_cache(monkeypatch):
    calls=[]
    async def fetch(*args,**kwargs):
        calls.append(1)
        await asyncio.sleep(0.01)
        return {'elements':[]}
    monkeypatch.setattr(routing,'fetch',fetch)
    async def check():
        results=await asyncio.gather(routing.places(START,1200),routing.places(START,1200))
        assert results[0].metadata['cache_hit'] is False
        assert results[1].metadata['cache_hit'] is True
    asyncio.run(check())
    assert len(calls)==1


@pytest.mark.parametrize('value,expected',[('nan',15),('invalid',15),('999',30),('-2',2)])
def test_timeout_configuration_is_bounded(monkeypatch,value,expected):
    monkeypatch.setenv('OVERPASS_TIMEOUT_SECONDS',value)
    assert routing.overpass_timeout()==expected
