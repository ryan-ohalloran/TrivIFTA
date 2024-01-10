# TrivIFTA/celery.py

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TrivIFTA.settings")

app = Celery("TrivIFTA")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.timezone = 'America/Chicago'

# Load task submodules from all registered Django app configs
app.autodiscover_tasks()