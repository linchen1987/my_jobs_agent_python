import json
import logging
import re
from datetime import datetime
from jobs_agent.llm.base import BaseLLM
from jobs_agent.core.prompt import process_job_data
from jobs_agent.sources.base import JobDetail, AnalysisResult, LLMAnalysis

logger = logging.getLogger(__name__)


def clean_llm_response(response: str) -> str:
    cleaned = re.sub(r"```json\s*\n?", "", response)
    cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def analyze_job_with_llm(
    llm_client: BaseLLM,
    detail: JobDetail,
) -> AnalysisResult:
    prompt_result = process_job_data(detail)

    if not isinstance(llm_client, BaseLLM):
        raise ValueError("llm_client必须是BaseLLM的实例")

    llm_response = llm_client.chat(prompt_result["prompt"], keep_history=False)

    cleaned_response = clean_llm_response(llm_response)

    try:
        cleaned_response_json: LLMAnalysis = json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        logger.error(f"原始响应: {llm_response[:500]}")
        logger.error(f"清理后响应: {cleaned_response[:500]}")
        raise

    source = detail["source"]
    item_id = detail["id"]
    global_id = f"{source}:{item_id}"

    return {
        "id": global_id,
        "source": source,
        "url": detail["url"],
        "title": detail["title"],
        "detail": detail,
        "llm_analysis": cleaned_response_json,
        "analyzed_at": datetime.now().isoformat(),
    }
