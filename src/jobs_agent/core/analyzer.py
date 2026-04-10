import json
import logging
import re
from datetime import datetime
from jobs_agent.llm.base import BaseLLM
from jobs_agent.core.prompt import process_job_data
from jobs_agent.sources.base import JobDetail, AnalysisResult, LLMAnalysis

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


def clean_llm_response(response: str) -> str:
    cleaned = re.sub(r"```json\s*\n?", "", response)
    cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def repair_llm_json(text: str) -> str:
    text = re.sub(r":\s*\*\*\*\s*([,}\n])", r": true\1", text)

    string_keys = (
        "reasoning|company_introduction|company_website"
        "|job_responsibilities|skill_requirements|salary_benefits"
    )
    text = re.sub(
        rf'("{string_keys}")\s*:\s*([^"\d\[{{][^"]*?)("\s*[,}}\n])',
        lambda m: f'{m.group(1)}: "{m.group(2)}{m.group(3)}"',
        text,
    )

    return text


def parse_llm_json(text: str) -> LLMAnalysis:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = repair_llm_json(text)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON修复后仍解析失败: {e}")
            raise


def analyze_job_with_llm(
    llm_client: BaseLLM,
    detail: JobDetail,
) -> AnalysisResult:
    prompt_result = process_job_data(detail)

    if not isinstance(llm_client, BaseLLM):
        raise ValueError("llm_client必须是BaseLLM的实例")

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        llm_response = llm_client.chat(prompt_result["prompt"], keep_history=False)
        cleaned_response = clean_llm_response(llm_response)

        try:
            cleaned_response_json: LLMAnalysis = parse_llm_json(cleaned_response)
            break
        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"第{attempt + 1}次JSON解析失败: {e}")
            if attempt < MAX_RETRIES:
                logger.info(f"重试 LLM 调用 ({attempt + 1}/{MAX_RETRIES})")
            else:
                logger.error(f"原始响应: {llm_response[:500]}")
                logger.error(f"清理后响应: {cleaned_response[:500]}")
                raise last_error

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
