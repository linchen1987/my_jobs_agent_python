import requests
import json
import os
from datetime import datetime
from urllib.parse import urlparse

def fetch_page(url):
    """
    抓取 URL 内容并返回
    
    Args:
        url: 目标URL
        
    Returns:
        str: 页面HTML内容，如果失败返回None
    """
    try:
        # 发送请求
        print(f"Fetching: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
        
        print(f"Successfully fetched {len(response.text)} characters")
        return response.text
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
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
        # 发送请求
        print(f"Fetching JSON from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
        
        print(f"Successfully fetched {len(response.text)} characters")
        
        # 解析 JSON
        try:
            json_data = json.loads(response.text)
            print(f"Successfully parsed JSON data (type: {type(json_data)})")
            return json_data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response content (first 200 chars): {response.text[:200]}")
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
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
        print("No content to save")
        return None
    
    # 创建 .data 目录（如果不存在）
    data_dir = '.data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")
    
    try:
        # 生成文件名
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{hostname}_{timestamp}.html"
        filepath = os.path.join(data_dir, filename)
        
        # 保存内容
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Content saved to: {filepath}")
        print(f"File size: {len(content)} characters")
        
        return filepath
        
    except Exception as e:
        print(f"Error saving file: {e}")
        return None

def fetch_and_save(url):
    """
    抓取 URL 内容并保存到 .data 目录（保持向后兼容）
    
    Args:
        url: 目标URL
        
    Returns:
        str: 保存的文件路径，如果失败返回None
    """
    content = fetch_page(url)
    if content:
        return save_content(content, url)
    return None

    result = fetch_and_save(url)
    if result:
        print(f"Successfully fetched and saved: {result}")
    else:
        print("Failed to fetch and save content")