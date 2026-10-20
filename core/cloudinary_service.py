from cloudinary.utils import api_sign_request
from django.conf import settings
from core.logger.logger_client import get_logger
import cloudinary.uploader


logger = get_logger(__name__)


class CloudinaryService():

    def create_signature(self, params_to_sign: dict) -> str:
        """
        Creates signature for a file upload
        """
        logger.info(f"Creating signature...")
        return api_sign_request(
            params_to_sign,
            settings.CLOUDINARY_API_SECRET
        )

    def delete_file(self, public_id):
        """
        Deletes a file from cloudinary
        """

        try:
            cloudinary.uploader.destroy(public_id, invalidate=True)
            logger.info(f"Deleted file with public_id ({public_id}) from storage")
        except:
            logger.error(f"Could not delete file with public_id ({public_id}) from storage") 