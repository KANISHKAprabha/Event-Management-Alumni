import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alumin_event.settings")

app = Celery("alumin_event")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()  # It'll find tasks.py inside installed apps
