"""Azure Storage service for file uploads and pre-signed URL generation."""
import logging
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse

from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from azure.core.exceptions import AzureError

from app.core.config import settings

logger = logging.getLogger(__name__)


class AzureStorageService:
    """Service for interacting with Azure Blob Storage."""
    
    def __init__(self):
        """Initialize Azure Storage client."""
        self.account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        self.account_key = settings.AZURE_STORAGE_ACCOUNT_KEY
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        
        # Initialize blob service client
        if self.connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
        elif self.account_name and self.account_key:
            account_url = f"https://{self.account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=self.account_key
            )
        else:
            logger.warning(
                "Azure Storage credentials not configured. "
                "Set AZURE_STORAGE_CONNECTION_STRING or both "
                "AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY."
            )
            self.blob_service_client = None
        
        # Ensure container exists
        if self.blob_service_client:
            self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        """Ensure the container exists, create if it doesn't."""
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            if not container_client.exists():
                container_client.create_container()
                logger.info(f"Created container: {self.container_name}")
        except AzureError as e:
            logger.error(f"Error ensuring container exists: {e}")
            raise
    
    def generate_presigned_url(
        self,
        blob_name: str,
        expiration_minutes: int = 60,
        permissions: Optional[BlobSasPermissions] = None
    ) -> Optional[str]:
        """
        Generate a pre-signed (SAS) URL for a blob.
        
        Args:
            blob_name: Name of the blob in the container
            expiration_minutes: Number of minutes until the URL expires (default: 60)
            permissions: BlobSasPermissions object. If None, defaults to read permission.
        
        Returns:
            Pre-signed URL string or None if generation fails
        """
        if not self.blob_service_client or not self.account_key:
            logger.error("Azure Storage not properly configured")
            return None
        
        try:
            # Default to read permission if not specified
            if permissions is None:
                permissions = BlobSasPermissions(read=True)
            
            # Calculate expiration time
            expiry_time = datetime.utcnow() + timedelta(minutes=expiration_minutes)
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=self.account_key,
                permission=permissions,
                expiry=expiry_time
            )
            
            # Construct the full URL
            blob_url = (
                f"https://{self.account_name}.blob.core.windows.net/"
                f"{self.container_name}/{blob_name}"
            )
            
            presigned_url = f"{blob_url}?{sas_token}"
            
            logger.info(f"Generated pre-signed URL for blob: {blob_name}")
            return presigned_url
            
        except Exception as e:
            logger.error(f"Error generating pre-signed URL: {e}")
            return None
    
    def upload_file(
        self,
        file_data: bytes,
        blob_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[str]:
        """
        Upload a file to Azure Blob Storage.
        
        Args:
            file_data: File content as bytes
            blob_name: Name of the blob in the container
            content_type: MIME type of the file (optional)
            metadata: Dictionary of metadata to attach to the blob (optional)
        
        Returns:
            URL of the uploaded blob or None if upload fails
        """
        if not self.blob_service_client:
            logger.error("Azure Storage not properly configured")
            return None
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Upload the file
            upload_kwargs = {}
            if content_type:
                upload_kwargs["content_settings"] = ContentSettings(
                    content_type=content_type
                )
            if metadata:
                upload_kwargs["metadata"] = metadata
            
            blob_client.upload_blob(
                data=file_data,
                overwrite=True,
                **upload_kwargs
            )
            
            # Return the blob URL
            blob_url = blob_client.url
            logger.info(f"Successfully uploaded file: {blob_name}")
            return blob_url
            
        except AzureError as e:
            logger.error(f"Error uploading file to Azure Storage: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading file: {e}")
            return None
    
    async def upload_file_async(
        self,
        file_data: bytes,
        blob_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[str]:
        """
        Upload a file to Azure Blob Storage asynchronously.
        
        Args:
            file_data: File content as bytes
            blob_name: Name of the blob in the container
            content_type: MIME type of the file (optional)
            metadata: Dictionary of metadata to attach to the blob (optional)
        
        Returns:
            URL of the uploaded blob or None if upload fails
        """
        # Note: azure-storage-blob doesn't have native async support,
        # but we can run it in an executor for async compatibility
        import asyncio
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.upload_file,
            file_data,
            blob_name,
            content_type,
            metadata
        )
    
    def delete_blob(self, blob_name: str) -> bool:
        """
        Delete a blob from Azure Storage.
        
        Args:
            blob_name: Name of the blob to delete
        
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.blob_service_client:
            logger.error("Azure Storage not properly configured")
            return False
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            logger.info(f"Successfully deleted blob: {blob_name}")
            return True
        except AzureError as e:
            logger.error(f"Error deleting blob: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting blob: {e}")
            return False
    
    def blob_exists(self, blob_name: str) -> bool:
        """
        Check if a blob exists in the container.
        
        Args:
            blob_name: Name of the blob to check
        
        Returns:
            True if blob exists, False otherwise
        """
        if not self.blob_service_client:
            return False
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            return blob_client.exists()
        except Exception as e:
            logger.error(f"Error checking blob existence: {e}")
            return False


# Singleton instance
azure_storage_service = AzureStorageService()
