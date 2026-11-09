from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Comment
from .service import CommentReplyService
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
        result, error = CommentReplyService().create_comment_or_reply(request.data, request.user, post_id=post_id)

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


class EditCommentReplyView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [throttle.EditCommentTokenBucketThrottle]

    def patch(self, request, *args, **kwargs):
        comment_id = kwargs.get("pk")
        result, error = CommentReplyService().edit_comment_or_reply(comment_id, request.data, request.user) #type: ignore
  
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


class ViewCommentReplyView(generics.RetrieveAPIView):
    queryset = Comment.objects.select_related("author").all()
    serializer_class = CommentSerializer


class ViewCommentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        post_id = kwargs.get("pk")
        result, error = CommentReplyService().view_comments_or_reply(request, current_view_instance=self, post_id=post_id)

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


class DeleteCommentReplyView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        comment_id = kwargs.get("pk")
        
        result, error = CommentReplyService().delete_comment_or_reply(comment_id, request.user)
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


class ViewEditDeleteCommentDispatcherView(APIView):

    def get(self, request, *args, **kwargs):
        view = ViewCommentReplyView.as_view()
        return view(request._request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        view = EditCommentReplyView.as_view()
        return view(request._request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        view = DeleteCommentReplyView.as_view()
        return view(request._request, *args, **kwargs)


""" -------------- THIS IS FOR REPLY SPECIFIC VIEW --------------- """

class CreateReplyView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [throttle.CreateCommentTokenBucketThrottle]

    def post(self, request, *args, **kwargs):
        comment_id = kwargs.get("pk")
        result, error = CommentReplyService().create_comment_or_reply(request.data, request.user, parent_comment_id=comment_id)

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


class ViewRepliesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        comment_id = kwargs.get("pk")
        result, error = CommentReplyService().view_comments_or_reply(request, current_view_instance=self, parent_comment_id=comment_id)

        if error:
            return api_error_response.error(
                message=error.get("message"),
                error=error.get("error"),
                status_code=error.get("status_code")
            )

        return api_success_response.success(
            message=result.get("message"),
            data=result.get("data"),
            status_code=result.get("status_code"),
            pagination=result.get("pagination")
        )


class CreateListCommentDispatcherView(APIView):

    def get(self, request, *args, **kwargs):
        return ViewCommentsView.as_view()(request._request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return CreateCommentView.as_view()(request._request, *args, **kwargs)


class CreateListReplyDispatcherView(APIView):

    def get(self, request, *args, **kwargs):
        return ViewRepliesView.as_view()(request._request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return CreateReplyView.as_view()(request._request, *args, **kwargs)