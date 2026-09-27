from .base import *  
import os


DEBUG = True
ALLOWED_HOSTS = ["*"]
 

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
CORS_ALLOW_ALL_ORIGINS = True
 
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", default="redis://redis:6379/0")

 
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = ["127.0.0.1"]
 

