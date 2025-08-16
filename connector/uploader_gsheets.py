from typing import List, Dict

from gspread import exceptions as gse

from common.logging import get_logger
from common.retry import retry_write_api
from connector.uploader_base import BaseUploader
from common.gsheets import get_write_client, open_by_url_or_id

log = get_logger(__name__)


class GoogleSheetsUploader(BaseUploader):
    """Append rows to a Google Sheet tab, creating the tab if missing."""

    def __init__(self, credentials_path: str, sheet_url_or_id: str, tab: str = "Ingested"):
        """Configure credentials, target spreadsheet URL/ID, and tab name."""
        self.credentials_path = credentials_path
        self.spreadsheet_url_or_id = sheet_url_or_id
        self.tab = tab
        self._client = None  # lazy init

    def _get_client(self):
        """Return an authorized gspread client with write scope."""
        if self._client is None:
            self._client = get_write_client(credentials_path=self.credentials_path)
        return self._client

    def _open_ws(self, client):
        """Open the worksheet by tab name or create it if it does not exist."""
        sh = open_by_url_or_id(client, self.spreadsheet_url_or_id)
        try:
            return sh.worksheet(self.tab)
        except gse.WorksheetNotFound:
            log.info("gsheets_tab_missing_creating sheet_ref=%s tab=%s", self.spreadsheet_url_or_id, self.tab)
            return sh.add_worksheet(title=self.tab, rows=1000, cols=26)

    @retry_write_api
    def upload(self, rows: List[Dict]) -> None:
        """Append rows (with header if needed) to the target worksheet."""
        if not rows:
            log.info("gsheets_upload_no_rows sheet_ref=%s tab=%s", self.spreadsheet_url_or_id, self.tab)
            return

        client = self._get_client()
        ws = self._open_ws(client)

        # Headers: keep order from first row's keys
        headers = list(rows[0].keys())

        # Write header if first row is empty (cheap check)
        existing_header = ws.row_values(1)
        if not existing_header:
            ws.append_row(headers, value_input_option="RAW")

        # Build batch and append (optionally chunk)
        batch = [[("" if r.get(h) is None else str(r.get(h))) for h in headers] for r in rows]

        # Optional chunking to avoid payload limits (uncomment if needed)
        # for i in range(0, len(batch), 500):
        #     ws.append_rows(batch[i:i+500], value_input_option="RAW")

        ws.append_rows(batch, value_input_option="RAW")

        log.info("gsheets_upload_ok sheet_ref=%s tab=%s rows=%d", self.spreadsheet_url_or_id, self.tab, len(rows))
