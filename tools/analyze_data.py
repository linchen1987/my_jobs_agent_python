import json
import re
from pathlib import Path
from typing import Dict, Any, Optional

# 导入本地模块
from prompt import process_job_data
from base_llm import BaseLLM
from load_json_data import load_json_data


def clean_llm_response(response: str) -> str:
    """
    清理LLM响应中的Markdown格式标记，提取纯净的JSON内容
    
    Args:
        response: LLM的原始响应字符串
        
    Returns:
        str: 清理后的纯净内容
    """
    # 移除 ```json 和 ``` 标记
    cleaned = re.sub(r'```json\s*\n?', '', response)
    cleaned = re.sub(r'\n?```$', '', cleaned)
    
    # 移除前后的空白字符
    cleaned = cleaned.strip()
    
    return cleaned


def analyze_job_with_llm(
    llm_client: BaseLLM,
    data: Optional[Dict[str, Any]] = None,
    json_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    分析招聘信息的主函数，支持直接传入数据或从文件加载
    
    Args:
        llm_client: LLM客户端实例（实现BaseLLM接口）
        data: 直接传入的JSON数据字典
        json_file_path: JSON数据文件路径
        
    Returns:
        Dict: 包含llm_analysis字段的字典，以便后续扩展
        
    Raises:
        ValueError: 当参数无效时
        FileNotFoundError: 当文件不存在时
        Exception: 其他处理过程中的异常
    """
    
    job_data = None
    input_source = "Unknown"
    
    if data:
        job_data = data
        input_source = "传入的数据"
    elif json_file_path:
        job_data = load_json_data(json_file_path)
        input_source = json_file_path
    else:
        raise ValueError("必须提供 data 或 json_file_path 中的一个作为数据源")

    # 2. 使用prompt.py生成提示词和处理数据
    prompt_result = process_job_data(job_data)
    
    # 3. 验证LLM客户端
    if not isinstance(llm_client, BaseLLM):
        raise ValueError("llm_client必须是BaseLLM的实例")
    
    # 4. 调用LLM分析
    llm_response = llm_client.chat(prompt_result['prompt'], keep_history=False)
    
    # 5. 清理LLM响应中的Markdown格式
    cleaned_response = clean_llm_response(llm_response)
    
    cleaned_response_json = json.loads(cleaned_response)
    
    
    # 6. 返回包含LLM分析结果的字典
    return {
        "llm_analysis": cleaned_response_json,
        "original_data": job_data
    }
