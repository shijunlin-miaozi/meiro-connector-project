# Integration test config
# load .env, mark tests as 'integration', and gate specific files by env toggles/creds.

import os
from pathlib import Path
import pytest
from dotenv import load_dotenv

# Load .env so os.getenv() picks up toggles/creds without importing app config
load_dotenv()

# Mark all tests in this folder as integration by default
pytestmark = pytest.mark.integration

# Per-file enablement rules (filename -> (env var, human-readable message)).
# HTTP ingestion has no toggle (always runs when -m integration is used).
FILE_TOGGLES = {
    "test_random_user_fetch.py": (
        "RUN_RANDOMUSER_INTEGRATION",
        "Enable with RUN_RANDOMUSER_INTEGRATION=1",
    ),
    "test_gsheets_read.py": (
        "RUN_SHEETS_INTEGRATION",
        "Enable with RUN_SHEETS_INTEGRATION=1 and set GOOGLE_APPLICATION_CREDENTIALS + SHEET_URL_OR_ID",
    ),
    "test_gsheets_write.py": (
        "RUN_SHEETS_WRITE",
        "Enable with RUN_SHEETS_WRITE=1 and set GOOGLE_APPLICATION_CREDENTIALS + UPLOAD_SHEET_URL_OR_ID",
    ),
    # "test_http_upload.py": no toggle by design
}

def pytest_collection_modifyitems(session, config, items):
    """Apply env-based skips to integration tests in this folder."""
    for item in items:
        p = Path(str(item.fspath))
        if "tests/integration" not in str(p):
            continue  # only manage tests in this folder

        fname = p.name

        # Random User network toggle
        if fname == "test_random_user_fetch.py":
            if os.getenv("RUN_RANDOMUSER_INTEGRATION") != "1":
                item.add_marker(pytest.mark.skip(reason=FILE_TOGGLES[fname][1]))

        # Google Sheets read: requires toggle + creds + sheet
        elif fname == "test_gsheets_read.py":
            if (
                os.getenv("RUN_SHEETS_INTEGRATION") != "1"
                or not os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                or not os.getenv("SHEET_URL_OR_ID")
            ):
                item.add_marker(pytest.mark.skip(reason=FILE_TOGGLES[fname][1]))

        # Google Sheets write: requires toggle + creds + upload sheet
        elif fname == "test_gsheets_write.py":
            if (
                os.getenv("RUN_SHEETS_WRITE") != "1"
                or not os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                or not os.getenv("UPLOAD_SHEET_URL_OR_ID")
            ):
                item.add_marker(pytest.mark.skip(reason=FILE_TOGGLES[fname][1]))

        # HTTP ingestion test runs whenever integration tests are selected
        # (no extra env toggles). Add checks here if you later require any.
