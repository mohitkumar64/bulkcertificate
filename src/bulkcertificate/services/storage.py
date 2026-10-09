"""File storage — isolated so S3 could replace this later."""

from pathlib import Path

from bulkcertificate.config import STORAGE_PATH


def _get_base_jobs_dir() -> Path:
    """Return the absolute path to the base jobs storage directory."""
    path = Path(STORAGE_PATH).resolve() / "jobs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_certificate_pdf(job_id: str, filename: str, pdf_bytes: bytes):
    """Write PDF bytes to the job's storage directory."""
    base_jobs_dir = _get_base_jobs_dir()
    job_dir = (base_jobs_dir / job_id).resolve()

    # Ensure job_dir is inside base_jobs_dir
    job_dir.relative_to(base_jobs_dir)
    job_dir.mkdir(parents=True, exist_ok=True)

    filepath = (job_dir / filename).resolve()
    # Ensure filepath is inside job_dir
    filepath.relative_to(job_dir)

    filepath.write_bytes(pdf_bytes)


def get_certificate_path(job_id: str, filename: str) -> Path | None:
    """Return the resolved path to a certificate file, or None if invalid or missing."""
    base_jobs_dir = _get_base_jobs_dir()
    job_dir = (base_jobs_dir / job_id).resolve()

    # Path-traversal protection on job_id
    try:
        job_dir.relative_to(base_jobs_dir)
    except ValueError:
        return None

    if not job_dir.is_dir():
        return None

    filepath = (job_dir / filename).resolve()

    # Path-traversal protection on filename
    try:
        filepath.relative_to(job_dir)
    except ValueError:
        return None

    if not filepath.is_file():
        return None

    return filepath


def list_certificate_files(job_id: str) -> list[str]:
    """List all PDF filenames stored for a job."""
    base_jobs_dir = _get_base_jobs_dir()
    job_dir = (base_jobs_dir / job_id).resolve()

    try:
        job_dir.relative_to(base_jobs_dir)
    except ValueError:
        return []

    if not job_dir.is_dir():
        return []

    return sorted(f.name for f in job_dir.iterdir() if f.suffix == ".pdf")
