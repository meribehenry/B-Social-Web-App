from rest_framework.renderers import JSONRenderer
from .logger.logger_client import get_logger

logger = get_logger(__name__)


class UniversalJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        status_code = renderer_context['response'].status_code
        is_success = status_code < 400

        # Standardized blueprint with separate error keys
        response_payload = {
            'status': 'success' if is_success else 'error',
            # 'message': None,
            # 'data': None,
            # 'error': None,
            # 'field_errors': None,
            # 'pagination': None
        }

        if is_success:
            # Case 1: Paginated View
            if isinstance(data, dict) and 'pagination' in data and 'results' in data:
                response_payload['data'] = data['results']
                response_payload['pagination'] = data['pagination']

            # Case 2: View explicitly passed a message/data/pagination dictionary
            elif isinstance(data, dict) and ('message' in data or 'data' in data or 'pagination' in data):
                response_payload['message'] = data.get('message')
                response_payload['data'] = data.get('data')
                response_payload['pagination'] = data.get('pagination')

            # Case 3: Standard unpaginated payload
            else:
                response_payload['data'] = data

        else:
            if isinstance(data, dict):
                if 'detail' in data:
                    # General DRF Error (401, 403, 404, 500)
                    response_payload['message'] = str(data['detail'])
                    response_payload['error'] = str(data['detail'])
                    
                    if 'data' in data:
                        response_payload['data'] = data.get('data')

                elif 'message' in data or "error" in data:
                    # Custom Error
                    response_payload['message'] = str(data['message'])
                    response_payload['error'] = str(data['error'])
                else:
                    # Serializer Field Validation Errors (400)
                    logger.info("Serializer error")
                    response_payload['message'] = "Validation failed."
                    response_payload['field_errors'] = data

            elif isinstance(data, list):
                # Top-level list errors
                logger.info("Serializer error")
                response_payload['message'] = "Validation failed."
                response_payload['field_errors'] = data
                
            else:
                # Raw text or unhandled exceptions
                response_payload['message'] = str(data)
                response_payload['error'] = str(data)

        return super().render(response_payload, accepted_media_type, renderer_context)