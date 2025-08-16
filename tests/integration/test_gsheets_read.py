# Integration: Google Sheets READ via GoogleSheetsConnector. 
# Skips unless RUN_SHEETS_INTEGRATION=1 and creds + SHEET_URL_OR_ID are set.

import os
from connector.google_sheets import GoogleSheetsConnector


def test_gsheets_read_basic():
    creds = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    spreadsheet = os.environ["SHEET_URL_OR_ID"]
    tab = os.getenv("SHEET_TAB", "Sheet1")

    conn = GoogleSheetsConnector(credentials_path=creds, spreadsheet_url_or_id=spreadsheet, sheet_tab=tab)
    rows = conn.fetch()
    assert isinstance(rows, list)
    # For the demo sheet, expect at least one row. Adjust if your sheet can be empty.
    assert len(rows) >= 1
