from core.email_service import EmailService
from celery import shared_task
from core.logger.logger_client import get_logger
from django.contrib.auth import get_user_model


logger = get_logger(__name__)

email_service = EmailService()



@shared_task(bind=True, retry_backoff=2, retry_backoff_max=300, retry_jitter=True, max_retries=5)
def send_welcome_email(self, email:str, *args, **kwargs):
    logger.info("Sending welcome email.... ")

    template_name = "authentication/email/welcome_email.html"

    User = get_user_model()
    user = User.objects.select_related("profile").filter(email=email).first()

    if not user or user.has_received_welcome_email: return

    values = {
        "display_name": user.profile.display_name,
        "username": user.username
    }

    try:
        email_service.send_email(email=email, values=values, subject="Welcome to B-Social", template_name=template_name)
        logger.info("Welcome email sent successfully")

    except Exception as exc:
        retries_left = self.max_retries - self.request.retries # type: ignore
        logger.info(f"Retrying send_welcome_email {retries_left} left")
        raise self.retry(exc=exc)



@shared_task(bind=True, retry_backoff=2, retry_backoff_max=300, retry_jitter=True, max_retries=5)
def send_otp_email(self, email:str, values:dict={}, *args, **kwargs):
    logger.info("Sending OTP email.... ")

    template_name = "authentication/email/otp_email.html"

    try:
        email_service.send_email(email=email, values=values, subject="OTP", template_name=template_name)
        logger.info("OTP email sent successfully")

    except Exception as exc:
        retries_left = self.max_retries - self.request.retries  # type: ignore
        logger.info(f"Retrying send_welcome_email {retries_left} left")
        raise self.retry(exc=exc)

    
