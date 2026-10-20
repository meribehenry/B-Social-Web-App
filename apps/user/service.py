from django.db import transaction
from apps.upload.models import UploadBatch
from apps.upload.service import UploadService
from apps.user.serializer import EditProfileSerializer, ProfileSerializer, UserSerializer
from core.logger.logger_client import get_logger
from .models import Profile, User
from core.response import ServiceResponseBuilder
from apps.upload.tasks import delete_media_file_task
from rest_framework import status
from datetime import datetime, timezone


logger = get_logger(__name__)


class UserService():
    def __init__(self) -> None:
        self.result = {}
        self.error = {}
        self.service_response_builder = ServiceResponseBuilder()

    def _retrieve_user(self, identifier, retrival_method):
        if retrival_method == "email":
            user = User.objects.filter(email=identifier).first()

        elif retrival_method == "username":
            user = User.objects.filter(username=identifier).first()

        elif retrival_method == "id":
            user = User.objects.filter(id=identifier).first()
        else:
            raise Exception ("Invalid retrival method or identifier could not retrieve user")
        
        return user

    def get_user_object(self, identifier, retrival_method="id", return_bool=False):
        """ 
        This funtion helps retrive user object for other services to use. Retrival methods includes: email, username and id. 
        Identifer refers to what you are using to retrive user. Return Boolean if you don't want the whole user object instead you are checking if user exists.
        """

        user = self._retrieve_user(identifier, retrival_method)

        if not return_bool:
            return user
        
        return user is not None


    def mark_user_verified(self, user):
        """
        Marks a user as verified
        """
        user.email_verified = True
        user.status = "active"
        user.is_active  = True
        user.save()

    def change_password(self, user, password):
        """
        Changes a user password
        """
        user.password = password
        print(user.password)
        user.save()


    def validate_create_user_values(self, values) -> KeyError | None:

        if "username" not in values: raise KeyError("username missing")
        if "password" not in values: raise KeyError("password missing")
        if "gender" not in values: raise KeyError("gender missing")
        if "display_name" not in values: raise KeyError("display name missing")
        if "email" not in values: raise KeyError("email missing")


    def create_new_user(self, values:dict) -> User | None :
        """
        This creates the user and his/her respective profile
        """
        logger.info("Creating new user....")
        self.validate_create_user_values(values)

        display_name = values.pop("display_name")

        with transaction.atomic():
            user = User.objects.create(**values)
            Profile.objects.create(display_name=display_name, user=new_user)

            new_user = User.objects.select_related("profile").get(pk=user.id)
            logger.info("New user created successfully")
            return new_user

        logger.error("Could not create new user")

        return None

    def view_user(self, user_id, current_user):
        user = User.objects.select_related("profile").filter(id=user_id).first()

        if not user:
            return self.result, self.service_response_builder.not_found_error(
                message="User not found"
            )

        if user != current_user:
            return self.result, self.service_response_builder.forbidden_error(
                message="You cannot perform this action"
            )

        self.result = self.service_response_builder.result(
            status_code = status.HTTP_200_OK,
            data = {"user": UserSerializer(user).data}
        )

        return self.result, self.error


