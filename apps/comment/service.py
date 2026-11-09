from apps.comment.pagination import CommentCursorPagination
from apps.comment.serializer import CommentSerializer, CreateCommentSerializer
from apps.post.service import PostService
from datetime import datetime, timezone, timedelta
from .models import Comment
from core.pagination import build_pagination_dict
from core.response import ServiceResponseBuilder
import uuid


Post = PostService().get_post_model()

class CommentReplyService():
    def __init__(self):
        self.service_response_builder = ServiceResponseBuilder()
        self.error = {}
        self.result = {}
    
    def create_comment_or_reply(self, data:dict, current_user, parent_comment_id: uuid.UUID|None = None, post_id: uuid.UUID|None = None) :
        """
        This handles comment and reply creation
        """
        if post_id and parent_comment_id:
            raise ValueError("Can only use either post_id or comment_id")
        post = None
        parent_comment = None

        if post_id:
            post = Post.objects.filter(id=post_id).first()  # Get the post

            # Check if the post exists
            if not post:
                self.error = self.service_response_builder.not_found_error(message="Post not found")
                return self.result, self.error 

        # If the parent comment id was passed to the function we fetch it from the db
        if parent_comment_id:
            parent_comment = Comment.objects.filter(id=parent_comment_id).first()

            # Return error if not found
            if not parent_comment:
                self.error = self.service_response_builder.not_found_error(message="Not found")
                return self.result, self.error
        
        serializer = CreateCommentSerializer(data=data)
        serializer.is_valid(raise_exception=True)   # Validate the data the user sent

        content = serializer.validated_data.get("content")

        # Create the comment and return the response for either comment creation or reply creation
        if post is None:
            post = parent_comment.post

        comment = Comment.objects.create(content=content, author=current_user, post=post, parent=parent_comment)

        name_to_send = "comment" if not comment.parent else "reply"
        self.result = self.service_response_builder.result(message=f"{name_to_send.title()} created successfully", 
                                                        data={name_to_send: CommentSerializer(comment).data},
                                                        status_code=201)

        return self.result, self.error

    
    def edit_comment_or_reply(self, comment_id:uuid.UUID, data:dict, current_user):
        """
        This handles comment and reply edition
        """
        comment = Comment.objects.filter(id=comment_id).first()

        if not comment:
            self.error = self.service_response_builder.not_found_error(message="Not found")
            return self.result, self.error 

        # Prevent another user from deleting a post
        if current_user != comment.author:
            self.error = self.service_response_builder.forbidden_error(message="You are not authorized to perform this action")
            return self.result, self.error

        serializer = CreateCommentSerializer(data=data)
        serializer.is_valid()

        new_content = serializer.validated_data.get("content")
        name_to_send = "Comment" if not comment.parent else "Reply"     # This is for the response name

        if (comment.date_created.replace(tzinfo=timezone.utc) + timedelta(hours=24)) <= (datetime.now(timezone.utc)):
            self.error = self.service_response_builder.validation_error(message=f"Cannot edit {name_to_send} after 24 hours")
            return self.result, self.error

        # Prevent a None value or same content from been saved
        if not new_content or new_content == comment.content:
            self.error = self.service_response_builder.bad_request_error(message=f"{name_to_send} field cannot be empty or left the same")
            return self.result, self.error 
        
        comment.content = new_content
        comment.date_edited = datetime.now(timezone.utc)
        comment.save(update_fields=["content", "date_edited"])
        
        self.result = self.service_response_builder.result(message=f"{name_to_send} successfully updated", 
                                                      data={name_to_send.lower(): CommentSerializer(comment).data})
        
        return self.result, self.error
        
    
    def delete_comment_or_reply(self, comment_id:uuid.UUID, current_user):
        """
        This handles comment and reply deletion
        """
        comment = Comment.objects.filter(id=comment_id).first()
        
        if not comment:
            self.error = self.service_response_builder.not_found_error(message="Not found")
            return self.result, self.error 

        if current_user != comment.author:
            self.error = self.service_response_builder.forbidden_error(message="You are not authorized to perform this action")
            return self.result, self.error

        name_to_send = "Comment" if not comment.parent else "Reply"
        comment.delete()
        self.result = self.service_response_builder.result(message=f"{name_to_send} successfully deleted")
        return self.result, self.error
    

    def view_comment(self, comment_id:uuid.UUID):
        comment = Comment.objects.filter(public_id=comment_id).first()

        if not comment:
            self.error = self.service_response_builder.not_found_error(message="Not found")
            return self.result, self.error 

        key_to_use = "comment" if not comment.parent else "reply"
        self.result = self.service_response_builder.result(data={key_to_use: CommentSerializer(comment).data})
        return self.result, self.error

    
    def view_comments_or_reply(self, request, current_view_instance, post_id:uuid.UUID|None = None, parent_comment_id:uuid.UUID|None = None,):
        if post_id and parent_comment_id:
            raise ValueError("Can only use either post_id or parent_comment_id")

        user = request.user

        if post_id:
            post = Post.objects.filter(id=post_id).first()

            if not post:
                self.error = self.service_response_builder.not_found_error(message="Post not found")
                return self.result, self.error

            key_to_use = "comments"
            queryset = Comment.objects.select_related("author").filter(post=post, author=user)

        else:
            parent_comment = Comment.objects.filter(id=parent_comment_id).first()
            
            # Return error if not found
            if not parent_comment:
                self.error = self.service_response_builder.not_found_error(message="Not found")
                return self.result, self.error
        
            key_to_use = "replies"
            queryset = Comment.objects.select_related("author").filter(parent=parent_comment_id) 

        paginator = CommentCursorPagination()

        page = paginator.paginate_queryset(queryset, request, view=current_view_instance)
        
        if page is not None:
            serializer = CommentSerializer(page, many=True)
            
            self.result = self.service_response_builder.result(
                                    data={key_to_use:serializer.data}, 
                                    pagination=build_pagination_dict(paginator)
                                    )
            return self.result, self.error

        # Fallback
        serializer = CommentSerializer(queryset, many=True)

        self.result = self.service_response_builder.result(data={key_to_use:serializer.data})
        return self.result, self.error