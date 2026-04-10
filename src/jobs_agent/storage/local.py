"""
本地文件系统存储实现
"""

import os
import mimetypes
import logging
from pathlib import Path
from typing import Union

from jobs_agent.storage.base import StorageClient, FileStat

logger = logging.getLogger(__name__)


class LocalStorageClient(StorageClient):
    """本地文件系统存储客户端"""

    def __init__(self, root_path: str = "."):
        """
        初始化本地存储客户端

        Args:
            root_path: 根目录路径，所有操作都相对于此路径
        """
        self.root_path = Path(root_path).resolve()
        logger.info(f"初始化本地存储客户端，根目录: {self.root_path}")

    def _resolve_path(self, path: str) -> Path:
        """
        解析路径，确保在根目录内

        Args:
            path: 相对路径

        Returns:
            绝对路径
        """
        if path.startswith("/"):
            path = path[1:]

        full_path = (self.root_path / path).resolve()

        try:
            full_path.relative_to(self.root_path)
        except ValueError:
            raise ValueError(f"路径 '{path}' 超出根目录范围")

        return full_path

    async def readdir(self, path: str) -> list[FileStat]:
        """读取目录内容"""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"目录不存在: {path}")

        if not full_path.is_dir():
            raise NotADirectoryError(f"不是目录: {path}")

        items = []
        for item in full_path.iterdir():
            stat = item.stat()
            mime_type = None
            if item.is_file():
                mime_type = mimetypes.guess_type(item.name)[0]

            items.append(
                FileStat(
                    filename=str(item.relative_to(self.root_path)),
                    basename=item.name,
                    lastmod=stat.st_mtime,
                    size=stat.st_size,
                    type="directory" if item.is_dir() else "file",
                    mime=mime_type,
                )
            )

        return items

    async def read_file(self, path: str) -> bytes:
        """读取文件内容"""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        if not full_path.is_file():
            raise IsADirectoryError(f"不是文件: {path}")

        logger.debug(f"读取文件: {full_path}")
        return full_path.read_bytes()

    async def write_file(self, path: str, content: Union[str, bytes]) -> None:
        """写入文件内容"""
        full_path = self._resolve_path(path)

        full_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, str):
            content = content.encode("utf-8")

        logger.debug(f"写入文件: {full_path}, 大小: {len(content)} 字节")
        full_path.write_bytes(content)

    async def unlink(self, path: str) -> None:
        """删除文件"""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        if full_path.is_file():
            full_path.unlink()
            logger.debug(f"删除文件: {full_path}")
        elif full_path.is_dir():
            import shutil

            shutil.rmtree(full_path)
            logger.debug(f"删除目录: {full_path}")

    async def stat(self, path: str) -> FileStat:
        """获取文件/目录信息"""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"文件/目录不存在: {path}")

        stat = full_path.stat()
        mime_type = None
        if full_path.is_file():
            mime_type = mimetypes.guess_type(full_path.name)[0]

        return FileStat(
            filename=str(full_path.relative_to(self.root_path)),
            basename=full_path.name,
            lastmod=stat.st_mtime,
            size=stat.st_size,
            type="directory" if full_path.is_dir() else "file",
            mime=mime_type,
        )

    async def exists(self, path: str) -> bool:
        """检查文件/目录是否存在"""
        full_path = self._resolve_path(path)
        return full_path.exists()

    async def ensure_dir(self, path: str) -> None:
        """确保目录存在"""
        full_path = self._resolve_path(path)
        full_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"确保目录存在: {full_path}")
