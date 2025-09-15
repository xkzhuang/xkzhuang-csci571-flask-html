from __future__ import annotations

import hashlib
import math
import os
from typing import Tuple

import requests


class GoogleMapService:
    """
    Google Maps Geocoding client that can geocode an address and return a geohash.
    - Requires environment variable GOOGLE_MAPS_API_KEY (or pass api_key).
    - Public method: getGeoHash(address: str, precision: int = 7) -> str
    """

    GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    _BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY", "")

    def getGeoHash(self, address: str, precision: int = 7) -> str:
        lat, lng = self._geocode(address)
        return self._encode_geohash(lat, lng, precision)

    def getGeoHashFromLatLng(self, lat: float, lng: float, precision: int = 7) -> str:
        return self._encode_geohash(lat, lng, precision)

    # --- internal helpers ---
    def _geocode(self, address: str) -> Tuple[float, float]:
        if not self.api_key:
            raise RuntimeError("Missing GOOGLE_MAPS_API_KEY")
        params = {"address": address, "key": self.api_key}
        resp = requests.get(self.GEOCODE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "OK" or not data.get("results"):
            raise RuntimeError(f"Geocoding failed: {data.get('status')}")
        loc = data["results"][0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])

    def _encode_geohash(self, lat: float, lon: float, precision: int = 7) -> str:
        # Implementation adapted from the geohash algorithm (no external deps)
        lat_interval = [-90.0, 90.0]
        lon_interval = [-180.0, 180.0]
        geohash = []
        bits = [16, 8, 4, 2, 1]
        bit = 0
        ch = 0
        even = True

        while len(geohash) < precision:
            if even:
                mid = (lon_interval[0] + lon_interval[1]) / 2
                if lon > mid:
                    ch |= bits[bit]
                    lon_interval[0] = mid
                else:
                    lon_interval[1] = mid
            else:
                mid = (lat_interval[0] + lat_interval[1]) / 2
                if lat > mid:
                    ch |= bits[bit]
                    lat_interval[0] = mid
                else:
                    lat_interval[1] = mid

            even = not even
            if bit < 4:
                bit += 1
            else:
                geohash.append(self._BASE32[ch])
                bit = 0
                ch = 0

        return "".join(geohash)
