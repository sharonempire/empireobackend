"""AWS S3 file upload/download service."""

import logging
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger("empireo.s3")

_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
            raise RuntimeError("AWS credentials are not configured")
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            config=Config(signature_version="s3v4"),
        )
    return _s3_client


def generate_file_key(folder: str, original_filename: str) -> str:
    """Generate a unique S3 key: folder/YYYY/MM/uuid_filename."""
    now = datetime.now(timezone.utc)
    ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else ""
    unique_name = f"{uuid.uuid4().hex}_{original_filename}"
    return f"{folder}/{now.year}/{now.month:02d}/{unique_name}"


def upload_file(file_bytes: bytes, file_key: str, content_type: str = "application/octet-stream") -> str:
    """Upload bytes to S3. Returns the file key."""
    client = get_s3_client()
    client.put_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=file_key,
        Body=file_bytes,
        ContentType=content_type,
    )
    logger.info("Uploaded %s to S3 bucket %s", file_key, settings.AWS_S3_BUCKET)
    return file_key


def generate_presigned_url(file_key: str, expires_in: int = 3600) -> str:
    """Generate a presigned download URL. Default expiry: 1 hour."""
    client = get_s3_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_S3_BUCKET, "Key": file_key},
        ExpiresIn=expires_in,
    )
    return url


def generate_presigned_upload(file_key: str, content_type: str = "application/octet-stream", expires_in: int = 3600) -> dict:
    """Generate a presigned POST for direct browser upload. Returns {url, fields}."""
    client = get_s3_client()
    response = client.generate_presigned_post(
        Bucket=settings.AWS_S3_BUCKET,
        Key=file_key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, 100 * 1024 * 1024],  # 100MB max
        ],
        ExpiresIn=expires_in,
    )
    return response


def delete_file(file_key: str) -> bool:
    """Delete a file from S3. Returns True if successful."""
    client = get_s3_client()
    try:
        client.delete_object(Bucket=settings.AWS_S3_BUCKET, Key=file_key)
        logger.info("Deleted %s from S3 bucket %s", file_key, settings.AWS_S3_BUCKET)
        return True
    except ClientError as e:
        logger.error("Failed to delete %s: %s", file_key, e)
        return False


def file_exists(file_key: str) -> bool:
    """Check if a file exists in S3."""
    client = get_s3_client()
    try:
        client.head_object(Bucket=settings.AWS_S3_BUCKET, Key=file_key)
        return True
    except ClientError:
        return False
