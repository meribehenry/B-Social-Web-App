from celery import shared_task
import cloudinary.api
from core.logger.logger_client import get_logger
from core.cloudinary_service import CloudinaryService
from datetime import datetime, timezone, timedelta #
from django.db import transaction
from django.db.models import Prefetch
from .models import UploadSession, UploadBatch
import cloudinary.uploader
import cloudinary.api


logger = get_logger(__name__)

cloudinary_service = CloudinaryService()


@shared_task(bind=True, retry_backoff=2, retry_backoff_max=300, retry_jitter=True, max_retries=5)
def delete_media_file_task(self, public_id: str|None = None, public_ids: list = [], resource_type: str|None = None, *args, **kwargs):
    """
    public_id (str) - The public_id of the file. Set this only if you are deleting one file\n
    public_ids (list) - The list of public_ids of many file. Set this when you are deleting more than one files. Also set the resource type for the whole list
    eg. delete_media_file_task(public_ids = ["94949", "9494949", "995959"], resource_type = "image")\n
    resource_type - The type of file, either (image), (video) or (raw). This is only required when deleting multiple files and each of the files must be of the same resource type
    
    """
    logger.info(f"Deleting file {public_id} in the background....")

    if resource_type and resource_type not in ["image", "raw", "video"]:
        raise ValueError("Resource type must either be (image), (video) or (raw)")

    try:
        if public_ids:
            if not resource_type: raise ValueError("Resource type required")

            if len(public_ids) > 1000:
                for i in range(0, len(public_ids), 999):
                    delete_media_file_task.delay(public_ids=public_ids[:i], resource_type=resource_type) # type: ignore

            result = cloudinary.api.delete_resources(public_ids, resource_type=resource_type, invalidate=True)

            deleted_media_file = result.get("deleted", {})

            for id, status in deleted_media_file.values():

                if status == "not_found":
                    logger.info(f"Media file {id} not found")

                elif status == "deleted":
                    logger.info(f"Media file {id} deleted")
                else:
                    logger.warning(f"Bad status for media file with public_id {id}. Status: {status}")


        elif public_id:
            result = cloudinary.uploader.destroy(public_id, invalidate=True)
        
            if result["result"] == "ok":
                logger.info(f"Deleted file {public_id}")

            elif result["result"] == "not found":
                logger.info(f"Media file not found")


    except ValueError as e:
        raise e

    except Exception as exc:
        retries_left = self.max_retries - self.request.retries  # type: ignore
        logger.info(f"Retrying delete_media_file_task {retries_left} left")
        raise self.retry(exc=exc)



@shared_task(
    name="apps.upload.tasks.mark_upload_exipred",
    bind=True, 
    retry_backoff=4, 
    retry_backoff_max=300, 
    retry_jitter=True, 
    max_retries=3
)
def mark_upload_expired(self, *args, **kwargs):
    logger.info("Marking Uploads expired....")
    try:
        time_passed = datetime.now(timezone.utc) - timedelta(minutes=0.5)

        expired_upload_queryset = UploadSession.objects.filter(status__in=["UPLOADING", "UPLOADED"], created_at__lt=time_passed)

        batches = UploadBatch.objects.prefetch_related(
            Prefetch("uploads", queryset=expired_upload_queryset , to_attr="expired_uploads")
            ).filter(
                    uploads__in=expired_upload_queryset 
                ).distinct()

        if batches.exists():
            with transaction.atomic():
                orphan_uploads = {"image": [], "video": []}

                for batch in batches:
                    for upload in batch.expired_uploads: # type: ignore

                        if upload.status == "UPLOADED":
                            orphan_uploads[upload.resource_type].append(upload.public_id)
                            
                        upload.status = "EXPIRED"
                        upload.updated_at = datetime.now(timezone.utc)
                        upload.save(update_fields=["status", "updated_at"])

                    batch.status = "EXPIRED"
                    batch.updated_at = datetime.now(timezone.utc)
                    batch.save(update_fields=["status", "updated_at"])

                delete_media_file_task.delay(public_ids=orphan_uploads["image"], resource_type="image") # type: ignore
                delete_media_file_task.delay(public_ids=orphan_uploads["video"], resource_type="video") # type: ignore

    except Exception as exc:
            retries_left = self.max_retries - self.request.retries  
            logger.info(f"Retrying mark_upload_expired {retries_left} left")
            raise self.retry(exc=exc)
