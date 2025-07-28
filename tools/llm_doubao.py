import os
import sys
from volcenginesdkarkruntime import Ark

# 添加当前目录到sys.path以便导入base_llm
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from base_llm import BaseLLM

class DoubaoChat(BaseLLM):
    """豆包大模型对话类"""
    
    def __init__(self, api_key: str = None, model: str = "doubao-seed-1-6-250615", **kwargs):
        """
        初始化豆包对话客户端
        
        Args:
            api_key: API密钥，如果不提供会从环境变量DOUBAO_API_KEY读取
            model: 模型ID，默认使用doubao-seed-1-6-250615
        """
        self.api_key = api_key or os.environ.get("DOUBAO_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("请设置DOUBAO_API_KEY环境变量或传入api_key参数")
            
        try:
            self.client = Ark(api_key=self.api_key)
            print(f"✅ 豆包大模型客户端初始化成功！使用模型：{self.model}")
        except Exception as e:
            print(f"❌ 客户端初始化失败: {e}")
            raise
    
    def chat(self, message: str, keep_history: bool = True, **kwargs) -> str:
        """
        发送消息并获取回复
        
        Args:
            message: 用户输入的消息
            keep_history: 是否保持对话历史（当前实现暂不支持历史记录）
            **kwargs: 其他参数，如temperature, max_tokens等
            
        Returns:
            模型的回复内容
        """
        try:
            # 构建消息
            messages = [{"role": "user", "content": message}]
            
            # 从kwargs中提取参数，设置默认值
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 2000)
            
            # 调用API
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,  # 控制回复的随机性
                max_tokens=max_tokens,    # 最大回复长度
            )
            
            # 获取回复内容
            return completion.choices[0].message.content
            
        except Exception as e:
            return f"❌ 请求失败: {e}"
    
    @property
    def model_name(self) -> str:
        """返回当前使用的模型名称"""
        return self.model
