from pythonjsonlogger import jsonlogger
from .filter import RequestFilter
import logging
import sys


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Define standard attributes you want to structure into the JSON
    log_format = "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_email)s %(user_id)s %(ip)s %(path)s %(duration_in_ms)s"
    formatter = jsonlogger.JsonFormatter(log_format)
    formatter = jsonlogger.JsonFormatter(log_format) #
   
    handler.setFormatter(formatter)
    handler.addFilter(RequestFilter())

    logger.addHandler(handler)

    return logger

