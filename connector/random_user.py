import requests
from typing import List, Dict, Optional

from common.logging import get_logger
from common.retry import retry_read_api
from connector.connector_base import BaseConnector
from connector.transforms import normalize_customers

log = get_logger(__name__)


class RandomUserConnector(BaseConnector):
    """Fetch synthetic users from randomuser.me with deterministic pagination."""
    BASE_URL = "https://randomuser.me/api/1.4/"
    TIMEOUT = 15
    DEFAULT_USER_AGENT = "randomuser-connector-demo/1.0"

    def __init__(self, results_per_page: int = 100, pages: int = 1, seed: Optional[str] = None, nat: Optional[str] = None,):
        """Configure page size/count, seed for determinism, and optional nat filter."""
        # Basic config
        self.results_per_page = max(1, min(int(results_per_page), 5000))
        self.pages = int(pages)

        # Deterministic pagination: If no seed is provided, use a stable default so pagination + retries are reproducible.
        self.seed = seed or "stable-demo-seed"

        # Nationality filter (e.g., "us,gb")
        self.nat = nat

        # Session reuse & User-Agent (connection pooling + friendlier to public APIs)
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": self.DEFAULT_USER_AGENT,
                "Accept": "application/json",
            }
        )

    @retry_read_api
    def _fetch_page(self, page: int) -> Dict:
        """Fetch a single API page with query params and return parsed JSON."""
        params = {"results": self.results_per_page, "page": page, "seed": self.seed}
        if self.nat:
            params["nat"] = self.nat
        resp = self._session.get(self.BASE_URL, params=params, timeout=self.TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def fetch(self) -> List[Dict]:
        """Fetch all configured pages and flatten into a list of rows."""
        rows: List[Dict] = []
        for p in range(1, self.pages + 1):
            data = self._fetch_page(p)
            results = data.get("results", [])
            for u in results:
                rows.append(
                    {
                        "id": (u.get("login", {}) or {}).get("uuid"),
                        "Email": u.get("email"),
                        "FirstName": (u.get("name", {}) or {}).get("first"),
                        "LastName": (u.get("name", {}) or {}).get("last"),
                        "Country": (u.get("location", {}) or {}).get("country"),
                        "LastPurchase": None,
                    }
                )
            log.info("randomuser_page_fetched page=%d results=%d total_so_far=%d", p, len(results), len(rows),)
        return rows

    def transform(self, rows: List[Dict]) -> List[Dict]:
        """Map API fields to the canonical customer schema and clean values."""
        return normalize_customers(rows)
