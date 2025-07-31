#!/usr/bin/env python3

import logging
from typing import List, Dict, Optional
from tools.fetch_page import fetch_json
from tools.parse_list import parse_eleduck_list
from tools.fetch_and_parse import fetch_and_parse_detail

# 获取当前模块的logger
logger = logging.getLogger(__name__)

def fetch_and_parse_all(source_url_list: List[str], offset: int = 0, limit: Optional[int] = None) -> List[Dict]:
    """
    抓取所有详情页数据并返回结构化数据列表
    
    Args:
        source_url_list: 源URL列表
        offset: 偏移量，从第几个开始返回 (默认0)
        limit: 限制数量，最多返回多少条数据 (默认None，即返回全部)
    
    Returns:
        List[Dict]: 包含详情页数据的列表，根据offset和limit参数过滤
    """
    logger.debug("=== 开始抓取和解析 eleduck 数据 ===")
    
    all_posts = []
    
    # Step 1: 抓取列表数据
    logger.info("Step 1: 抓取列表数据...")
    for i, source_url in enumerate(source_url_list, 1):
        logger.debug(f"📥 抓取第 {i} 页: {source_url}")
        data = fetch_json(source_url)
        
        if data:
            posts = parse_eleduck_list(data)
            logger.debug(f"✅ 解析到 {len(posts)} 个帖子")
            all_posts.extend(posts)
        else:
            logger.error("❌ 抓取失败")
    
    logger.info(f"📊 总共获取到 {len(all_posts)} 个帖子")
    
    # Step 2: 根据参数过滤帖子列表
    total_posts = len(all_posts)
    
    if offset > 0 or (limit is not None and limit > 0):
        logger.info("Step 2: 应用过滤参数...")
        logger.debug(f"   - 从第 {offset + 1} 个开始")
        if limit is not None:
            logger.debug(f"   - 最多处理 {limit} 条")
        else:
            logger.debug("   - 处理全部剩余数据")
        
        # 应用切片过滤
        if limit is not None:
            filtered_posts = all_posts[offset:offset + limit]
        else:
            filtered_posts = all_posts[offset:]
        
        logger.info(f"   - 过滤结果: 将处理 {len(filtered_posts)}/{total_posts} 个帖子")
    else:
        logger.info("Step 2: 无过滤参数，处理全部帖子")
        filtered_posts = all_posts
    
    # Step 3: 抓取并解析过滤后帖子的详情页
    logger.info("Step 3: 抓取详情页数据...")
    
    all_details = []
    success_count = 0
    
    for i, post in enumerate(filtered_posts, 1):
        post_id = post.get('id', '')
        post_url = post.get('url', '')
        post_title = post.get('title', 'Unknown')
        
        logger.debug(f"[{i}/{len(filtered_posts)}] 处理帖子: {post_title}")
        logger.debug(f"📝 ID: {post_id}")
        logger.debug(f"🔗 URL: {post_url}")
        
        if not post_url:
            logger.warning("❌ 跳过: 无效的URL")
            continue
            
        # 抓取详情页数据
        detail_data = fetch_and_parse_detail(post_url)
        
        if detail_data:
            # 添加列表页的元数据到详情数据中
            detail_data['list_metadata'] = post
            all_details.append(detail_data)
            success_count += 1
        else:
            logger.error("❌ 详情页解析失败")
    
    logger.info(f"📊 成功获取 {success_count}/{len(filtered_posts)} 个详情页数据")
    logger.info(f"📋 返回 {len(all_details)} 条详情数据")
    
    return all_details 