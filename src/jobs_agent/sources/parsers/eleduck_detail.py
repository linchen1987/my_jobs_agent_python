#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from bs4 import BeautifulSoup
import re

def analyze_eleduck_page(html_file_path):
    """
    分析电鸭社区页面结构并抓取文章正文
    
    Args:
        html_file_path: HTML文件路径
    
    Returns:
        dict: 包含标题、正文等信息的字典
    """
    
    # 检查文件是否存在
    if not os.path.exists(html_file_path):
        raise FileNotFoundError(f"HTML文件不存在: {html_file_path}")
    
    # 读取HTML文件
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    result = {
        'title': '',
        'content': '',
        'meta_info': {},
        'tags': []
    }
    
    # 1. 抓取页面标题
    page_title = soup.find('h1', class_='page-title')
    if page_title:
        # 提取纯文本标题，去除HTML标签
        title_text = page_title.get_text(strip=True)
        # 移除类别标签，只保留主标题
        result['title'] = re.sub(r'^[^】]*】', '', title_text).strip()
    
    # 2. 抓取文章正文
    post_content = soup.find('div', class_='post-contents')
    if post_content:
        # 查找包含实际内容的rich-content区域
        rich_content = post_content.find('div', class_='rich-content')
        if rich_content:
            # 提取文本内容，保留基本格式
            content_parts = []
            
            for element in rich_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li']):
                if element.name.startswith('h'):
                    # 标题
                    content_parts.append(f"\n{element.get_text(strip=True)}\n")
                elif element.name == 'p':
                    # 段落
                    content_parts.append(element.get_text(strip=True))
                elif element.name in ['ul', 'ol']:
                    # 列表 - 跳过，因为li会单独处理
                    continue
                elif element.name == 'li':
                    # 列表项
                    content_parts.append(f"• {element.get_text(strip=True)}")
            
            result['content'] = '\n'.join(content_parts).strip()
    
    # 3. 抓取元数据信息
    meta_info_div = soup.find('div', class_='meta-info')
    if meta_info_div:
        meta_text = meta_info_div.get_text()
        # 提取阅读数、评论数等信息
        if '阅读' in meta_text:
            read_match = re.search(r'(\d+)阅读', meta_text)
            if read_match:
                result['meta_info']['reads'] = int(read_match.group(1))
        
        if '评论' in meta_text:
            comment_match = re.search(r'(\d+)评论', meta_text)
            if comment_match:
                result['meta_info']['comments'] = int(comment_match.group(1))
    
    # 4. 抓取标签信息
    field_items = soup.find_all('div', class_='field-item')
    for field in field_items:
        label_div = field.find('div', class_='field-label')
        body_div = field.find('div', class_='field-body')
        
        if label_div and body_div:
            label = label_div.get_text(strip=True).replace(':', '')
            tags = [a.get_text(strip=True) for a in body_div.find_all('a')]
            if tags:
                result['tags'].append({
                    'category': label,
                    'values': tags
                })
    
    return result

def extract_text_content(result):
    """
    从分析结果中提取纯文本内容
    
    Args:
        result: analyze_eleduck_page函数的返回结果
        
    Returns:
        str: 格式化的文本内容
    """
    
    lines = []
    
    # 添加标题
    if result['title']:
        lines.append(f"标题: {result['title']}")
        lines.append("=" * 50)
    
    # 添加正文
    if result['content']:
        lines.append("正文内容:")
        lines.append(result['content'])
        lines.append("")
    
    # 添加标签信息
    if result['tags']:
        lines.append("标签信息:")
        for tag_group in result['tags']:
            lines.append(f"{tag_group['category']}: {', '.join(tag_group['values'])}")
        lines.append("")
    
    # 添加元数据
    if result['meta_info']:
        lines.append("统计信息:")
        for key, value in result['meta_info'].items():
            lines.append(f"{key}: {value}")
    
    return '\n'.join(lines)

if __name__ == "__main__":
    try:
        # 分析HTML页面
        html_file = '.data/eleduck_detail.html'
        result = analyze_eleduck_page(html_file)
        
        # 输出结果
        print("=== 页面分析结果 ===")
        print(f"页面标题: {result['title']}")
        print(f"正文长度: {len(result['content'])} 字符")
        print(f"标签数量: {len(result['tags'])}")
        print(f"元数据: {result['meta_info']}")
        print("\n=== 抓取的文章内容 ===")
        print(extract_text_content(result))
        
    except Exception as e:
        print(f"错误: {e}")
