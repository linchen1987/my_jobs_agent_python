# Multi-Source Support: Phase 1 Design

## 目标

将当前硬编码的 eleduck 数据源抽象为可扩展的多数据源框架。Phase 1 范围：

- 抽象数据源接口（`BaseSource`）
- 迁移 eleduck 为第一个 Source 实现
- 优化内存数据模型（TypedDict）
- 精简持久化数据结构
- 提供数据迁移脚本

**不包含**：新增数据源（V2EX / Remote OK 等）、JS 渲染支持、反爬基础设施。

---

## 1. 当前 Workflow 回顾

```
run.py
 ├─ fetch_and_parse_all(source_url_list)    ← 硬编码 eleduck URL
 │    ├─ fetch_json(url)                    ← 通用 HTTP
 │    ├─ parse_eleduck_list(data)           ← eleduck 专用
 │    ├─ fetch_and_parse_detail(url)        ← eleduck 专用
 │    │    ├─ fetch_page(url)
 │    │    └─ analyze_eleduck_page(html)
 │    └─ → List[dict]                       ← 无类型约束
 │
 ├─ analyze_job_with_llm(llm, job_data)     ← 通用，不关心数据源
 │    └─ → { "llm_analysis": {...}, "original_data": job_data }
 │
 └─ handle_results(...)
      ├─ save to analyzed_jobs.json / jobs.json / jobs.md
      └─ telegram notify
```

**问题**：步骤 1 与 eleduck 强耦合；数据流全链路使用 `dict`，无类型约束。

---

## 2. 目录结构变更

```
新增:
  sources/
    __init__.py           # create_sources_from_env() 工厂函数
    base.py               # BaseSource 抽象基类 + TypedDict 模型
    eleduck.py            # EleduckSource 实现
  migrate.py              # 一次性数据迁移脚本

改造:
  tools/fetch_and_parse_all.py   # 接收 list[BaseSource]
  run.py                         # 使用 sources 列表替代 URL 列表

不变:
  tools/parse_list.py            # eleduck 内部调用
  tools/parse_detail_page.py     # eleduck 内部调用
  tools/fetch_page.py            # 通用 HTTP
  tools/analyze_data.py          # 通用 LLM 分析
  tools/prompt.py                # 通用 prompt
  tools/telegram.py              # 通用通知
  storage/                       # 通用存储
```

---

## 3. In-Memory Data Structure

### 3.1 定义 (`sources/base.py`)

使用 `TypedDict` 定义标准数据模型，所有数据源统一输出。

```python
from typing import TypedDict


class JobListItem(TypedDict):
    """列表页解析后的标准输出"""
    id: str                  # 源内唯一 ID
    source: str              # 数据源标识，如 "eleduck"
    url: str                 # 详情页 URL
    title: str               # 标题
    extra: dict              # 源特有元数据


class JobDetail(TypedDict):
    """详情页解析后的标准输出，是 pipeline 的核心数据单元"""
    id: str                  # 等同 list_item.id
    source: str              # 等同 list_item.source
    url: str                 # 等同 list_item.url
    title: str               # 详情页标题
    content: str             # 正文纯文本
    tags: list[dict]         # [{ "category": str, "values": list[str] }]
    list_item: JobListItem   # 原始列表项（替代旧 list_metadata）
    extra: dict              # 源特有详情元数据（如 reads, comments）


class LLMAnalysis(TypedDict):
    """LLM 返回的分析结果（LLM JSON 输出直接反序列化为此结构）"""
    is_qualified: bool
    analysis: dict
    extracted_info: dict


class AnalysisResult(TypedDict):
    """一条职位的完整分析结果，只在内存中使用，不直接持久化"""
    id: str                    # global_id: "source:id"
    source: str
    url: str
    title: str
    detail: JobDetail
    llm_analysis: LLMAnalysis
    analyzed_at: str           # ISO format timestamp


class AnalyzedRecord(TypedDict):
    """去重用的已分析记录，持久化到 analyzed_jobs.json"""
    id: str                    # global_id: "source:id"
    source: str
    url: str
    is_qualified: bool
    analyzed_at: str           # ISO format timestamp
    reason: str
```

### 3.2 与旧模型对比

