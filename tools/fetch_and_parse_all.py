#!/usr/bin/env python3

import logging
from typing import List, Dict, Optional
from tools.fetch_page import fetch_json
from tools.parse_list import parse_eleduck_list
from tools.fetch_and_parse import fetch_and_parse_detail

logger = logging.getLogger(__name__)


def fetch_and_parse_all(
    source_url_list: List[str], offset: int = 0, limit: Optional[int] = None
) -> List[Dict]:
    """
    抓取所有详情页数据并返回结构化数据列表

    Args:
        source_url_list: 源URL列表
        offset: 偏移量，从第几个开始返回 (默认0)
        limit: 限制数量，最多返回多少条数据 (默认None，即返回全部)

    Returns:
        List[Dict]: 包含详情页数据的列表，根据offset和limit参数过滤
    """
    all_posts = []

    logger.info(f"fetch_list: {len(source_url_list)} source(s)")
    for i, source_url in enumerate(source_url_list, 1):
        logger.debug(f"fetch_list[{i}]: {source_url}")
        data = fetch_json(source_url)

        if data:
            posts = parse_eleduck_list(data)
            logger.debug(f"fetch_list[{i}]: parsed {len(posts)} posts")
            all_posts.extend(posts)
        else:
            logger.error(f"fetch_list[{i}] failed: {source_url}")

    total = len(all_posts)
    logger.info(f"fetch_list done: {total} posts")

    if offset > 0 or (limit is not None and limit > 0):
        filtered_posts = (
            all_posts[offset : offset + limit]
            if limit is not None
            else all_posts[offset:]
        )
        logger.info(
            f"filter: {len(filtered_posts)}/{total} posts (offset={offset}, limit={limit})"
        )
    else:
        filtered_posts = all_posts

    all_details = []
    success_count = 0

    for i, post in enumerate(filtered_posts, 1):
        post_url = post.get("url", "")
        post_title = post.get("title", "Unknown")
        logger.info(f"[{i}/{len(filtered_posts)}] {post_title}")

        if not post_url:
            logger.warning(f"skip: no url - {post_title}")
            continue

        detail_data = fetch_and_parse_detail(post_url)

        if detail_data:
            detail_data["list_metadata"] = post
            all_details.append(detail_data)
            success_count += 1
        else:
            logger.error(f"detail failed: {post_url}")

    logger.info(f"done: {success_count}/{len(filtered_posts)} details fetched")

    return all_details
