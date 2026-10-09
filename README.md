# Bulk Certificate Generator

A high-performance, asynchronous bulk certificate generation backend built with **FastAPI**, **SQLite + SQLAlchemy**, **Celery + Redis**, and **ReportLab + svglib**.

---

## 1. Architecture Overview

```text
Client
  │
  │ POST /api/v1/certificates/jobs
  ▼
FastAPI
  │  (Validates with Pydantic & creates job in SQLite)
  ▼
SQLite (Metadata & Progress Source of Truth)
  │
  │ Enqueues job_id
  ▼
Redis (Celery Message Broker)
  │
  ├─────────────────────┬─────────────────────┐
  ▼                     ▼                     ▼
Worker 1              Worker 2              Worker 3
(Concurrency: 3)
  │
  ▼
process_generation_job(job_id)
  │
  ▼
Certificate Generator (Immutable SVG -> Memory XML -> PDF bytes)
  │
  ▼
Filesystem Storage: storage/jobs/{job_id}/certificate-{index:03d}.pdf
  │
  ▼
FastAPI Retrieval: GET /api/v1/certificates/jobs/{job_id}/files/{filename}
```

### Key Design Decisions & Invariants


1. **Whole-Job Task Boundary**: The Celery task boundary is the entire generation job (e.g. 500 certificates), executed sequentially within the assigned worker. This keeps progress tracking, rate-limiting, and error handling clean.
2. **Short SQLite Transactions**: Database transactions are never held open while rendering PDFs or writing files. Every DB update is a short write + commit + close.
3. **Immutable SVG Template**: The source template (`src/bulkcertificate/templates/certificate.svg`) is never mutated on disk. Dynamic values are replaced in memory via XML element IDs and converted to PDF bytes via `svglib` + `ReportLab`.
4. **Failure Isolation**: A rendering failure for one recipient does not stop other recipients. Individual failures are caught, logged, and increment `failed_count`, setting the final status to `COMPLETED_WITH_ERRORS`.
5. **Progress Invariants**:
   $$\text{processed\_count} = \text{successful\_count} + \text{failed\_count}$$
   $$\text{processed\_count} \le \text{total\_count}$$
6. **Strict Path-Traversal Protection**: File retrieval validates path relativity against the base job storage directory using `Path.relative_to()`.

---

## 2. API Endpoints

### 1. Health Check
- **Endpoint**: `GET /api/v1/health`
- **Response**: `200 OK`
  ```json
  { "status": "ok" }
  ```

### 2. Create Bulk Certificate Job
- **Endpoint**: `POST /api/v1/certificates/jobs`
- **Status**: `202 Accepted`
- **Request Body**:
  ```json
  {
    "event_name": "Python Workshop 2026",
    "issue_date": "2026-10-08",
    "recipients": [
      {
        "name": "Mohit Kumar",
        "email": "mohit@example.com"
      },
      {
        "name": "Rahul Sharma",
        "email": "rahul@example.com"
      }
    ]
  }
  ```
- **Response Body**:
  ```json
  {
    "job_id": "8c1e2f3a-...",
    "status": "PENDING"
  }
  ```

### 3. Check Job Status & Progress
- **Endpoint**: `GET /api/v1/certificates/jobs/{job_id}`
- **Response Body**:
  ```json
  {
    "job_id": "8c1e2f3a-...",
    "status": "COMPLETED",
    "event_name": "Python Workshop 2026",
    "issue_date": "2026-10-08",
    "total_count": 2,
    "processed_count": 2,
    "successful_count": 2,
    "failed_count": 0,
    "progress": 100.0,
    "error_message": null
  }
  ```

### 4. Retrieve Certificate PDF
- **Endpoint**: `GET /api/v1/certificates/jobs/{job_id}/files/{filename}`
- **Example**: `GET /api/v1/certificates/jobs/8c1e2f3a-.../files/certificate-001.pdf`
- **Response**: `200 OK` (binary PDF with `Content-Type: application/pdf`)

---

## 3. Quickstart with Docker Compose

To start the complete production stack (FastAPI + Celery Worker + Redis with shared storage and database):

```bash
docker compose up --build
```

Services:
- **API**: http://localhost:8000
- **Redis**: localhost:6379
- **Celery Worker**: 3 concurrent worker processes

To stop:
```bash
docker compose down
```

---

## 4. Local Development & Testing

### Installation via `uv`

```bash
cd bulkcertificate
uv sync
```

### Running Tests

Run the complete formal `pytest` test suite:

```bash
uv run pytest -v
```

All 19 test cases verify:
- Input validation (empty names, invalid emails, date parsing, recipient batch size limit $\le 500$)
- SVG field injection & PDF byte rendering
- Job lifecycle (`PENDING` -> `PROCESSING` -> `COMPLETED`)
- Progress updates & invariant validation
- Recipient failure isolation (`COMPLETED_WITH_ERRORS`)
- Path traversal rejection on file retrieval
- 404 handling on missing jobs and missing files

---

## 5. Configuration (Environment Variables)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/app.db` | SQLAlchemy connection URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Celery broker URL |
| `STORAGE_PATH` | `./storage` | Directory storing generated PDFs |
| `TEMPLATE_PATH` | `src/bulkcertificate/templates/certificate.svg` | Path to immutable SVG template |
| `CELERY_WORKER_CONCURRENCY` | `3` | Worker concurrency |
