"""Pydantic schemas for job creation requests and responses."""

from datetime import date
from pydantic import BaseModel, Field, EmailStr, field_validator


MAX_RECIPIENTS = 500


# ---------- request schemas ----------

class RecipientSchema(BaseModel):
    name: str = Field(..., min_length=1, description="Recipient's full name")
    email: EmailStr = Field(..., description="Recipient's email address")


class CreateJobRequest(BaseModel):
    event_name: str = Field(..., min_length=1, description="Event or workshop name")
    issue_date: date = Field(..., description="Certificate issue date (YYYY-MM-DD)")
    recipients: list[RecipientSchema] = Field(
        ..., min_length=1, max_length=MAX_RECIPIENTS,
        description=f"List of recipients (1–{MAX_RECIPIENTS})",
    )


# ---------- response schemas ----------

class CreateJobResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    event_name: str
    issue_date: date
    total_count: int
    processed_count: int
    successful_count: int
    failed_count: int
    progress: float
    error_message: str | None = None
