import asyncio
import math
import logging
import os
import time
from urllib.parse import urlparse
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import httpx
from fastapi import HTTPException
from .models import Point, RouteRequest

# Shared within the single-worker MVP. Never exceed one upstream start/second.
_gate = asyncio.Lock()
_last_request = 0.0
_cache = {}
logger = logging.getLogger(__name__)
_place_gate = asyncio.Lock()
_overpass_cooldowns = {}

class PlaceResults(list):
    def __init__(self, values, metadata):
        super().__init__(values)
        self.metadata = metadata

class PlaceLookupError(ValueError):
    pass


def overpass_timeout():
    try:
        value = float(os.getenv('OVERPASS_TIMEOUT_SECONDS', '15'))
        return min(30, max(2, value)) if math.isfinite(value) else 15
    except ValueError:
        return 15


def overpass_endpoints():
    primary = os.getenv('OVERPASS_URL', 'https://overpass-api.de/api/interpreter').strip()
    alternative = os.getenv('OVERPASS_FALLBACK_URL', 'https://overpass.private.coffee/api/interpreter').strip()
    endpoints = list(dict.fromkeys(e for e in (primary, alternative) if e))
    for endpoint in endpoints:
        url = urlparse(endpoint)
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise PlaceLookupError('Overpass endpoints must be HTTPS URLs without credentials')
    if not endpoints:
        raise PlaceLookupError('No Overpass endpoint configured')
    return endpoints


