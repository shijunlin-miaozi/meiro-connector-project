from typing import List, Dict

from common.logging import get_logger
from common.retry import retry_read_api
from connector.connector_base import BaseConnector
from connector.transforms import normalize_customers
from common.gsheets import get_read_client, open_by_url_or_id

log = get_logger(__name__)


class GoogleSheetsConnector(BaseConnector):
    """Read rows from a Google Sheet (read-only scope) and normalize them."""

    def __init__(self, credentials_path: str, spreadsheet_url_or_id: str, sheet_tab: str = "Sheet1"):
        """Configure credentials, spreadsheet ID/URL, and target worksheet tab."""
        self.credentials_path = credentials_path
        self.spreadsheet_url_or_id = spreadsheet_url_or_id
        self.sheet_tab = sheet_tab
        self._client = None  # lazy init

    def _get_client(self):
        if self._client is None:
            self._client = get_read_client(credentials_path=self.credentials_path)
        return self._client

    @retry_read_api
    def fetch(self) -> List[Dict]:
        """Fetch all records from the configured worksheet as a list of dicts."""
        client = self._get_client()
        sh = open_by_url_or_id(client, self.spreadsheet_url_or_id)
        ws = sh.worksheet(self.sheet_tab)
        records = ws.get_all_records()  # or get_all_records(default_blank="")
        log.info(
            "sheets_fetch_ok sheet_ref=%s tab=%s rows=%d",
            self.spreadsheet_url_or_id,
            self.sheet_tab,
            len(records),
        )
        return records

    def transform(self, rows: List[Dict]) -> List[Dict]:
        """Normalize sheet rows to the canonical customer schema."""
        return normalize_customers(rows)
