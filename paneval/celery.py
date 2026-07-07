"""Celery."""
import datetime
import os

from celery import Celery
from celery.schedules import crontab

from django.conf import settings
import sys
from datetime import timedelta

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paneval.settings')

app = Celery('paneval')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        30.0,
        app.signature('paneval.apps.evaluation.tasks.init_ssh_executor'),
        name='init_ssh_executor'
    )
