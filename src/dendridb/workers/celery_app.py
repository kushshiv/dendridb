from celery import Celery

from dendridb.config import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()
    app = Celery("dendridb", include=["dendridb.workers.tasks"])
    app.conf.update(
        broker_url=settings.broker_url,
        result_backend=settings.result_backend_url,
        task_always_eager=settings.celery_task_always_eager,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
    )
    app.autodiscover_tasks(["dendridb.workers.tasks"])
    return app


celery_app = create_celery_app()
