import os
import time
import requests

from llm.base import BaseLLM


class OpenAIChat(BaseLLM):
    def __init__(
        self, api_key: str = None, model: str = None, base_url: str = None, **kwargs
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_MODEL_ID", "gpt-4")
        self.base_url = base_url or os.environ.get("OPENAI_API_ENDPOINT")

        if not self.api_key:
            raise ValueError("请设置OPENAI_API_KEY环境变量或传入api_key参数")

        if not self.base_url:
            raise ValueError("请设置OPENAI_API_ENDPOINT环境变量或传入base_url参数")

        print(f"✅ OpenAI Compatible 客户端初始化成功！使用模型：{self.model}")

    def chat(
        self,
        message: str,
        keep_history: bool = True,
        max_retries: int = 3,
        retry_delay: int = 1,
        **kwargs,
    ) -> str:
        messages = [{"role": "user", "content": message}]

        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)

        # 深度思考参数：enabled启用深度思考，disabled禁用深度思考
        thinking_config = {"type": "disabled"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "thinking": thinking_config,
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()
                result = response.json()

                return result["choices"][0]["message"]["content"]

            except Exception as e:
                if attempt < max_retries - 1:
                    print(
                        f"⚠️ 第 {attempt + 1} 次请求失败: {e}，{retry_delay}秒后重试..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"❌ 已重试 {max_retries} 次，请求仍然失败: {e}")
                    return f"❌ 请求失败: {e}"

    @property
    def model_name(self) -> str:
        return self.model
