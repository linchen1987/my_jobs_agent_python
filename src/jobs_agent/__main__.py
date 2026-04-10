import os
import json
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from jobs_agent.sources import create_sources_from_env
from jobs_agent.sources.base import BaseSource, AnalysisResult, AnalyzedRecord
from jobs_agent.core.pipeline import fetch_and_parse_all
from jobs_agent.llm.openai import OpenAIChat
from jobs_agent.core.analyzer import analyze_job_with_llm
from jobs_agent.notify.telegram import notify_jobs, is_configured as telegram_configured
from jobs_agent.storage import create_storage_from_env, StorageClient

load_dotenv()

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

storage: StorageClient = None


def _clean_text(text):
    if not text or text == "未提及":
        return "未提及"
    return str(text).replace("\n", " ").replace("|", "｜").strip()


def _truncate_text(text, max_length=100):
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def _extract_job_fields(job: AnalysisResult) -> dict:
    llm_analysis = job.get("llm_analysis", {})
    extracted_info = llm_analysis.get("extracted_info", {})
    return {
        "url": job.get("url", ""),
        "id": job.get("id", ""),
        "title": job.get("title", ""),
        "company_intro": extracted_info.get("company_introduction", "未提及"),
        "company_website": extracted_info.get("company_website", "未提及"),
        "skill_req": extracted_info.get("skill_requirements", "未提及"),
        "salary": extracted_info.get("salary_benefits", "未提及"),
    }


def create_notification_markdown(qualified_jobs: list[AnalysisResult]) -> str:
    if not qualified_jobs:
        return ""

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    markdown = f"# 新职位通知 - {current_time}\n\n"
    markdown += f"发现 {len(qualified_jobs)} 个新的符合条件的招聘信息：\n\n"
    markdown += "| URL | ID | 公司介绍 | 公司网站 | 技能要求 | 薪资待遇 |\n"
    markdown += "|-----|----|---------|---------|---------|---------|\n"

    for job in qualified_jobs:
        f = _extract_job_fields(job)
        company_intro = _truncate_text(_clean_text(f["company_intro"]))
        skill_req = _truncate_text(_clean_text(f["skill_req"]))
        company_website = _clean_text(f["company_website"])
        salary = _clean_text(f["salary"])

        markdown += f"| [{f['id']}]({f['url']}) | {f['id']} | {company_intro} | {company_website} | {skill_req} | {salary} |\n"

    return markdown


def create_markdown_table(qualified_jobs: list[AnalysisResult]) -> str:
    if not qualified_jobs:
        return "## 分析结果\n\n暂无符合条件的招聘信息。\n"

    markdown = "## 招聘信息分析结果\n\n"
    markdown += f"共找到 {len(qualified_jobs)} 个符合条件的招聘信息：\n\n"
    markdown += "| URL | ID | 公司介绍 | 公司网站 | 技能要求 | 薪资待遇 |\n"
    markdown += "|-----|----|---------|---------|---------|---------|\n"

    for job in qualified_jobs:
        f = _extract_job_fields(job)
        company_intro = _truncate_text(_clean_text(f["company_intro"]))
        skill_req = _truncate_text(_clean_text(f["skill_req"]))
        company_website = _clean_text(f["company_website"])
        salary = _clean_text(f["salary"])

        markdown += f"| [{f['id']}]({f['url']}) | {f['id']} | {company_intro} | {company_website} | {skill_req} | {salary} |\n"

    return markdown


async def save_notifications(new_qualified_jobs: list[AnalysisResult]) -> None:
    if not new_qualified_jobs:
        return

    notifications_path = "jobs_notifications.md"
    new_notification_content = create_notification_markdown(new_qualified_jobs)

    existing_content = ""
    if await storage.exists(notifications_path):
        try:
            existing_content = await storage.read_text(notifications_path)
        except Exception as e:
            logger.warning(f"加载现有通知失败: {e}")
            existing_content = ""

    if existing_content:
        all_content = new_notification_content + "\n---\n\n" + existing_content
    else:
        all_content = new_notification_content

    try:
        await storage.write_text(notifications_path, all_content)
        print(
            f"\n📢 发现 {len(new_qualified_jobs)} 个新职位，已保存到 {notifications_path}"
        )
    except Exception as e:
        logger.error(f"保存通知失败: {e}")


