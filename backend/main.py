from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .models import ParseRequest, RouteRequest
from .preferences import parse_preferences
from .routing import plan

app = FastAPI(title='Runningo')

@app.get('/api/health')
async def health():
    return {'status': 'ok'}

@app.post('/api/preferences')
async def preferences(req: ParseRequest):
    return await parse_preferences(req.text, req.current)

@app.post('/api/route')
async def route(req: RouteRequest):
    return await plan(req)

static = Path(__file__).resolve().parents[1] / 'frontend' / 'dist'
if static.exists():
    app.mount('/', StaticFiles(directory=static, html=True), name='frontend')
