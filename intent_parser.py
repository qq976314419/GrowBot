import json
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class IntentParser:
    """使用LLM解析用户意图，返回动作和参数"""
    def __init__(self, llm_client, module_manager):
        self.llm = llm_client
        self.module_manager = module_manager

    def parse(self, user_input: str, history: list) -> Tuple[str, Dict[str, Any]]:
        capabilities_summary = self.module_manager.get_capabilities_summary()

        system_prompt = f"""你是一个智能助手 GrowBot，需要解析用户输入并决定执行哪个动作。当前我已具备以下能力模块：

{capabilities_summary}

可用动作说明：

1. create_module: 用户想要创建一个新功能模块，且当前能力列表中**没有**能完成该功能的模块。你需要提取模块的功能描述（description），描述应清晰完整。**注意：如果用户请求可以通过编写一段Python代码来实现（例如获取实时天气、查询网络信息、处理数据等），你应该选择此动作，并生成相应的功能描述。生成的模块可以设计为需要用户输入（如城市名），通过 input() 获取或在 main 函数中接受参数。**
2. run_module: 用户想要运行一个已有的模块。你需要提取模块名（module_name）和可能的参数列表（args，字符串列表）。模块名必须来自上面的能力列表。只有当用户请求的功能明显与某个已有模块匹配时，才选择此动作。
3. system_command: 用户想要执行系统命令（如打开文件夹、启动应用等）。你需要提取完整的命令字符串（command），注意命令中可能包含路径和参数。常见指令如“打开C盘”应转换为 "open C:\\\\" 或 "open C:/"；“打开文件夹 D:\\data” 转换为 "open D:\\\\data"；启动应用如“运行记事本”转换为 "notepad"。命令字符串应该尽可能符合操作系统原生命令。
4. 如果用户请求同时包含多个不同的功能（例如“CPU和内存使用率”），并且这些功能分别由独立的模块提供（如 cpu_usage 和 memory_usage），**你应该选择 create_module 动作**，描述中明确指出需要创建一个组合模块，该模块应调用现有的相关模块来同时返回所有请求的信息。
5. chat: 如果用户只是普通聊天、询问信息，或无法匹配以上动作，则直接回复。你需要提供友好的回应（response）。但请记住：对于可以通过编写代码获取的信息（如网络搜索），优先选择 create_module。

请以严格的JSON格式输出，不要包含其他文本。例如：
{{"action": "create_module", "description": "获取当前CPU使用率"}}
{{"action": "create_module", "description": "创建一个模块，同时获取CPU和内存使用率"}}
{{"action": "create_module", "description": "创建一个模块，用于搜索并返回关于OpenClaw项目的信息"}}
{{"action": "run_module", "module_name": "cpu_usage", "args": []}}
{{"action": "system_command", "command": "open C:\\\\"}}
{{"action": "chat", "response": "你好，有什么可以帮助你的？"}}

用户输入：{user_input}
"""

        messages = [{"role": "system", "content": system_prompt}]
        # 添加历史消息
        messages.extend(history)

        try:
            response_text = self.llm.chat(messages, temperature=0.1)
            # 清理可能的markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            result = json.loads(response_text)
            action = result.get("action")
            params = {k: v for k, v in result.items() if k != "action"}
            return action, params
        except Exception as e:
            logger.error(f"意图解析失败：{e}")
            return "chat", {"response": "抱歉，我无法理解您的请求。"}