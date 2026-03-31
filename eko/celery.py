"""Celery application configuration for the EKO project."""

import logging
import os

from celery import Celery

logger = logging.getLogger(__name__)

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eko.settings')

# Create Celery app
app = Celery('eko')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for verifying Celery is working."""
    logger.debug('Request: %r', self.request)
