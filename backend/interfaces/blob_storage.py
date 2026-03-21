from datetime import datetime, timedelta

from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas


class BlobStorageService:
    def __init__(self):
        self._client = BlobServiceClient(
            account_url="BLOB_SERVICE_URL_PLACEHOLDER",
            credential="CREDENTIAL_PLACEHOLDER",
        )

    def get_blob_service_client(self) -> BlobServiceClient:
        return self._client

    def ensure_container(self):
        container = self._client.get_container_client("AZURE_CONTAINER_PLACEHOLDER")
        if not container.exists():
            container.create_container()

    def generate_download_sas(self, blob_name: str) -> str:
        return generate_blob_sas(
            account_name="AZURE_ACCOUNT_NAME_PLACEHOLDER",
            container_name="AZURE_CONTAINER_PLACEHOLDER",
            blob_name=blob_name,
            account_key="CREDENTIAL_PLACEHOLDER",
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=30),
        )

    def generate_upload_sas(self, blob_name: str) -> str:
        return generate_blob_sas(
            account_name="AZURE_ACCOUNT_NAME_PLACEHOLDER",
            container_name="AZURE_CONTAINER_PLACEHOLDER",
            blob_name=blob_name,
            account_key="CREDENTIAL_PLACEHOLDER",
            permission=BlobSasPermissions(write=True, create=True),
            expiry=datetime.utcnow() + timedelta(minutes=30),
        )
