import os
import io
import hashlib
from typing import Tuple, Generator, BinaryIO, Optional
from fastapi import UploadFile, HTTPException, status
from app.config import settings

class StorageManager:
    """
    Unified Storage Manager supporting local disk and S3-compatible object storage
    (Cloudflare R2, AWS S3, MinIO).
    Preserves SHA-256 integrity, private access, and zero public exposure.
    """
    def __init__(self):
        self.backend = settings.STORAGE_BACKEND.lower()
        self._s3_client = None

        if self.backend == "s3":
            try:
                import boto3
                from botocore.config import Config
                
                cfg = Config(signature_version="s3v4")
                kwargs = {
                    "config": cfg,
                    "region_name": settings.S3_REGION_NAME or "auto"
                }
                if settings.S3_ENDPOINT_URL:
                    kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
                if settings.S3_ACCESS_KEY_ID and settings.S3_SECRET_ACCESS_KEY:
                    kwargs["aws_access_key_id"] = settings.S3_ACCESS_KEY_ID
                    kwargs["aws_secret_access_key"] = settings.S3_SECRET_ACCESS_KEY

                self._s3_client = boto3.client("s3", **kwargs)
                self.bucket = settings.S3_BUCKET_NAME
            except Exception as e:
                # Fallback to local if S3 client configuration fails
                self.backend = "local"
                self._s3_client = None

        if self.backend == "local":
            if settings.ENVIRONMENT.lower() == "production" and not settings.ALLOW_EPHEMERAL_STORAGE:
                raise RuntimeError(
                    "Production safety violation: STORAGE_DIR cannot accidentally become the production storage backend "
                    "on ephemeral cloud instances. Configure STORAGE_BACKEND=s3 (e.g. Cloudflare R2 / AWS S3) or "
                    "explicitly set ALLOW_EPHEMERAL_STORAGE=true to opt into local ephemeral storage."
                )
            os.makedirs(settings.STORAGE_DIR, exist_ok=True)

    async def save_file(
        self,
        file: UploadFile,
        file_uuid: str,
        ext: str,
        max_size: int = 10 * 1024 * 1024
    ) -> Tuple[str, int, str]:
        """
        Saves file to chosen storage backend.
        Returns: (storage_identifier, file_size, sha256_hash)
        """
        hasher = hashlib.sha256()
        file_size = 0
        storage_filename = f"{file_uuid}{ext}.bin"

        if self.backend == "s3" and self._s3_client:
            key = f"documents/{storage_filename}"
            buffer = io.BytesIO()
            while chunk := await file.read(1024 * 1024):
                file_size += len(chunk)
                if file_size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {max_size // (1024 * 1024)}MB."
                    )
                hasher.update(chunk)
                buffer.write(chunk)

            buffer.seek(0)
            self._s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=buffer.getvalue(),
                ContentType="application/octet-stream"
            )
            return key, file_size, hasher.hexdigest()
        else:
            # Local storage backend
            os.makedirs(settings.STORAGE_DIR, exist_ok=True)
            storage_path = os.path.join(settings.STORAGE_DIR, storage_filename)
            try:
                import aiofiles
                async with aiofiles.open(storage_path, "wb") as out_file:
                    while chunk := await file.read(1024 * 1024):
                        file_size += len(chunk)
                        if file_size > max_size:
                            raise HTTPException(
                                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                detail=f"File exceeds maximum allowed size of {max_size // (1024 * 1024)}MB."
                            )
                        hasher.update(chunk)
                        await out_file.write(chunk)
            except Exception:
                if os.path.exists(storage_path):
                    os.remove(storage_path)
                raise

            return storage_path, file_size, hasher.hexdigest()

    def exists(self, storage_identifier: str) -> bool:
        if self.backend == "s3" and self._s3_client:
            try:
                self._s3_client.head_object(Bucket=self.bucket, Key=storage_identifier)
                return True
            except Exception:
                return False
        return os.path.exists(storage_identifier)

    def delete(self, storage_identifier: str) -> bool:
        if self.backend == "s3" and self._s3_client:
            try:
                self._s3_client.delete_object(Bucket=self.bucket, Key=storage_identifier)
                return True
            except Exception:
                return False
        if os.path.exists(storage_identifier):
            try:
                os.remove(storage_identifier)
                return True
            except OSError:
                return False
        return False

    def get_stream(self, storage_identifier: str) -> Generator[bytes, None, None]:
        if self.backend == "s3" and self._s3_client:
            resp = self._s3_client.get_object(Bucket=self.bucket, Key=storage_identifier)
            stream = resp["Body"]
            while chunk := stream.read(1024 * 1024):
                yield chunk
        else:
            with open(storage_identifier, "rb") as f:
                while chunk := f.read(1024 * 1024):
                    yield chunk

    def get_presigned_upload_url(
        self,
        storage_identifier: str,
        content_type: str = "application/octet-stream",
        content_length: Optional[int] = None,
        expires_in: int = 300
    ) -> Optional[str]:
        """
        Generates S3 Presigned PUT URL for direct browser-to-S3 uploads.
        Bypasses serverless request body limits (e.g. Vercel 4.5MB limit)
        while preserving server-side authorization and private buckets.
        """
        if self.backend == "s3" and self._s3_client:
            try:
                return self._s3_client.generate_presigned_url(
                    "put_object",
                    Params={
                        "Bucket": self.bucket,
                        "Key": storage_identifier,
                        "ContentType": content_type,
                        **({"ContentLength": content_length} if content_length is not None else {}),
                    },
                    ExpiresIn=expires_in
                )
            except Exception as e:
                print(f"Error generating presigned upload url: {e}")
                return None
        return None


    def put_verified_object(self, storage_identifier: str, data: bytes, content_type: str) -> None:
        """Persist server-verified bytes under a fresh key unreachable by the presigned PUT URL."""
        if self.backend != "s3" or not self._s3_client:
            raise RuntimeError("Verified direct-upload finalization requires configured S3 storage.")
        self._s3_client.put_object(
            Bucket=self.bucket,
            Key=storage_identifier,
            Body=data,
            ContentLength=len(data),
            ContentType=content_type,
        )

    def read_object_limited(self, storage_identifier: str, max_size: int) -> bytes:
        """Read an object only up to max_size + 1 bytes for server-side verification."""
        if self.backend == "s3" and self._s3_client:
            response = self._s3_client.get_object(Bucket=self.bucket, Key=storage_identifier)
            body = response["Body"]
            try:
                data = body.read(max_size + 1)
            finally:
                body.close()
            return data
        with open(storage_identifier, "rb") as handle:
            return handle.read(max_size + 1)

    def get_presigned_download_url(
        self,
        storage_identifier: str,
        filename: Optional[str] = None,
        expires_in: int = 300
    ) -> Optional[str]:
        """
        Generates S3 Presigned GET URL for direct browser downloads.
        Bypasses serverless response body limits while enforcing zero-trust auth.
        """
        if self.backend == "s3" and self._s3_client:
            try:
                params = {
                    "Bucket": self.bucket,
                    "Key": storage_identifier
                }
                if filename:
                    # Sanitize filename for HTTP header
                    clean_name = filename.replace('"', '\\"')
                    params["ResponseContentDisposition"] = f'attachment; filename="{clean_name}"'
                return self._s3_client.generate_presigned_url(
                    "get_object",
                    Params=params,
                    ExpiresIn=expires_in
                )
            except Exception as e:
                print(f"Error generating presigned download url: {e}")
                return None
        return None

    def get_object_metadata(self, storage_identifier: str) -> Optional[dict]:
        """
        Retrieves object metadata (size, content type) from S3 to verify uploaded assets.
        """
        if self.backend == "s3" and self._s3_client:
            try:
                res = self._s3_client.head_object(Bucket=self.bucket, Key=storage_identifier)
                return {
                    "size": res.get("ContentLength", 0),
                    "content_type": res.get("ContentType", ""),
                    "etag": res.get("ETag", "").strip('"')
                }
            except Exception:
                return None
        if os.path.exists(storage_identifier):
            return {
                "size": os.path.getsize(storage_identifier),
                "content_type": "application/octet-stream",
                "etag": ""
            }
        return None

storage_manager = StorageManager()