```
旧 (dict, 无类型约束)                      新 (TypedDict)
─────────────────────────────────────      ─────────────────────────────────────
fetch_and_parse_all 返回:                  fetch_and_parse_all 返回:
[                                          [
  {                                          {
    "title": "...",                            "id": "gYfZOZ",
    "content": "...",                          "source": "eleduck",
    "meta_info": {...},                        "url": "https://...",
    "tags": [...],                             "title": "...",
    "list_metadata": {    ← flat dict          "content": "...",
      "id": "...",                              "tags": [...],
      "url": "...",                             "list_item": {...},
      "title": "...",  ← 重复                    "extra": {...}
      ...                                     }
    }                                       ]
  }
]

analyze_job_with_llm 返回:                 analyze_job_with_llm 返回:
{                                          AnalysisResult(
  "llm_analysis": {...},                     id="eleduck:gYfZOZ",
  "original_data": {    ← 整个旧 dict        source="eleduck",
    "title": "...",                           url="https://...",
    "content": "...",                         title="...",
    "list_metadata": {...}                    detail=JobDetail(...),
  }                                          llm_analysis=LLMAnalysis(...),
}                                            analyzed_at="2026-04-10T..."
                                           )
```

**关键改进**：
- `source` 字段贯穿全链路，支持多源区分
- `global_id = f"{source}:{id}"` 解决跨源 ID 冲突
- `list_item` 替代 `list_metadata`，语义更清晰
- `title` 只保留一份（detail 层级），不再重复
- `AnalysisResult` 扁平化，消除 3 层嵌套访问

---

## 4. Persistence Data Structure

### 设计原则

- **analyzed_jobs.json** 是唯一的必需持久化文件，只做去重
- **jobs.json** 删除，不再持久化完整分析结果。符合条件的结果通过 Telegram 通知即可；如需回溯可从 `analyzed_jobs.json` 中找到 `is_qualified=true` 的记录
- **jobs.md** 和 **jobs_notifications.md** 保留为可选输出，通过环境变量控制开关，默认关闭

### 4.1 analyzed_jobs.json（去重记录 — 必需）

唯一职责：记录已分析过的职位 ID，避免重复抓取和 LLM 调用。

```json
[
  {
    "id": "eleduck:gYfZOZ",
    "source": "eleduck",
    "url": "https://eleduck.com/tposts/gYfZOZ",
    "is_qualified": true,
    "analyzed_at": "2026-04-10T12:00:00",
    "reason": "符合远程开发岗位要求"
  }
]
```

变更点：
- `id` → `source:id` 格式（global_id），避免跨源冲突
- `createdAt` → `analyzed_at`，命名统一
- 新增 `source` 字段
- 保留 `url`, `is_qualified`, `reason` 用于调试和审计，但这些字段不参与去重逻辑（去重只看 `id`）

### 4.2 jobs.json — 删除

**删除理由**：

| 维度 | 分析 |
|------|------|
| 数据冗余 | `is_qualified` 信息已在 `analyzed_jobs.json` 中 |
| 体积膨胀 | 旧格式保存 content 全文 + 三层嵌套，持续增长 |
| 消费者 | 唯一消费者是 `jobs.md` 和 `jobs_notifications.md`，两者均改为可选且默认关闭 |
| 通知渠道 | Telegram 通知直接从内存中的 `AnalysisResult` 构造，不依赖此文件 |

删除后，如需查看符合条件的职位列表，可直接过滤 `analyzed_jobs.json` 中 `is_qualified=true` 的记录。

### 4.3 jobs.md（可选，默认关闭）

通过环境变量控制：

```env
# 是否生成 jobs.md 报告（默认 false）
SAVE_JOBS_MD=false
```

只展示**本次运行**符合条件的结果，直接从内存中的 `new_qualified_jobs`（`list[AnalysisResult]`）生成，不依赖任何持久化文件。每次运行覆盖写入。格式不变。

### 4.4 jobs_notifications.md（可选，默认关闭）

通过环境变量控制：

```env
# 是否保存通知到本地文件（默认 false）
SAVE_NOTIFICATIONS=false
```

格式不变，新通知 prepend 到现有内容前。

### 4.5 新增环境变量汇总

```env
# 可选持久化输出开关
SAVE_JOBS_MD=false          # 是否生成 jobs.md 报告
SAVE_NOTIFICATIONS=false     # 是否保存通知到 jobs_notifications.md
```

---

## 5. 改造后的 Pipeline

