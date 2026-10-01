from core.email_service import EmailService
from celery import shared_task
from core.logger.logger_client import get_logger


logger = get_logger(__name__)

email_service = EmailService()


@shared_task
def send_welcome_email(email:str, values:dict={}):
    logger.info("Sending welcome email.... ")
    template_name = "authentication/email/welcome_email.html"
    result = email_service.send_email(email=email, values=values, subject="Welcome to B-Social", template_name=template_name)

    if result:
        logger.info("Welcome email sent successfully")
    else:
        logger.info("Welcome email not sent")


@shared_task
def send_otp_email(email:str, values:dict={}):
    logger.info("Sending OTP email.... ")
    template_name = "authentication/email/otp_email.html"

    result = email_service.send_email(email=email, values=values, subject="OTP", template_name=template_name)

    if result:
            logger.info("OTP email sent successfully")
    else:
        logger.info("OTP email not sent")

    