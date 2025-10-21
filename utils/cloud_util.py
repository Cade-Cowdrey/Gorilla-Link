import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from flask import current_app
from werkzeug.utils import secure_filename

def _s3_client():
    return boto3.client(
        "s3",
        region_name=current_app.config["S3_REGION"],
        aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
    )

def upload_file(file_storage, folder="uploads"):
    filename = secure_filename(file_storage.filename)
    key = f"{folder}/{filename}"
    bucket = current_app.config["S3_BUCKET"]
    client = _s3_client()
    client.upload_fileobj(
        file_storage,
        bucket,
        key,
        ExtraArgs={"ACL": "public-read", "ContentType": file_storage.mimetype or "application/octet-stream"}
    )
    region = current_app.config["S3_REGION"]
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"

def delete_file(key):
    bucket = current_app.config["S3_BUCKET"]
    client = _s3_client()
    try:
        client.delete_object(Bucket=bucket, Key=key)
        return True
    except (BotoCoreError, ClientError):
        return False
