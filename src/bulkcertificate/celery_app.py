"""Celery application configuration."""

from celery import Celery

from bulkcertificate.config import CELERY_WORKER_CONCURRENCY, REDIS_URL


def create_celery_app() -> Celery:
    """Create and configure the Celery application."""
    backend = REDIS_URL if REDIS_URL.startswith("redis") else None
    app = Celery(
        "bulkcertificate",
        broker=REDIS_URL,
        backend=backend,
        include=["bulkcertificate.tasks.generation"],
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        worker_concurrency=CELERY_WORKER_CONCURRENCY,
        broker_connection_retry_on_startup=False,
        broker_connection_max_retries=1,
    )
    return app


celery_app = create_celery_app()