class ProfileService():
    def __init__(self) -> None:
        self.service_response_builder = ServiceResponseBuilder()
        self.user_service = UserService()
        self.result = {}
        self.error = {}


    def add_profile_medias(self, medias, batch, profile):
        logger.info("Adding profile media....")

        for media_info in medias:
            upload_session = media_info.pop("upload_session")
            if media_info.get("purpose") == "profile_pic":
                profile.profile_pic_public_id = media_info.get("public_id")
                profile.profile_pic_url = media_info.get("secure_url")

                profile.save(update_fields=["profile_pic_url", "profile_pic_public_id"])
                
            else:
                profile.profile_banner_public_id = media_info.get("public_id")
                profile.profile_banner_url = media_info.get("secure_url")

                profile.save(update_fields=["profile_banner_url", "profile_banner_public_id"])

            upload_session.status = "USED"
            upload_session.updated_at = datetime.now(timezone.utc)
            upload_session.save(update_fields=["status", "updated_at"])

        batch.status = "USED"
        batch.updated_at = datetime.now(timezone.utc)
        batch.save(update_fields=["status", "updated_at"])

        logger.info("Successfully added profile media")


    def edit_profile(self, user_id, data, current_user):
        logger.info("Updating profile....")
        profile = Profile.objects.select_related("user").filter(user_id=user_id).first()

        if not profile:
            self.error = self.service_response_builder.not_found_error(
                message="User not found"
            )
            return self.result, self.error

        if profile.user != current_user:
            self.error = self.service_response_builder.forbidden_error(
                message= "You are not authorized to perform this action"
            )
            logger.info("User not authorized")
            return self.result, self.error

        serializer = EditProfileSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        display_name = serializer.data.get("display_name", "")
        bio = serializer.data.get("bio", "")
        batch_id = serializer.data.get("batch_id", "")
        profession =  serializer.data.get("profession", "")

        if display_name is None and batch_id is None and bio is None and profession is None:
            self.error = self.service_response_builder.bad_request_error(
                message="Invaild request. Please ensure you update at least one field"
            )
            logger.info("Invaild request. No field updated, all is None")
            return self.result, self.error 

        if display_name == "":
            self.error = self.service_response_builder.bad_request_error(
                message="Display name cannot be empty"
            )
            logger.info("Invaild request. No display name")
            return self.result, self.error

        if (not profile.bio and not bio) and (not profile.batch_id and not batch_id) \
            and not (profile.profession and not profession):
            self.error = self.service_response_builder.bad_request_error(
                message="Invaild request. Please ensure you update at least one field"
            )
            logger.info("Invaild request. No field updated")
            return self.result, self.error 

        batch = ""
        medias = []

        if batch_id:
            validate_result = UploadService().validate_upload(batch_id, "profile")
            if isinstance(validate_result, tuple):
                return validate_result

            medias, batch = validate_result["medias"], validate_result["batch"] 

        with transaction.atomic():

            if display_name:
                profile.display_name = display_name
                profile.save(update_fields=["display_name"])

            if bio is not None:
                profile.bio = bio
                profile.save(update_fields=["bio"])

            if profession is not None:
                profile.profession = profession
                profile.save(update_fields=["profession"])

            old_profile_medias = []
            
            if batch_id is not None:
                old_batch = UploadBatch.objects.prefetch_related("uploads").filter(id=profile.batch_id).first()
                
                if old_batch:
                    old_batch.uploads.all().update(status="UNUSED")
                    old_batch.status = "UNUSED"
                    old_batch.save(update_fields=["status"])
                    logger.info("Marked old media file upload as unused")

                if batch_id == "" and (profile.profile_pic_url or profile.profile_banner_url):
                    profile.batch_id = None
                    profile.save(update_fields=["batch_id"])
                    logger.info("Changed the profile batch_id to none")

                if batch_id:
                    profile.batch_id = batch.id
                    profile.save(update_fields=["batch_id"])
                    logger.info("Changed the profile batch_id to to the new batch_id")

                if profile.profile_pic_public_id: old_profile_medias.append(
                    {"id": profile.profile_pic_public_id, "resource_type": "image"}
                    )

                if profile.profile_banner_public_id: old_profile_medias.append(
                    {"id": profile.profile_banner_public_id, "resource_type": "image"}
                    )

                profile.profile_pic_public_id = None
                profile.profile_banner_public_id = None

                logger.info("Removed all the old profile media if they existed")

                if medias:
                    self.add_profile_medias(medias, batch, profile)

            profile.last_updated = datetime.now(timezone.utc)
            profile.save(update_fields=["last_updated"])

            self.result = self.service_response_builder.result(
                message = "Profile successfully updated",
                status_code = status.HTTP_200_OK,
                data = {"profile": ProfileSerializer(profile).data}
            )

            if old_profile_medias:
                # Send old files to celery worker to be deleted in cloudinary
                sorted_old_post_medias = UploadService().sort_old_media_files(old_profile_medias)
                delete_media_file_task.delay(public_ids=sorted_old_post_medias["image"], resource_type="image") # type: ignore
                delete_media_file_task.delay(public_ids=sorted_old_post_medias["video"], resource_type="video") # type: ignore

            logger.info("Profile successfully updated")
            return self.result, self.error
    
        self.error = self.service_response_builder.internal_server_error(
            message="Could not edit profile. Please try again"
        )
        logger.info("Could not edit profile")
        return self.result, self.error

    def view_profile(self, user_id):
        profile = Profile.objects.select_related("user").filter(user_id=user_id).first()

        if not profile:
            return self.result, self.service_response_builder.not_found_error(
                message="User not found"
            )

        self.result = self.service_response_builder.result(
            status_code = status.HTTP_200_OK,
            data = {"user": ProfileSerializer(profile).data}
        )

        return self.result, self.error