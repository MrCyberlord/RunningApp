import asyncio
import json
import math
import pytest
import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from .models import Point, Preferences, RouteRequest
from .preferences import validate_model_output, parse_preferences
from .routing import moving_minutes, kind
from . import routing
from .main import app

@pytest.mark.parametrize('meters,mode,expected', [(4800,'walking',60),(8000,'jogging',60),(2400,'walking',30),(0,'jogging',0)])
def test_time(meters,mode,expected):
    assert moving_minutes(meters,mode) == pytest.approx(expected)

@pytest.mark.parametrize('meters,mode', [(-1,'walking'),(math.inf,'walking'),(math.nan,'walking'),(10,'driving')])
def test_invalid_time(meters,mode):
    with pytest.raises(ValueError): moving_minutes(meters,mode)

def test_valid_model():
    p = validate_model_output(json.dumps({'mode':'jogging','minutes':45,'stop_minutes':5,'preferences':['fruit','water']}))
    assert p.mode == 'jogging' and p.stop_minutes == 5

@pytest.mark.parametrize('value', [
    {'mode':'flying'}, {'minutes':500}, {'minutes':'30'}, {'preferences':['imaginary']},
    {'stop_minutes':30}, {'geometry':[]}, {'minutes':True}, {'preferences':['fruit']*5}
])
def test_invalid_model(value):
    data = Preferences().model_dump() | value
    with pytest.raises(ValueError): validate_model_output(json.dumps(data))

@pytest.mark.parametrize('raw', ['{}','[]','not json'])
def test_invalid_envelopes(raw):
    with pytest.raises(ValueError): validate_model_output(raw)

def test_fallback_is_honest(monkeypatch):
    monkeypatch.setenv('MODEL_PROVIDER','none')
    result = asyncio.run(parse_preferences('100 minutes',Preferences(minutes=40)))
    assert result['source'] == 'form_fallback'
    assert result['preferences']['minutes'] == 40

def test_model_failure(monkeypatch):
    monkeypatch.setenv('MODEL_PROVIDER','ollama')
    async def bad(*args,**kwargs): raise httpx.ConnectError('offline')
    monkeypatch.setattr(httpx.AsyncClient,'post',bad)
    result = asyncio.run(parse_preferences('jog',Preferences()))
    assert result['source'] == 'form_fallback'

def test_model_success(monkeypatch):
    monkeypatch.setenv('MODEL_PROVIDER','ollama')
    monkeypatch.setenv('GEMMA_MODEL','gemma3:4b')
    async def good(*args,**kwargs):
        return httpx.Response(200,request=httpx.Request('POST','http://localhost'),json={'message':{'content':Preferences(mode='jogging').model_dump_json()}})
    monkeypatch.setattr(httpx.AsyncClient,'post',good)
    result = asyncio.run(parse_preferences('jog',Preferences()))
    assert result['source'] == 'gemma' and result['preferences']['mode'] == 'jogging'

def test_place_classification():
    assert kind({'shop':'supermarket'}) is None
    assert kind({'shop':'greengrocer'}) == 'fruit'
    assert kind({'amenity':'drinking_water','drinking_water':'no'}) is None
    assert kind({'leisure':'garden'}) == 'greenery'

def mock_route(meters):
    async def routed(points):
        s = points[0]
        return {'type':'LineString','coordinates':[[s.lon,s.lat],[s.lon+.001,s.lat],[s.lon,s.lat]]},meters,800,'mock pedestrian',[]
    return routed

async def no_places(*args): return []

def test_route_returns_and_uses_distance(monkeypatch):
    monkeypatch.setattr(routing,'places',no_places)
    monkeypatch.setattr(routing,'routed',mock_route(1600))
    result = asyncio.run(routing.plan(RouteRequest(start=Point(lat=12,lon=77),minutes=30)))
    assert result['moving_minutes'] == 20
    assert result['stop_minutes'] == 0
    assert result['geometry']['coordinates'][0] == result['geometry']['coordinates'][-1]
    assert result['total_minutes'] <= 30

def test_budget_excludes_overlong_route(monkeypatch):
    monkeypatch.setattr(routing,'places',no_places)
    monkeypatch.setattr(routing,'routed',mock_route(10000))
    with pytest.raises(HTTPException):
        asyncio.run(routing.plan(RouteRequest(start=Point(lat=12,lon=77),minutes=10)))

def test_no_fake_route_on_outage(monkeypatch):
    async def down(*args): raise httpx.ConnectError('offline')
    monkeypatch.setattr(routing,'places',down)
    monkeypatch.setattr(routing,'routed',down)
    with pytest.raises(HTTPException):
        asyncio.run(routing.plan(RouteRequest(start=Point(lat=12,lon=77))))

