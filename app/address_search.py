"""Optional, provider-backed address suggestions. No address logs or persistence.
The API key is read only from Render server environment.
Reference: https://apidocs.geoapify.com/docs/geocoding/address-autocomplete/
"""
from __future__ import annotations

import json
import math
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from fastapi import HTTPException

PROVIDER_URL = "https://api.geoapify.com/v1/geocode/autocomplete"
MAX_RESPONSE_BYTES = 120_000


def geocoder_enabled() -> bool:
    return bool(os.getenv("MOVE_GEOAPIFY_API_KEY", "").strip())


def find_addresses(term: str) -> list[dict]:
    """Brazil-only previews. Deliberately not integrated with fares or live dispatch."""
    api_key = os.getenv("MOVE_GEOAPIFY_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503,
                            detail="Busca real desativada. Continue com os locais demonstrativos.")
    text = " ".join(term.split())
    if not 4 <= len(text) <= 100:
        raise HTTPException(status_code=422, detail="Digite de 4 a 100 caracteres.")
    if any(ord(c) < 32 for c in text):
        raise HTTPException(status_code=422, detail="Texto de busca invalido.")
    query = urlencode({
        "text": text, "lang": "pt", "limit": 5,
        "filter": "countrycode:br", "format": "json",
        "apiKey": api_key
    })
    request = Request(PROVIDER_URL + "?" + query, headers={
        "Accept": "application/json",
        "User-Agent": "YawaraMoveSandbox/1.0 (https://yawara-move-demo.onrender.com)"
    })
    try:
        with urlopen(request, timeout=5) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Oversized provider response")
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise ValueError("Malformed provider response")
        results = []
        for row in data["results"][:10]:
            if not isinstance(row, dict) or str(row.get("country_code", "")).lower() != "br":
                continue
            lat, lon, label = row.get("lat"), row.get("lon"), row.get("formatted")
            if not (isinstance(lat, (int, float)) and not isinstance(lat, bool)
                    and isinstance(lon, (int, float)) and not isinstance(lon, bool)
                    and math.isfinite(lat) and math.isfinite(lon)
                    and -34.5 <= lat <= 5.5 and -74.0 <= lon <= -33.0
                    and isinstance(label, str) and 4 <= len(label) <= 160):
                continue
            results.append({"label": label[:140], "lat": float(lat), "lon": float(lon)})
            if len(results) == 5:
                break
        return results
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, TypeError, OSError):
        # Never return provider URL, raw query or credential to clients.
        raise HTTPException(503, "Busca de enderecos temporariamente indisponivel.") from None
