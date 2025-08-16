# Integration: Google Sheets WRITE via GoogleSheetsUploader. 
# Skips unless RUN_SHEETS_WRITE=1 and creds + UPLOAD_SHEET_URL_OR_ID are set.

import os
import uuid

from connector.uploader_gsheets import GoogleSheetsUploader

def test_gsheets_write_smoke():
    creds = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    dest = os.environ["UPLOAD_SHEET_URL_OR_ID"]
    tab = os.getenv("UPLOAD_SHEET_TAB", "Ingested")

    uploader = GoogleSheetsUploader(credentials_path=creds, sheet_url_or_id=dest, tab=tab)

    batch_id = str(uuid.uuid4())
    rows = [
            {"customer_id": "c-001","email":"alice.tan@example.com","first_name":"Alice","last_name":"Tan","country":"US","last_purchase_at":"2025-08-01T09:00:00+00:00","batch_id":batch_id,"ingested_at":"2025-08-16T19:23:00.298172+00:00"},
            {"customer_id": "c-002","email":"bob@example.net","first_name":"Bob","last_name":"Lee","country":"SG","last_purchase_at":"2025-07-15T10:00:00+00:00","batch_id":batch_id,"ingested_at":"2025-08-16T19:23:00.298172+00:00"},
    ]

    # No exception indicates success.
    uploader.upload(rows)
