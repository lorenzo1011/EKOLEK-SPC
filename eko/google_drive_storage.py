"""Google Drive Storage backend for Django file uploads."""

import io
import json
import logging
import mimetypes
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

logger = logging.getLogger(__name__)

GDRIVE_IMAGE_URL_TEMPLATE = "https://lh3.googleusercontent.com/d/{file_id}"

@deconstructible
class GoogleDriveStorage(Storage):
    """
    Google Drive Storage backend for Django
    """
    
    def __init__(self, credentials_file=None, folder_id=None):
        self.credentials_file = credentials_file or getattr(settings, 'GOOGLE_DRIVE_CREDENTIALS_FILE', None)
        self.credentials_json = getattr(settings, 'GOOGLE_DRIVE_CREDENTIALS_JSON', None)
        
        # OAuth credentials (preferred over service account)
        self.oauth_refresh_token = getattr(settings, 'GOOGLE_DRIVE_OAUTH_REFRESH_TOKEN', None)
        self.oauth_client_id = getattr(settings, 'GOOGLE_DRIVE_OAUTH_CLIENT_ID', None)
        self.oauth_client_secret = getattr(settings, 'GOOGLE_DRIVE_OAUTH_CLIENT_SECRET', None)
        
        self.folder_id = folder_id or getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', None)
        self._service = None
        
        logger.info(f"GoogleDriveStorage initialized | OAuth: {bool(self.oauth_refresh_token)} | Folder: {self.folder_id}")
        
    @property
    def service(self):
        """Get or create Google Drive service"""
        if self._service is None:
            try:
                credentials = None
                
                # PREFERRED: Try OAuth first (more reliable than service accounts)
                if self.oauth_refresh_token and self.oauth_client_id and self.oauth_client_secret:
                    logger.info("Using OAuth credentials")
                    try:
                        credentials = OAuthCredentials(
                            None,  # No access token initially
                            refresh_token=self.oauth_refresh_token,
                            token_uri='https://oauth2.googleapis.com/token',
                            client_id=self.oauth_client_id,
                            client_secret=self.oauth_client_secret,
                            scopes=['https://www.googleapis.com/auth/drive.file']
                        )
                        
                        logger.info("Refreshing OAuth access token...")
                        credentials.refresh(Request())
                        logger.info("OAuth credentials refreshed successfully")
                    except Exception as e:
                        logger.error("OAuth authentication failed: %s", e)
                        credentials = None
                
                # FALLBACK: Try service account credentials JSON
                if credentials is None and self.credentials_json:
                    logger.info("Falling back to service account credentials")
                    try:
                        credentials_dict = json.loads(self.credentials_json)
                        
                        credentials = Credentials.from_service_account_info(
                            credentials_dict,
                            scopes=['https://www.googleapis.com/auth/drive.file']
                        )
                        logger.info("Service account credentials created")
                    except Exception as e:
                        logger.error("Service account authentication failed: %s", e)
                        credentials = None
                
                # FALLBACK: Try credentials file
                if credentials is None and self.credentials_file and os.path.exists(self.credentials_file):
                    logger.info("Using credentials file: %s", self.credentials_file)
                    credentials = Credentials.from_service_account_file(
                        self.credentials_file,
                        scopes=['https://www.googleapis.com/auth/drive.file']
                    )
                
                if credentials is None:
                    raise Exception("No valid Google Drive credentials found")
                
                # Build the service
                self._service = build('drive', 'v3', credentials=credentials)
                logger.info("Google Drive service initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Google Drive service: {e}")
                raise
        return self._service
    
    def _save(self, name, content):
        """Save file to Google Drive"""
        logger.info(f"_save called for: {name}")
        
        try:
            # Ensure we have a folder ID
            if not self.folder_id:
                error_msg = "Google Drive folder ID not configured"
                raise Exception(error_msg)
            
            # Prepare file metadata
            file_metadata = {
                'name': name,
                'parents': [self.folder_id]  # This puts it in your shared folder
            }
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(name)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Prepare file content
            file_content = content.read()
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=mime_type,
                resumable=False  # Try non-resumable upload first
            )
            
            # Upload file to your shared folder
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink,parents'
            ).execute()
            
            # Verify the file was created in the correct folder
            if self.folder_id not in file.get('parents', []):
                logger.warning(f"File may not be in the correct folder: {file}")
            
            # Set file permissions to be publicly viewable - CRITICAL for images to display
            try:
                permission = self.service.permissions().create(
                    fileId=file['id'],
                    body={
                        'role': 'reader',
                        'type': 'anyone',
                        'allowFileDiscovery': False
                    },
                    supportsAllDrives=True,
                    fields='id'
                ).execute()
                logger.info("Public permission set for file: %s (Permission ID: %s)", file['id'], permission.get('id'))
            except Exception as perm_error:
                logger.error("Failed to set public permissions: %s", perm_error)
                # This is critical - if permissions fail, the image won't be viewable
            
            logger.info(f"File uploaded to Google Drive: {name} (ID: {file['id']}) in folder {self.folder_id}")
            logger.info(f"WebContentLink: {file.get('webContentLink', 'N/A')}")
            return file['id']  # Return file ID as the "name"
            
        except Exception as e:
            logger.error(f"Error uploading file to Google Drive: {e}")
            # Instead of raising, fall back to local storage
            from django.core.files.storage import FileSystemStorage

            local_storage = FileSystemStorage()
            content.seek(0)  # Reset file pointer
            local_name = local_storage._save(name, content)
            logger.warning(f"Falling back to local storage for file: {name} -> {local_name}")
            return local_name
    
    def _open(self, name, mode='rb'):
        """Open file from Google Drive"""
        try:
            # Download file content
            file_content = self.service.files().get_media(fileId=name).execute()
            return ContentFile(file_content)
        except Exception as e:
            logger.error(f"Error opening file from Google Drive: {e}")
            raise
    
    def delete(self, name):
        """Delete file from Google Drive"""
        try:
            self.service.files().delete(fileId=name).execute()
            logger.info(f"File deleted from Google Drive: {name}")
        except Exception as e:
            logger.error(f"Error deleting file from Google Drive: {e}")
            raise
    
    def exists(self, name):
        """Check if file exists in Google Drive"""
        try:
            self.service.files().get(fileId=name).execute()
            return True
        except Exception:
            return False
    
    def listdir(self, path):
        """List directory contents (not applicable for Google Drive)"""
        return [], []
    
    def size(self, name):
        """Get file size"""
        try:
            file_metadata = self.service.files().get(fileId=name, fields='size').execute()
            return int(file_metadata.get('size', 0))
        except Exception:
            return 0
    
    def url(self, name):
        """Get public URL for full-size image."""
        return GDRIVE_IMAGE_URL_TEMPLATE.format(file_id=name)
    
    def get_available_name(self, name, max_length=None):
        """
        Return a filename that's free on the target storage system and
        available for new content to be written to.
        """
        return name
    
    def get_alternative_name(self, file_root, file_ext):
        """
        Return an alternative filename, by adding an underscore and a random 7
        character alphanumeric string (before the file extension, if one
        exists) to the filename.
        """
        import uuid
        return f"{file_root}_{uuid.uuid4().hex[:7]}{file_ext}"
