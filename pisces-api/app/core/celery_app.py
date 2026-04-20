"""Celery application instance and configuration."""

from __future__ import annotations

import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

_BROKER_URL = os.getenv("CELERY_BROKER_URL", "sqla+sqlite:///./pisces.db")
_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "db+sqlite:///./pisces.db")

celery_app = Celery("pisces")

celery_app.conf.update(
    broker_url=_BROKER_URL,
    result_backend=_RESULT_BACKEND,
    # Serialisation — never use pickle
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Reliability
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Time limits: translation can take a long time
    task_time_limit=2400,       # 40 min hard limit
    task_soft_time_limit=1800,  # 30 min soft limit
    # Results
    result_expires=86400,  # keep results for 24 h
    # Task discovery
    imports=["app.tasks.translation_tasks"],
)