```
run.py
 ├─ fetch_and_parse_all(sources)            ← 接收 list[BaseSource]
 │    └─ 每个 source 调用 fetch_list / fetch_detail
 │    └─ → list[JobDetail]
 │
 ├─ analyze_job_with_llm(llm, detail)       ← 逐条分析
 │    └─ → AnalysisResult
 │
 ├─ save analyzed_jobs.json                 ← 唯一必需持久化（去重）
 │
 ├─ telegram notify (if configured)         ← 发送符合条件的职位
 │
 ├─ [可选] save jobs.md (if SAVE_JOBS_MD)   ← 默认关闭
 └─ [可选] save notifications (if SAVE_NOTIFICATIONS) ← 默认关闭
```

与旧流程对比：

| 环节 | 旧 | 新 |
|------|----|----|
| 数据源 | 硬编码 eleduck URL | `list[BaseSource]` |
| 列表/详情解析 | eleduck 专用函数 | Source 内部封装 |
| 数据模型 | 自由 dict | TypedDict |
| 持久化 | 3 个文件全量写入 | 1 个必需 + 2 个可选 |
| 去重 ID | 裸 id | `source:id` |

---

## 6. BaseSource 接口

```python
# sources/base.py

from abc import ABC, abstractmethod
from typing import Optional


class BaseSource(ABC):
    """数据源抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """数据源唯一标识，如 'eleduck'"""
        ...

    @abstractmethod
    def fetch_list(self) -> list[JobListItem]:
        """抓取列表页，返回标准化的 job 列表"""
        ...

    @abstractmethod
    def fetch_detail(self, item: JobListItem) -> Optional[JobDetail]:
        """抓取并解析单个详情页，失败返回 None"""
        ...

    def global_id(self, item_id: str) -> str:
        """生成跨源唯一 ID"""
        return f"{self.name}:{item_id}"
```

---

## 7. EleduckSource 实现

```python
# sources/eleduck.py

from sources.base import BaseSource, JobListItem, JobDetail


class EleduckSource(BaseSource):
    """Eleduck 数据源"""

    def __init__(self, pages: int = 2):
        self.pages = pages

    @property
    def name(self) -> str:
        return "eleduck"

    def fetch_list(self) -> list[JobListItem]:
        from tools.fetch_page import fetch_json
        from tools.parse_list import parse_eleduck_list

        items = []
        for page in range(1, self.pages + 1):
            url = f"https://svc.eleduck.com/api/v1/posts?page={page}"
            data = fetch_json(url)
            if not data:
                continue
            posts = parse_eleduck_list(data)
            for post in posts:
                items.append({
                    "id": post["id"],
                    "source": self.name,
                    "url": post["url"],
                    "title": post.get("title", ""),
                    "extra": post,
                })
        return items

    def fetch_detail(self, item: JobListItem) -> JobDetail | None:
        from tools.fetch_and_parse import fetch_and_parse_detail

        result = fetch_and_parse_detail(item["url"])
        if not result:
            return None

        return {
            "id": item["id"],
            "source": self.name,
            "url": item["url"],
            "title": result.get("title", item["title"]),
            "content": result.get("content", ""),
            "tags": result.get("tags", []),
            "list_item": item,
            "extra": result.get("meta_info", {}),
        }
```

---

## 8. 核心流程代码

### 8.1 fetch_and_parse_all.py (改造后)

```python
from sources.base import BaseSource, JobDetail

def fetch_and_parse_all(
    sources: list[BaseSource],
    analyzed_ids: set | None = None,
    detail_delay: float = 3.0,
) -> list[JobDetail]:
    all_details = []

    for source in sources:
        items = source.fetch_list()
        logger.info(f"[{source.name}] list: {len(items)} items")

        if analyzed_ids:
            before = len(items)
            items = [it for it in items if source.global_id(it["id"]) not in analyzed_ids]
            logger.info(f"[{source.name}] dedup: skipped {before - len(items)}")

        for i, item in enumerate(items, 1):
            detail = source.fetch_detail(item)
            if detail:
                all_details.append(detail)
            if i < len(items) and detail_delay > 0:
                time.sleep(detail_delay)

    return all_details
```

### 8.2 run.py (改造后，关键片段)

