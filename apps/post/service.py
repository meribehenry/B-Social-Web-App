from datetime import datetime, timedelta, timezone
from django.db import transaction
from rest_framework import status
from apps.upload.models import UploadBatch
from core.response import ServiceResponseBuilder
from .serializer import CreatePostSerializer, EditPostSerializer, PostSerializer
from .models import Post, PostMedia, PostTag
from apps.upload.service import UploadService
from apps.upload.tasks import delete_media_file_task
from core.logger.logger_client import get_logger


logger = get_logger(__name__)


class PostService():

    def __init__(self):
        self.service_response_builder = ServiceResponseBuilder()
        self.error = {}
        self.result = {}


    def get_post(self, post_id, return_bool=False) -> Post | bool | None:
        if return_bool:
            return Post.objects.filter(id=post_id).exists()

        post = Post.objects.filter(id=post_id).first()

        return post

    def get_optimised_post(self, post_id) -> Post | bool | None:

            optimised_post = Post.objects.select_related(
                "author"
                ).prefetch_related(
                    "medias", 
                    "tags"
                    ).get(
                        pk=post_id
                        )
    
            return optimised_post


    def create_post_medias(self, medias, batch, post, current_user):
        logger.info("Creating post media/medias....")
        for media_info in medias:
            upload_session = media_info.pop("upload_session")
            media_info.pop("purpose")
            PostMedia.objects.create(**media_info, post=post, user=current_user)

            upload_session.status = "USED"
            upload_session.updated_at = datetime.now(timezone.utc)
            upload_session.save(update_fields=["status", "updated_at"])

        batch.status = "USED"
        batch.updated_at = datetime.now(timezone.utc)
        batch.save(update_fields=["status", "updated_at"])
        logger.info("Post media/medias successfully created")


    def post_not_found_result(self):
        self.error = self.service_response_builder.not_found_error(
            message="Post not found"
        )
        logger.info("Post not found")
        return self.result, self.error


    def create_post(self, data, current_user):
        logger.info("Post creation starting....")

        serializer = CreatePostSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.data

        title = validated_data.get("title", "")
        content = validated_data.get("content", "")
        batch_id = validated_data.get("batch_id")
        tags = validated_data.get("tags")

        if not content and not batch_id:
            self.error = self.service_response_builder.bad_request_error(
                message="Invaild request. Post must contain either a content or media files (batch_id)"
            )
            logger.info("Post creation faied (Invalid request). Post must contain either a content or media files (batch_id)")
            return self.result, self.error 

        medias = []
        batch = ""

        if batch_id:
            validate_result = UploadService().validate_upload(batch_id, "post")
            if isinstance(validate_result, tuple):
                return validate_result

            medias, batch = validate_result["medias"], validate_result["batch"] 

        with transaction.atomic():
            post = Post.objects.create(
                title=title,
                content=content,
                author=current_user,
                )
            
            if tags:
                tag_objects = []

                logger.info("Creating post tag/tags....")
                for tag_dict in tags:
                    tag_object, _ = PostTag.objects.get_or_create(name=tag_dict["name"].strip())
                    tag_objects.append(tag_object)

                post.tags.set(tag_objects)
                logger.info("Post tag/tags created")

            if batch_id:
                post.batch_id=batch.id
                post.save(update_fields=["batch_id"])

            if medias:
                self.create_post_medias(medias, batch, post, current_user)

            optimised_post = Post.objects.select_related(
                "author"
                ).prefetch_related(
                    "medias", 
                    "tags"
                    ).get(
                        pk=post.id
                        )

            self.result = self.service_response_builder.result(
                message = "Post successfully created",
                status_code = status.HTTP_201_CREATED,
                data = {"post": PostSerializer(optimised_post).data}
            )

            logger.info("Post successfully created")
            return self.result, self.error

        self.error = self.service_response_builder.internal_server_error(
            message="Could not create post. Please try again"
        )
        logger.info("Could not create post")
        return self.result, self.error


    def edit_post(self, post_id, data, current_user):
        logger.info("Updating post....")
        post = Post.objects.select_related("author").prefetch_related("medias", "tags").filter(id=post_id).first()
    
        if not post:
            return self.post_not_found_result()

        if post.author != current_user:
            self.error = self.service_response_builder.forbidden_error(
                message= "You are not authorized to perform this action"
            )
            logger.info("User not authorized")
            return self.result, self.error
        

        if datetime.now(timezone.utc) > (post.date_created + timedelta(hours=48)):
            self.error =  self.service_response_builder.validation_error(
                message="Post cannot be edited after 48 hours"
            )
            logger.info("Cannot edit post after 48 hours")
            return self.result, self.error
        
        serializer = EditPostSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.data

        title=  validated_data.get("title", "")
        content =  validated_data.get("content", "")
        batch_id =  validated_data.get("batch_id", "")
        tags =  validated_data.get("tags", [])

        if content is None and batch_id is None and tags is None and title is None:
            self.error = self.service_response_builder.bad_request_error(
                message="Invaild request. Please ensure you update at least one field"
            )
            logger.info("Invaild request. No field updated, all is None")
            return self.result, self.error 

        if (not post.title and not title) and (not post.content and not content) and (not post.medias.all() and not batch_id)\
            and not (post.tags.all() and not tags):
            self.error = self.service_response_builder.bad_request_error(
                message="Invaild request. Please ensure you update at least one field"
            )
            logger.info("Invaild request. No field updated")
            return self.result, self.error 
        
        medias = []
        batch = ""

        if batch_id:
            validate_result = UploadService().validate_upload(batch_id)
            if isinstance(validate_result, tuple):
                return validate_result

            medias, batch = validate_result["medias"], validate_result["batch"] 

        with transaction.atomic():

            if title is not None: 
                post.title = title
                post.save(update_fields=["title"])
                logger.info("Title updated")

            if content is not None: 
                post.content = content
                post.save(update_fields=["content"])
                logger.info("Content updated")

            if tags is not None:
                post.tags.all().delete()
                tag_objects = []

                logger.info("Updating tags")
                for tag_dict in tags:
                    tag_object, _ = PostTag.objects.get_or_create(name=tag_dict["name"].strip())
                    tag_objects.append(tag_object)

                post.tags.set(tag_objects)
                logger.info("Tags updated")

            old_post_medias = []

            if batch_id is not None:
                old_batch = UploadBatch.objects.prefetch_related("uploads").filter(id=post.batch_id).first()
                
                if old_batch:
                    old_batch.uploads.all().update(status="UNUSED")
                    old_batch.status = "UNUSED"
                    old_batch.save(update_fields=["status"])
                    logger.info("Marked old media file upload as unused")

                if batch_id == "" and post.medias.exists():
                    post.batch_id = None
                    post.save(update_fields=["batch_id"])
                    logger.info("Changed the post batch_id to none")

                if batch_id:
                    post.batch_id = batch.id
                    post.save(update_fields=["batch_id"])
                    logger.info("Changed the post batch_id to to the new batch_id")

                old_post_medias = post.medias.all().values("public_id", "resource_type")
                post.medias.all().delete()
                logger.info("Deleted all the old post media if they existed")

                if medias:
                    self.create_post_medias(medias, batch, post, current_user)

            post.is_edited = True
            post.date_edited = datetime.now(timezone.utc)
            post.save(update_fields=["is_edited", "date_edited"])

            self.result = self.service_response_builder.result(
                message = "Post successfully updated",
                status_code = status.HTTP_200_OK,
                data = {"post": PostSerializer(post).data}
            )

            if old_post_medias:
                # Send old files to celery worker to be deleted in cloudinary
                sorted_old_post_medias = UploadService().sort_old_media_files(old_post_medias)
                delete_media_file_task.delay(public_ids=sorted_old_post_medias["image"], resource_type="image") # type: ignore
                delete_media_file_task.delay(public_ids=sorted_old_post_medias["video"], resource_type="video") # type: ignore

            logger.info("Post successfully updated")
            return self.result, self.error

        self.error = self.service_response_builder.internal_server_error(
            message="Could not edit post. Please try again"
        )
        logger.info("Could not edit post")
        return self.result, self.error


    def delete_post(self, post_id, current_user):
        logger.info("Deleting post....")
        post = Post.objects.select_related("author").prefetch_related("medias", "tags").filter(id=post_id).first()

        if not post:
            return self.post_not_found_result()

        if post.author != current_user:
            self.service_response_builder.forbidden_error(
                message= "You are not authorized to perform this action"
            )
            logger.info("User not authorized")
            return self.result, self.error

        old_post_medias = []
        if post.medias.all(): # type: ignore
            old_post_medias = post.medias.all().values("id", "resoucre_type") # type: ignore
            post.medias.delete() # type: ignore 
            logger.info("Deleted all the post media")

        post.delete()

        self.result = self.service_response_builder.result(
            message = "Post successfully deleted",
            status_code = status.HTTP_200_OK,
        )
        
        # Delete it files from storage
        if old_post_medias:
            sorted_old_post_medias = UploadService().sort_old_media_files(old_post_medias)
            delete_media_file_task.delay(public_ids=sorted_old_post_medias["image"], resource_type="image") # type: ignore
            delete_media_file_task.delay(public_ids=sorted_old_post_medias["video"], resource_type="video") # type: ignore

        logger.info("Post deleted successfully")
        return self.result, self.error