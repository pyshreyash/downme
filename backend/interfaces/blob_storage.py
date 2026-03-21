from datetime import datetime, timedelta, UTC
from azure.storage.blob import ContainerSasPermissions, BlobServiceClient, generate_container_sas
from azure.core.exceptions import ResourceExistsError

from backend.config import settings

class BlobStorageService:
    def __init__(self):
        self.blob_service_client = BlobServiceClient(
            account_url=settings.azure_blob_endpoint,
            credential=settings.azure_account_key,
            api_version="2023-11-03"
        )

    @staticmethod
    def game_container_name(game_name: str) -> str:
        return f"gm-{game_name.lower()}"
    
    def generate_download_sas(self, game_name: str) -> str:
        container_name = self.game_container_name(game_name)
        sas_token = generate_container_sas(
            account_name=settings.azure_account_name,
            container_name=container_name,
            account_key=settings.azure_account_key,
            permission=ContainerSasPermissions(read=True, list=True),
            expiry=datetime.now(UTC) + timedelta(seconds=settings.download_sas_minutes))
        
        return sas_token
    
    def create_upload_container(self, game_name: str):
        container_name = self.game_container_name(game_name)
        
        try:
            self.blob_service_client.create_container(container_name)
        except ResourceExistsError:
            raise ResourceExistsError(f"Fatal Error: Container '{container_name}' already exists.")
        
    def generate_upload_sas(self, game_name: str) -> tuple[str, str]:
        container_name = self.game_container_name(game_name)
        sas_token = generate_container_sas(
            account_name=settings.azure_account_name,
            container_name=container_name,
            account_key=settings.azure_account_key,
            permission=ContainerSasPermissions(read=True, write=True, list=True),
            expiry=datetime.now(UTC) + timedelta(seconds=settings.upload_sas_minutes))
        
        return sas_token, container_name