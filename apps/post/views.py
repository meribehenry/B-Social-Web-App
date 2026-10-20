from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Post
from .service import PostService
from rest_framework import generics
from .serializer import PostSerializer
from core.response import APIErrorResponseHandler, APISuccessResponseHandler


api_success_response = APISuccessResponseHandler()
api_error_response = APIErrorResponseHandler()


class CreatePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        post_service = PostService()
        result, error = post_service.create_post(request.data, request.user)

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


class EditPostView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        post_id = kwargs.get("pk")
        post_service = PostService()

        result, error = post_service.edit_post(post_id, request.data, request.user)
  
        if error:
            return api_error_response.error(
                message=error.get("message"),
                error=error.get("message"),
                status_code=error.get("status")
            )

        return api_success_response.success(
            message=result.get("message"),
            data=result.get("data"),
            status_code=result.get("status")
        )


class ViewPostView(generics.RetrieveAPIView):
    # permission_classes = [IsAuthenticated]

    queryset = Post.objects.defer("batch_id").select_related("author").prefetch_related("medias", "tags").all()
    serializer_class = PostSerializer


class ViewPostsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    
    queryset = Post.objects.defer("batch_id").select_related("author").prefetch_related("medias", "tags").all()
    serializer_class = PostSerializer


class DeletePostView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        post_id = kwargs.get("pk")
        post_service = PostService()
        
        result, error = post_service.delete_post(post_id, request.user)
        if error:
            return api_error_response.error(
                message=error.get("message"),
                error=error.get("message"),
                status_code=error.get("status")
            )

        return api_success_response.success(
            message=result.get("message"),
            data=result.get("data"),
            status_code=result.get("status")
        )


class CreateListPostDispatcherView(APIView):

    def get(self, request, *args, **kwargs):
        return ViewPostsView.as_view()(request._request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return CreatePostView.as_view()(request._request, *args, **kwargs)


class ViewEditDeletePostDispatcherView(APIView):

    def get(self, request, *args, **kwargs):
        print(f"KWARGS: {kwargs}")
        view = ViewPostView.as_view()
        return view(request._request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        view = EditPostView.as_view()
        return view(request._request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        print(f"KWARGS: {kwargs}")
        view = DeletePostView.as_view()
        return view(request._request, *args, **kwargs)



# class DeletePostView(generics.DestroyAPIView):
#     permission_classes = [IsAuthenticated]

#     queryset = Post.objects.defer("batch_id").select_related("author").prefetch_related("medias", "tags").all()
#     serializer_class = PostSerializer

#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()
#         self.perform_destroy(instance)
#         return Response(
#             {"message": "Post deleted successfully"},
#             status=status.HTTP_200_OK   # or 204 if you prefer
#         )