from __future__ import annotations

from typing import Dict, Any, List, Optional
import re
from flask import Blueprint, request, jsonify

CATEGORY_TO_SEGMENT = {
    "default": "",
    "music": "KZFzniwnSyZfZ7v7nJ",
    "sports": "KZFzniwnSyZfZ7v7nE",
    "arts": "KZFzniwnSyZfZ7v7na",
    "theatre": "KZFzniwnSyZfZ7v7na",
    "film": "KZFzniwnSyZfZ7v7nn",
    "miscellaneous": "KZFzniwnSyZfZ7v7n1",
}


def mapToSegmentId(category: Optional[str]) -> str:
    if not category:
        return "ERROR"
    key = category.strip().lower()
    return CATEGORY_TO_SEGMENT.get(key, "ERROR")


def create_search_blueprint(ticketmaster_service, google_service, ticketmaster_api_key: str) -> Blueprint:
    bp = Blueprint("search", __name__)

    @bp.get("/search/events")
    def get_events():
        keyword = request.args.get("keyword", type=str, default="").strip()
        distance = request.args.get("distance", default=10, type=int)
        category = request.args.get("category", type=str)
        location = request.args.get("location", type=str, default="").strip()

        # Validate basic required fields
        if not keyword:
            return jsonify({"error": "keyword is required"}), 400
        if distance is None or distance <= 0:
            return jsonify({"error": "distance must be a positive integer"}), 400
        if not location:
            return jsonify({"error": "location is required"}), 400

        # Category mapping
        segment_id = mapToSegmentId(category) if category else ""
        if "ERROR" == segment_id:
            return jsonify({"error": "valid category is required"}), 400

        # Geocode to geohash (accept "lat,lon" directly as a convenience)
        latlon_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location)
        if latlon_match:
            lat = float(latlon_match.group(1))
            lon = float(latlon_match.group(2))
            geo_hash = google_service.getGeoHashFromLatLng(lat, lon)
        else:
            try:
                geo_hash = google_service.getGeoHash(location)
            except Exception as ex:
                return jsonify({"error": f"failed to geocode location: {ex}"}), 500

        params: Dict[str, Any] = {
            "apikey": ticketmaster_api_key,
            "unit": "miles",
            "radius": distance,
            "keyword": keyword,
            "geoPoint": geo_hash,
        }
        if segment_id:
            params["segmentId"] = segment_id

        try:
            data = ticketmaster_service.get("/events", params)
        except Exception as ex:
            return jsonify({"error": f"ticketmaster error: {ex}"}), 502

        events = _map_events_response(data)
        return jsonify(events)

    @bp.get("/search/events/<string:event_id>")
    def get_event_by_id(event_id: str):
        print(f"get_event_by_id: {event_id}")
        
        params = {"apikey": ticketmaster_api_key}
        try:
            data = ticketmaster_service.get(f"/events/{event_id}", params)
        except Exception as ex:
            return jsonify({"error": f"ticketmaster error: {ex}"}), 502
        return jsonify(data)

    @bp.get("/search/venues/<string:event_id>")
    def get_venues_by_event_id(event_id: str):
        print(f"get_venues_by_event_id: {event_id}")
        
        params = {"apikey": ticketmaster_api_key}
        try:
            data = ticketmaster_service.get(f"/venues/{event_id}", params)
        except Exception as ex:
            return jsonify({"error": f"ticketmaster error: {ex}"}), 502
        return jsonify(data)

    return bp


def _extract_genre_from_classification(classification: Dict[str, Any]) -> str:
    """Extract genre from a single classification object."""
    # Check each classification field and skip if name is "undefined" (case-insensitive)
    segment_name = (classification.get("segment") or {}).get("name")
    if segment_name and segment_name.lower() != "undefined":
        return segment_name
    
    genre_name = (classification.get("genre") or {}).get("name")
    if genre_name and genre_name.lower() != "undefined":
        return genre_name
    
    subgenre_name = (classification.get("subGenre") or {}).get("name")
    if subgenre_name and subgenre_name.lower() != "undefined":
        return subgenre_name
    
    type_name = (classification.get("type") or {}).get("name")
    if type_name and type_name.lower() != "undefined":
        return type_name
    
    subtype_name = (classification.get("subtype") or {}).get("name")
    if subtype_name and subtype_name.lower() != "undefined":
        return subtype_name
    
    return "N/A"


def _map_events_response(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    events_raw = data.get("_embedded", {}).get("events", []) if isinstance(data, dict) else []
    mapped: List[Dict[str, Any]] = []
    for e in events_raw:
        # date/time
        start = (e.get("dates") or {}).get("start") or {}
        local_date = start.get("localDate")
        local_time = start.get("localTime")
        if local_date and local_time:
            date_time = f"{local_date} {local_time}"
        else:
            date_time = local_date or ""

        # genre
        genre = ""
        classifications = e.get("classifications", []) or []
        if not classifications:
            genre = "N/A"

        for c in classifications:
            if c.get("primary") is True:
                genre = _extract_genre_from_classification(c)
                break
        if not genre and e.get("classifications"):
            c0 = e["classifications"][0]
            genre = _extract_genre_from_classification(c0)

        # venue
        venue = ""
        venues = (e.get("_embedded") or {}).get("venues", [])
        if venues:
            venue = (venues[0] or {}).get("name", "")

        # icon - choose the smallest by area
        icon = ""
        images = e.get("images", []) or []
        if images:
            smallest = min(images, key=lambda i: (i.get("width", 1) or 1) * (i.get("height", 1) or 1))
            icon = smallest.get("url", "")

        mapped.append(
            {
                "id": e.get("id", ""),
                "name": e.get("name", "").strip(),
                "dateTime": date_time,
                "genre": genre,
                "venue": venue,
                "icon": icon,
            }
        )

    return mapped
