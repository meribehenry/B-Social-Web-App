import contextvars

current_request = contextvars.ContextVar("current_request", default=None)
current_request_id = contextvars.ContextVar("current_request_id", default='-')