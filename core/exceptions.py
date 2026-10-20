from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.db.utils import OperationalError
from .logger.logger_client import get_logger


logger = get_logger(__name__)



def custom_exception_handler(exc, context):
    """
    Custom exception handler
    """
    response = exception_handler(exc, context)

    if response is not None:
        return response


    if isinstance(exc, OperationalError):
            logger.error("Database temporarily unavailable")
            return Response(
            {
                "detail": "Database temporarily unavailable. Please try again later"
            }, 
            status = status.HTTP_503_SERVICE_UNAVAILABLE
        )
    

    logger.error("An unexpected server error occurred")
    return Response(
        {
            "detail": f"An unexpected server error occurred {exc} {context}"
        }, 
        status = status.HTTP_500_INTERNAL_SERVER_ERROR
    )