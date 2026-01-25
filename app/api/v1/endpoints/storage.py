"""Storage API endpoints for Azure Blob Storage operations."""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field

from app.services.azure_storage_service import azure_storage_service
from azure.storage.blob import BlobSasPermissions

logger = logging.getLogger(__name__)

router = APIRouter()


class PresignedUrlRequest(BaseModel):
    """Request model for generating pre-signed URL."""
    blob_name: str = Field(..., description="Name of the blob in the container")
    expiration_minutes: Optional[int] = Field(
        default=60,
        ge=1,
        le=1440,
        description="Number of minutes until the URL expires (1-1440, default: 60)"
    )
    permissions: Optional[str] = Field(
        default="read",
        description="Permissions for the URL: 'read', 'write', or 'read,write'"
    )


class PresignedUrlResponse(BaseModel):
    """Response model for pre-signed URL generation."""
    presigned_url: str = Field(..., description="Pre-signed URL for the blob")
    blob_name: str = Field(..., description="Name of the blob")
    expiration_minutes: int = Field(..., description="Expiration time in minutes")
    expires_at: str = Field(..., description="ISO format timestamp when URL expires")


class UploadResponse(BaseModel):
    """Response model for file upload."""
    blob_url: str = Field(..., description="URL of the uploaded blob")
    blob_name: str = Field(..., description="Name of the blob in the container")
    uploaded_at: str = Field(..., description="ISO format timestamp of upload")


@router.post("/presigned-url", response_model=PresignedUrlResponse)
async def generate_presigned_url(request: PresignedUrlRequest):
    """
    Generate a pre-signed (SAS) URL for uploading or downloading a blob.
    
    This endpoint creates a time-limited URL that can be used to access
    a blob in Azure Storage without requiring authentication.
    
    **Use cases:**
    - Allow clients to upload files directly to Azure Storage
    - Provide temporary access to private blobs
    - Enable secure file sharing with expiration
    
    **Permissions:**
    - `read`: Download/view the blob
    - `write`: Upload/overwrite the blob
    - `read,write`: Both read and write access
    """
    try:
        # Parse permissions
        permissions = None
        if request.permissions:
            perm_list = [p.strip() for p in request.permissions.split(",")]
            if "read" in perm_list and "write" in perm_list:
                permissions = BlobSasPermissions(read=True, write=True)
            elif "write" in perm_list:
                permissions = BlobSasPermissions(write=True)
            else:
                permissions = BlobSasPermissions(read=True)
        
        # Generate pre-signed URL
        presigned_url = azure_storage_service.generate_presigned_url(
            blob_name=request.blob_name,
            expiration_minutes=request.expiration_minutes,
            permissions=permissions
        )
        
        if not presigned_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate pre-signed URL. Check Azure Storage configuration."
            )
        
        # Calculate expiration timestamp
        expires_at = datetime.utcnow() + timedelta(minutes=request.expiration_minutes)
        
        return PresignedUrlResponse(
            presigned_url=presigned_url,
            blob_name=request.blob_name,
            expiration_minutes=request.expiration_minutes,
            expires_at=expires_at.isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error generating pre-signed URL: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating pre-signed URL: {str(e)}"
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    blob_name: Optional[str] = Form(
        None,
        description="Custom blob name. If not provided, a UUID-based name will be generated."
    ),
    folder: Optional[str] = Form(
        None,
        description="Optional folder path prefix for organizing files (e.g., 'images/', 'documents/')"
    )
):
    """
    Upload a file directly to Azure Blob Storage.
    
    This endpoint accepts a file upload and stores it in Azure Storage.
    The file can be organized in folders by providing a folder prefix.
    
    **File naming:**
    - If `blob_name` is provided, it will be used as-is
    - If not provided, a UUID-based name will be generated
    - Original filename can be preserved by including it in `blob_name`
    
    **Example blob names:**
    - `images/profile.jpg` (with folder="images/")
    - `documents/report-2024.pdf` (with folder="documents/")
    - `{uuid}-original-filename.jpg` (auto-generated)
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Generate blob name if not provided
        if not blob_name:
            # Preserve original extension if possible
            original_filename = file.filename or "file"
            file_extension = ""
            if "." in original_filename:
                file_extension = "." + original_filename.split(".")[-1]
            
            blob_name = f"{uuid4()}{file_extension}"
        
        # Add folder prefix if provided
        if folder:
            # Ensure folder ends with /
            if not folder.endswith("/"):
                folder += "/"
            blob_name = f"{folder}{blob_name}"
        
        # Determine content type
        content_type = file.content_type
        
        # Upload file
        blob_url = await azure_storage_service.upload_file_async(
            file_data=file_content,
            blob_name=blob_name,
            content_type=content_type,
            metadata={
                "original_filename": file.filename or "unknown",
                "uploaded_at": datetime.utcnow().isoformat(),
                "content_type": content_type or "application/octet-stream"
            }
        )
        
        if not blob_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload file. Check Azure Storage configuration."
            )
        
        return UploadResponse(
            blob_url=blob_url,
            blob_name=blob_name,
            uploaded_at=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )


@router.get("/presigned-url")
async def generate_presigned_url_get(
    blob_name: str = Query(..., description="Name of the blob in the container"),
    expiration_minutes: int = Query(
        default=60,
        ge=1,
        le=1440,
        description="Number of minutes until the URL expires (1-1440, default: 60)"
    ),
    permissions: str = Query(
        default="read",
        description="Permissions for the URL: 'read', 'write', or 'read,write'"
    )
):
    """
    Generate a pre-signed (SAS) URL using GET method (query parameters).
    
    This is an alternative to the POST endpoint, useful for simple GET requests.
    See the POST endpoint documentation for more details.
    """
    try:
        # Parse permissions
        perm_list = [p.strip() for p in permissions.split(",")]
        if "read" in perm_list and "write" in perm_list:
            blob_permissions = BlobSasPermissions(read=True, write=True)
        elif "write" in perm_list:
            blob_permissions = BlobSasPermissions(write=True)
        else:
            blob_permissions = BlobSasPermissions(read=True)
        
        # Generate pre-signed URL
        presigned_url = azure_storage_service.generate_presigned_url(
            blob_name=blob_name,
            expiration_minutes=expiration_minutes,
            permissions=blob_permissions
        )
        
        if not presigned_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate pre-signed URL. Check Azure Storage configuration."
            )
        
        # Calculate expiration timestamp
        expires_at = datetime.utcnow() + timedelta(minutes=expiration_minutes)
        
        return PresignedUrlResponse(
            presigned_url=presigned_url,
            blob_name=blob_name,
            expiration_minutes=expiration_minutes,
            expires_at=expires_at.isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error generating pre-signed URL: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating pre-signed URL: {str(e)}"
        )
