# Integration: FastAPI ingestion endpoint (/ingest). 
# Uses TestClient and a temp OUT path to verify JSONL writes.

import json
import pytest
from pathlib import Path
from starlette.testclient import TestClient

import common.ingestion_api as ingestion

def test_http_e2e_writes_jsonl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Redirect output file to a temp location
    out_file = tmp_path / "ingested.jsonl"
    monkeypatch.setattr(ingestion, "OUT", out_file)

    client = TestClient(ingestion.app)
    payload = {"rows": [{"a": 1}, {"a": 2, "b": "x"}]}
    resp = client.post("/ingest", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["received"] == 2

    # Read JSONL and assert two lines
    lines = out_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    objs = [json.loads(line) for line in lines]
    assert objs[0]["a"] == 1 and objs[1]["a"] == 2
