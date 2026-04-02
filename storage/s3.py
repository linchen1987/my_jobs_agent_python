"""
S3 兼容存储实现

支持 AWS S3 和其他 S3 兼容的对象存储服务（如 MinIO、Cloudflare R2、阿里云 OSS 等）
"""

import logging
from datetime import datetime
from typing import Union

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from .base import StorageClient, FileStat

logger = logging.getLogger(__name__)


def _normalize_path(path: str) -> str:
    """规范化 S3 路径，移除前导和尾随斜杠"""
    return path.strip("/")


class S3StorageClient(StorageClient):
    """S3 兼容存储客户端"""

    def __init__(
        self,
        bucket: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        region: str = "auto",
        root_path: str = "",
    ):
        """
        初始化 S3 存储客户端

        Args:
            bucket: S3 存储桶名称
            endpoint_url: S3 兼容服务的端点 URL（可选，AWS S3 可不设置）
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key
            region: AWS 区域（默认 'auto'，某些 S3 兼容服务需要）
            root_path: 根路径前缀（可选）
        """
        self.bucket = bucket
        self.root_path = _normalize_path(root_path)

        config_kwargs = {
            "region_name": region,
        }

        if access_key_id and secret_access_key:
            config_kwargs["aws_access_key_id"] = access_key_id
            config_kwargs["aws_secret_access_key"] = secret_access_key

        # 默认使用 AWS V4 签名（适用于原生 AWS S3）
        s3_config = Config(signature_version="s3v4")

        if endpoint_url:
            if not endpoint_url.startswith(("http://", "https://")):
                endpoint_url = f"https://{endpoint_url}"
            config_kwargs["endpoint_url"] = endpoint_url

            # 对于非 AWS S3 的第三方 S3 兼容服务（如阿里云 OSS、Cloudflare R2、MinIO），
            # 使用 V2 签名（signature_version="s3"）+ virtual hosted style，
            # 因为 boto3 的 V4 签名会强制使用 aws-chunked 编码，部分第三方服务不支持
            if not any(
                aws_domain in endpoint_url
                for aws_domain in ["amazonaws.com", ".s3.", ".s3-"]
            ):
                s3_config = Config(
                    signature_version="s3",
                    s3={"addressing_style": "virtual"},
                )
                logger.debug("使用 V2 签名 + virtual hosted style（自定义 endpoint）")

        config_kwargs["config"] = s3_config
        self.client = boto3.client("s3", **config_kwargs)

        logger.info(
            f"初始化 S3 存储客户端: bucket={bucket}, "
            f"endpoint={endpoint_url or 'AWS S3'}, "
            f"root_path={self.root_path or '/'}"
        )

    def _get_key(self, path: str) -> str:
        """
        获取完整的 S3 key

        Args:
            path: 相对路径

        Returns:
            完整的 S3 key
        """
        normalized = _normalize_path(path)
        if self.root_path:
            return f"{self.root_path}/{normalized}"
        return normalized

    async def readdir(self, path: str) -> list[FileStat]:
        """读取目录内容"""
        prefix = self._get_key(path)
        if prefix:
            prefix = prefix + "/"

        items = []
        paginator = self.client.get_paginator("list_objects_v2")

        try:
            for page in paginator.paginate(
                Bucket=self.bucket, Prefix=prefix, Delimiter="/"
            ):
                for common_prefix in page.get("CommonPrefixes", []):
                    dir_prefix = common_prefix["Prefix"]
                    dir_name = dir_prefix.rstrip("/").split("/")[-1]
                    items.append(
                        FileStat(
                            filename=f"/{dir_prefix.rstrip('/')}",
                            basename=dir_name,
                            lastmod=datetime.now(),
                            size=0,
                            type="directory",
                        )
                    )

                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key == prefix:
                        continue

                    basename = key.split("/")[-1]
                    items.append(
                        FileStat(
                            filename=f"/{key}",
                            basename=basename,
                            lastmod=obj["LastModified"],
                            size=obj["Size"],
                            type="file",
                            etag=obj.get("ETag", "").strip('"'),
                        )
                    )

        except ClientError as e:
            logger.error(f"读取目录失败: {path}, 错误: {e}")
            raise

        return items

    async def read_file(self, path: str) -> bytes:
        """读取文件内容"""
        key = self._get_key(path)

        try:
            logger.debug(f"读取 S3 对象: {key}")
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"文件不存在: {path}")
            logger.error(f"读取文件失败: {path}, 错误: {e}")
            raise

    async def write_file(self, path: str, content: Union[str, bytes]) -> None:
        """写入文件内容"""
        key = self._get_key(path)

        if isinstance(content, str):
            content = content.encode("utf-8")

        try:
            logger.debug(f"写入 S3 对象: {key}, 大小: {len(content)} 字节")
            self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        except ClientError as e:
            logger.error(f"写入文件失败: {path}, 错误: {e}")
            raise

    async def unlink(self, path: str) -> None:
        """删除文件"""
        key = self._get_key(path)

        try:
            logger.debug(f"删除 S3 对象: {key}")
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except ClientError as e:
            logger.error(f"删除文件失败: {path}, 错误: {e}")
            raise

    async def stat(self, path: str) -> FileStat:
        """获取文件/目录信息"""
        key = self._get_key(path)

        if not key:
            return FileStat(
                filename="/",
                basename="",
                lastmod=datetime.now(),
                size=0,
                type="directory",
            )

        try:
            response = self.client.head_object(Bucket=self.bucket, Key=key)
            basename = key.split("/")[-1]

            return FileStat(
                filename=f"/{key}",
                basename=basename,
                lastmod=response["LastModified"],
                size=response["ContentLength"],
                type="file",
                etag=response.get("ETag", "").strip('"'),
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                try:
                    prefix = key + "/"
                    response = self.client.list_objects_v2(
                        Bucket=self.bucket, Prefix=prefix, MaxKeys=1
                    )
                    if response.get("Contents"):
                        basename = key.split("/")[-1]
                        return FileStat(
                            filename=f"/{key}",
                            basename=basename,
                            lastmod=datetime.now(),
                            size=0,
                            type="directory",
                        )
                except ClientError:
                    pass

            raise FileNotFoundError(f"文件/目录不存在: {path}")

    async def exists(self, path: str) -> bool:
        """检查文件/目录是否存在"""
        try:
            await self.stat(path)
            return True
        except FileNotFoundError:
            return False

    async def ensure_dir(self, path: str) -> None:
        """
        确保目录存在

        注意：S3 不需要显式创建目录，目录由对象键的前缀隐式定义
        """
        logger.debug(f"S3 跳过创建目录: {path}")
