from __future__ import annotations

from pathlib import Path

from app.services.storage import S3StorageProvider, get_storage_provider
from app.utils.config import settings


def test_storage_provider_uses_local_by_default(tmp_path):
    provider = get_storage_provider(str(tmp_path / "resumes"))
    assert provider.__class__.__name__ == "LocalStorageProvider"

    stored = provider.save_file(b"hello", "resume.txt")
    assert Path(stored).exists()
    assert Path(stored).read_bytes() == b"hello"
    assert provider.get_file(stored) == b"hello"
    assert provider.delete_file(stored) is True


def test_s3_provider_uses_mocked_client(monkeypatch):
    calls = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            calls["created"] = kwargs

        def put_object(self, Bucket, Key, Body):
            calls["put"] = {"Bucket": Bucket, "Key": Key, "Body": Body}

        def get_object(self, Bucket, Key):
            calls["get"] = {"Bucket": Bucket, "Key": Key}
            import io
            return {"Body": io.BytesIO(b"s3-content")}

        def delete_object(self, Bucket, Key):
            calls["delete"] = {"Bucket": Bucket, "Key": Key}

    monkeypatch.setattr("boto3.client", lambda *args, **kwargs: FakeClient(*args, **kwargs))
    settings.storage_provider = "s3"
    settings.storage_bucket = "demo-bucket"
    settings.storage_region = "ap-southeast-2"
    settings.storage_endpoint_url = "https://example.test"
    settings.storage_access_key = "key"
    settings.storage_secret_key = "secret"

    provider = S3StorageProvider(
        bucket="demo-bucket",
        region="ap-southeast-2",
        endpoint_url="https://example.test",
        access_key="key",
        secret_key="secret",
    )
    saved = provider.save_file(b"payload", "resume.pdf")
    assert saved == "s3://demo-bucket/" + saved.split("/")[-1]
    assert calls["put"]["Bucket"] == "demo-bucket"
    assert provider.get_file(saved) == b"s3-content"
    assert calls["get"]["Bucket"] == "demo-bucket"
    assert provider.delete_file(saved) is True

    settings.storage_provider = "local"
