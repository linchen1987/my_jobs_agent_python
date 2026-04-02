import logging
import requests
import json
import os
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def fetch_page(url):
    """
    抓取 URL 内容并返回

    Args:
        url: 目标URL

    Returns:
        str: 页面HTML内容，如果失败返回None
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        logger.info(f"fetch_page: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        logger.info(f"fetch_page ok: {len(response.text)} chars")
        return response.text

    except requests.exceptions.RequestException as e:
        logger.error(f"fetch_page failed: {url} - {e}")
        return None
    except Exception as e:
        logger.error(f"fetch_page error: {url} - {e}")
        return None

def fetch_json(url):
    """
    抓取 URL 内容并解析为 JSON 字典

    Args:
        url: 目标URL

    Returns:
        dict: 解析后的JSON数据，如果失败返回None
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*'
        }
        logger.info(f"fetch_json: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        logger.info(f"fetch_json ok: {len(response.text)} chars")

        try:
            json_data = json.loads(response.text)
            return json_data
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}, response[:200]: {response.text[:200]}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"fetch_json failed: {url} - {e}")
        return None
    except Exception as e:
        logger.error(f"fetch_json error: {url} - {e}")
        return None

def save_content(content, url):
    """
    保存内容到 .data 目录

    Args:
        content: 要保存的内容
        url: 原始URL（用于生成文件名）

    Returns:
        str: 保存的文件路径，如果失败返回None
    """
    if not content:
        logger.warning("save_content: no content")
        return None

    data_dir = '.data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{hostname}_{timestamp}.html"
        filepath = os.path.join(data_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"saved: {filepath} ({len(content)} chars)")
        return filepath

    except Exception as e:
        logger.error(f"save_content failed: {e}")
        return None

def fetch_and_save(url):
    """
    抓取 URL 内容并保存到 .data 目录

    Args:
        url: 目标URL

    Returns:
        str: 保存的文件路径，如果失败返回None
    """
    content = fetch_page(url)
    if content:
        return save_content(content, url)
    return None
