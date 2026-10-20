from .celery import app as celery_app
from . import cloudinary_config 
 
__all__ = ("celery_app",)
