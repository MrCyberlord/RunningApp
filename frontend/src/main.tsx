import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './style.css';

type Point = {lat:number;lon:number};
type Kind = 'greenery'|'scenic'|'fruit'|'water';
type Prefs = {mode:'walking'|'jogging';minutes:number;stop_minutes:number;preferences:Kind[]};
type Place = Point & {id:string;name:string;kind:Kind;osm_url:string};
type Route = {place_lookup?:{status:'ok'|'empty'|'unavailable';provider?:string;cache_hit?:boolean};geometry:{coordinates:number[][]};distance_m:number;moving_minutes:number;stop_minutes:number;total_minutes:number;provider:string;places:Place[];stops:Place[];warnings:string[];snapped_start:Point};
const choices: {id:Kind;icon:string;label:string}[] = [{id:'greenery',icon:'♧',label:'Parks & gardens'},{id:'scenic',icon:'☀',label:'Scenic spots'},{id:'fruit',icon:'◉',label:'Fruit stop'},{id:'water',icon:'◌',label:'Drinking water'}];
const colors = {greenery:'#398351',scenic:'#9c6b23',fruit:'#d26d35',water:'#287cad'};
async function api<T>(path:string,body:unknown):Promise<T>{
  const response = await fetch('/api/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(150000)});
  if(!response.ok){const data=await response.json().catch(()=>({}));throw new Error(typeof data.detail==='string'?data.detail:response.status===422?'Check your time and stop settings. Stop time must be less than total time.':'The service is unavailable. Please try again.');}
  return response.json();
}
function MapControls({start,route,onStart}:{start:Point|null;route:Route|null;onStart:(p:Point)=>void}){
  const map=useMap();
  useMapEvents({click:e=>onStart({lat:e.latlng.lat,lon:e.latlng.lng})});
  useEffect(()=>{if(route)map.fitBounds(route.geometry.coordinates.map(c=>[c[1],c[0]] as [number,number]),{padding:[30,30]});else if(start)map.setView([start.lat,start.lon],15);},[start,route,map]);
  useEffect(()=>{
    let frame=0;
    const resize=()=>{
      cancelAnimationFrame(frame);
      frame=requestAnimationFrame(()=>{
        map.invalidateSize({pan:false});
        if(route)map.fitBounds(route.geometry.coordinates.map(c=>[c[1],c[0]] as [number,number]),{padding:[30,30],animate:false});
      });
    };
    const observer=new ResizeObserver(resize);
    observer.observe(map.getContainer());
    resize();
    return ()=>{observer.disconnect();cancelAnimationFrame(frame);};
  },[map,route]);
  return null;
}
function App(){
 const [start,setStart]=useState<Point|null>(null);
 const [prefs,setPrefs]=useState<Prefs>({mode:'walking',minutes:30,stop_minutes:0,preferences:['greenery']});
 const [tileWarning,setTileWarning]=useState('');
 const [text,setText]=useState(''); const [route,setRoute]=useState<Route|null>(null);
 const [busy,setBusy]=useState(''); const [error,setError]=useState(''); const [ai,setAi]=useState('Optional Gemma interpretation. Form controls always work without AI.');
 function change(next:Prefs){setPrefs(next);setRoute(null);setError('');}
 function select(p:Point){if(busy)return;setStart(p);setRoute(null);setError('');}
 async function locate(){setBusy('Finding your location…');setError('');if(!navigator.geolocation){setError('Geolocation is unavailable. Tap the map to choose a start.');setBusy('');return;}
 navigator.geolocation.getCurrentPosition(p=>{setStart({lat:p.coords.latitude,lon:p.coords.longitude});setRoute(null);setBusy('');},()=>{setError('Location was unavailable or permission was declined. Tap the map to choose a start.');setBusy('');},{timeout:12000,maximumAge:60000});}
 async function interpret(){setBusy('Asking Gemma…');setError('');try{const data=await api<{preferences:Prefs;source:string;message:string}>('preferences',{text,current:prefs});setPrefs(data.preferences);setAi(data.message);setRoute(null);}catch(e){setError((e as Error).message);setAi('AI was not used. Form settings are unchanged.');}finally{setBusy('');}}
 async function plan(){if(busy)return;if(!start){setError('Choose a starting point by tapping the map, or select Use my location, before planning a route.');return;}setBusy('Finding real paths & nearby places…');setRoute(null);setError('');try{setRoute(await api<Route>('route',{...prefs,start}));}catch(e){setError((e as Error).message);}finally{setBusy('');}}
 return <><header><a className="brand" href="/" aria-label="Runningo home"><span className="brandmark">r<span>↗</span></span>runningo<span className="brand-dot">.</span></a><span className="challenge">HACKTOBERFEST <span> / </span> TOUCH GRASS</span><span className="header-note">Less scrolling. More strolling.</span></header>
 <main><section className="intro"><div className="eyebrow"><span className="tiny-dot"/> A LITTLE FRESH AIR, PLANNED</div><h1>Your next good<br/> <em>outside</em> starts here.</h1><p>A walk, a jog, a little detour. Make the most of the time you have.</p></section>
 <div className="workspace"><section className="planner" aria-label="Route settings"><div className="panel-title"><h2>Make it your outing</h2><span>01 — PLAN</span></div>
 <fieldset disabled={!!busy}><legend>Starting point</legend><div className="location-box"><span>◎</span><div><strong>{start?'Start selected':'Pick a spot on the map'}</strong><small>{start?start.lat.toFixed(5)+', '+start.lon.toFixed(5):'Your route will bring you back here'}</small></div></div><button className="locate" onClick={locate}>⌖ Use my location</button>
 <legend className="field-label">How are you heading out?</legend><div className="segmented">{(['walking','jogging'] as const).map(mode=><button key={mode} aria-pressed={prefs.mode===mode} className={prefs.mode===mode?'active':''} onClick={()=>change({...prefs,mode})}>{mode==='walking'?'↟ Walking':'↗ Jogging'}</button>)}</div>
 <div className="time-label"><label htmlFor="minutes">Time to spare</label><strong>{prefs.minutes}<small> min total</small></strong></div><input id="minutes" type="range" min="10" max="120" step="5" value={prefs.minutes} onChange={e=>change({...prefs,minutes:+e.target.value,stop_minutes:Math.min(prefs.stop_minutes,+e.target.value-1)})}/><div className="range-labels"><span>10 min</span><span>120 min</span></div>
 <legend className="field-label">A little something along the way</legend><div className="preferences">{choices.map(c=><button key={c.id} aria-pressed={prefs.preferences.includes(c.id)} className={prefs.preferences.includes(c.id)?'selected':''} onClick={()=>change({...prefs,preferences:prefs.preferences.includes(c.id)?prefs.preferences.filter(p=>p!==c.id):[...prefs.preferences,c.id]})}><span>{c.icon}</span>{c.label}<span className="check">{prefs.preferences.includes(c.id)?'✓':'+'}</span></button>)}</div>
 <label className="stop-label" htmlFor="stop">Optional stop time <span><input id="stop" type="number" min="0" max={Math.min(30,prefs.minutes-1)} value={prefs.stop_minutes} onChange={e=>change({...prefs,stop_minutes:+e.target.value})}/> min</span></label><small className="hint">Included in total time, even if no mapped stop is found.</small>
 <details><summary>Describe your ideal outing <span>GEMMA · OPTIONAL</span></summary><label className="sr-only" htmlFor="request">Natural language request</label><textarea id="request" value={text} maxLength={1000} onChange={e=>setText(e.target.value)} placeholder="A 30-minute jog with a park and a 5-minute fruit stop"/><button className="locate" disabled={!text.trim()} onClick={interpret}>Interpret request</button><p className="hint" role="status">{ai}</p></details>
 <p id="route-prerequisite" className="hint" role="status">{!start?'Choose a starting point on the map or use your location before planning.':'Start selected. Ready to find a route.'}</p><button className="primary" disabled={!!busy} aria-busy={!!busy} aria-describedby="route-prerequisite" onClick={plan}>{busy||(start?'Find my fresh-air route':'Choose a start to plan a route')}{!busy&&<span>↗</span>}</button><p className="under-button">Real paths. A return to your start. A little room to breathe.</p></fieldset>
 {error&&<div className="error" role="alert">{error}</div>}</section>
 <section className="map-section" aria-label="Route map and results"><div className="map-top"><span><span className="tiny-dot"/> YOUR PATCH OF OUTSIDE</span><span>Tap the map to set your start</span></div><div className="map-wrap"><MapContainer center={[12.976,77.592]} zoom={14} className="map" aria-label="Interactive map. Click a location to set your start."><TileLayer eventHandlers={{tileerror:()=>setTileWarning('Some map tiles could not load. Check your connection or try again later.')}} url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'/><MapControls start={start} route={route} onStart={select}/>{start&&<CircleMarker center={[start.lat,start.lon]} radius={9} pathOptions={{color:'#fff',weight:3,fillColor:'#193f32',fillOpacity:1}}><Popup>Your selected start</Popup></CircleMarker>}{route&&<><Polyline positions={route.geometry.coordinates.map(c=>[c[1],c[0]])} pathOptions={{color:'#236a49',weight:5}}/>{route.places.map(p=><React.Fragment key={p.id}><CircleMarker center={[p.lat,p.lon]} radius={route.stops.some(s=>s.id===p.id)?9:5} interactive={false} pathOptions={{color:colors[p.kind],fillOpacity:.85}}/><CircleMarker center={[p.lat,p.lon]} radius={22} pathOptions={{stroke:false,fillOpacity:0}}><Popup><strong>{p.name}</strong><br/>{choices.find(c=>c.id===p.kind)?.label}<br/><a href={p.osm_url} target="_blank" rel="noreferrer">View mapped source ↗</a><br/>{route.stops.some(s=>s.id===p.id)?'Planned near this mapped point; entrance unverified':'Nearby marker only; not a planned stop'}<br/>Access and availability unverified</Popup></CircleMarker></React.Fragment>)}</>}</MapContainer>{!start&&<div className="map-hint"><span>◎</span><div><strong>Every good outing starts somewhere.</strong><small>Tap a path or use your current location.</small></div></div>}{busy&&<div className="map-loading" role="status">{busy}<small>Public services can take a moment.</small></div>}</div>
 {tileWarning&&<p className="error" role="status">{tileWarning}</p>}<div className="legend">{choices.map(c=><span key={c.id}><i style={{background:colors[c.id]}}/>{c.label}</span>)}</div>
 {route?<div className="results" aria-live="polite"><div className="result-heading"><h2>Your fresh-air route</h2><span>REAL ROUTING · NO DEMO DATA</span></div><div className="stats"><div><strong>{(route.distance_m/1000).toFixed(2)}<small> km</small></strong><span>distance</span></div><div><strong>{Math.ceil(route.moving_minutes)}<small> min</small></strong><span>moving estimate</span></div><div><strong>{route.stop_minutes}<small> min</small></strong><span>optional stop</span></div><div><strong>{Math.ceil(route.total_minutes)}<small> min</small></strong><span>total estimate</span></div></div><p className="hint">Pedestrian network: {route.provider}. {route.provider==='openrouteservice'&&<a href="https://openrouteservice.org/">© openrouteservice by HeiGIT</a>} Start snaps to a mapped path within 100 m.</p>{route.stops.map(p=><p key={p.id}>Suggested stop: <a href={p.osm_url} target="_blank" rel="noreferrer">{p.name} ↗</a> · near the route; entrance unverified.</p>)}{route.place_lookup?.status==='unavailable'?<p>Place lookup is unavailable. Nearby places are unknown.</p>:!route.places.length&&<p>Place lookup succeeded. No matching mapped places were returned in the search area.</p>}<ul className="warnings">{route.warnings.map(w=><li key={w}>{w}</li>)}</ul></div>:<div className="empty-result"><span className="leaf">♧</span><div><h3>A small break can go a long way.</h3><p>Choose your start, set your pace, and we’ll find a real route back.<br/>The initial map view is Bengaluru, not your detected location.</p></div></div>}
 </section></div><footer><span>Made for getting out there. <strong>Runningo / Touch Grass</strong></span><span>OSM places & paths · <a href="https://routing.openstreetmap.de/about.html">FOSSGIS</a> · <a href="https://www.openstreetmap.org/fixthemap">Fix the map</a></span></footer><p className="privacy">No accounts or location storage. Planning sends coordinates to routing and place providers. Optional interpretation sends your text to the configured model. Browser location needs permission and HTTPS or localhost.</p></main></>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
