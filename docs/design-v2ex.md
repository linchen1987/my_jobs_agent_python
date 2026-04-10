# V2EX 数据源接入设计

## 概述

将 V2EX 酷工作（`?tab=jobs`）作为新数据源接入 jobs_agent，抓取帖子数据供 LLM 分析筛选。

**核心决策**：
- 数据来源：Atom RSS Feed（`/feed/tab/jobs.xml`），一次请求获取全部帖子完整内容
- 抓取范围：jobs tab 全量（含 jobs/cv/career/outsourcing/meet 节点），由 LLM 过滤非招聘帖
- 详情获取：零额外请求，content 直接从 RSS feed 缓存中提取

---

## 第一阶段：V2EX 数据抓取（独立脚本验证）

**目标**：实现 V2EX 数据抓取能力，可通过脚本独立测试观测原始数据。

### 1.1 新增文件

```
src/jobs_agent/sources/
  v2ex.py                           # V2exSource 类
  parsers/
    v2ex_feed.py                    # Atom XML feed 解析器

scripts/
  debug_v2ex.py                     # 测试脚本：抓取并打印 V2EX 帖子数据
```

### 1.2 模块职责

#### `sources/parsers/v2ex_feed.py` — Feed 解析器

输入：Atom XML 字符串（`/feed/tab/jobs.xml` 响应体）

输出：`list[dict]`，每个 dict 包含：

| 字段 | 来源 | 说明 |
|---|---|---|
| `id` | `<id>` 解析 | 从 `tag:www.v2ex.com,...:/t/{id}` 提取 topic ID |
| `url` | `<link rel="alternate">` | 帖子页面 URL |
| `title` | `<title>` | 帖子标题 |
| `content_html` | `<content type="html">` | 完整 HTML 内容 |
| `content_text` | BeautifulSoup 转换 | HTML → 纯文本 |
| `author` | `<author><name>` | 发帖人 |
| `published` | `<published>` | 发布时间 ISO 8601 |
| `updated` | `<updated>` | 最后更新时间 |

关键处理：
- Atom XML 命名空间处理：`http://www.w3.org/2005/Atom`
- HTML content 在 CDATA 中，需 `BeautifulSoup(html).get_text()` 转纯文本
- Topic ID 提取：优先从 `<link>` href 正则匹配 `/t/(\d+)`，回退从 `<id>` 解析

#### `sources/v2ex.py` — V2exSource 类

```
V2exSource(BaseSource)
  ├── name: str = "v2ex"
  ├── __init__(offset=0, limit=0)
  ├── fetch_list() -> list[JobListItem]
  │     GET /feed/tab/jobs.xml → parse_v2ex_feed() → 映射为 JobListItem[]
  │     extra 中缓存 content_html / content_text / author / published / updated
  └── fetch_detail(item) -> Optional[JobDetail]
        从 item["extra"] 提取，零网络请求
        content = extra["content_text"]
        tags = []  (RSS 无标签信息)
```

与 EleduckSource 的区别：
- 无分页，一次 RSS 获取全部
- `fetch_detail` 不发网络请求
- 无结构化 tags

#### `scripts/debug_v2ex.py` — 测试脚本

用法：`uv run scripts/debug_v2ex.py [topic_id_or_url]`

行为：
- 无参数：抓取 RSS feed，打印帖子列表摘要（id、标题、作者、节点、时间）
- 带参数：抓取并打印单条帖子完整内容（id、title、content_text、author、url）

### 1.3 依赖

- `beautifulsoup4`：HTML → 纯文本（检查是否已在依赖中，否则添加到 pyproject.toml）
- `xml.etree.ElementTree`：标准库，无需安装

### 1.4 验收标准

- [ ] `debug_v2ex.py` 可正确抓取并打印帖子列表
- [ ] 可通过 topic ID 查看单条帖子内容
- [ ] HTML 转纯文本质量可读，无残留标签
- [ ] 错误处理：网络异常、XML 解析失败有日志

---

## 第二阶段：集成到 jobs_agent 主流程

**目标**：将 V2exSource 注册到 pipeline，实现与 Eleduck 相同的自动化分析流程。

### 2.1 修改文件

```
src/jobs_agent/sources/__init__.py   # 注册 V2EX 数据源
.env.example                         # 添加 V2EX 配置项
```

### 2.2 改动内容

#### `sources/__init__.py` — 注册数据源

```python
v2ex_enabled = os.getenv("V2EX_ENABLED", "true").lower() in ("true", "1", "yes")
if v2ex_enabled:
    from jobs_agent.sources.v2ex import V2exSource
    offset = int(os.getenv("V2EX_OFFSET", "0"))
    limit = int(os.getenv("V2EX_LIMIT", "0"))
    sources.append(V2exSource(offset=offset, limit=limit))
```

#### `.env.example` — 新增配置

```
# V2EX 数据源配置
V2EX_ENABLED=true
V2EX_OFFSET=0
V2EX_LIMIT=0
```

### 2.3 集成要点

| 方面 | 说明 |
|---|---|
| 去重 | 全局 ID 格式 `v2ex:1204629`，与 eleduck 前缀隔离 |
| 延迟 | `fetch_detail` 无网络请求，`FETCH_DETAIL_DELAY` 对 V2EX 无实际影响 |
| LLM 分析 | 复用现有 `core/analyzer.py`，V2EX content_text 与 eleduck raw_content 等价 |
| 存储 | 复用 `analyzed_jobs.json` 去重账本，source 字段为 `"v2ex"` |
| 通知 | 复用现有 Telegram 通知，消息中 source 标识为 `"v2ex"` |

### 2.4 验收标准

- [ ] `python -m jobs_agent` 同时抓取 eleduck + v2ex 数据
- [ ] `V2EX_ENABLED=false` 可独立关闭 V2EX 数据源
- [ ] 去重正常：已分析过的 v2ex 帖子不会重复处理
- [ ] GitHub Actions 定时任务正常触发双数据源
- [ ] LLM 能正确区分 V2EX 中的招聘帖和职场讨论帖

---

## 数据流全景

```
第一阶段（独立测试）:
  debug_v2ex.py
    → fetch_page("/feed/tab/jobs.xml")
    → parse_v2ex_feed(xml)
    → 打印帖子摘要/详情

第二阶段（集成后）:
  __main__.py::main()
    → create_sources_from_env()
        → EleduckSource(...)    # 已有
        → V2exSource(...)       # 新增
    → fetch_and_parse_all(sources, analyzed_ids)
        → v2ex.fetch_list()     # 1次 RSS 请求
        → v2ex.fetch_detail()   # 0次网络请求
    → analyze_job_with_llm()    # 复用
    → handle_results()          # 复用
```
