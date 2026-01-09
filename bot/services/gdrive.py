"""
Google Drive API service for file operations
"""
import os
import io
import logging
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from bot.config import GDRIVE_CREDENTIALS_FILE, GDRIVE_BASE_FOLDER_ID, TEMP_FILES_DIR

logger = logging.getLogger(__name__)

# Google Drive service instance
_drive_service = None


def get_drive_service():
    """Get or create Google Drive service instance"""
    global _drive_service

    if _drive_service is not None:
        return _drive_service

    try:
        credentials = service_account.Credentials.from_service_account_file(
            GDRIVE_CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        _drive_service = build('drive', 'v3', credentials=credentials)
        return _drive_service
    except Exception as e:
        logger.error(f"Failed to initialize Google Drive service: {e}")
        return None


async def download_file(file_id: str, destination_path: str) -> bool:
    """
    Download file from Google Drive
    Returns True if successful, False otherwise
    """
    try:
        service = get_drive_service()
        if not service:
            logger.error("Google Drive service not available")
            return False

        request = service.files().get_media(fileId=file_id)

        # Create temp directory if not exists
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

        with open(destination_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Download progress: {int(status.progress() * 100)}%")

        logger.info(f"File downloaded to {destination_path}")
        return True

    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        return False


async def get_file_as_bytes(file_id: str) -> Optional[bytes]:
    """
    Download file from Google Drive and return as bytes
    """
    try:
        service = get_drive_service()
        if not service:
            logger.error("Google Drive service not available")
            return None

        request = service.files().get_media(fileId=file_id)
        file_data = io.BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        file_data.seek(0)
        return file_data.read()

    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        return None


async def get_file_info(file_id: str) -> Optional[dict]:
    """Get file metadata from Google Drive"""
    try:
        service = get_drive_service()
        if not service:
            return None

        file_info = service.files().get(
            fileId=file_id,
            fields='id, name, size, mimeType, modifiedTime'
        ).execute()

        return file_info

    except Exception as e:
        logger.error(f"Error getting file info {file_id}: {e}")
        return None


async def list_files_in_folder(folder_id: str = None) -> list:
    """List files in a Google Drive folder"""
    try:
        service = get_drive_service()
        if not service:
            return []

        folder = folder_id or GDRIVE_BASE_FOLDER_ID
        query = f"'{folder}' in parents and trashed = false"

        results = service.files().list(
            q=query,
            fields="files(id, name, size, mimeType, modifiedTime)",
            orderBy="modifiedTime desc"
        ).execute()

        return results.get('files', [])

    except Exception as e:
        logger.error(f"Error listing files in folder: {e}")
        return []


def ensure_temp_dir():
    """Ensure temp directory exists"""
    os.makedirs(TEMP_FILES_DIR, exist_ok=True)


def cleanup_temp_file(file_path: str):
    """Remove temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temp file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up temp file {file_path}: {e}")
