"""
招聘信息判断和提取提示词函数
"""

from typing import Dict, List, Any, Optional
import json


def create_job_analysis_prompt(title: str, content: str, categories: List[Dict]) -> str:
    """
    创建用于分析招聘信息的提示词
    
    Args:
        title: 文章标题
        content: 文章内容
        categories: 分类标签信息
        
    Returns:
        str: 格式化的提示词
    """
    
    # 格式化分类信息
    categories_text = ""
    if categories:
        for cat in categories:
            category_name = cat.get("category", "")
            values = cat.get("values", [])
            if category_name and values:
                categories_text += f"- {category_name}: {', '.join(values)}\n"
    
    prompt = f"""
请分析以下招聘信息，判断是否符合标准并提取关键信息。

## 输入信息：
**标题：** {title}

**内容：** 
{content}

**分类标签：**
{categories_text if categories_text else "无"}

## 判断标准：
1. 是否是招聘信息
2. 不是一次性项目，而是长期的全职或兼职工作
3. 是开发类工作，不是产品运营类
4. 过滤掉时薪**明显**低于 100 元的工作

## 请按以下格式返回分析结果：

```json
{{
    "is_qualified": true/false,
    "analysis": {{
        "is_recruitment": true/false,
        "is_long_term": true/false, 
        "is_development": true/false,
        "salary_meets_requirement": true/false/null,
        "reasoning": "详细分析原因（20 字以内，尽量少）"
    }},
    "extracted_info": {{
        "company_introduction": "公司/产品介绍",
        "company_website": "公司/产品网站",
        "job_responsibilities": "职位职责",
        "skill_requirements": "技能要求", 
        "salary_benefits": "薪资待遇"
    }}
}}
```

注意：
- 如果不符合标准，extracted_info 可以为空或null
- 如果信息中没有明确的薪资信息，salary_meets_requirement 设为 null
- 尽量从内容中提取具体信息，如果某项信息不存在则标明"未提及"
"""
    
    return prompt


def analyze_job_posting(title: str, content: str, categories: List[Dict]) -> Dict[str, Any]:
    """
    分析招聘信息的工具函数
    
    Args:
        title: 文章标题
        content: 文章内容  
        categories: 分类标签信息
        
    Returns:
        Dict: 包含分析结果的字典
    """
    
    # 创建提示词
    prompt = create_job_analysis_prompt(title, content, categories)
    
    # 注意：这里返回提示词，实际使用时需要调用LLM API
    return {
        "prompt": prompt,
        "input_data": {
            "title": title,
            "content": content,
            "categories": categories
        }
    }


def extract_categories_from_tags(tags: List[Dict]) -> List[Dict]:
    """
    从JSON数据的tags字段中提取categories信息
    
    Args:
        tags: JSON中的tags字段
        
    Returns:
        List[Dict]: 格式化的categories信息
    """
    categories = []
    if tags:
        for tag in tags:
            if isinstance(tag, dict) and "category" in tag and "values" in tag:
                categories.append({
                    "category": tag["category"],
                    "values": tag["values"]
                })
    return categories


def process_job_data(job_data: Dict) -> Dict[str, Any]:
    """
    处理完整的招聘数据
    
    Args:
        job_data: 完整的招聘数据JSON
        
    Returns:
        Dict: 处理结果
    """
    
    # 提取基本信息
    title = job_data.get("title", "")
    content = job_data.get("content", "")
    tags = job_data.get("tags", [])
    
    # 转换tags为categories格式
    categories = extract_categories_from_tags(tags)
    
    # 分析招聘信息
    result = analyze_job_posting(title, content, categories)
    
    # 添加原始数据引用
    result["original_data"] = {
        "meta_info": job_data.get("meta_info"),
        "list_metadata": job_data.get("list_metadata")
    }
    
    return result


# 示例使用函数
def example_usage():
    """
    示例用法
    """
    
    # 示例数据（基于提供的JSON）
    example_data = {
        "title": "需要一名thinkphp开发",
        "content": "需求\n\n维护已有CRM 系统。\n\n技术栈\n\nthinkphp6，可升级为 thinkphp8vue2、element-ui",
        "tags": [
            {
                "category": "招聘类型",
                "values": ["外包零活"]
            },
            {
                "category": "职业", 
                "values": ["开发"]
            },
            {
                "category": "工作方式",
                "values": ["线上兼职", "远程工作"]
            }
        ]
    }
    
    # 处理数据
    result = process_job_data(example_data)
    
    print("生成的提示词：")
    print(result["prompt"])
    
    return result


def test_with_real_data():
    """
    使用实际的JSON数据进行测试
    """
    
    # 实际的JSON数据（来自detail_0Xfl1r.json）
    real_data = {
        "title": "需要一名thinkphp开发",
        "content": "需求\n\n维护已有CRM 系统。\n\n技术栈\n\nthinkphp6，可升级为 thinkphp8vue2、element-ui",
        "meta_info": {
            "reads": 259,
            "comments": 20
        },
        "tags": [
            {
                "category": "招聘类型",
                "values": ["外包零活"]
            },
            {
                "category": "职业",
                "values": ["开发"]
            },
            {
                "category": "工作方式",
                "values": ["线上兼职", "远程工作"]
            }
        ],
        "list_metadata": {
            "id": "0Xfl1r",
            "url": "https://eleduck.com/posts/0Xfl1r",
            "created_at": "2025-07-20T12:56:49.837+08:00",
            "title": "需要一名thinkphp开发",
            "full_title": "【已结束】需要一名thinkphp开发",
            "summary": "需求 维护已有CRM 系统。 技术栈 thinkphp6，可升级为 thinkphp8   vue2、element-ui ",
            "views_count": 259,
            "comments_count": 20,
            "upvotes_count": 2,
            "downvotes_count": 0,
            "category": "招聘&找人",
            "user_nickname": "chuck",
            "pinned": False,
            "featured": False
        }
    }
    
    # 处理完整数据
    result = process_job_data(real_data)
    
    print("\n" + "="*60)
    print("完整数据测试结果：")
    print("="*60)
    print("\n输入数据概况：")
    print(f"- 标题: {real_data['title']}")
    print(f"- 分类: {real_data['list_metadata']['category']}")
    print(f"- 浏览量: {real_data['meta_info']['reads']}")
    print(f"- 评论数: {real_data['meta_info']['comments']}")
    
    print(f"\n提取的分类标签：")
    categories = result['input_data']['categories']
    for cat in categories:
        print(f"- {cat['category']}: {', '.join(cat['values'])}")
    
    print(f"\n生成的提示词长度: {len(result['prompt'])} 字符")
    print("\n注意：实际使用时，需要将生成的提示词发送给LLM API进行分析")
    
    return result


if __name__ == "__main__":
    # 运行基础示例
    example_usage()
    
    # 运行完整数据测试
    test_with_real_data()
