"""generation_jobs table — stores job metadata and recipient payload."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text, DateTime, Date, JSON
from bulkcertificate.db.database import Base


# ---------- helpers ----------

def _utcnow():
    return datetime.now(timezone.utc)


def _new_id():
    return str(uuid.uuid4())


# ---------- status constants ----------

STATUS_PENDING = "PENDING"
STATUS_PROCESSING = "PROCESSING"
STATUS_COMPLETED = "COMPLETED"
STATUS_COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
STATUS_FAILED = "FAILED"


# ---------- table ----------

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String, primary_key=True, default=_new_id)
    event_name = Column(String, nullable=False)
    issue_date = Column(Date, nullable=False)
    recipients = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default=STATUS_PENDING)
    total_count = Column(Integer, nullable=False)
    processed_count = Column(Integer, nullable=False, default=0)
    successful_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
