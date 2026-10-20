from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.user.service import ProfileService, UserService
from core.response import APIErrorResponseHandler, APISuccessResponseHandler


api_error_response_handler = APIErrorResponseHandler()
api_success_response_handler = APISuccessResponseHandler()


class GetUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        user_service = UserService()

        result, error = user_service.view_user(user_id, request.user)

        if error:
            return api_error_response_handler.error(
                message=error.get("message"),
                error=error.get("message"),
                status_code=error.get("status_code")
            )

        return api_success_response_handler.success(
            message=result.get("message"),
            data=result.get("data"),
            status_code=result.get("status_code")
        )
            

class ViewUserProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        profile_service = ProfileService()

        result, error = profile_service.view_profile(user_id)

        if error:
            return api_error_response_handler.error(
                message=error.get("message"),
                error=error.get("message"),
                status_code=error.get("status")
            )

        return api_success_response_handler.success(
            message=result.get("message"),
            data=result.get("data"),
            status_code=result.get("status")
        )


class EditProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        
        user_id = kwargs.get("pk")
        profile_service = ProfileService()

        result, error = profile_service.edit_profile(user_id, request.data, request.user)
  
        if error:
            return api_error_response_handler.error(
                message=error.get("message"),
                error=error.get("message"),
                status_code=error.get("status_code")
            )

        return api_success_response_handler.success(
            message=result.get("message"),
            data=result.get("data"),
            status_code=result.get("status_code")
        )
    

class ViewEditProfileDispatcherView(APIView):

    def get(self, request, *args, **kwargs):
        view = ViewUserProfileView.as_view()
        return view(request._request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        view = EditProfileView.as_view()
        return view(request._request, *args, **kwargs)