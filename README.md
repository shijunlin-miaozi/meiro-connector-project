# Meiro-Style Connector (Python + Docker)

A production-leaning demo for data connectors that showcases the **fetch → normalize → upload** lifecycle with:
- **Sources**: Google Sheets (service account), Random User API (public)
- **Destinations**: CSV, Stdout, HTTP→FastAPI receiver, Google Sheets write
- **Good practices**: OOP/SOLID, Docker, unit & integration tests, GitHub Actions CI, typed config, retries (Tenacity), structured logs

---

## Highlights

- **Two real connectors**
  - `GoogleSheetsConnector`: read-only auth, open by URL/ID, least privilege
  - `RandomUserConnector`: deterministic pagination (`seed`), session reuse, User-Agent
- **Uploaders**
  - `CsvUploader`, `StdoutUploader`
  - `HttpUploader` → writes JSONL to a local FastAPI receiver
  - `GoogleSheetsUploader` (append rows, create tab if missing)
- **Transforms**
  - Canonical schema (`customer_id`, `email`, `first_name`, `last_name`, `country`, `last_purchase_at`)
  - Email validation, UTC normalization, name casing, ISO-2 country codes
- **Resilience**
  - Targeted retries (network/transient status codes only)
  - Log context for traceability
  - Batch metadata (`batch_id`, `ingested_at`) in the pipeline

---

## Repository Layout

```
.
├─ common/
│  ├─ config.py               # env loading (dotenv), typed Settings
│  ├─ logging.py              # key=value structured logs
│  ├─ retry.py                # tenacity retry wrappers (read/write)
│  ├─ gsheets.py              # Google Sheets helpers (auth, open by URL/ID)
│  └─ ingestion_api.py        # FastAPI receiver: POST /ingest → JSONL
├─ connector/
│  ├─ connector_base.py       # abstract BaseConnector
│  ├─ google_sheets.py        # GoogleSheetsConnector (read-only)
│  ├─ random_user.py          # RandomUserConnector (seeded, session)
│  ├─ transforms.py           # normalize + helpers (email/date/country/name)
│  ├─ uploader_base.py        # abstract BaseUploader
│  ├─ uploader.py             # CSV / Stdout / HTTP (+chunked helper)
│  └─ uploader_gsheets.py     # GoogleSheetsUploader (append/create)
├─ tests/
│  ├─ unit/                   # fast, deterministic tests
│  └─ integration/            # HTTP (no secrets), Sheets/RandomUser (opt-in)
├─ scripts/
│  ├─ healthcheck.sh          # docker/env preflight checks
│  ├─ run_unit_tests.sh       # run unit tests locally/in CI
│  ├─ run_integration_tests.sh# run HTTP + optional RandomUser/Sheets integrations
│  ├─ run_randomuser_http.sh  # start receiver + send RandomUser→HTTP
│  ├─ run_sheets_to_sheets.sh # Sheets→Sheets pipeline (needs creds)
│  └─ clean_up.sh             # stop/remove containers/images + clean out
├─ .github/workflows/ci.yml   # unit + HTTP integ + optional Sheets/RandomUser jobs
├─ .env.example               # sample configuration
├─ requirements.txt           # pinned dependencies
├─ Dockerfile                 # non-root image, cached deps
├─ pytest.ini                 # default to unit tests (testpaths)
└─ main.py                    # pipeline entrypoint
```

---

## Prerequisites

- **Docker Desktop** (daemon running)
- **Python 3.11+** (optional for running locally without Docker)
- For Google Sheets:
  1. Create a **Service Account** in Google Cloud
  2. Download `credentials.json` to repo root
  3. Share Sheets with the service account email:
     - Source (read): **Viewer**
     - Destination (write): **Editor**

---

## Configuration

Copy the template and fill in values:

```bash
cp .env.example .env
```

Key vars:

- `CONNECTOR` = `randomuser` | `sheets`
- **Random User**: `RANDOMUSER_RESULTS`, `RANDOMUSER_PAGES`, `RANDOMUSER_SEED`, `RANDOMUSER_NAT`
- **Sheets (read)**: `GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json`, `SHEET_URL_OR_ID`, `SHEET_TAB`
- **Sheets (write)**: `UPLOAD_SHEET_URL_OR_ID`, `UPLOAD_SHEET_TAB`
- **HTTP uploader**: `UPLOAD_URL`, `CHUNK_SIZE`
- **CSV uploader**: `OUTPUT_PATH` (default `/app/out/customers.csv`)

> Keep `credentials.json` **out of Git**. It’s mounted into the container by scripts.

---

## Build

```bash
docker build -t meiro-connector .
./scripts/healthcheck.sh
```

---

## Run Demos (Docker)

1) **RandomUser → HTTP receiver** (writes `./out/ingested.jsonl`)

```bash
./scripts/run_randomuser_http.sh
# Re-run to append more. Stop receiver with: docker stop ingest-receiver
```

2) **Google Sheets (read) → Google Sheets (write)**

```bash
# Requires .env + credentials.json and sheet sharing
./scripts/run_sheets_to_sheets.sh
```

---

## Tests

### Locally (Python)

```bash
# Unit tests (default via pytest.ini)
pytest -q

# Specific integration tests (by file path)
pytest -q tests/integration/test_http_upload.py
pytest -q tests/integration/test_gsheets_read.py       # needs creds + env
pytest -q tests/integration/test_gsheets_write.py      # needs creds + env
pytest -q tests/integration/test_random_user_fetch.py  # network
```

### In Docker

```bash
./scripts/run_unit_tests.sh
./scripts/run_integration_tests.sh
```

### In GitHub Actions

- Workflow: `.github/workflows/ci.yml`
- Runs **unit** + **HTTP integration** by default
- Optional **Sheets** jobs run when repo secrets are present:
  - `GCP_SA_JSON`, `SHEET_URL_OR_ID`, `UPLOAD_SHEET_URL_OR_ID` (+ optional tabs)
- Optional **RandomUser** job toggled via repo variable `RUN_RANDOMUSER_INTEGRATION='1'`

---

## Design Notes

- **Retries** (Tenacity)
  - Reads: retry on timeouts / 429 / 5xx
  - Writes: conservative retry policy (avoid duplicate effects)
- **Idempotency & Traceability**
  - Pipeline adds `batch_id` + `ingested_at` per run
  - For true idempotency, a server-side key would be used (out of scope for demo)
- **Least Privilege**
  - Read scope: `spreadsheets.readonly`
  - Write scope: `spreadsheets`
- **FastAPI Receiver**
  - `POST /ingest` writes JSONL
  - Override output path locally: `INGEST_OUT=/path/to/ingested.jsonl`
  - Docker scripts bind `./out` to `/data` and set `INGEST_OUT=/data/ingested.jsonl`

---

## Troubleshooting

- **Port already in use**: change `PORT` in `run_randomuser_http.sh` (default `8010`)
- **No rows written**: check the receiver logs and that `INGEST_OUT` points to a mounted path
- **Sheets auth errors**: verify `credentials.json` path inside container (`/app/credentials.json`) and sharing permissions
- **Missing image warnings**: run `docker build -t meiro-connector .` again after code changes

