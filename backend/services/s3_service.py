import boto3
from datetime import datetime
from typing import Optional
from config import settings


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_s3_access_key,
            aws_secret_access_key=settings.aws_s3_secret_access_key,
            region_name=settings.aws_s3_region
        )
        self.bucket_name = settings.aws_s3_bucket

    def upload_podcast(self, file_path: str, article_id: Optional[int] = None) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if article_id:
            s3_key = f"podcasts/article_{article_id}_{timestamp}.mp3"
        else:
            s3_key = f"podcasts/podcast_{timestamp}.mp3"

        self.s3_client.upload_file(
            file_path,
            self.bucket_name,
            s3_key,
            ExtraArgs={'ContentType': 'audio/mpeg'}
        )

        s3_url = f"https://{self.bucket_name}.s3.{settings.aws_s3_region}.amazonaws.com/{s3_key}"
        return s3_url


s3_service = S3Service()
