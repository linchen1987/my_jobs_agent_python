#!/usr/bin/env python3

from typing import List, Dict
from tools.fetch_page import fetch_json
from tools.parse_list import parse_eleduck_list
from tools.fetch_and_parse import fetch_and_parse_detail

def fetch_and_parse_all(source_url_list: List[str]) -> List[Dict]:
    """
    抓取所有详情页数据并返回结构化数据列表
    
    Args:
        source_url_list: 源URL列表
    
    Returns:
        List[Dict]: 包含所有详情页数据的列表
    """
    print("=== 开始抓取和解析 eleduck 数据 ===\n")
    
    all_posts = []
    all_details = []
    
    # Step 1: 抓取列表数据
    print("Step 1: 抓取列表数据...")
    for i, source_url in enumerate(source_url_list, 1):
        print(f"\n📥 抓取第 {i} 页: {source_url}")
        data = fetch_json(source_url)
        
        if data:
            posts = parse_eleduck_list(data)
            print(f"✅ 解析到 {len(posts)} 个帖子")
            all_posts.extend(posts)
        else:
            print("❌ 抓取失败")
    
    print(f"\n📊 总共获取到 {len(all_posts)} 个帖子")
    
    # Step 2: 抓取并解析每个帖子的详情页
    print("\nStep 2: 抓取详情页数据...")
    
    success_count = 0
    for i, post in enumerate(all_posts, 1):
        post_id = post.get('id', '')
        post_url = post.get('url', '')
        post_title = post.get('title', 'Unknown')
        
        print(f"\n[{i}/{len(all_posts)}] 处理帖子: {post_title}")
        print(f"📝 ID: {post_id}")
        print(f"🔗 URL: {post_url}")
        
        if not post_url:
            print("❌ 跳过: 无效的URL")
            continue
            
        # 抓取详情页数据
        detail_data = fetch_and_parse_detail(post_url)
        
        if detail_data:
            # 添加列表页的元数据到详情数据中
            detail_data['list_metadata'] = post
            all_details.append(detail_data)
            success_count += 1
        else:
            print("❌ 详情页解析失败")
    
    print(f"\n📊 成功获取 {success_count}/{len(all_posts)} 个详情页数据")
    return all_details 