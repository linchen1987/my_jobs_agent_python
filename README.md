# Jobs Agent

## GitHub Actions 定时任务

本项目通过 GitHub Actions 实现每天定时执行任务（北京时间 9:00），同时支持手动触发。

### 配置 Secrets

在 GitHub 仓库中进入 **Settings > Secrets and variables > Actions**，点击 **New repository secret** 添加以下配置：

| Secret 名称 | 说明 | 必填 |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI Compatible API Key | Yes |
| `OPENAI_API_ENDPOINT` | API 端点 URL | No |
| `OPENAI_MODEL_ID` | 模型 ID | No |
| `STORAGE_TYPE` | 存储类型（`local` 或 `s3`） | No |
| `STORAGE_ROOT_PATH` | 存储根路径 | No |
| `S3_BUCKET` | S3 存储桶名称 | No |
| `S3_ENDPOINT_URL` | S3 端点 URL | No |
| `S3_ACCESS_KEY_ID` | S3 Access Key ID | No |
| `S3_SECRET_ACCESS_KEY` | S3 Secret Access Key | No |
| `S3_REGION` | S3 区域 | No |
| `TELEGRAM_ENABLED` | 是否启用 Telegram 通知（`true`/`false`） | No |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | No |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | No |

### 手动触发

进入 **Actions** 页面，选择 **Daily Job Agent** workflow，点击 **Run workflow** 即可手动触发执行。

## 本地开发

```bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入必要的配置

# 运行完整流程
uv run python -m jobs_agent

# 数据迁移（旧格式 → Phase 1 新格式，只需运行一次）
uv run migrate.py
```

### 调试抓取

通过 id 或 url 快速查看单个职位的抓取结果：

```bash
uv run debug-fetch-eleduck.py L5fbk3
uv run debug-fetch-eleduck.py https://eleduck.com/posts/L5fbk3
```

### 测试模式

通过环境变量控制抓取范围，避免全量抓取：

```bash
# 只抓第 11 条（跳过前 10 条）
ELEDUCK_OFFSET=10 ELEDUCK_LIMIT=1 uv run python -m jobs_agent

# 只抓 1 页，取前 2 条
ELEDUCK_PAGES=1 ELEDUCK_OFFSET=0 ELEDUCK_LIMIT=2 uv run python -m jobs_agent
```
