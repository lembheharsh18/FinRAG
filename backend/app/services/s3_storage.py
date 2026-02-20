"""
S3 Storage Service for FinRAG.

Handles file uploads, downloads, and deletion using AWS S3.
Falls back to local filesystem when S3 is not configured.
"""

import os
import logging
from typing import Optional
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class S3StorageError(Exception):
    """Custom exception for S3 storage errors."""

    def __init__(self, message: str, error_code: str = "S3_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class S3StorageService:
    """
    S3 file storage service with local fallback.

    When AWS credentials and bucket name are configured, files are
    stored in S3. Otherwise, falls back to the local upload directory.
    """

    def __init__(self) -> None:
        """Initialize S3 client if credentials are available."""
        self._client = None
        self._bucket: Optional[str] = getattr(settings, "aws_s3_bucket_name", None)
        self._region: str = getattr(settings, "aws_region", "us-east-1")
        self._use_s3: bool = False

        if self._bucket and getattr(settings, "aws_access_key_id", None):
            try:
                import boto3
                from botocore.config import Config as BotoConfig

                self._client = boto3.client(
                    "s3",
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=self._region,
                    config=BotoConfig(
                        retries={"max_attempts": 3, "mode": "standard"},
                        connect_timeout=10,
                        read_timeout=30,
                    ),
                )
                self._use_s3 = True
                logger.info(
                    f"S3 storage initialized — bucket: {self._bucket}, region: {self._region}"
                )
            except ImportError:
                logger.warning(
                    "boto3 not installed — falling back to local file storage. "
                    "Install boto3: pip install boto3"
                )
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
        else:
            logger.info("S3 not configured — using local file storage")

    @property
    def is_s3_enabled(self) -> bool:
        """Check whether S3 storage is active."""
        return self._use_s3

    def upload_file(
        self,
        local_path: str,
        s3_key: str,
        content_type: str = "application/pdf",
    ) -> str:
        """
        Upload a file to S3 (or keep local).

        Args:
            local_path: Path to the local file.
            s3_key: The S3 object key (e.g. "users/{uid}/{doc_id}.pdf").
            content_type: MIME type of the file.

        Returns:
            The S3 key on success, or the local path if using local storage.
        """
        if not os.path.exists(local_path):
            raise S3StorageError(f"Local file not found: {local_path}", "FILE_NOT_FOUND")

        if not self._use_s3:
            logger.debug(f"Local storage — file stays at: {local_path}")
            return local_path

        try:
            self._client.upload_file(
                Filename=local_path,
                Bucket=self._bucket,
                Key=s3_key,
                ExtraArgs={"ContentType": content_type},
            )
            logger.info(f"Uploaded to S3: s3://{self._bucket}/{s3_key}")
            return s3_key
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise S3StorageError(f"Failed to upload file to S3: {e}", "UPLOAD_FAILED")

    def download_file(self, s3_key: str, local_path: str) -> str:
        """
        Download a file from S3 to a local path.

        Args:
            s3_key: The S3 object key.
            local_path: Destination path on the local filesystem.

        Returns:
            The local path where the file was saved.
        """
        if not self._use_s3:
            # In local mode, s3_key IS the local path
            if os.path.exists(s3_key):
                return s3_key
            raise S3StorageError(f"Local file not found: {s3_key}", "FILE_NOT_FOUND")

        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            self._client.download_file(
                Bucket=self._bucket,
                Key=s3_key,
                Filename=local_path,
            )
            logger.info(f"Downloaded from S3: {s3_key} → {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"S3 download failed: {e}")
            raise S3StorageError(f"Failed to download file from S3: {e}", "DOWNLOAD_FAILED")

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3 (or local filesystem).

        Args:
            s3_key: The S3 object key or local path.

        Returns:
            True if deletion succeeded.
        """
        if not self._use_s3:
            try:
                if os.path.exists(s3_key):
                    os.unlink(s3_key)
                    logger.info(f"Deleted local file: {s3_key}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete local file: {e}")
                return False

        try:
            self._client.delete_object(Bucket=self._bucket, Key=s3_key)
            logger.info(f"Deleted from S3: s3://{self._bucket}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"S3 deletion failed: {e}")
            raise S3StorageError(f"Failed to delete file from S3: {e}", "DELETE_FAILED")

    def get_presigned_url(self, s3_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for temporary access to an S3 object.

        Args:
            s3_key: The S3 object key.
            expires_in: Seconds until the URL expires (default 1 hour).

        Returns:
            Presigned URL string, or None if not using S3.
        """
        if not self._use_s3:
            return None

        try:
            url = self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": s3_key},
                ExpiresIn=expires_in,
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None


# Module-level singleton
_s3_service: Optional[S3StorageService] = None


def get_s3_storage_service() -> S3StorageService:
    """Get or create the S3 storage service singleton."""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3StorageService()
    return _s3_service
