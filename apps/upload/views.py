from core.response import APIErrorResponseHandler, APISuccessResponseHandler
from .service import UploadService
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


upload_service = UploadService()
api_error_response_handler = APIErrorResponseHandler()
api_success_response_handler = APISuccessResponseHandler()


class UploadMediaFileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        result, error = upload_service.start_upload(request.data, request.user)
        if error:
            return api_error_response_handler.error(
                error=error.get("error"), 
                message=error.get("message"), 
                status_code=error.get("status_code"),
            )

        return api_success_response_handler.success(
                message=result.get("message"), 
                status_code=result.get("status_code"),
                data = result.get("data")
            )


class WebhookCallbackView(APIView):

    def post(self, request):
        result, _ = upload_service.validate_webhook_result(request.header, request.body)

        return api_success_response_handler.success(
            status_code=result.get("status_code"),
        )
