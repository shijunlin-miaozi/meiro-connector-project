import csv
import time
import itertools
import requests
from typing import List, Dict, Iterable, Optional, Any
from pathlib import Path

from common.logging import get_logger
from connector.uploader_base import BaseUploader
from common.retry import retry_write_api

log = get_logger(__name__)

def chunked(iterable: Iterable[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    """Yield lists of up to `size` items; size <= 0 yields the entire iterable."""
    if size <= 0:
        yield list(iterable)
        return
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk


class CsvUploader(BaseUploader):
    """Write rows to a CSV file, creating parent directories if needed."""
    def __init__(self, output_path: str) -> None:
        self.output_path = Path(output_path)

    def upload(self, rows: List[Dict[str, Any]]) -> None:
        if not rows:
            log.warning("csv_upload_no_rows path=%s", self.output_path)
            return

        # Ensure directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build union of all keys (preserving order from first row)
        first_keys = list(rows[0].keys())
        all_keys = set(first_keys)
        extra_keys: List[str] = []
        for r in rows[1:]:
            for k in r.keys():
                if k not in all_keys:
                    all_keys.add(k)
                    extra_keys.append(k)
        fieldnames = first_keys + extra_keys

        with self.output_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

        log.info("csv_upload_ok path=%s rows=%d cols=%d", self.output_path, len(rows), len(fieldnames))


class StdoutUploader(BaseUploader):
    """Print each row to stdout (debug/demo helper)."""
    def upload(self, rows: List[Dict[str, Any]]) -> None:
        """Print rows line by line to standard output."""
        for r in rows:
            print(r)


class HttpUploader(BaseUploader):
    """POST rows (optionally chunked) to an HTTP ingestion endpoint with retries."""
    def __init__(self, url: str, chunk_size: Optional[int] = None, timeout: int = 20) -> None:
        """Configure target URL, optional chunk size, and request timeout."""
        self.url = url
        self.chunk_size = int(chunk_size) if chunk_size else 0
        self.timeout = timeout
        # Reuse a session + add a UA
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "connector-demo/1.0", "Accept": "application/json"})

    @retry_write_api  # retries only on transient errors (429/5xx/timeouts), 2 attempts total
    def _post_batch(self, batch: List[Dict[str, Any]]) -> requests.Response:
        return self._session.post(self.url, json={"rows": batch}, timeout=self.timeout)

    def upload(self, rows: List[Dict[str, Any]]) -> None:
        """Send rows in chunks as JSON to the endpoint and log results."""
        if not rows:
            log.warning("http_upload_no_rows url=%s", self.url)
            return

        total = 0
        size = self.chunk_size or len(rows)
        for i, chunk in enumerate(chunked(rows, size), start=1):
            t0 = time.time()
            resp = self._post_batch(chunk)
            elapsed = int((time.time() - t0) * 1000)

            if resp.status_code >= 300:
                log.error(
                    "http_upload_failed url=%s status=%s body=%s elapsed_ms=%d chunk=%d size=%d",
                    self.url, resp.status_code, resp.text[:500], elapsed, i, len(chunk)
                )
                resp.raise_for_status()

            total += len(chunk)
            log.info(
                "http_upload_ok url=%s chunk=%d sent=%d elapsed_ms=%d",
                self.url, i, len(chunk), elapsed
            )

        log.info("http_upload_done url=%s total_sent=%d", self.url, total)
