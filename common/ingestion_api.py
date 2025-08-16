import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pathlib import Path
from common.logging import get_logger

log = get_logger(__name__)

app = FastAPI(title="Local Ingestion API")

# Local: set INGEST_OUT to override; Docker: default writes to /app/out/ingested.jsonl
OUT = Path(os.getenv("INGEST_OUT", "/app/out/ingested.jsonl"))

@app.post("/ingest")
async def ingest(request: Request):
    payload = await request.json()
    rows = payload.get("rows", [])
    
    # create the directory at request time (after tests can monkeypatch OUT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    
    with OUT.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r)+"\n")
    log.info("api_ingest rows=%d file=%s", len(rows), OUT)
    return JSONResponse({"status": "ok", "received": len(rows)})
