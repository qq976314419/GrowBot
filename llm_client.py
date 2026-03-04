import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, provider="openai", model=None, base_url=None):
        """
        初始化 LLM 客户端，API 密钥从环境变量获取。
        环境变量命名规则：{provider.upper()}_API_KEY
        例如：OPENAI_API_KEY, DEEPSEEK_API_KEY
        """
        self.provider = provider.lower()
        env_var = f"{self.provider.upper()}_API_KEY"
        self.api_key = os.getenv(env_var)
        if not self.api_key:
            raise ValueError(f"未找到环境变量 {env_var}，请设置后再试。")

        # 设置默认模型
        default_models = {
            "openai": "gpt-4",
            "deepseek": "deepseek-chat"
        }
        self.model = model or default_models.get(self.provider, "gpt-4")

        # 构建客户端参数
        client_kwargs = {"api_key": self.api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        else:
            if self.provider == "deepseek":
                client_kwargs["base_url"] = "https://api.deepseek.com/v1"
            # OpenAI 使用官方 API，无需设置 base_url

        self.client = OpenAI(**client_kwargs)
        logger.info(f"LLM客户端初始化成功，提供商：{self.provider}，模型：{self.model}")

    def _call_chat_completion(self, messages, temperature=0.2):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content

    def chat(self, messages, temperature=0.2):
        return self._call_chat_completion(messages, temperature)

    def generate_code(self, prompt):
        messages = [
            {"role": "system", "content": """你是一个Python专家，只生成纯Python代码，不要包含任何额外的文本、解释、示例或说明。代码中只能包含必要的注释（以#开头），不要使用中文注释。代码应该可以直接被Python解释器执行。生成的模块必须包含一个名为main的函数作为入口。main函数应定义为无参数（def main():）或接受一个列表参数（def main(args=None):），以便在需要时接收用户输入。如果模块需要用户输入，应该在main函数内部使用input()获取，或者通过args参数接收。如果模块需要第三方库，请在代码开头用注释说明依赖，例如：# requires: requests。可以在注释中提供建议的模块名，例如：# module_name: fib。不要包含任何Markdown标记（如```python）或自然语言描述。"""},
            {"role": "user", "content": prompt}
        ]
        return self._call_chat_completion(messages)

    def fix_code(self, code, error_msg):
        prompt = f"以下代码执行出错：\n\n{code}\n\n错误信息：{error_msg}\n请提供修正后的完整代码，只返回纯Python代码，不要包含任何额外文本。"
        return self.generate_code(prompt)