def test_api_input_bounds():
    client = TestClient(app)
    assert client.get('/api/health').status_code == 200
    assert client.post('/api/route',json={'start':{'lat':100,'lon':77}}).status_code == 422
    assert client.post('/api/preferences',json={'text':'jog','current':{'minutes':10,'stop_minutes':10}}).status_code == 422


def test_place_decoding_and_private_filter(monkeypatch):
    async def fake_fetch(*args,**kwargs):
        return {'elements': [
            {'type':'node','id':1,'lat':12,'lon':77,'tags':{'shop':'greengrocer','name':'Mapped shop'}},
            {'type':'way','id':2,'center':{'lat':12.001,'lon':77},'tags':{'leisure':'garden'}},
            {'type':'node','id':3,'lat':12,'lon':77,'tags':{'leisure':'park','access':'private'}},
            {'type':'node','id':4,'lat':12,'lon':77,'tags':{'shop':'supermarket'}}]}
    monkeypatch.setattr(routing,'fetch',fake_fetch)
    monkeypatch.setattr(routing,'_cache',{})
    places = asyncio.run(routing.places(Point(lat=12,lon=77),500))
    assert len(places) == 2
    assert places[0]['osm_url'] == 'https://www.openstreetmap.org/node/1'
    assert places[1]['name'] == 'Unnamed mapped garden'

def test_stop_time_is_added_only_for_included_place(monkeypatch):
    async def fruit(*args):
        return [{'id':'node/1','lat':12.002,'lon':77,'distance_m':222,'kind':'fruit','name':'Mapped fruit shop','osm_url':'https://www.openstreetmap.org/node/1'}]
    async def routed(points):
        return {'type':'LineString','coordinates':[[p.lon,p.lat] for p in points]},1600,1000,'mock',[]
    monkeypatch.setattr(routing,'places',fruit)
    monkeypatch.setattr(routing,'routed',routed)
    result = asyncio.run(routing.plan(RouteRequest(start=Point(lat=12,lon=77),minutes=30,stop_minutes=5,preferences=['fruit'])))
    assert result['moving_minutes'] == 20
    assert result['stop_minutes'] == 5
    assert result['total_minutes'] == 25
    assert result['stops'][0]['id'] == 'node/1'


def test_ollama_schema_requires_fields_and_current_defaults(monkeypatch):
    monkeypatch.setenv('MODEL_PROVIDER', 'ollama')
    monkeypatch.setenv('GEMMA_MODEL', 'gemma3:270m')
    current = Preferences(mode='jogging', minutes=55, preferences=['water'], stop_minutes=6)
    async def good(*args, **kwargs):
        payload = kwargs['json']
        assert payload['model'] == 'gemma3:270m'
        assert payload['options']['temperature'] == 0
        assert payload['stream'] is False
        schema = payload['format']
        assert schema['additionalProperties'] is False
        assert set(schema['required']) == set(Preferences.model_fields)
        for key, value in current.model_dump().items():
            assert schema['properties'][key]['default'] == value
        assert schema['properties']['minutes']['minimum'] == 10
        assert schema['properties']['stop_minutes']['maximum'] == 30
        assert schema['properties']['preferences']['items']['enum'] == ['greenery','scenic','fruit','water']
        prompt = payload['messages'][0]['content']
        assert 'remove negated preferences' in prompt
        assert current.model_dump_json() in prompt
        return httpx.Response(200, request=httpx.Request('POST','http://localhost'),
                              json={'message':{'content': current.model_dump_json()}})
    monkeypatch.setattr(httpx.AsyncClient, 'post', good)
    result = asyncio.run(parse_preferences('Keep my settings.', current))
    assert result['source'] == 'gemma'
    assert result['preferences'] == current.model_dump()

@pytest.mark.parametrize('bad', [
    {'mode':'walking','minutes':30,'preferences':[]},
    {'mode':'walking','minutes':30,'preferences':['fruit'],'stop_minutes':30},
    {'mode':'jogging','minutes':'45','preferences':[],'stop_minutes':5},
    {'mode':'walking','minutes':30,'preferences':[],'stop_minutes':0,'coordinates':[]},
])
def test_invalid_ollama_output_keeps_form_and_fallback_label(monkeypatch, bad):
    monkeypatch.setenv('MODEL_PROVIDER', 'ollama')
    monkeypatch.setenv('GEMMA_MODEL', 'gemma3:270m')
    current = Preferences(minutes=50, stop_minutes=4, preferences=['water'])
    async def invalid(*args, **kwargs):
        return httpx.Response(200, request=httpx.Request('POST','http://localhost'),
                              json={'message':{'content':json.dumps(bad)}})
    monkeypatch.setattr(httpx.AsyncClient, 'post', invalid)
    result = asyncio.run(parse_preferences('No fruit stop.', current))
    assert result['source'] == 'form_fallback'
    assert result['preferences'] == current.model_dump()
    assert 'form settings were kept' in result['message']


