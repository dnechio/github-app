import tempfile
from functools import lru_cache
from pathlib import Path

import boto3
from loguru import logger

from app.core.config import settings
from app.db.mongodb import get_file_s3_key


@lru_cache(maxsize=1)
def _s3():
    kwargs = dict(
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    if settings.AWS_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


def download_file_to_tmp(file_id: str) -> Path:
    s3_key = get_file_s3_key(file_id)
    if not s3_key:
        raise FileNotFoundError(f"No S3 key found for file_id={file_id}")

    suffix = Path(s3_key).suffix or ".bin"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    logger.debug(f"Downloading s3://{settings.AWS_S3_BUCKET}/{s3_key} → {tmp.name}")
    _s3().download_fileobj(settings.AWS_S3_BUCKET, s3_key, tmp)
    tmp.flush()

    return Path(tmp.name)


def upload_text(content: str, s3_key: str) -> None:
    """Uploads extracted text back to S3 (used to store the processed text for later use)."""
    _s3().put_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=s3_key,
        Body=content.encode("utf-8"),
        ContentType="text/plain; charset=utf-8",
    )