def retry_after_seconds(value):
    try:
        delay = float(value)
        return max(60, delay) if math.isfinite(delay) else 60
    except (TypeError, ValueError):
        try:
            return max(60, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return 60


async def overpass_data(query, endpoints):
    failures = []
    for index, endpoint in enumerate(endpoints):
        if time.monotonic() < _overpass_cooldowns.get(endpoint, 0):
            raise PlaceLookupError('Overpass rate-limit cooldown active')
        try:
            # Includes the shared limiter/queue wait, unlike a read timeout alone.
            async with asyncio.timeout(overpass_timeout()):
                data = await fetch('POST', endpoint, data={'data': query}, timeout=overpass_timeout())
            if not isinstance(data, dict) or not isinstance(data.get('elements'), list) or data.get('remark'):
                raise ValueError('Incomplete or invalid Overpass response')
            return data, {'provider': urlparse(endpoint).hostname, 'attempts': index + 1,
                          'cache_hit': False, 'failures': failures}
        except (httpx.HTTPError, ValueError, TimeoutError) as exc:
            reason = 'DeadlineExceeded' if isinstance(exc, TimeoutError) else failure_reason(exc)
            failures.append(reason)
            logger.warning('Overpass attempt %s (%s) failed: %s', index+1, urlparse(endpoint).hostname, reason)
            if isinstance(exc, httpx.HTTPStatusError):
                status = exc.response.status_code
                if status == 429:
                    _overpass_cooldowns[endpoint] = time.monotonic() + retry_after_seconds(exc.response.headers.get('Retry-After'))
                if status not in (408, 500, 502, 503, 504):
                    break
    raise PlaceLookupError(' / '.join(failures))


def failure_reason(exc):
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        try:
            provider_code = exc.response.json().get("code")
        except (ValueError, AttributeError):
            provider_code = None
        code = provider_code if provider_code in ("NoSegment", "NoRoute", "InvalidQuery", "TooBig") else None
        return f"HTTP {status}" + (f" ({code})" if code else "")
    if isinstance(exc, httpx.TimeoutException):
        return type(exc).__name__
    if isinstance(exc, httpx.RequestError):
        return type(exc).__name__
    if isinstance(exc, PlaceLookupError):
        return str(exc)
    return "Invalid or unusable provider response"


async def fetch(method, url, **kwargs):
    global _last_request
    async with _gate:
        await asyncio.sleep(max(0, 1.05 - (time.monotonic() - _last_request)))
        _last_request = time.monotonic()
        async with httpx.AsyncClient(timeout=30, headers={'User-Agent': os.getenv('USER_AGENT', 'Runningo/0.1')}) as client:
            r = await client.request(method, url, **kwargs)
            r.raise_for_status()
            return r.json()


def distance(a, b):
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dlat, dlon = p2-p1, math.radians(b.lon-a.lon)
    h = math.sin(dlat/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlon/2)**2
    return 6371000 * 2 * math.asin(min(1, math.sqrt(h)))


def moving_minutes(meters, mode):
    if not math.isfinite(meters) or meters < 0 or mode not in ('walking', 'jogging'):
        raise ValueError('Invalid route distance or mode')
    # User pace estimate, explicitly independent of provider's default pace.
    return meters / (4800 if mode == 'walking' else 8000) * 60


def destination(start, meters, bearing):
    angle, d = math.radians(bearing), meters / 6371000
    lat, lon = math.radians(start.lat), math.radians(start.lon)
    lat2 = math.asin(math.sin(lat)*math.cos(d)+math.cos(lat)*math.sin(d)*math.cos(angle))
    lon2 = lon + math.atan2(math.sin(angle)*math.sin(d)*math.cos(lat), math.cos(d)-math.sin(lat)*math.sin(lat2))
    return Point(lat=math.degrees(lat2), lon=(math.degrees(lon2)+180)%360-180)


def kind(tags):
    if tags.get('leisure') in ('park', 'garden'): return 'greenery'
    if tags.get('tourism') == 'viewpoint': return 'scenic'
    if tags.get('shop') == 'greengrocer': return 'fruit'
    if tags.get('amenity') == 'drinking_water' and tags.get('drinking_water') != 'no': return 'water'
    return None

async def places(start, radius):
    try:
        # One bounded lookup with at most two upstream calls, including queue wait.
        async with asyncio.timeout(overpass_timeout()*2 + 2):
            async with _place_gate:
                return await cached_places(start, radius)
    except TimeoutError as exc:
        raise PlaceLookupError('LookupDeadlineExceeded') from exc


async def cached_places(start, radius):
    endpoints = overpass_endpoints()
    radius = min(5000, max(50, int(radius)))
    key = (tuple(endpoints), round(start.lat, 4), round(start.lon, 4), radius)
    if key in _cache and time.monotonic() - _cache[key][0] < 600:
        previous = _cache[key][1]
        return PlaceResults(previous, {**previous.metadata, 'cache_hit': True, 'attempts': 0})
    area = f'(around:{radius},{start.lat},{start.lon})'
    query = f'[out:json][timeout:{max(1,int(overpass_timeout()-2))}];(' + ''.join('nwr' + tag + area + ';' for tag in
        ('[leisure~"^(park|garden)$"]', '[tourism=viewpoint]', '[shop=greengrocer]', '[amenity=drinking_water]')) + ');out center tags;'
    data, metadata = await overpass_data(query, endpoints)
    result = []
    for e in data.get('elements', []):
        tags = e.get('tags', {})
        k = kind(tags)
        center = e if 'lat' in e else e.get('center', {})
        if not k or 'lat' not in center or tags.get('access') in ('private', 'no'):
            continue
        p = Point(lat=center['lat'], lon=center['lon'])
        result.append({'id': str(e['type']) + '/' + str(e['id']), 'name': tags.get('name') or 'Unnamed mapped ' +
            {'greenery': tags.get('leisure', 'park'), 'scenic': 'viewpoint', 'fruit': 'greengrocer', 'water': 'drinking-water point'}[k],
            'kind': k, 'lat': p.lat, 'lon': p.lon, 'distance_m': round(distance(start,p)),
            'osm_url': f"https://www.openstreetmap.org/{e['type']}/{e['id']}"})
    result.sort(key=lambda p: p['distance_m'])
    if len(_cache) >= 128: _cache.pop(next(iter(_cache)))
    lookup = PlaceResults(result[:100], {**metadata, 'status': 'ok' if result else 'empty'})
    _cache[key] = (time.monotonic(), lookup)
    return lookup

async def routed(points):
    coords = [[p.lon, p.lat] for p in points]
    key = os.getenv('ORS_API_KEY')
    if key:
        data = await fetch('POST', 'https://api.openrouteservice.org/v2/directions/foot-walking/geojson',
            headers={'Authorization': key}, json={'coordinates': coords, 'radiuses': [100]*len(points)})
        f = data['features'][0]
        return f['geometry'], f['properties']['summary']['distance'], f['properties']['summary']['duration'], 'openrouteservice', []
    url = 'https://routing.openstreetmap.de/routed-foot/route/v1/foot/' + ';'.join(f'{x},{y}' for x,y in coords)
    data = await fetch('GET', url, params={'overview': 'full', 'geometries': 'geojson', 'steps': 'false', 'radiuses': ';'.join(['100']*len(points))})
    if data.get('code') != 'Ok': raise ValueError('No pedestrian route')
    r = data['routes'][0]
    return r['geometry'], r['distance'], r['duration'], 'FOSSGIS OSRM foot', data.get('waypoints', [])

async def plan(req: RouteRequest):
    warnings = []
    budget = req.minutes - req.stop_minutes
    target = budget * (80 if req.mode == 'walking' else 8000/60)
    try:
        nearby = await places(req.start, min(5000, max(500, round(target/2))))
        place_lookup = getattr(nearby, 'metadata', {'status': 'ok' if nearby else 'empty'})
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        nearby = []
        reason = failure_reason(exc)
        place_lookup = {'status': 'unavailable', 'reason': reason, 'cache_hit': False}
        logger.warning('Place lookup failed: %s', reason)
        warnings.append(f'Place service unavailable ({reason}). No places or stops have been invented; routing continues without them.')
    candidates = [p for p in nearby if p['kind'] in req.preferences and 150 < p['distance_m'] < target/2]
    candidates.sort(key=lambda p: abs(p['distance_m']-target/3))
    best = None
    failures = []
    radius = target / 4.8
    for attempt in range(3):
        selected = candidates[attempt:attempt+1] if attempt < len(candidates) else []
        if selected:
            points = [req.start, Point(lat=selected[0]['lat'], lon=selected[0]['lon']), req.start]
        else:
            points = [req.start, destination(req.start, radius, 30+attempt*100),
                      destination(req.start, radius, 130+attempt*100), req.start]
        try:
            geom, meters, seconds, provider, waypoints = await routed(points)
            coords = geom['coordinates']
            if geom.get('type') != 'LineString' or len(coords) < 2 or not math.isfinite(meters) or meters < 100:
                failures.append('Invalid or too-short route geometry')
                continue
            first, last = Point(lon=coords[0][0],lat=coords[0][1]), Point(lon=coords[-1][0],lat=coords[-1][1])
            if distance(first, last) > 20 or distance(first,req.start) > 100:
                failures.append("Route did not return near the selected start")
                continue
            # A stop is proposed only when the pedestrian network passes near its mapped point.
            if selected and min(distance(Point(lon=c[0],lat=c[1]),points[1]) for c in coords) > 80:
                selected = []
            stop = req.stop_minutes
            moving = moving_minutes(meters,req.mode)
            total = moving + stop
            logger.info("Pedestrian attempt %s: %.1f m, %.2f total minutes (budget %s)", attempt+1, meters, total, req.minutes)
            if total > req.minutes:
                failures.append("Returned pedestrian route exceeded the time budget")
            if total <= req.minutes and (best is None or total > best['total_minutes']):
                best = {'geometry': geom, 'distance_m': round(meters), 'moving_minutes': moving,
                        'stop_minutes': stop, 'total_minutes': total, 'provider_duration_seconds': seconds,
                        'provider': provider, 'stops': selected, 'places': nearby, 'place_lookup': place_lookup,
                        'snapped_start': {'lat': first.lat, 'lon': first.lon}, 'warnings': [], 'demo_data': False}
            if not selected:
                radius *= min(1.4, max(0.25, target/max(meters,1)*0.95))
            if best and total >= req.minutes*0.8:
                break
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            reason = failure_reason(exc)
            logger.warning('Pedestrian routing attempt %s failed: %s', attempt+1, reason)
            failures.append(reason)
            if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in (401, 403, 429):
                break
            continue
    if best is None:
        raise HTTPException(503, 'No real pedestrian round trip fitting this time budget was found. ' + '; '.join(dict.fromkeys(failures)) + '. Try another start or more minutes, or retry later if the provider is unavailable.')
    matched = {p['kind'] for p in best['stops']}
    unmet = [p for p in req.preferences if p not in matched]
    if unmet:
        warnings.append('Requested preferences not included in the route: ' + ', '.join(unmet) + '. Nearby markers do not count as planned stops.')
    if req.preferences and not best['stops']:
        warnings.append('No requested place could be included. This route does not guarantee greenery, scenery, fruit or water.')
    if req.stop_minutes and not best['stops']:
        warnings.append('The requested pause is included in total time, but no mapped place is assigned to it. Choose a suitable place to pause; access is unverified.')
    if best['total_minutes'] < req.minutes * 0.8:
        warnings.append('This route is shorter than your available time; no closer match was found in the limited search.')
    best['warnings'] = warnings + ['Returns to the same mapped start; paths may overlap or be out-and-back.',
        'Walking estimate uses 4.8 km/h; jogging uses 8 km/h. Terrain, crossings and pauses can add time.',
        'OSM data may be incomplete. Access, road suitability, opening hours, stock and water quality are unverified.']
    return best
