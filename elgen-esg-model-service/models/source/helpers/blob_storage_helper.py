import logging
import os

from azure.core.exceptions import AzureError
from azure.core.paging import ItemPaged
from azure.storage.blob import BlobServiceClient, BlobProperties

from configuration.config import blob_storage_configuration, app_config
from source.exceptions.azure_blob_storage_exception_handler import BlobStorageRetrievalError

logger = logging.getLogger(__name__)


def create_local_model_folder_if_not_exists() -> bool:
    """
    Create the local model folder directory.
    :return: If the folder was created anew.
    """
    directory_to_create = os.path.join(app_config.MODEL_DIRECTORY, app_config.MODEL_NAME.split("/")[-1])
    if os.path.exists(directory_to_create):
        logger.info("Local model folder already exists.")
        return False

    logger.info("Creating local model directory...")
    os.makedirs(directory_to_create, exist_ok=True)
    return True


class BlobStorageModelDownloader:
    """
    Class responsible for model download from Azure Blob Storage
    """

    def __init__(self) -> None:
        self.blob_service_client = BlobServiceClient.from_connection_string(
            blob_storage_configuration.BLOB_STORAGE_CONNECTION_STRING)
        self.container_client = self.blob_service_client.get_container_client(blob_storage_configuration.CONTAINER)

    def _get_blob_list(self) -> ItemPaged[BlobProperties]:
        """
        Lists the contents of the model path in blob storage.
        :return: A generator with the model path contents.
        """
        logger.info("Retrieving model file list from Azure Blob Storage...")
        try:
            return self.container_client.list_blobs(
                name_starts_with=f"{blob_storage_configuration.BLOB_STORAGE_MODELS_DIRECTORY}/"
                                 f"{app_config.MODEL_NAME.split('/')[-1]}"
            )
        except IndexError as model_name_error:
            logger.error(model_name_error)
            raise BlobStorageRetrievalError(
                f"Cannot find model named: {app_config.MODEL_NAME} in "
                f"{blob_storage_configuration.BLOB_STORAGE_MODELS_DIRECTORY}: {model_name_error}")

    # Download all model files from the blob storage to the local folder
    def download_model(self) -> None:
        """
        Downloads all the files related to the model.
        :return: None
        """
        if not blob_storage_configuration.DOWNLOAD_FROM_BLOB_STORAGE:
            logger.info("Model acquisition from Azure Blob Storage is disabled. Will revert back to HuggingFace.")
            return None

        if not create_local_model_folder_if_not_exists():
            logger.info("Skipping model download...")
            return None

        logger.info("Start of model download...")
        for blob in self._get_blob_list():
            local_file_path = os.path.join(
                app_config.MODEL_DIRECTORY,
                blob.name.replace(f"{blob_storage_configuration.BLOB_STORAGE_MODELS_DIRECTORY}/", "")
            )

            logger.info(f"Downloading {blob.name} into {local_file_path}")
            os.makedirs(local_file_path.replace(blob.name.split("/")[-1], ""), exist_ok=True)
            with (open(local_file_path, "wb") as local_file):
                try:
                    blob_data = self.blob_service_client.get_blob_client(
                        container=blob_storage_configuration.CONTAINER,
                        blob=blob
                    ).download_blob()
                except AzureError as blob_error:
                    raise BlobStorageRetrievalError(
                        f"Unable to retrieve blob {blob.name} from Blob Storage: {blob_error}"
                    )
                local_file.write(blob_data.readall())

        logger.info("Model download completed.")
