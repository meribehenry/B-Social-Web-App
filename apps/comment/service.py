from apps.comment.pagination import CommentCursorPagination
from apps.comment.serializer import CommentSerializer, CreateCommentSerializer
from apps.post.service import PostService
from datetime import datetime, timezone, timedelta
from .models import Comment
from core.response import ServiceResponseBuilder


Post = PostService().get_post_model()

class CommentService():
    def __init__(self):
        self.service_response_builder = ServiceResponseBuilder()
        self.error = {}
        self.result = {}
    
    def create_comment(self, post_id, data:dict, current_user):
        post = Post.objects.filter(id=post_id).first()

        if not post:
            self.error = self.service_response_builder.not_found_error(message="Post not found")
            return self.result, self.error 

        serializer = CreateCommentSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        content = serializer.validated_data.get("content")
            
        comment = Comment.objects.create(content=content, author=current_user, post=post)
        
        self.result = self.service_response_builder.result(message="Comment created successfully", 
                                                      data= CommentSerializer(comment).data,
                                                      status_code=201)

        return self.result, self.error
    
    def edit_comment(self, comment_id, data:dict, current_user):
        comment = Comment.objects.filter(id=comment_id).first()

        if not comment:
            self.error = self.service_response_builder.not_found_error(message="Comment not found")
            return self.result, self.error 

        if current_user != comment.author:
            self.error = self.service_response_builder.forbidden_error(message="You are not authorized to edit this comment")
            return self.result, self.error

        serializer = CreateCommentSerializer(data=data)
        serializer.is_valid()

        new_content = serializer.validated_data.get("content")

        if (comment.date_created.replace(tzinfo=timezone.utc) + timedelta(hours=48)) <= (datetime.now(timezone.utc)):
            self.error = self.service_response_builder.validation_error(message="Cannot edit comment after 48 hours")
            return self.result, self.error

        if not new_content or new_content == comment.content:
            self.error = self.service_response_builder.bad_request_error(message="Comment field cannot be empty or left the same")
            return self.result, self.error 
        
        comment.content = new_content
        comment.date_edited = datetime.now(timezone.utc)
        comment.save(update_fields=["content", "date_edited"])
        
        self.result = self.service_response_builder.result(message="Comment successfully updated", 
                                                      data= CommentSerializer(comment).data)
        
        return self.result, self.error
        
    
    def delete_comment(self, comment_id, current_user):
        comment = Comment.objects.filter(public_id=comment_id).first()
        
        if not comment:
            self.error = self.service_response_builder.not_found_error(message="Comment not found")
            return self.result, self.error 

        # if current_user != comment.author and current_user.role != "admin" and current_user.role != "moderator":
        #     self.error = self.service_response_builder.forbidden_error(message="You are not authorized to delete this comment")
        #     return self.result, self.error
        
        comment.delete()
        self.result = self.service_response_builder.result(message="Comment successfully deleted")
        return self.result, self.error
    

    def view_comment(self, comment_id):
        comment = Comment.objects.filter(public_id=comment_id).first()

        if not comment:
            self.error = self.service_response_builder.not_found_error(message="Comment not found")
            return self.result, self.error 

        self.result = self.service_response_builder.result(data=CommentSerializer(comment).data)
        return self.result, self.error

    
    def view_comments(self, request, post_id, current_view_instance):
        post = Post.objects.filter(id=post_id).first()

        if not post:
            self.error = self.service_response_builder.not_found_error(message="Post not found")
            return self.result, self.error

        queryset = Comment.objects.select_related("author").all()

        paginator = CommentCursorPagination()

        page = paginator.paginate_queryset(queryset, request, view=current_view_instance)


        if page is not None:
            serializer = CommentSerializer(page, many=True)
            self.result = self.service_response_builder.result(data={"comments":serializer.data})
            return self.result, self.error

        # Fallback
        serializer = CommentSerializer(queryset, many=True)

        self.result = self.service_response_builder.result(data={"comments":serializer.data})
        return self.result, self.error
         
        