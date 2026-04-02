import logging
import os
import tempfile
from tools.fetch_page import fetch_page
from tools.parse_detail_page import analyze_eleduck_page, extract_text_content

logger = logging.getLogger(__name__)


def fetch_and_parse_detail(url):
    """演示使用分离的 fetch 和 parse 功能爬取电鸭社区文章"""
    html_content = fetch_page(url)

    if not html_content:
        logger.error(f"parse_detail skipped: page fetch failed - {url}")
        return None

    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_file = f.name

        result = analyze_eleduck_page(temp_file)
        extract_text_content(result)
        logger.info(f"parse_detail ok: {url}")
        return result

    except Exception as e:
        logger.error(f"parse_detail failed: {url} - {e}")
        return None
    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
