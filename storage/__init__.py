"""
存储模块

提供统一的存储接口，支持本地文件系统和 S3 兼容存储
"""

import os
import logging
from typing import Literal

from .base import StorageClient, FileStat
from .local import LocalStorageClient
from .s3 import S3StorageClient

logger = logging.getLogger(__name__)

StorageType = Literal["local", "s3"]


def create_storage_client(
    storage_type: StorageType = "local",
    root_path: str = ".",
    bucket: str | None = None,
    endpoint_url: str | None = None,
    access_key_id: str | None = None,
    secret_access_key: str | None = None,
    region: str = "auto",
) -> StorageClient:
    """
    创建存储客户端

    Args:
        storage_type: 存储类型 ('local' 或 's3')
        root_path: 本地存储的根路径，或 S3 存储的前缀路径
        bucket: S3 存储桶名称
        endpoint_url: S3 兼容服务的端点 URL
        access_key_id: AWS Access Key ID
        secret_access_key: AWS Secret Access Key
        region: AWS 区域

    Returns:
        StorageClient 实例

    Raises:
        ValueError: 当配置无效时
    """
    if storage_type == "local":
        logger.info(f"创建本地存储客户端，根目录: {root_path}")
        return LocalStorageClient(root_path=root_path)

    elif storage_type == "s3":
        if not bucket:
            raise ValueError("S3 存储需要提供 bucket 参数")

        logger.info(f"创建 S3 存储客户端，bucket: {bucket}, root_path: {root_path}")
        return S3StorageClient(
            bucket=bucket,
            endpoint_url=endpoint_url,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            region=region,
            root_path=root_path,
        )

    else:
        raise ValueError(f"不支持的存储类型: {storage_type}")


def create_storage_from_env() -> StorageClient:
    """
    从环境变量创建存储客户端

    环境变量:
        STORAGE_TYPE: 存储类型 ('local' 或 's3')，默认 'local'
        STORAGE_ROOT_PATH: 存储根路径，默认 '.data'
        S3_BUCKET: S3 存储桶名称
        S3_ENDPOINT_URL: S3 兼容服务的端点 URL（可选）
        S3_ACCESS_KEY_ID: AWS Access Key ID
        S3_SECRET_ACCESS_KEY: AWS Secret Access Key
        S3_REGION: AWS 区域，默认 'auto'

    Returns:
        StorageClient 实例
    """
    storage_type = os.getenv("STORAGE_TYPE", "local").lower()
    root_path = os.getenv("STORAGE_ROOT_PATH", ".data")

    if storage_type == "s3":
        bucket = os.getenv("S3_BUCKET")
        endpoint_url = os.getenv("S3_ENDPOINT_URL")
        access_key_id = os.getenv("S3_ACCESS_KEY_ID")
        secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
        region = os.getenv("S3_REGION", "auto")

        if not bucket:
            raise ValueError("S3 存储需要设置 S3_BUCKET 环境变量")

        if not access_key_id or not secret_access_key:
            raise ValueError(
                "S3 存储需要设置 S3_ACCESS_KEY_ID 和 S3_SECRET_ACCESS_KEY 环境变量"
            )

        return create_storage_client(
            storage_type="s3",
            root_path=root_path,
            bucket=bucket,
            endpoint_url=endpoint_url,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            region=region,
        )

    else:
        return create_storage_client(storage_type="local", root_path=root_path)


__all__ = [
    "StorageClient",
    "FileStat",
    "LocalStorageClient",
    "S3StorageClient",
    "StorageType",
    "create_storage_client",
    "create_storage_from_env",
]
