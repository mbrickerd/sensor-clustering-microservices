from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import (
    BlobServiceClient, ContainerClient, PublicAccess, ContentSettings
)
from azure.identity import DefaultAzureCredential
from loguru import logger
from typing import Optional, Union, List


class StorageService:
    account_name: str
    container_name: str
    user_id: str
    blob_service_client: BlobServiceClient
    container_client: ContainerClient

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, user_id: str, container_name: str, account_name: str) -> None:
        self.user_id = user_id
        self.container_name = container_name
        self.account_name = account_name
        
        credential = DefaultAzureCredential()
        account_url = f"https://{account_name}.blob.core.windows.net"
        self.blob_service_client = BlobServiceClient(account_url, credential=credential)
        self.container_client = self._get_container_client()

    def _get_container_client(self) -> ContainerClient:
        """
        Ensure the container exists, or create it if it doesn't, and return the container client.
        """
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            container_client.get_container_properties()
            logger.info(f"Container '{self.container_name}' already exists.")

        except ResourceNotFoundError:
            container_client = self.blob_service_client.create_container(
                self.container_name, public_access=PublicAccess.Container
            )
            logger.info(f"Container '{self.container_name}' has been created.")

        return container_client

    def read_blob(self, blob_name: str, binary: bool) -> Union[str, bytes]:
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_content = blob_client.download_blob()

        if binary:
            blob_bytes: bytes = blob_content.readall()
            return blob_bytes

        else:
            blob_text: str = blob_content.content_as_text()
            return blob_text

    def write_blob(self, blob_name: str, content: bytes, content_type: str) -> None:
        try:
            blob_client = self.container_client.get_blob_client(blob=blob_name)
            blob_client.upload_blob(
                content,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
            )
            logger.info(
                "Content uploaded successfully to "
                + f"https://{self.blob_service_client.account_name}.blob.core.windows.net/"
                + f"{self.container_name}/{blob_name}"
            )

        except Exception as err:
            logger.error(f"Failed to upload content to blob '{blob_name}': {err}")
            raise

    def list_blobs(self, prefix: Optional[str] = None) -> List[str]:
        return [
            blob.name
            for blob in self.container_client.list_blobs(name_starts_with=prefix)
        ]

    def delete_blob(self, blob_name: str) -> None:
        try:
            blob_client = self.container_client.get_blob_client(blob=blob_name)
            blob_client.delete_blob()

        except Exception as err:
            logger.error(f"Failed to delete blob '{blob_name}': {err}")
            raise

    def close(self) -> None:
        self.blob_service_client.close()