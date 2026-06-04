from uuid import UUID

from celery import Celery

from app.config import get_settings
from app.db import get_sessionmaker
from app.models import BackgroundJob
from app.services.operations import process_notification_job

settings = get_settings()

celery_app = Celery(
    "ai_growth_ops",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    accept_content=["json"],
    enable_utc=True,
    result_serializer="json",
    task_serializer="json",
    timezone="UTC",
)


@celery_app.task(name="app.worker.healthcheck")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@celery_app.task(name="app.worker.process_notification_job")
def process_notification_job_task(job_id: str) -> dict[str, str]:
    session = get_sessionmaker()()
    try:
        job = session.get(BackgroundJob, UUID(job_id))
        if job is None:
            return {"status": "not_found", "job_id": job_id}
        notification, processed_job = process_notification_job(session, job=job)
        session.commit()
        return {
            "status": processed_job.status,
            "job_id": str(processed_job.id),
            "notification_id": str(notification.id),
            "notification_status": notification.status,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
