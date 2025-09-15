from __future__ import annotations

from typing import Dict, Any
import requests


class TicketMasterService:
    BASE_URL = "https://app.ticketmaster.com/discovery/v2"

    def __init__(self):
        self.session = requests.Session()

    def get(self, subpath: str, params: Dict[str, Any]):
        url = f"{self.BASE_URL}{subpath}"
        resp = self.session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
