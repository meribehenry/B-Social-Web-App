from .context import current_request, current_request_id  
from .logger_client import get_logger
import time
import uuid


logger = get_logger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # BEFORE
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.request_id = request_id
        request.start_time = time.time()

        # SET it in contextvars so everyone can read it
        token_req = current_request.set(request)
        token_id = current_request_id.set(request_id)

        logger.info(
            "Request Starting",
            extra={
                "request_id": request_id,
                "path": request.path,
                "method": request.method,
            }
        )

        response = self.get_response(request)

        # AFTER - your existing logic
        duration_ms = (time.time() - request.start_time) * 1000
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "path": request.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
        )
        response["X-Request-ID"] = request_id
           
        # CLEAN UP - very important
        current_request.reset(token_req)
        current_request_id.reset(token_id)

        return response