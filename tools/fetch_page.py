import logging
import requests
import json
import os
import time
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _request_with_retry(
    method, url, headers=None, max_retries=3, base_delay=2.0, **kwargs
):
    retries = 0
    delay = base_delay

    while True:
        try:
            response = requests.request(method, url, headers=headers, **kwargs)

            if response.status_code in RETRYABLE_STATUS_CODES and retries < max_retries:
                retries += 1
                logger.warning(
                    f"请求返回 {response.status_code}，第 {retries}/{max_retries} 次重试，"
                    f"等待 {delay:.1f}s - {url}"
                )
                time.sleep(delay)
                delay = min(delay * 2, 60.0)
                continue

            if response.status_code in RETRYABLE_STATUS_CODES:
                logger.error(
                    f"请求最终失败（已重试 {max_retries} 次）: {url} - {response.status_code}"
                )
                return None

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            retries += 1
            if retries <= max_retries:
                logger.warning(
                    f"请求失败，第 {retries}/{max_retries} 次重试，等待 {delay:.1f}s - {url} - {e}"
                )
                time.sleep(delay)
                delay = min(delay * 2, 60.0)
            else:
                logger.error(f"请求最终失败（已重试 {max_retries} 次）: {url} - {e}")
                return None
        except Exception as e:
            logger.error(f"请求异常: {url} - {e}")
            return None


def fetch_page(url, max_retries=3, base_delay=2.0):
    logger.info(f"fetch_page: {url}")
    response = _request_with_retry(
        "GET",
        url,
        headers=DEFAULT_HEADERS,
        max_retries=max_retries,
        base_delay=base_delay,
        timeout=30,
    )
    if response is None:
        return None

    logger.info(f"fetch_page ok: {len(response.text)} chars")
    return response.text


def fetch_json(url, max_retries=3, base_delay=2.0):
    headers = {**DEFAULT_HEADERS, "Accept": "application/json, text/plain, */*"}
    logger.info(f"fetch_json: {url}")
    response = _request_with_retry(
        "GET",
        url,
        headers=headers,
        max_retries=max_retries,
        base_delay=base_delay,
        timeout=30,
    )
    if response is None:
        return None

    logger.info(f"fetch_json ok: {len(response.text)} chars")

    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}, response[:200]: {response.text[:200]}")
        return None


def save_content(content, url):
    if not content:
        logger.warning("save_content: no content")
        return None

    data_dir = ".data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{hostname}_{timestamp}.html"
        filepath = os.path.join(data_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"saved: {filepath} ({len(content)} chars)")
        return filepath

    except Exception as e:
        logger.error(f"save_content failed: {e}")
        return None


def fetch_and_save(url):
    content = fetch_page(url)
    if content:
        return save_content(content, url)
    return None
