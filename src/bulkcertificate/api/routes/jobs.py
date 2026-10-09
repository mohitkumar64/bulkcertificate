"""API routes for certificate generation jobs."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from bulkcertificate.db.database import get_db
from bulkcertificate.db.queries import create_job, get_job
from bulkcertificate.schemas.job import (
    CreateJobRequest,
    CreateJobResponse,
    JobStatusResponse,
)

router = APIRouter(prefix="/api/v1/certificates", tags=["certificates"])


# ---------- POST — create job ----------

@router.post("/jobs", response_model=CreateJobResponse, status_code=202)
def create_generation_job(request: CreateJobRequest, db: Session = Depends(get_db)):
    """Accept a bulk certificate generation request.

    Returns 202 Accepted — actual generation happens in a background worker.
    """
    # Convert recipients to plain dicts for JSON storage
    recipients_data = [r.model_dump() for r in request.recipients]

    job = create_job(
        db,
        event_name=request.event_name,
        issue_date=request.issue_date,
        recipients=recipients_data,
    )

    # Enqueue background generation task
    try:
        from bulkcertificate.tasks.generation import process_generation_job

        process_generation_job.apply_async(args=[job.id], retry=False)
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning(
            "Could not enqueue Celery task for job %s (broker may be offline): %s",
            job.id,
            exc,
        )

    return CreateJobResponse(job_id=job.id, status=job.status)


# ---------- GET — job status ----------

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Return current status and progress of a generation job."""
    job = get_job(db, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    progress = 0.0
    if job.total_count > 0:
        progress = round(job.processed_count / job.total_count * 100, 1)

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        event_name=job.event_name,
        issue_date=job.issue_date,
        total_count=job.total_count,
        processed_count=job.processed_count,
        successful_count=job.successful_count,
        failed_count=job.failed_count,
        progress=progress,
        error_message=job.error_message,
    )


# ---------- GET — certificate retrieval ----------

@router.get("/jobs/{job_id}/files/{filename}")
def get_certificate_file(job_id: str, filename: str, db: Session = Depends(get_db)):
    """Retrieve a generated certificate PDF.

    Verifies the job exists and safely resolves the file path.
    Protects against path traversal.
    """
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    from bulkcertificate.services.storage import get_certificate_path
    from fastapi.responses import FileResponse

    file_path = get_certificate_path(job_id, filename)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Certificate file not found")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename,
    )