```python
from sources.eleduck import EleduckSource
from tools.fetch_and_parse_all import fetch_and_parse_all

sources = [EleduckSource(pages=2)]

# 去重集合使用 global_id
analyzed_ids = {record["id"] for record in analyzed_jobs}

all_jobs_data = fetch_and_parse_all(sources, analyzed_ids=analyzed_ids)

# ... LLM 分析 ...

# 持久化：只写 analyzed_jobs.json
new_records = [
    {
        "id": result["id"],
        "source": result["source"],
        "url": result["url"],
        "is_qualified": result["llm_analysis"]["is_qualified"],
        "analyzed_at": result["analyzed_at"],
        "reason": result["llm_analysis"].get("analysis", {}).get("reasoning", ""),
    }
    for result in analysis_results
]

# 可选输出
if os.getenv("SAVE_JOBS_MD", "false").lower() in ("true", "1"):
    ...
if os.getenv("SAVE_NOTIFICATIONS", "false").lower() in ("true", "1"):
    ...
```

---

## 9. 数据迁移方案

### 迁移脚本 (`migrate.py`)

一次性运行，将旧格式数据迁移为新格式。

```python
"""
数据迁移脚本：将旧格式数据迁移为 Phase 1 新格式

- analyzed_jobs.json: id 加 source 前缀，精简字段
- jobs.json: 删除（备份为 .bak）
"""

import json
import os

SOURCE = "eleduck"


def migrate_analyzed_jobs(path: str):
    if not os.path.exists(path):
        print(f"跳过 {path}（文件不存在）")
        return

    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)

    migrated = []
    for r in records:
        old_id = r.get("id", "")
        migrated.append({
            "id": f"{SOURCE}:{old_id}",
            "source": SOURCE,
            "url": r.get("url", ""),
            "is_qualified": r.get("is_qualified", False),
            "analyzed_at": r.get("createdAt", ""),
            "reason": r.get("reason", ""),
        })

    backup = path + ".bak"
    os.rename(path, backup)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(migrated, f, ensure_ascii=False, indent=2)

    print(f"✅ {path}: {len(records)} records migrated (backup: {backup})")


def remove_jobs_json(path: str):
    if not os.path.exists(path):
        print(f"跳过 {path}（文件不存在）")
        return

    backup = path + ".bak"
    os.rename(path, backup)
    print(f"✅ {path} renamed to {backup}（不再使用）")


def main():
    data_dir = os.getenv("STORAGE_ROOT_PATH", ".data")

    migrate_analyzed_jobs(os.path.join(data_dir, "analyzed_jobs.json"))
    remove_jobs_json(os.path.join(data_dir, "jobs.json"))

    print("\n迁移完成。旧文件备份为 .bak")


if __name__ == "__main__":
    main()
```

---

## 10. 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `sources/__init__.py` | 新建 | 模块入口，`create_sources_from_env()` |
| `sources/base.py` | 新建 | `BaseSource`, TypedDict 模型 |
| `sources/eleduck.py` | 新建 | `EleduckSource` 实现 |
| `tools/fetch_and_parse_all.py` | 改造 | 接收 `list[BaseSource]` |
| `tools/analyze_data.py` | 改造 | 输入/输出使用新 TypedDict |
| `run.py` | 改造 | 使用 sources 列表，精简持久化逻辑，删除 jobs.json 相关代码 |
| `tools/telegram.py` | 改造 | 访问路径适配扁平结构 |
| `migrate.py` | 新建 | 一次性迁移脚本（迁移 analyzed_jobs.json，删除 jobs.json） |
| `tools/parse_list.py` | 保留 | eleduck 内部使用 |
| `tools/parse_detail_page.py` | 保留 | eleduck 内部使用 |
| `tools/fetch_page.py` | 不变 | 通用 HTTP |
| `tools/prompt.py` | 不变 | prompt 逻辑不变 |
| `storage/` | 不变 | 存储逻辑不变 |
| `tools/llm_openai.py` | 不变 | LLM 客户端不变 |
| `tools/base_llm.py` | 不变 | LLM 抽象不变 |

---

## 11. 实施顺序

```
1. 新建 sources/base.py              — 定义 TypedDict + BaseSource
2. 新建 sources/eleduck.py           — 迁移 eleduck 逻辑
3. 新建 sources/__init__.py          — 工厂函数
4. 改造 fetch_and_parse_all.py       — 接收 sources 列表
5. 改造 analyze_data.py              — 输入/输出适配
6. 改造 run.py                       — 精简持久化，删除 jobs.json 逻辑
7. 改造 telegram.py                  — 访问路径适配
8. 新建 migrate.py                   — 迁移脚本
9. 运行 migrate.py                   — 迁移已有数据
10. 端到端测试                        — 确保功能不变
```
