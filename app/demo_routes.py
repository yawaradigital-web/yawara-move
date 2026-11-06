"""Noncommercial, click-triggered OSRM demo routing between six predefined sample points.
Public demo service may be withdrawn; never use for real dispatch or billing.
Policy: https://routing.openstreetmap.de/about.html
"""
from __future__ import annotations
import json
import time
from threading import Lock
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from fastapi import HTTPException

POINTS = (
    (-46.6559, -23.5614),  # Avenida Paulista
    (-46.6576, -23.5874),  # Parque Ibirapuera
    (-46.6350, -23.5340),  # Estacao da Luz
    (-46.6564, -23.6261),  # Aeroporto de Congonhas
    (-46.6333, -23.5505),  # Praca da Se
    (-46.5496, -23.6933),  # Shopping Metropole
)
PROVIDER = "OSRM demo / OpenStreetMap"
_cache = {}
_lock = Lock()
_last_upstream = 0.0
_CACHE_SECONDS = 900
_MAX_BYTES = 500_000


def demo_route(origin: int, destination: int):
    """Never accept arbitrary hostnames, URLs or user GPS coordinates."""
    global _last_upstream
    if not (0 <= origin < len(POINTS) and 0 <= destination < len(POINTS)):
        raise HTTPException(422, "Ponto demonstrativo invalido")
    if origin == destination:
        raise HTTPException(422, "Origem e destino devem ser diferentes")
    key = (origin, destination)
    now = time.monotonic()
    with _lock:
        saved = _cache.get(key)
        if saved and now - saved[0] < _CACHE_SECONDS:
            return {**saved[1], "cached": True}
        if now - _last_upstream < 1.1:
            raise HTTPException(429, "Limite do servidor de rotas. Tente novamente em instantes",
                                headers={"Retry-After": "2"})
        _last_upstream = now

    a, b = POINTS[origin], POINTS[destination]
    coords = f"{a[0]:.4f},{a[1]:.4f};{b[0]:.4f},{b[1]:.4f}"
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=simplified&geometries=geojson&steps=false"
    req = Request(url, headers={
        "User-Agent": "YawaraMove-Demo/1.0 (+https://yawara-move-demo.onrender.com; educational demo)",
        "Accept": "application/json",
    })
    try:
        with urlopen(req, timeout=6) as response:
            raw = response.read(_MAX_BYTES + 1)
        if len(raw) > _MAX_BYTES:
            raise ValueError("route response too large")
        payload = json.loads(raw.decode("utf-8"))
        route = payload["routes"][0]
        coords_out = route["geometry"]["coordinates"]
        meters, seconds = float(route["distance"]), float(route["duration"])
        if (payload.get("code") != "Ok" or not 0 < meters <= 200_000
                or not 0 < seconds <= 100_000
                or not isinstance(coords_out, list)
                or not 2 <= len(coords_out) <= 4000
                or any(not isinstance(p, list) or len(p) != 2 or
                       not all(isinstance(x, (int, float)) and abs(x) <= 180 for x in p)
                       for p in coords_out)):
            raise ValueError("unusable route geometry")
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, IndexError, TypeError, OSError) as exc:
        raise HTTPException(503, "Rota demonstrativa indisponivel. Utilize os pontos ilustrativos.") from None

    result = {
        "status": "demo", "source": PROVIDER,
        "distance_km": round(meters / 1000, 2),
        "duration_minutes_illustrative": round(seconds / 60),
        "coordinates": coords_out,
        "routing": "road_demo_not_guaranteed",
        "commercial_dispatch": False,
        "cached": False,
    }
    with _lock:
        if len(_cache) > 35:
            _cache.clear()
        _cache[key] = (time.monotonic(), result)
    return result
