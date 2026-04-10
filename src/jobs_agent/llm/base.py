from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLM(ABC):
    """LLM抽象基类，定义所有LLM实现的通用接口"""
    
    @abstractmethod
    def __init__(self, api_key: str = None, model: str = None, **kwargs):
        """
        初始化LLM客户端
        
        Args:
            api_key: API密钥
            model: 模型ID
            **kwargs: 其他特定于实现的参数
        """
        pass
    
    @abstractmethod
    def chat(self, message: str, keep_history: bool = True, **kwargs) -> str:
        """
        发送消息并获取回复
        
        Args:
            message: 用户输入的消息
            keep_history: 是否保持对话历史
            **kwargs: 其他特定于实现的参数
            
        Returns:
            模型的回复内容
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回当前使用的模型名称"""
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            包含模型信息的字典
        """
        return {
            "model_name": self.model_name,
            "provider": self.__class__.__name__
        } 