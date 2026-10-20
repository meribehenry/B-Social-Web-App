from collections.abc import Mapping

from core.response import ServiceResponseBuilder
from datetime import datetime, timezone
from time import time, sleep
import cloudinary.exceptions
from django.db import transaction
from rest_framework import status
from .models import UploadBatch, UploadSession
from core.cloudinary_service import CloudinaryService
from django.conf import settings
from apps.upload.serializer import MediaUploadSerializer
from core.logger.logger_client import get_logger
import cloudinary.api 
import hashlib
import hmac
import json


cloudinary_service = CloudinaryService()

logger = get_logger(__name__)


class UploadService():
    def __init__(self):
        self.result = {}
        self.error = {}
        self.service_response_builder = ServiceResponseBuilder()


    def get_preset(self, file_info):
        logger.info(f"Getting upload preset for a media file...")
        upload_preset = ""
        if file_info["purpose"] == "post": upload_preset = "b_social_posts"

        elif file_info["purpose"] == "profile_pic": upload_preset = "b_social_profile_pic"

        elif file_info["purpose"] == "profile_banner": upload_preset = "b_social_profile_banner"

        logger.info(f"Upload preset fora media file obtained")
        return upload_preset
    

    def get_asset_folder(self, file_info, user_id):
        logger.info(f"Getting assset for file....")
        folder = f"uploads/{user_id}"
        if file_info["purpose"] == "post": folder = folder + "/post"

        elif file_info["purpose"] == "profile_pic": folder = folder + "/profile_pic"

        elif file_info["purpose"] == "profile_banner": folder = folder + "/profile_banner"


        logger.info(f"Asset folder for media file obtained")
        return folder + f"/{file_info["resource_type"]}"


    def validate_files_info(self, files_info: list, user_id: str, pass_other_validation=False, pass_len_validation=True) -> tuple:
        """
        This validates all the files the front-end wants us to generate a signature for.
        """
        logger.info("Validating files info....")

        file_purpose = set()
        profile_pic_exist = False # True if an upload file info contained a profile picture
        profile_banner_exist = False # True if an upload file info contained a profile banner

        for file_info in files_info:
   
            if pass_other_validation: # Incase there is no serializer this conditional helps with this specific checks
                if file_info["extension"] not in {"png", "img", "mp4", "jpg", "gif", "jpeg", "avif", "mkv"}:
                    return False, "Invalid extension. Please enter the supported extension"

                if file_info["size"] > 104857600:
                    return False, "File size is to large. Please enter files less than 100MB"

                if file_info["purpose"] not in {"post", "profile_pic", "profile_banner"}:
                    return False, "Purpose must either be (post or profile_pic or profile_banner)"

                if file_info["resource_type"] not in {"image", "video"}:
                    if file_info["purpose"] not in {"post", "profile_pic", "profile_banner"}:
                        return False, "Resource type must either be (image or video)"

            file_purpose.add(file_info["purpose"]) # type: ignore


            if pass_len_validation:
                if file_info["purpose"] == "post" and len(files_info) > 5: # This ensures only 5 post media can be uploaded at once
                    return False, "Cannot upload more than 5 media file for a post"
                
                elif file_info["purpose"] in {"profile_pic", "profile_banner"}: 
                    if len(files_info) > 2: # this makes sure that only one profile banner and one profile picture can be uploaded at the same time
                        return False, f"You can only upload one profile picture and one profile banner"
                    
                    if file_info["purpose"] == "profile_pic": # this prevent uploading more than one profile picture
                        if profile_pic_exist: 
                            return False, f"Cannot upload more than 1 profile picture" # Profile image already exists in one of the files_info
                        else:
                            profile_pic_exist = True # Set True if it doesn't exist in one of the files_info

                    elif file_info["purpose"] == "profile_banner": # this prevent uploading more than one profile banner
                        if profile_banner_exist:
                            return False, f"Cannot upload more than 1 profile banner" # Profile banner already exists in one of the files_info
                        else:
                            profile_banner_exist = True # Set True if it doesn't exist in one of the files_info

            file_info["upload_preset"] = self.get_preset(file_info)
            file_info["asset_folder"] = self.get_asset_folder(file_info, user_id)
            logger.info("Validation passed successfully")

        # This prevent a post uploads and profile uploads from begin done at the same time
        if "post" in file_purpose and ("profile_pic" in file_purpose or "profile_banner" in file_purpose):
            return False, "Cannot upload post with profile_pic or profile_banner at the same time"

        return True, files_info


    def start_upload(self, data, user) -> tuple:
        logger.info("Starting upload....")
        serializer = MediaUploadSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        files_info: list = serializer.data.get("files_info")

        if not files_info:
            logger.info("No media file info found")
            return self.result, self.service_response_builder.bad_request_error(
                message="Invalid request. Please enter atleast one media file"
            )

        files_info_result = self.validate_files_info(files_info, user.id)

        if files_info_result[0] is False:
            logger.info("Validation failed")
            return self.result, self.service_response_builder.bad_request_error(
                message=files_info_result[1]
            )

        files_info = files_info_result[1]

        batch = UploadBatch.objects.create(user=user)

        uploads = []

        logger.info("Creating signatures")
        for file_info in files_info:
            upload = UploadSession.objects.create(
                batch=batch,
                user=user,
                resource_type=file_info.get("resource_type"),
                public_id="temporary",
                purpose=file_info.get("purpose"),
                bytes=file_info.get("size"),
                format=file_info.get("extension"),
                asset_folder=file_info.get("asset_folder")
            )

            public_id = f"users/{user.id}/uploads/{batch.id}/{upload.id}"

            upload.public_id = public_id
            upload.save(update_fields=["public_id"])

            timestamp = int(time())

            params = {
                "timestamp": timestamp,
                "asset_folder": file_info.get("asset_folder"),
                "use_asset_folder_as_public_id_prefix": True,
                "public_id":  public_id,
                "resource_type": upload.resource_type,
                "expire_at": int(time()) + 3600,
                "format": file_info.get("extension"),
                "bytes": file_info.get("size")
            }

            upload_preset = file_info.get("upload_preset")

            if upload_preset: params["upload_preset"] = upload_preset

            signature = cloudinary_service.create_signature(params)

            upload_data = {
                "upload_id": str(upload.id),
                "asset_folder": params.get("asset_folder"),
                "expire_at": params.get("expire_at"),
                "use_asset_folder_as_public_id_prefix": params.get("use_asset_folder_as_public_id_prefix"),
                "public_id": public_id,
                "resource_type":upload.resource_type,
                "timestamp": timestamp,
                "signature": signature,
                "api_key": settings.CLOUDINARY_API_KEY,
                "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
                "format": params["format"],
                "bytes": params["bytes"]
            }

            if upload_preset: upload_data["upload_preset"] = upload_preset

            uploads.append(upload_data)


        self.result = self.service_response_builder.result(
            message="Signatures created. You can proceed to uploading the media files",
            data = {"uploads": uploads, "batch_id":batch.id},
            status_code = status.HTTP_201_CREATED
        )
        logger.info("Signatures created successfully")

        return self.result, self.error

    def check_upload_batch(self, batch_id):
        logger.info("Checking the upload batch")
        batch = UploadBatch.objects.prefetch_related("uploads",).filter(id=batch_id).first()

        if not batch:
            logger.info("Check failed")
            return None, {"message": f"Batch of id {batch_id} not found", "status_code":status.HTTP_404_NOT_FOUND, "error": "Not found"}
          
        if batch.status in {"EXPIRED", "FAILED"}:
            logger.info("Check failed")
            return None, {"message": f"Batch upload {batch.status.lower()}. Please try again", "status_code":status.HTTP_422_UNPROCESSABLE_ENTITY, "error": "Validation error"}
        
        if batch.status in ["UPLOADED", "UPLOADING"]:
            logger.info("Check passed")
            return True, batch

        if batch.status in ["USED", "UNUSED"]:
            logger.info("Check failed")
            return None, {"message": f"Batch id {batch.id} already used", "status_code":status.HTTP_409_CONFLICT, "error": "Conflict error"}

        # Incase you only want to verify with webhooks only the uncomment this and remove UPLOADING in the third IF statment 
        # logger.info("Check failed")
        # return None, {"message": f"Batch of id {batch.id} still uploading" , "status_code":status.HTTP_400_BAD_REQUEST, "error": "Bad request"}
        

    def validate_and_update_upload_session(self, batch, not_allowed_purpose, service_purpose:str):
        """Batch must be loaded with prefetch"""
        logger.info("Validating batch upload sessions")

        medias = []
        with transaction.atomic():
            for upload_session in batch.uploads.all():
                if upload_session.status == "UPLOADING":
                    try:
                        # result = cloudinary.api.resource(upload_session.public_id, resource_type=upload_session.resource_type)
                        result = {
                            "secure_url": "ops.png",
                        }

                    except cloudinary.exceptions.NotFound:
                        logger.info("Media file not found")
                        return None, {"message": f"File of public_id {upload_session.public_id} not found in storage", "status_code":status.HTTP_404_NOT_FOUND, "error": "Not found"}
                    
                    except Exception:
                        logger.error("An error occured")
                        return None, {"message": "An error occured", "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR, "error": "Internal server error"}

                    if upload_session.purpose in not_allowed_purpose:
                        return None, {"message": f"Cannot use file meant for {upload_session.purpose} for this action ({service_purpose})", "status_code":status.HTTP_400_BAD_REQUEST, "error": "Bad request error"}
                    
                    upload_session.secure_url = result.get("secure_url")
                    upload_session.status = "UPLOADED"
                    upload_session.updated_at = datetime.now(timezone.utc)
                    upload_session.save(update_fields=["secure_url", "status", "updated_at"])
                    logger.info(f"Upload session with an upload id {upload_session.id} marked as uploaded")

                if upload_session.purpose in not_allowed_purpose: # This prevent the wrong batch from been used for a particular purpose
                    return None, {"message": f"Cannot use file meant for {upload_session.purpose} for this action ({service_purpose})", "status_code":status.HTTP_400_BAD_REQUEST, "error": "Bad request error"}
                                    
                medias.append(
                    {
                        "public_id": upload_session.public_id,
                        "resource_type": upload_session.resource_type,
                        "secure_url": upload_session.secure_url,
                        "upload_session": upload_session,
                        "format": upload_session.format,
                        "asset_folder": upload_session.asset_folder,
                        "size": upload_session.bytes,
                        "upload_session_id": upload_session.id,
                        "upload_session": upload_session,
                        "purpose": upload_session.purpose,
                    }
                )
                
            batch.status = "UPLOADED"
            batch.updated_at = datetime.now(timezone.utc)
            batch.save(update_fields=["status", "updated_at"])
            logger.info(f"Validation completed, upload batch with an id {batch.id} marked as uploaded")

            return True, medias


    def validate_webhook_result(self, headers: Mapping["str", "str"], raw_body):
        logger.info("Validation webhook result....")

        # timestamp = headers.get('X-Cld-Timestamp')
        # signature = headers.get('X-Cld-Signature')

        # if not timestamp or not signature:
        #     return self.result, self.service_response_builder.bad_request_error(
        #         message="Signature is missing"
        #     )

        # # 2. Anti-replay: reject if older than 5 mins
        # try:
        #     if abs(int(datetime.now(timezone.utc).timestamp()) - int(timestamp)) > 300:
        #         return self.result, self.service_response_builder.bad_request_error(
        #             message="Timestamp too old"
        #         )
        # except:
        #     return self.result, self.service_response_builder.bad_request_error(
        #         message="Invalid timestamp"
        #     )

        # # 3. Compute expected signature
        # payload_to_sign = raw_body + timestamp.encode("utf-8") + settings.CLOUDINARY_API_SECRET.encode("utf-8")
        # expected_signature = hashlib.sha1(payload_to_sign).hexdigest()
    
        # # Some accounts use SHA256 now, if SHA1 fails try this:
        # # expected_signature = hashlib.sha256(payload_to_sign).hexdigest()

        # # 4. Secure compare
        # if not hmac.compare_digest(expected_signature, signature):
        #     return self.result, self.service_response_builder.forbidden_error(
        #         message="Invalid signature"
        #     )

        # # Parse the raw_body
        result = json.loads(raw_body)
 
        upload_session = UploadSession.objects.select_related("batch").filter(id=result.get("upload_id")).first()

        if upload_session and upload_session.status == "UPLOADING":
            with transaction.atomic():
                upload_session.status = "UPLOADED"
                upload_session.secure_url = result.get("secure_url")
                upload_session.updated_at = datetime.now(timezone.utc)
                upload_session.save(update_fields=["secure_url", "status", "updated_at"])
                logger.info(f"Upload session with an upload id {upload_session.id} marked as uploaded")

                batch = upload_session.batch
                batch_contain_uploading_session = batch.uploads.filter(status="UPLOADING").exists()

                if not batch_contain_uploading_session:
                    batch.status = "UPLOADED"
                    batch.updated_at = datetime.now(timezone.utc)
                    batch.save(update_fields=["status", "updated_at"])
                    logger.info(f"Upload batch with an id {batch.id} marked as uploaded")

        self.result = self.service_response_builder.result(
            status_code = status.HTTP_200_OK
        )
        logger.info("Validation completed")
        return self.result, self.error
    

    def validate_upload(self, batch_id:str, service_purpose:str):
        """
        This is used by services to vaidate what the user uploaded
        """
        logger.info("Validating the upload....")
        not_allowed_purpose = {"post", "profile_pic", "profile_banner"}
        
        if service_purpose == "profile":
            not_allowed_purpose.remove("profile_pic")
            not_allowed_purpose.remove("profile_banner")
        elif service_purpose == "post":
            not_allowed_purpose.remove("post")
        else:
            raise ValueError("service_purpose must be either for post or profile")
        
        upload_service = UploadService()

        batch_result = upload_service.check_upload_batch(batch_id)

        if batch_result[0] is None:
            self.error = {
                "error":batch_result[1]["error"],
                "message": batch_result[1]["message"],
                "status_code": batch_result[1]["status_code"]
            }
            logger.info("Upload validation failed")
            return self.result, self.error 

        batch = batch_result[1]

        update_result = upload_service.validate_and_update_upload_session(batch, not_allowed_purpose, service_purpose)

        if update_result[0] is None:

            self.error = {
                "error":update_result[1]["error"],
                "message": update_result[1]["message"],
                "status_code": update_result[1]["status_code"]
            }
            logger.info("Upload validation failed")
            return self.result, self.error

        logger.info("Upload validation suceeded")
        return {"medias": update_result[1], "batch": batch}


    def sort_old_media_files(self, old_medias_files):
        logger.info("Sorting media files public_id for deletion in cloundinary")
        sorted_files = {
            "image": [],
            "video": [],
        }

        for media in old_medias_files:
            if media.get("resource_type") == "image":
                sorted_files["image"].append(media.get("id"))

            elif media.get("resource_type") == "video":
                sorted_files["video"].append(media.get("id"))

        logger.info("Media files sorted")
        return sorted_files