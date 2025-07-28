import json
from typing import Dict, Any

def load_json_data(json_file_path: str) -> Dict[str, Any]:
    """
    加载JSON数据文件
    
    Args:
        json_file_path: JSON文件路径
        
    Returns:
        解析后的JSON数据
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"📄 成功加载数据文件: {json_file_path}")
        return data
    except Exception as e:
        print(f"❌ 加载数据文件失败: {e}")
        raise
