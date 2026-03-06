from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "psych_rag",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.ingestion_worker",
        "app.workers.research_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    "research-agent-monday": {
        "task": "app.workers.research_worker.run_research_agent",
        "schedule": crontab(day_of_week="monday", hour=2, minute=0),
    },
    "research-agent-thursday": {
        "task": "app.workers.research_worker.run_research_agent",
        "schedule": crontab(day_of_week="thursday", hour=2, minute=0),
    },
}
