"""Plain functions for job CRUD — no repository classes."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from bulkcertificate.models.job import (
    GenerationJob,
    STATUS_PENDING,
    STATUS_PROCESSING,
    STATUS_COMPLETED,
    STATUS_COMPLETED_WITH_ERRORS,
    STATUS_FAILED,
)


def _utcnow():
    return datetime.now(timezone.utc)


# ---------- create ----------

def create_job(db: Session, event_name: str, issue_date, recipients: list[dict]) -> GenerationJob:
    """Create a new generation job in PENDING status and commit."""
    from datetime import date

    parsed_date = issue_date
    if isinstance(issue_date, str):
        parsed_date = date.fromisoformat(issue_date)

    job = GenerationJob(
        event_name=event_name,
        issue_date=parsed_date,
        recipients=recipients,
        status=STATUS_PENDING,
        total_count=len(recipients),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


# ---------- read ----------

def get_job(db: Session, job_id: str) -> GenerationJob | None:
    """Return a job by ID or None."""
    return db.query(GenerationJob).filter(GenerationJob.id == job_id).first()


# ---------- status updates ----------

def set_job_processing(db: Session, job_id: str):
    """Mark job as PROCESSING and record start time."""
    db.query(GenerationJob).filter(GenerationJob.id == job_id).update({
        "status": STATUS_PROCESSING,
        "started_at": _utcnow(),
    })
    db.commit()


def set_job_completed(db: Session, job_id: str):
    """Mark job as COMPLETED."""
    db.query(GenerationJob).filter(GenerationJob.id == job_id).update({
        "status": STATUS_COMPLETED,
        "completed_at": _utcnow(),
    })
    db.commit()


def set_job_completed_with_errors(db: Session, job_id: str):
    """Mark job as COMPLETED_WITH_ERRORS."""
    db.query(GenerationJob).filter(GenerationJob.id == job_id).update({
        "status": STATUS_COMPLETED_WITH_ERRORS,
        "completed_at": _utcnow(),
    })
    db.commit()


def set_job_failed(db: Session, job_id: str, error_message: str):
    """Mark job as FAILED with an error message."""
    db.query(GenerationJob).filter(GenerationJob.id == job_id).update({
        "status": STATUS_FAILED,
        "error_message": error_message,
        "completed_at": _utcnow(),
    })
    db.commit()


# ---------- progress ----------

def update_job_progress(
    db: Session,
    job_id: str,
    processed_count: int,
    successful_count: int,
    failed_count: int,
):
    """Persist current progress counters. Short transaction per Section 15."""
    db.query(GenerationJob).filter(GenerationJob.id == job_id).update({
        "processed_count": processed_count,
        "successful_count": successful_count,
        "failed_count": failed_count,
    })
    db.commit()
