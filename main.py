import argparse
from uuid import uuid4
from datetime import datetime, timezone

from connector.google_sheets import GoogleSheetsConnector
from connector.random_user import RandomUserConnector
from connector.uploader import CsvUploader, StdoutUploader, HttpUploader
from connector.uploader_gsheets import GoogleSheetsUploader
from common.config import settings
from common.logging import get_logger

log = get_logger(__name__)

def build_connector():
    if settings.CONNECTOR == "sheets":
        return GoogleSheetsConnector(
            credentials_path=settings.GOOGLE_APPLICATION_CREDENTIALS,
            spreadsheet_url_or_id=settings.SHEET_URL_OR_ID,  # pass URL or ID here
            sheet_tab=settings.SHEET_TAB,
        )
    elif settings.CONNECTOR == "randomuser":
        return RandomUserConnector(
            results_per_page=settings.RANDOMUSER_RESULTS,
            pages=settings.RANDOMUSER_PAGES,
            seed=settings.RANDOMUSER_SEED,
            nat=settings.randomuser_nat_csv,
        )
    raise SystemExit(f"Unknown CONNECTOR '{settings.CONNECTOR}'")

def build_uploader(kind: str):
    if kind == "csv":
        return CsvUploader(settings.OUTPUT_PATH)
    if kind == "stdout":
        return StdoutUploader()
    if kind == "http":
        if not settings.UPLOAD_URL:
            raise SystemExit("UPLOAD_URL must be set for http uploader")
        return HttpUploader(url=settings.UPLOAD_URL, chunk_size=settings.CHUNK_SIZE)
    if kind == "gsheets":
        upload_sheet = settings.UPLOAD_SHEET_URL_OR_ID
        upload_tab = settings.UPLOAD_SHEET_TAB or "Ingested"
        creds = settings.GOOGLE_APPLICATION_CREDENTIALS
        if not (creds and upload_sheet):
            raise SystemExit(
                "For gsheets uploader, set GOOGLE_APPLICATION_CREDENTIALS and UPLOAD_SHEET_URL_OR_ID (or SHEET_URL_OR_ID)."
            )
        return GoogleSheetsUploader(credentials_path=creds, sheet_url_or_id=upload_sheet, tab=upload_tab)
    raise SystemExit(f"Unknown uploader '{kind}'")

def run_pipeline(uploader_kind: str):
    conn = build_connector()
    uploader = build_uploader(uploader_kind)
    log.info("pipeline_start connector=%s uploader=%s", settings.CONNECTOR, uploader_kind)

    rows = conn.fetch()
    log.info("fetch_done rows=%d", len(rows))

    clean = conn.transform(rows)
    log.info("transform_done rows=%d", len(clean))

    # --- Per-run metadata (applied to every row) -------
    # batch_id: run UUID for traceability (enables later dedupe).
    # ingested_at: UTC timestamp captured once per run.
    # Note: This doesn’t prevent duplicates; real prevention needs
    # sink-side idempotency (e.g., Idempotency-Key or DB UPSERT).
    batch_id = str(uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    for r in clean:
        r["batch_id"] = batch_id
        r.setdefault("ingested_at", now_iso)
    log.info("metadata_added batch_id=%s rows=%d", batch_id, len(clean))
    # ----------------------------------------------------

    uploader.upload(clean)
    log.info("upload_done")
    log.info("pipeline_end")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--uploader", choices=["csv", "stdout", "http", "gsheets"], default="csv")
    args = p.parse_args()
    run_pipeline(args.uploader)
