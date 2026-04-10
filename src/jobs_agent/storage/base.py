"""
存储抽象基类

定义统一的存储接口，支持本地文件系统和 S3 兼容存储
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union
from datetime import datetime


@dataclass
class FileStat:
    """文件/目录信息"""

    filename: str
    basename: str
    lastmod: datetime
    size: int
    type: str
    mime: str | None = None
    etag: str | None = None


class StorageClient(ABC):
    """存储客户端抽象基类"""

    @abstractmethod
    async def readdir(self, path: str) -> list[FileStat]:
        """
        读取目录内容

        Args:
            path: 目录路径

        Returns:
            目录中的文件和子目录列表
        """
        pass

    @abstractmethod
    async def read_file(self, path: str) -> bytes:
        """
        读取文件内容

        Args:
            path: 文件路径

        Returns:
            文件内容（字节）
        """
        pass

    @abstractmethod
    async def write_file(self, path: str, content: Union[str, bytes]) -> None:
        """
        写入文件内容

        Args:
            path: 文件路径
            content: 文件内容（字符串或字节）
        """
        pass

    @abstractmethod
    async def unlink(self, path: str) -> None:
        """
        删除文件

        Args:
            path: 文件路径
        """
        pass

    @abstractmethod
    async def stat(self, path: str) -> FileStat:
        """
        获取文件/目录信息

        Args:
            path: 文件/目录路径

        Returns:
            文件/目录信息
        """
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """
        检查文件/目录是否存在

        Args:
            path: 文件/目录路径

        Returns:
            是否存在
        """
        pass

    @abstractmethod
    async def ensure_dir(self, path: str) -> None:
        """
        确保目录存在，如果不存在则创建

        Args:
            path: 目录路径
        """
        pass

    async def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """
        读取文本文件

        Args:
            path: 文件路径
            encoding: 文本编码

        Returns:
            文件内容（字符串）
        """
        content = await self.read_file(path)
        return content.decode(encoding)

    async def write_text(
        self, path: str, content: str, encoding: str = "utf-8"
    ) -> None:
        """
        写入文本文件

        Args:
            path: 文件路径
            content: 文本内容
            encoding: 文本编码
        """
        await self.write_file(path, content.encode(encoding))
