# Assignment 2 Flask App

A simple Flask app that searches Ticketmaster events with Google Maps geocoding.

## Routes
- `GET /` or `/index.html` — serve the UI
- `GET /search/events` — search events
  - query params: `keyword` (required), `distance` (positive int), `category` (one of: Music, Sports, Arts & Theatre, Film, Miscellaneous), `location` (required)
- `GET /search/event/<id>` — get event detail by id

## Services
- GoogleMapService: geocode an address and return geohash (`getGeoHash`)
- TicketMasterService: GET wrapper on base endpoint `https://app.ticketmaster.com/discovery/v2`

## Setup
1. Python 3.10+
2. Create a venv and install deps:
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3. Export API keys:
```
export GOOGLE_MAPS_API_KEY=your_google_api_key
export TICKETMASTER_API_KEY=your_ticketmaster_api_key
```
4. Run the app:
```
python app.py
```
Open http://localhost:5000

## Notes
- The UI "Auto-Detect" checkbox uses ipinfo.io to infer a location and populates the Location input.
- The results table shows: Date Time, Icon, Event, Genre, Venue.
