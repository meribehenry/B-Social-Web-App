from pythonjsonlogger import jsonlogger
import logging
import sys


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Define standard attributes you want to structure into the JSON
    log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
    formatter = jsonlogger.JsonFormatter(log_format) #
   
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

