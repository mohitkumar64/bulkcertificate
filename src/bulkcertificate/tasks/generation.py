"""Background task for bulk certificate generation."""

import logging
from pathlib import Path

from bulkcertificate.celery_app import celery_app
from bulkcertificate.config import TEMPLATE_PATH
from bulkcertificate.db.database import get_session_factory
from bulkcertificate.db.queries import (
    get_job,
    set_job_completed,
    set_job_completed_with_errors,
    set_job_failed,
    set_job_processing,
    update_job_progress,
)
from bulkcertificate.services.certificate_generator import generate_certificate
from bulkcertificate.services.storage import save_certificate_pdf

logger = logging.getLogger(__name__)


def _create_session():
    """Create a new database session."""
    session_factory = get_session_factory()
    return session_factory()


def _format_certificate_filename(index: int) -> str:
    """Return standardised certificate filename, e.g. certificate-001.pdf."""
    return f"certificate-{index:03d}.pdf"


def _generate_single_recipient_certificate(template_path: Path, recipient: dict) -> bytes:
    """Generate PDF bytes for a single recipient."""
    recipient_name = recipient.get("name", "") if isinstance(recipient, dict) else str(recipient)
    fields = {
        "text1": recipient_name,
    }
    return generate_certificate(template_path, fields)


@celery_app.task(name="bulkcertificate.tasks.generation.process_generation_job")
def process_generation_job(job_id: str) -> dict:
    """Celery task: process all certificate generations for a job.

    Workflow:
    1. Load job from DB and mark as PROCESSING (short transaction).
    2. Check certificate template existence.
    3. Loop through recipients sequentially:
       - Generate certificate PDF in memory.
       - Save to storage/jobs/{job_id}/certificate-{index:03d}.pdf.
       - Isolate single recipient failures (try/except per recipient).
       - Persist progress counters after every recipient (short transaction).
    4. Set final status: COMPLETED or COMPLETED_WITH_ERRORS.
    5. Handle unrecoverable job-level errors -> FAILED.
    """
    logger.info("Starting certificate generation job: %s", job_id)

    # 1. Load job and set to PROCESSING
    session = _create_session()
    try:
        job = get_job(session, job_id)
        if job is None:
            logger.error("Job %s not found in database", job_id)
            return {"job_id": job_id, "status": "NOT_FOUND"}

        recipients = list(job.recipients or [])
        total_count = job.total_count

        set_job_processing(session, job_id)
    except Exception as exc:
        logger.exception("Failed to initialize job %s: %s", job_id, exc)
        try:
            set_job_failed(session, job_id, str(exc))
        except Exception:
            pass
        return {"job_id": job_id, "status": "FAILED", "error": str(exc)}
    finally:
        session.close()

    # 2. Check template existence
    template_path = Path(TEMPLATE_PATH)
    if not template_path.exists():
        error_msg = f"Certificate template not found at {template_path}"
        logger.error(error_msg)
        session = _create_session()
        try:
            set_job_failed(session, job_id, error_msg)
        finally:
            session.close()
        return {"job_id": job_id, "status": "FAILED", "error": error_msg}

    # 3. Process recipients sequentially
    processed_count = 0
    successful_count = 0
    failed_count = 0

    try:
        for idx, recipient in enumerate(recipients, start=1):
            filename = _format_certificate_filename(idx)
            try:
                pdf_bytes = _generate_single_recipient_certificate(template_path, recipient)
                save_certificate_pdf(job_id, filename, pdf_bytes)
                successful_count += 1
            except Exception as exc:
                logger.warning(
                    "Recipient generation failed for job %s, recipient #%d (%s): %s",
                    job_id,
                    idx,
                    recipient,
                    exc,
                )
                failed_count += 1

            processed_count += 1

            # Persist progress after each certificate (short transaction)
            session = _create_session()
            try:
                update_job_progress(
                    session,
                    job_id=job_id,
                    processed_count=processed_count,
                    successful_count=successful_count,
                    failed_count=failed_count,
                )
            finally:
                session.close()

        # 4. Set final status
        session = _create_session()
        try:
            if failed_count == 0:
                set_job_completed(session, job_id)
                final_status = "COMPLETED"
            else:
                set_job_completed_with_errors(session, job_id)
                final_status = "COMPLETED_WITH_ERRORS"
        finally:
            session.close()

        logger.info(
            "Finished job %s with status %s (success=%d, failed=%d, total=%d)",
            job_id,
            final_status,
            successful_count,
            failed_count,
            total_count,
        )

        return {
            "job_id": job_id,
            "status": final_status,
            "total_count": total_count,
            "processed_count": processed_count,
            "successful_count": successful_count,
            "failed_count": failed_count,
        }

    except Exception as exc:
        logger.exception("Unrecoverable failure in job %s: %s", job_id, exc)
        session = _create_session()
        try:
            set_job_failed(session, job_id, str(exc))
        finally:
            session.close()
        return {"job_id": job_id, "status": "FAILED", "error": str(exc)}
