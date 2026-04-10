from typing import List, Dict

def parse_eleduck_list(data: Dict) -> List[Dict]:
    """
    解析 eleduck API 返回的数据
    参数: data - API 返回的 JSON 数据
    返回一个list，每个item包含 { id: str, url: str, created_at: str, title: str, summary: str }
    """
    eleduck_detail_url_prefix = "https://eleduck.com/posts"
    eleduck_detail_url_prefix_t = "https://eleduck.com/tposts"
    try:
        posts = data.get('posts', [])
        result = []
        
        for post in posts:
            post_id = post.get('id', '')
            if not post_id:
                continue
            
            # Check if category ID is 22 (人才库) to use correct URL prefix
            category_info = post.get('category', {})
            category_id = category_info.get('id', '')
            if category_id == 22:
                url_prefix = eleduck_detail_url_prefix_t
            else:
                url_prefix = eleduck_detail_url_prefix
                
            item = {
                'id': post_id,
                'url': f"{url_prefix}/{post_id}",
                'created_at': post.get('published_at', ''),
                'title': post.get('title', ''),
                'full_title': post.get('full_title', ''),
                'summary': post.get('summary', ''),
                'views_count': post.get('views_count', 0),
                'comments_count': post.get('comments_count', 0),
                'upvotes_count': post.get('upvotes_count', 0),
                'downvotes_count': post.get('downvotes_count', 0),
                'category': category_info.get('name', ''),
                'user_nickname': post.get('user', {}).get('nickname', ''),
                'pinned': post.get('pinned', False),
                'featured': post.get('featured', False)
            }
            
            result.append(item)
        
        return result
        
    except Exception as e:
        print(f"错误: {e}")
        return []
