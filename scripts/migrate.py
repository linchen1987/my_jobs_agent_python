"""
数据迁移脚本：将旧格式数据迁移为 Phase 1 新格式

- analyzed_jobs.json: id 加 source 前缀，精简字段
- jobs.json: 备份为 .bak
"""

import asyncio
import json
import logging

from dotenv import load_dotenv

from storage import StorageClient, create_storage_from_env

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SOURCE = "eleduck"


async def migrate_analyzed_jobs(storage: StorageClient, path: str):
    if not await storage.exists(path):
        print(f"跳过 {path}（文件不存在）")
        return

    content = await storage.read_text(path)
    records = json.loads(content)

    migrated = []
    for r in records:
        old_id = r.get("id", "")
        migrated.append(
            {
                "id": f"{SOURCE}:{old_id}",
                "source": SOURCE,
                "url": r.get("url", ""),
                "is_qualified": r.get("is_qualified", False),
                "analyzed_at": r.get("createdAt", ""),
                "reason": r.get("reason", ""),
            }
        )

    backup_path = path + ".bak"
    await storage.write_text(backup_path, content)
    logger.info(f"已备份: {backup_path}")

    await storage.write_text(path, json.dumps(migrated, ensure_ascii=False, indent=2))
    print(f"✅ {path}: {len(records)} records migrated (backup: {backup_path})")


async def backup_jobs_json(storage: StorageClient, path: str):
    if not await storage.exists(path):
        print(f"跳过 {path}（文件不存在）")
        return

    content = await storage.read_text(path)
    backup_path = path + ".bak"
    await storage.write_text(backup_path, content)
    await storage.unlink(path)
    print(f"✅ {path} → {backup_path}（备份后删除原文件）")


async def main():
    storage = create_storage_from_env()

    await migrate_analyzed_jobs(storage, "analyzed_jobs.json")
    await backup_jobs_json(storage, "jobs.json")

    print("\n迁移完成。旧文件备份为 .bak")


if __name__ == "__main__":
    asyncio.run(main())
