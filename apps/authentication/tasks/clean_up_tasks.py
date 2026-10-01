from celery import shared_task
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta, timezone
from core.logger.logger_client import get_logger
from ..models import UserToken, RevokedAccessToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken 



User = get_user_model()

logger = get_logger(__name__)


@shared_task(name="apps.authentication.tasks.clean_up_tasks.delete_unverified_user")
def delete_unverified_user():
    passed_time = datetime.now(timezone.utc) -  timedelta(minutes=15)
    try:
        results = User.objects.filter(email_verified=False, date_joined__lt =passed_time  ).delete()
        logger.info(f"Deleted {results[0]} unverified user from the User table", extra={"time": datetime.now(timezone.utc)})
    except Exception as e:
        logger.error(f'Could not delete unverified user', extra={"time": datetime.now(timezone.utc), "trace": e})



@shared_task(name="apps.authentication.tasks.clean_up_tasks.delete_expired_otp_or_reset_token")
def delete_expired_otp_or_reset_token():
    current_time = datetime.now(timezone.utc)
    try:
        results = UserToken.objects.filter(expires_at__lt=current_time).delete()
        logger.info(
            f"Deleted {results[0]} expired OTP and Reset token from the UserToken table", 
            extra={
                "time": datetime.now(timezone.utc)
            }
        )
    except Exception as e:
            logger.error(f'Could not delete expired OTP and Reset token', extra={"time": datetime.now(timezone.utc), "trace": e})
    


@shared_task(name="apps.authentication.tasks.clean_up_tasks.delete_expired_access_token")
def delete_expired_access_token():
    current_time = datetime.now(timezone.utc)
    results = RevokedAccessToken.objects.filter(expires_at__lt=current_time ).delete()
    try:
        logger.info(
            f"Deleted {results[0]} expired revoked access token from the RevokedAccessToken table", 
            extra={
                "time": datetime.now(timezone.utc)
            }
    )
    except Exception as e:
        logger.error(f'Could not delete expired revoked access token', extra={"time": datetime.now(timezone.utc), "trace": e})



@shared_task(name="apps.authentication.tasks.clean_up_tasks.delete_expired_refresh_token")
def delete_expired_refresh_token():
    current_time = datetime.now(timezone.utc)
    try:
        results = OutstandingToken.objects.filter(expires_at__lt=current_time ).delete()
        logger.info(
            f"Deleted {results[0]} expired  refresh token from the OutstandingToken table", 
            extra={
                "time": datetime.now(timezone.utc)
            }
        )
    except Exception as e:
        logger.error(f'Could not delete expired refresh token', extra={"time": datetime.now(timezone.utc), "trace": e})
    