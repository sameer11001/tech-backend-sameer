import os
import uuid6
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig


class S3Service:

    def __init__(self, s3_client , bucket_name: str,transfer_config: TransferConfig, aws_region:str, aws_s3_bucket_name:str, tmp_dir: str = "./tmp"):
        self.s3_client  = s3_client
        self.bucket = bucket_name
        self.aws_region = aws_region
        self.aws_s3_bucket_name = aws_s3_bucket_name
        self.transfer_config = transfer_config
        self.tmp_dir = tmp_dir
        os.makedirs(self.tmp_dir, exist_ok=True)

    def _generate_key(self, filename: str) -> str:
        prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{uuid6.uuid7().hex}{prefix}-{filename}"

    def _head_object(self, key: str) -> None:
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("404", "NoSuchKey", "NotFound"):
                raise FileNotFoundError(f"S3 key not found: {key}") from e
            raise

    def upload_fileobj(self, file: bytes,file_name: str, encrypt: bool = False) -> str:
        key = self._generate_key(file_name)
        extra_args = {"ServerSideEncryption": "AES256"} if encrypt else {}
        self.s3_client.upload_fileobj(file, self.bucket, key, ExtraArgs=extra_args, Config=self.transfer_config)
        return key
    def upload_file(self, file_name: str, encrypt: bool = False) -> str:
        key = self._generate_key(file_name)
        extra_args = {"ServerSideEncryption": "AES256"} if encrypt else {}
        self.s3_client.upload_file(file_name, self.bucket, key, ExtraArgs=extra_args, Config=self.transfer_config)
        return key
    
    def download_file(self, key: str, local_name: str = None) -> str:
        self._head_object(key)
        filename = local_name or os.path.basename(key)
        dest = os.path.join(self.tmp_dir, filename)
        self.s3_client.download_file(self.bucket, key, dest)
        return dest

    def delete_file(self, key: str) -> None:
        self._head_object(key)
        self.s3_client.delete_object(Bucket=self.bucket, Key=key)

    def generate_presigned_url(
        self, key: str, operation: str = "get_object", expires_in: int = 3600
    ) -> str:
        if operation == "get_object":
            self._head_object(key)
        params = {"Bucket": self.bucket, "Key": key}
        return self.s3_client.generate_presigned_url(operation, Params=params, ExpiresIn=expires_in)
    
    def get_cdn_url(self, key: str) -> str:

        return f"https://{self.aws_s3_bucket_name}.s3.{self.aws_region}.amazonaws.com/{key}"