async def process_data(
    sources: list[BaseSource],
) -> tuple[list[AnalyzedRecord], list[AnalysisResult]]:
    print("=== 开始数据处理阶段 ===\n")

    await storage.ensure_dir(".")

    analyzed_jobs: list[dict] = []
    analyzed_json_path = "analyzed_jobs.json"
    if await storage.exists(analyzed_json_path):
        try:
            content = await storage.read_text(analyzed_json_path)
            analyzed_jobs = json.loads(content)
        except Exception as e:
            logger.warning(f"加载已分析记录失败: {e}")
            analyzed_jobs = []

    analyzed_ids = {
        record.get("id", "") for record in analyzed_jobs if record.get("id")
    }

    print("🚀 初始化LLM客户端...")
    llm_client = OpenAIChat()

    print(f"\n📥 开始抓取数据...（跳过 {len(analyzed_ids)} 个已分析的）")
    all_jobs_data = fetch_and_parse_all(sources, analyzed_ids=analyzed_ids)

    if not all_jobs_data:
        print("❌ 没有获取到新的数据")
        return [], []

    print(f"\n📊 获取到 {len(all_jobs_data)} 个新招聘信息，开始分析...")

    new_qualified_jobs: list[AnalysisResult] = []
    new_analyzed_records: list[AnalyzedRecord] = []

    for i, detail in enumerate(all_jobs_data, 1):
        print(f"\n[{i}/{len(all_jobs_data)}] 分析中: {detail['id']}")

        try:
            result = analyze_job_with_llm(llm_client, detail)
        except Exception as e:
            logger.error(f"分析失败 {detail['id']}: {e}")
            continue

        llm_analysis = result["llm_analysis"]
        is_qualified = llm_analysis.get("is_qualified", False)
        reason = llm_analysis.get("analysis", {}).get("reasoning", "")

        new_analyzed_records.append(
            {
                "id": result["id"],
                "source": result["source"],
                "url": result["url"],
                "is_qualified": is_qualified,
                "analyzed_at": result["analyzed_at"],
                "reason": reason,
            }
        )

        if is_qualified:
            new_qualified_jobs.append(result)
            print("✅ 符合条件")
        else:
            print("❌ 不符合条件")

    print(
        f"\n📈 数据处理完成！跳过 {len(analyzed_ids)} 个已分析项，新增 {len(new_qualified_jobs)} 个符合条件的招聘信息"
    )

    return new_analyzed_records, new_qualified_jobs


async def handle_results(
    new_analyzed_records: list[AnalyzedRecord],
    new_qualified_jobs: list[AnalysisResult],
) -> None:
    print("\n=== 开始后续动作阶段 ===\n")

    analyzed_json_path = "analyzed_jobs.json"

    existing_analyzed_jobs: list[dict] = []
    if await storage.exists(analyzed_json_path):
        try:
            content = await storage.read_text(analyzed_json_path)
            existing_analyzed_jobs = json.loads(content)
        except Exception as e:
            logger.warning(f"加载现有已分析记录失败: {e}")
            existing_analyzed_jobs = []

    all_analyzed_jobs = new_analyzed_records + existing_analyzed_jobs

    print(f"💾 保存已分析记录表...（总共 {len(all_analyzed_jobs)} 个已分析记录）")
    await storage.write_text(
        analyzed_json_path, json.dumps(all_analyzed_jobs, ensure_ascii=False, indent=2)
    )

    save_jobs_md = os.getenv("SAVE_JOBS_MD", "false").lower() in ("true", "1")
    if save_jobs_md and new_qualified_jobs:
        print("📝 生成Markdown报告...")
        markdown_content = create_markdown_table(new_qualified_jobs)
        await storage.write_text("jobs.md", markdown_content)
        print("✅ 报告已保存到 jobs.md")

    save_notifications_flag = os.getenv("SAVE_NOTIFICATIONS", "false").lower() in (
        "true",
        "1",
    )
    if save_notifications_flag and new_qualified_jobs:
        await save_notifications(new_qualified_jobs)

    if new_qualified_jobs and telegram_configured():
        print("📲 发送 Telegram 通知...")
        success = notify_jobs(new_qualified_jobs)
        if success:
            print("✅ Telegram 通知已发送")
        else:
            print("⚠️ Telegram 通知发送失败")


async def main():
    global storage

    print("=== 开始招聘信息分析流程 ===\n")

    storage = create_storage_from_env()
    storage_type = os.getenv("STORAGE_TYPE", "local")
    print(f"📦 存储类型: {storage_type}\n")

    try:
        sources = create_sources_from_env()
        if not sources:
            print("❌ 没有可用的数据源")
            return

        new_analyzed_records, new_qualified_jobs = await process_data(sources)
        await handle_results(new_analyzed_records, new_qualified_jobs)

        print(f"\n🎉 流程完成！新增 {len(new_qualified_jobs)} 个符合条件的招聘信息")

    except Exception as e:
        logger.error(f"程序执行出错: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
