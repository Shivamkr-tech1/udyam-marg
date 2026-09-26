import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from .schemas import AnalyzeRequest
from .services.finance import calculate_financial_plan
from .services.geo import analyze_area, init_db, resolve_location
from .services.credit import mock_creditworthiness_score
from .services.advisory import generate_advisory

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

frontend_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    title='UDYAM MARG API',
    version='0.1.0',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)



@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'udyam-marg'}


@app.post('/api/analyze')
def analyze(req: AnalyzeRequest):
    try:
        finance = calculate_financial_plan(req.margin_capital)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    location = resolve_location(req.location, req.lat, req.lon)
    geo = analyze_area(location['lat'], location['lon'], req.business_category, location['name'])
    advisory = generate_advisory(req.business_category, location, geo, finance)
    credit = mock_creditworthiness_score()

    return {
        'input': req.model_dump(),
        'location': location,
        'financial': finance,
        'geospatial': geo,
        'advisory': advisory,
        'alternative_creditworthiness': credit,
        'prototype_notes': [
            'Financial calculations are deterministic and rule-based.',
            'POI, demographics and market prices are realistic mock data for demonstration.',
            'Bhashini is represented by browser Web Speech API hooks in the frontend.',
            'Alternative creditworthiness uses synthetic sample features only.',
        ],
    }
