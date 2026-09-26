from __future__ import annotations

import csv
import json
import math
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / 'data'
DB_PATH = DATA_DIR / 'udyam_marg.db'

try:
    import h3
except Exception:  # pragma: no cover
    h3 = None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def h3_cell(lat: float, lon: float, resolution: int = 8) -> str:
    if h3 is None:
        # Conceptual fallback cell when h3 package is unavailable.
        return f'fallback-{round(lat, 2)}-{round(lon, 2)}'
    if hasattr(h3, 'latlng_to_cell'):
        return h3.latlng_to_cell(lat, lon, resolution)
    return h3.geo_to_h3(lat, lon, resolution)


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS pois (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        channel TEXT,
        village TEXT,
        district TEXT
    )''')
    cur.execute('SELECT COUNT(*) FROM pois')
    if cur.fetchone()[0] == 0:
        with open(DATA_DIR / 'pois.csv', newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                cur.execute(
                    'INSERT INTO pois(name, category, lat, lon, channel, village, district) VALUES(?,?,?,?,?,?,?)',
                    (row['name'], row['category'], float(row['lat']), float(row['lon']), row['channel'], row['village'], row['district'])
                )
    conn.commit()
    conn.close()


def resolve_location(location_text: str | None, lat: float | None, lon: float | None) -> dict[str, Any]:
    if lat is not None and lon is not None:
        return {'name': location_text or f'{lat:.4f}, {lon:.4f}', 'lat': lat, 'lon': lon, 'source': 'user_coordinates'}

    with open(DATA_DIR / 'locations.json', encoding='utf-8') as f:
        locations = json.load(f)
    q = (location_text or '').strip().lower()
    for loc in locations:
        haystack = ' '.join([loc['name'], loc.get('block', ''), loc.get('district', ''), loc.get('state', '')]).lower()
        if q and (q in haystack or loc['name'].lower() in q):
            return {**loc, 'source': 'mock_location_lookup'}

    # DEMO fallback instead of a live geocoder.
    default = locations[0]
    return {**default, 'source': 'mock_default_location', 'warning': 'Location not in demo gazetteer; using sample rural location.'}


def load_demographics(location_name: str) -> dict[str, Any]:
    with open(DATA_DIR / 'demographics.json', encoding='utf-8') as f:
        rows = json.load(f)
    target = location_name.lower()
    for row in rows:
        if row['location'].lower() in target or target in row['location'].lower():
            return row
    return rows[0]


def analyze_area(lat: float, lon: float, category: str, location_name: str) -> dict[str, Any]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM pois').fetchall()
    conn.close()

    nearby_5, nearby_10 = [], []
    for row in rows:
        d = haversine_km(lat, lon, row['lat'], row['lon'])
        item = dict(row) | {'distance_km': round(d, 2), 'h3_cell': h3_cell(row['lat'], row['lon'])}
        if d <= 10:
            nearby_10.append(item)
        if d <= 5:
            nearby_5.append(item)

    cat = category.lower().strip()
    competitors = [p for p in nearby_10 if p['category'].lower() == cat]
    cells = defaultdict(lambda: {'all_pois': 0, 'competitors': 0})
    for p in nearby_10:
        cells[p['h3_cell']]['all_pois'] += 1
        if p['category'].lower() == cat:
            cells[p['h3_cell']]['competitors'] += 1

    demo = load_demographics(location_name)
    pop_density_factor = demo.get('population_within_10km', 0)
    consumer_5 = int(pop_density_factor * 0.34)
    consumer_10 = int(pop_density_factor)
    channels = Counter(p['channel'] for p in nearby_10 if p.get('channel'))

    density = len(competitors) / (math.pi * 10 * 10) * 100
    density_label = 'Low' if len(competitors) <= 2 else 'Moderate' if len(competitors) <= 5 else 'High'

    return {
        'consumer_base_estimate': {'within_5km': consumer_5, 'within_10km': consumer_10},
        'population_proxy_note': 'Mock census-derived estimate for demo; replace with Census/Data.gov.in layers in production.',
        'poi_counts': {'within_5km': len(nearby_5), 'within_10km': len(nearby_10)},
        'competitor_mapping': {
            'category': category,
            'competitors_within_10km': len(competitors),
            'density_label': density_label,
            'competitors_per_100_sq_km': round(density, 2),
            'nearest': sorted(competitors, key=lambda x: x['distance_km'])[:5],
        },
        'distribution_channels': [{'channel': k, 'poi_count': v} for k, v in channels.most_common()],
        'h3_demand_zones': [
            {'cell': cell, **stats} for cell, stats in sorted(cells.items(), key=lambda x: x[1]['all_pois'], reverse=True)[:8]
        ],
        'demographics': demo,
    }
