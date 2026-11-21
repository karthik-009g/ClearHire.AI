"""Storage abstraction with local filesystem and S3-compatible providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import uuid

from app.utils.config import settings


class StorageProvider(ABC):
    @abstractmethod
    def save_file(self, file_bytes: bytes, filename: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_file(self, stored_path: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def delete_file(self, stored_path: str) -> bool:
        raise NotImplementedError


class LocalStorageProvider(StorageProvider):
    def __init__(self, root_dir: str):
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_bytes: bytes, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        safe_name = f"{uuid.uuid4().hex}{suffix}"
        destination = self.root / safe_name
        destination.write_bytes(file_bytes)
        return str(destination)

    def get_file(self, stored_path: str) -> bytes:
        file_path = Path(stored_path)
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"File not found: {stored_path}")
        return file_path.read_bytes()

    def delete_file(self, stored_path: str) -> bool:
        file_path = Path(stored_path)
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False


class S3StorageProvider(StorageProvider):
    def __init__(
        self,
        bucket: str | None = None,
        region: str | None = None,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        use_ssl: bool = True,
        force_path_style: bool = True,
    ):
        self.bucket = bucket or settings.storage_bucket
        if not self.bucket:
            raise ValueError("storage_bucket must be configured when storage_provider='s3'")

        try:
            import boto3
            from botocore.config import Config
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("boto3 is required for S3 storage support. Install it in the backend environment.") from exc

        self.client = boto3.client(
            "s3",
            region_name=region or settings.storage_region,
            endpoint_url=endpoint_url or settings.storage_endpoint_url,
            aws_access_key_id=access_key or settings.storage_access_key,
            aws_secret_access_key=secret_key or settings.storage_secret_key,
            use_ssl=use_ssl if use_ssl is not None else settings.storage_use_ssl,
            config=Config(s3={"addressing_style": "path" if force_path_style else "virtual"}),
        )

    def save_file(self, file_bytes: bytes, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        key = f"{uuid.uuid4().hex}{suffix}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=file_bytes)
        return f"s3://{self.bucket}/{key}"

    def get_file(self, stored_path: str) -> bytes:
        bucket, key = self._parse_s3_path(stored_path)
        if not bucket or not key:
            raise ValueError(f"Invalid S3 stored path: {stored_path}")
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def delete_file(self, stored_path: str) -> bool:
        bucket, key = self._parse_s3_path(stored_path)
        if not bucket or not key:
            return False
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    def _parse_s3_path(self, stored_path: str) -> tuple[str | None, str | None]:
        if not stored_path.startswith("s3://"):
            return None, None
        path = stored_path[5:]
        bucket, _, key = path.partition("/")
        return bucket or None, key or None


def get_storage_provider(root_dir: str) -> StorageProvider:
    if str(settings.storage_provider).lower() == "s3":
        return S3StorageProvider(
            bucket=settings.storage_bucket,
            region=settings.storage_region,
            endpoint_url=settings.storage_endpoint_url,
            access_key=settings.storage_access_key,
            secret_key=settings.storage_secret_key,
            use_ssl=settings.storage_use_ssl,
            force_path_style=settings.storage_force_path_style,
        )
    return LocalStorageProvider(root_dir=root_dir)
