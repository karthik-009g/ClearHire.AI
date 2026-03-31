"""Storage abstraction to support Local now and S3 later."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import uuid


class StorageProvider(ABC):
    @abstractmethod
    def save_file(self, file_bytes: bytes, filename: str) -> str:
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

    def delete_file(self, stored_path: str) -> bool:
        file_path = Path(stored_path)
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False


def get_storage_provider(root_dir: str) -> StorageProvider:
    return LocalStorageProvider(root_dir=root_dir)
