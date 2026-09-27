from celery import Celery
from celery.signals import worker_process_init, task_postrun
from django.db import close_old_connections
import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
 
app = Celery("b-social")
app.config_from_object("django.conf:settings.base", namespace="CELERY")
app.autodiscover_tasks()   # finds tasks.py inside every INSTALLED_APPS entry


@worker_process_init.connect
def on_worker_init(**kwargs):
    # Each forked worker closes any inherited connection
    # and will create a fresh one on first DB query
    close_old_connections()
    print("Worker forked - old DB connection closed, will reconnect fresh")

@task_postrun.connect
def on_task_end(**kwargs):
    # After every task, close the connection so it goes back to pool
    # Prevents leak if a task forgets to close
    close_old_connections()
