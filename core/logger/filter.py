from .context import current_request, current_request_id
import logging
import time


SKIP_PATHS = {'/health', '/healthz', '/ready', '/live'}

class RequestFilter(logging.Filter):
    def filter(self, record):
        request = current_request.get()
        request_id = current_request_id.get()

        path = start_time = getattr(request, 'path', None)
        if path in SKIP_PATHS:
            # Skips health checks response from been logged
            return False
        
        if request:
            start_time = getattr(request, 'start_time', None)
            record.request_id = request_id
            record.user_email = getattr(request.user, 'email', 'Anonymous')
            record.user_id = getattr(request.user, 'id', 'Anonymous')
            record.ip = request.META.get('REMOTE_ADDR', '')
            record.path = request.path
            record.duration_in_ms = round((time.time() - start_time) * 1000, 2) if start_time else '-'

        else:
            record.request_id = '-'
            record.user = '-'
            record.ip = '-'
            record.path = '-'
        return True