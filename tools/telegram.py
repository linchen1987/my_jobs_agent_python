import os
import logging
from typing import List, Dict, Any

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


def _get_config() -> tuple[str, str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    return token, chat_id


def is_enabled() -> bool:
    return os.getenv("TELEGRAM_ENABLED", "false").lower() in ("true", "1", "yes")


def is_configured() -> bool:
    if not is_enabled():
        return False
    token, chat_id = _get_config()
    return bool(token and chat_id)


def send_message(text: str, parse_mode: str = "HTML") -> bool:
    token, chat_id = _get_config()
    if not token or not chat_id:
        logger.warning(
            "Telegram 未配置 (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)，跳过通知"
        )
        return False

    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("Telegram 通知发送成功")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram 通知发送失败: {e}")
        return False


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_jobs_message(jobs: List[Dict[str, Any]]) -> str:
    lines = [f"🔔 发现 {len(jobs)} 个新的符合条件的招聘信息：\n"]

    for i, job in enumerate(jobs, 1):
        original_data = job.get("original_data", {})
        list_metadata = original_data.get("list_metadata", {})
        llm_analysis = job.get("llm_analysis", {})
        extracted_info = llm_analysis.get("extracted_info", {})

        url = list_metadata.get("url", "")
        title = list_metadata.get("title", "")
        company_intro = extracted_info.get("company_introduction", "未提及")
        skill_req = extracted_info.get("skill_requirements", "未提及")
        salary = extracted_info.get("salary_benefits", "未提及")

        def _short(text: str, max_len: int = 200) -> str:
            text = str(text).replace("\n", " ").strip()
            return text[:max_len] + "..." if len(text) > max_len else text

        lines.append(f"<b>{i}. {_escape_html(_short(title))}</b>")
        lines.append(f"\n<b>URL:</b> {url}")
        lines.append(f"\n<b>公司:</b> {_escape_html(_short(company_intro))}")
        lines.append(f"\n<b>技能:</b> {_escape_html(_short(skill_req))}")
        lines.append(f"\n<b>薪资:</b> {_escape_html(_short(salary))}")
        lines.append("")

    return "\n".join(lines)


def notify_jobs(jobs: List[Dict[str, Any]]) -> bool:
    if not jobs:
        return True
    if not is_configured():
        logger.info("Telegram 未配置，跳过发送")
        return False

    message = format_jobs_message(jobs)

    if len(message) <= 4096:
        return send_message(message)

    for i in range(0, len(message), 4096):
        chunk = message[i : i + 4096]
        send_message(chunk)
    return True
