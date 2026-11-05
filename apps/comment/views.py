from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Comment
from .service import CommentService
from rest_framework import generics
from .serializer import CommentSerializer
from core.response import APIErrorResponseHandler, APISuccessResponseHandler
from . import throttle



api_success_response = APISuccessResponseHandler()
api_error_response = APIErrorResponseHandler()


class CreateCommentView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [throttle.CreateCommentTokenBucketThrottle]

    def post(self, request, *args, **kwargs):
        post_id = kwargs.get("pk")
        result, error = CommentService().create_comment(post_id, request.data, request.user)

        if error:
            return api_error_response.error(
                message=error.get("message"),
                error=error.get("error"),
                status_code=error.get("status_code")
            )

        return api_success_response.success(
            message=result.get("message"),
            data=result.get("data"),
            status_code=result.get("status_code")
        )


class EditCommentView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [throttle.EditCommentTokenBucketThrottle]

    def patch(self, request, *args, **kwargs):
        comment_id = kwargs.get("pk")
        result, error = CommentService().edit_comment(comment_id, request.data, request.user)
  
        if error:
            return api_error_response.error(
                message=error.get("message"),
                error=error.get("error"),
                status_code=error.get("status_code")
            )

        return api_success_response.success(
            message=result.get("message"),
            data=result.get("data"),
            status_code=result.get("status_code")
        )


class ViewCommentView(generics.RetrieveAPIView):
    queryset = Comment.objects.select_related("author").all()
    serializer_class = CommentSerializer


class ViewCommentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        post_id = kwargs.get("pk")
        result, error = CommentService().view_comments(request, post_id, current_view_instance=self)

        if error:
            return api_error_response.error(
                message=error.get("message"),
                error=error.get("error"),
                status_code=error.get("status_code")
            )

        return api_success_response.success(
            message=result.get("message"),
            data=result.get("data"),
            status_code=result.get("status_code")
        )


class DeleteCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        comment_id = kwargs.get("pk")
        
        result, error = CommentService().delete_comment(comment_id, request.user)
        if error:
            return api_error_response.error(
                message=error.get("message"),
                error=error.get("error"),
                status_code=error.get("status_code")
            )

        return api_success_response.success(
            message=result.get("message"),
            data=result.get("data"),
            status_code=result.get("status_code")
        )


class CreateListCommentDispatcherView(APIView):

    def get(self, request, *args, **kwargs):
        return ViewCommentsView.as_view()(request._request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return CreateCommentView.as_view()(request._request, *args, **kwargs)


class ViewEditDeleteCommentDispatcherView(APIView):

    def get(self, request, *args, **kwargs):
        view = ViewCommentView.as_view()
        return view(request._request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        view = EditCommentView.as_view()
        return view(request._request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        view = DeleteCommentView.as_view()
        return view(request._request, *args, **kwargs)