@pytest.mark.parametrize('status,code', [(400,'NoSegment'),(400,'NoRoute'),(429,None)])
def test_provider_error_reason_is_actionable_and_sanitized(status,code):
    response = httpx.Response(status, request=httpx.Request('GET','https://example.test/?key=SECRET'),
                              json={'code':code,'message':'SECRET'})
    exc = httpx.HTTPStatusError('SECRET', request=response.request, response=response)
    reason = routing.failure_reason(exc)
    assert f'HTTP {status}' in reason
    if code: assert code in reason
    assert 'SECRET' not in reason


def test_rate_limit_does_not_repeat_routing_requests(monkeypatch):
    attempts = []
    async def limited(points):
        attempts.append(points)
        response = httpx.Response(429, request=httpx.Request('GET','https://example.test'))
        raise httpx.HTTPStatusError('rate limited',request=response.request,response=response)
    monkeypatch.setattr(routing,'places',no_places)
    monkeypatch.setattr(routing,'routed',limited)
    with pytest.raises(HTTPException) as error:
        asyncio.run(routing.plan(RouteRequest(start=Point(lat=12,lon=77))))
    assert len(attempts) == 1
    assert 'HTTP 429' in error.value.detail


def test_timeout_identified_in_route_error(monkeypatch):
    async def timeout(points): raise httpx.ReadTimeout('private details')
    monkeypatch.setattr(routing,'places',no_places)
    monkeypatch.setattr(routing,'routed',timeout)
    with pytest.raises(HTTPException) as error:
        asyncio.run(routing.plan(RouteRequest(start=Point(lat=12,lon=77))))
    assert 'ReadTimeout' in error.value.detail
    assert 'private details' not in error.value.detail


def test_over_budget_route_is_adjusted_before_success(monkeypatch):
    attempts = []
    async def adjust(points):
        attempts.append(points)
        return await mock_route(3200 if len(attempts)==1 else 2300)(points)
    monkeypatch.setattr(routing,'places',no_places)
    monkeypatch.setattr(routing,'routed',adjust)
    result = asyncio.run(routing.plan(RouteRequest(start=Point(lat=12,lon=77),minutes=30)))
    assert len(attempts)==2
    assert result['moving_minutes'] == pytest.approx(28.75)
    assert routing.distance(attempts[1][0],attempts[1][1]) < routing.distance(attempts[0][0],attempts[0][1])


def test_default_router_is_pedestrian_not_driving(monkeypatch):
    monkeypatch.delenv('ORS_API_KEY',raising=False)
    async def fetched(method,url,**kwargs):
        assert method == 'GET'
        assert '/routed-foot/route/v1/foot/' in url
        assert 'driving' not in url and 'routed-car' not in url
        return {'code':'Ok','routes':[{'geometry':{'type':'LineString','coordinates':[[77,12],[77,12]]},'distance':200,'duration':150}]}
    monkeypatch.setattr(routing,'fetch',fetched)
    result = asyncio.run(routing.routed([Point(lat=12,lon=77),Point(lat=12,lon=77)]))
    assert result[3] == 'FOSSGIS OSRM foot'


@pytest.mark.parametrize('unavailable', [False, True])
def test_pause_survives_missing_places_and_budget_is_respected(monkeypatch, unavailable):
    async def missing(*args):
        if unavailable: raise routing.PlaceLookupError('HTTP 504')
        return []
    monkeypatch.setattr(routing,'places',missing)
    monkeypatch.setattr(routing,'routed',mock_route(1600))
    result=asyncio.run(routing.plan(RouteRequest(start=Point(lat=12,lon=77),minutes=30,stop_minutes=5,preferences=['greenery'])))
    assert result['total_minutes']==25
    assert result['stop_minutes']==5
    assert result['stops']==[]
    assert result['place_lookup']['status']==('unavailable' if unavailable else 'empty')
    assert any('no mapped place is assigned' in w for w in result['warnings'])
    assert any('not included in the route: greenery' in w for w in result['warnings'])


def test_partial_preference_match_warns_for_unmet_kind(monkeypatch):
    async def fruit(*args):
        return [{'id':'node/1','lat':12.002,'lon':77,'distance_m':222,'kind':'fruit','name':'Test fixture','osm_url':'https://www.openstreetmap.org/node/1'}]
    async def routed(points):
        return {'type':'LineString','coordinates':[[p.lon,p.lat] for p in points]},1600,1000,'mock',[]
    monkeypatch.setattr(routing,'places',fruit)
    monkeypatch.setattr(routing,'routed',routed)
    result=asyncio.run(routing.plan(RouteRequest(start=Point(lat=12,lon=77),preferences=['fruit','greenery'])))
    assert result['stops'][0]['kind']=='fruit'
    assert any('not included in the route: greenery.' in w for w in result['warnings'])
