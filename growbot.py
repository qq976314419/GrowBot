import json
import os
import logging
from module_manager import ModuleManager
from code_executor import CodeExecutor
from utils import execute_system_command

logger = logging.getLogger(__name__)


class GrowBot:
    def __init__(self, llm_client, config):
        self.llm = llm_client
        self.max_fix_attempts = config.get("app", {}).get("max_fix_attempts", 3)
        module_dir = config.get("app", {}).get("module_dir", "modules")
        self.module_manager = ModuleManager(module_dir, llm_client=self.llm)
        self.executor = CodeExecutor()
        self.module_manager.scan_and_load()
        # 初始化对话历史，最多保留20条消息
        self.conversation_history = []
        self.max_history = 20
        logger.info("GrowBot 初始化完成，当前能力：\n" + self.module_manager.get_capabilities_summary())

    def add_to_history(self, role, content):
        """添加消息到历史记录"""
        self.conversation_history.append({"role": role, "content": content})
        # 如果历史过长，截断
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def handle_user_request(self, user_input):
        if not user_input.strip():
            return
        logger.info(f"用户输入: {user_input}")
        # 将用户输入加入历史
        self.add_to_history("user", user_input)

        intent, params = self._parse_intent(user_input)
        logger.info(f"解析意图: {intent}, 参数: {params}")
        print(f"[调试] 意图: {intent}, 参数: {params}")

        if intent == "create_module":
            description = params.get("description")
            if description:
                self.create_module_from_llm(description)
            else:
                print("无法理解要创建的模块描述。")
                self.add_to_history("assistant", "无法理解要创建的模块描述。")
        elif intent == "run_module":
            module_name = params.get("module_name")
            args = params.get("args", [])
            if module_name:
                if module_name not in self.module_manager.modules:
                    print(f"模块 {module_name} 不存在，尝试根据请求自动创建...")
                    self.add_to_history("assistant", f"模块 {module_name} 不存在，正在尝试自动创建...")
                    self.create_module_from_llm(f"创建一个名为 {module_name} 的模块，功能：{user_input}")
                else:
                    self.run_module(module_name, args)
            else:
                print("未指定要运行的模块名。")
                self.add_to_history("assistant", "未指定要运行的模块名。")
        elif intent == "system_command":
            command = params.get("command")
            if command:
                self.execute_system_command(command)
            else:
                print("无法理解要执行的系统命令。")
                self.add_to_history("assistant", "无法理解要执行的系统命令。")
        elif intent == "chat":
            response = params.get("response", "抱歉，我无法理解您的请求。")
            print(f"GrowBot: {response}")
            self.add_to_history("assistant", response)
        else:
            msg = "无法识别您的意图，请稍后再试。"
            print(msg)
            self.add_to_history("assistant", msg)

    def _parse_intent(self, user_input):
        """使用LLM解析用户意图，参考当前已有能力和对话历史"""
        capabilities_summary = self.module_manager.get_capabilities_summary()

        system_prompt = f"""你是一个智能助手 GrowBot，需要解析用户输入并决定执行哪个动作。当前我已具备以下能力模块：

{capabilities_summary}

可用动作说明：

1. create_module: 用户想要创建一个新功能模块，且当前能力列表中**没有**能完成该功能的模块。你需要提取模块的功能描述（description），描述应清晰完整。**注意：如果用户请求可以通过编写一段Python代码来实现（例如获取实时天气、查询网络信息、处理数据等），你应该选择此动作，并生成相应的功能描述。生成的模块可以设计为需要用户输入（如城市名），通过 input() 获取或在 main 函数中接受参数。特别地，如果用户询问某个具体信息（如“介绍一下OpenClaw项目”），而你没有相关知识，但可以通过网络搜索获取，则应该选择 create_module，描述类似于“创建一个模块，用于搜索并返回关于[关键词]的信息”。**
2. run_module: 用户想要运行一个已有的模块。你需要提取模块名（module_name）和可能的参数列表（args，字符串列表）。模块名必须来自上面的能力列表。只有当用户请求的功能明显与某个已有模块匹配时，才选择此动作。
3. system_command: 用户想要执行系统命令（如打开文件夹、启动应用等）。你需要提取完整的命令字符串（command），注意命令中可能包含路径和参数。常见指令如“打开C盘”应转换为 "open C:\\\\" 或 "open C:/"；“打开文件夹 D:\\data” 转换为 "open D:\\\\data"；启动应用如“运行记事本”转换为 "notepad"。命令字符串应该尽可能符合操作系统原生命令。**注意：对于无法通过简单系统命令完成的任务（如获取CPU使用率），应优先考虑 create_module。**
4. 如果用户请求同时包含多个不同的功能（例如“CPU和内存使用率”），并且这些功能分别由独立的模块提供（如 cpu_usage 和 memory_usage），**你应该选择 create_module 动作**，描述中明确指出需要创建一个组合模块，该模块应调用现有的相关模块来同时返回所有请求的信息。**不要选择 run_module 只运行其中一个模块**，也不要选择 chat。
5. chat: 如果用户只是普通聊天、询问信息，或无法匹配以上动作，则直接回复。你需要提供友好的回应（response）。但请记住：对于可以通过编写代码获取的信息（如网络搜索），优先选择 create_module。

请以严格的JSON格式输出，不要包含其他文本。例如：
{{"action": "create_module", "description": "获取当前CPU使用率"}}
{{"action": "create_module", "description": "创建一个模块，同时获取CPU和内存使用率"}}
{{"action": "create_module", "description": "创建一个模块，用于搜索并返回关于OpenClaw项目的信息"}}
{{"action": "create_module", "description": "获取指定城市的实时天气，需要用户输入城市名"}}
{{"action": "run_module", "module_name": "cpu_usage", "args": []}}
{{"action": "system_command", "command": "open C:\\\\"}}
{{"action": "chat", "response": "你好，有什么可以帮助你的？"}}

用户输入：{user_input}
"""

        # 构建消息列表，包含历史对话和当前用户输入
        messages = [{"role": "system", "content": system_prompt}]
        # 添加历史消息（最近10条，避免过长）
        for msg in self.conversation_history[-10:]:
            messages.append(msg)
        # 当前用户输入已经在历史中，但为了确保解析的是最新，我们也可以再添加一次，但历史中已有，所以省略
        # 实际上我们已经在历史中添加了用户输入，但为了确保解析基于最新输入，我们可以直接使用历史中最后一条

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

    def execute_system_command(self, cmd):
        result = execute_system_command(cmd)
        # 将命令执行结果加入历史
        if result:
            self.add_to_history("assistant", f"系统命令执行成功：{cmd}")
        else:
            self.add_to_history("assistant", f"系统命令执行失败：{cmd}")

    def create_module_from_llm(self, description):
        logger.info(f"开始生成模块，描述：{description}")
        print(f"正在根据需求生成模块：{description}")

        attempt = 0
        code = None
        module_name = None

        while attempt < self.max_fix_attempts:
            try:
                if attempt == 0:
                    code = self.llm.generate_code(description)
                else:
                    pass

                # 提取模块名
                module_name = None
                for line in code.split('\n'):
                    if line.strip().startswith('# module_name:'):
                        module_name = line.split(':', 1)[1].strip()
                        break
                if not module_name:
                    if attempt == 0:
                        module_name = input("请为模块命名：").strip()
                    else:
                        import re
                        words = re.findall(r'\w+', description)
                        if words:
                            base = '_'.join(words[:3]).lower()
                        else:
                            base = 'module'
                        module_name = f"{base}_{attempt + 1}"

                module = self.module_manager.create_module(module_name, code)
                logger.info(f"模块 {module_name} 创建成功")
                print(f"模块 {module_name} 创建成功，已加载。")

                print(f"正在自动运行模块 {module_name}...")
                # 运行模块，并捕获输出加入历史
                self.run_module(module_name, [])
                return

            except SyntaxError as e:
                error_msg = str(e)
                logger.error(f"模块 {module_name} 语法错误: {error_msg}")
                print(f"创建模块时发生语法错误：{error_msg}")
                attempt += 1
                if attempt >= self.max_fix_attempts:
                    print("已达到最大修复次数，放弃。")
                    self.add_to_history("assistant", f"创建模块 {module_name} 失败，已达最大修复次数。")
                    return
                print("正在请求LLM修复代码...")
                fixed_code = self.llm.fix_code(code, error_msg)
                code = fixed_code

            except Exception as e:
                error_msg = str(e)
                logger.error(f"创建模块失败: {error_msg}")
                print(f"创建模块失败：{error_msg}")
                attempt += 1
                if attempt >= self.max_fix_attempts:
                    print("已达到最大修复次数，放弃。")
                    self.add_to_history("assistant", f"创建模块 {module_name} 失败，已达最大修复次数。")
                    return
                if code is not None:
                    print("正在请求LLM修复代码...")
                    fixed_code = self.llm.fix_code(code, error_msg)
                    code = fixed_code
                else:
                    code = self.llm.generate_code(description)

    def run_module(self, module_name, args=None):
        if module_name not in self.module_manager.modules:
            logger.error(f"模块 {module_name} 不存在")
            print(f"模块 {module_name} 不存在")
            self.add_to_history("assistant", f"模块 {module_name} 不存在")
            return

        original_module = self.module_manager.modules[module_name]

        if args is None or (isinstance(args, list) and len(args) == 0):
            args = []

        attempt = 0
        current_module = original_module
        using_temp = False
        temp_path = None

        while attempt < self.max_fix_attempts:
            logger.info(f"运行模块 {module_name} (尝试 {attempt + 1}, 使用临时: {using_temp})")
            print(f"运行模块 {module_name} (尝试 {attempt + 1})...")
            result = self.executor.run_function(current_module, args=args)

            # 检查是否因参数不足而失败
            if not result["success"] and "takes 0 positional arguments" in result.get("error", ""):
                print("模块需要参数，请提供：")
                args_input = input("请输入参数（空格分隔）：").strip()
                args = args_input.split() if args_input else []
                continue

            error_keywords = ["错误", "失败", "无法获取", "网络请求错误", "Error", "Failed", "Exception", "not found",
                              "timeout", "连接"]
            output = result.get("output", "")
            output_has_error = any(keyword in output for keyword in error_keywords)

            if result["success"] and not output_has_error:
                print("执行成功！")
                if output:
                    print("输出：", output)
                if result["result"] is not None:
                    print("返回值：", result["result"])
                # 将执行结果加入历史
                summary = f"模块 {module_name} 执行成功"
                if output:
                    summary += f"\n输出：{output[:200]}..."  # 截断避免过长
                if result["result"] is not None:
                    summary += f"\n返回值：{str(result['result'])[:200]}..."
                self.add_to_history("assistant", summary)

                if using_temp and temp_path:
                    logger.info(f"临时模块执行成功，提升为永久")
                    self.module_manager.promote_temp_to_permanent(module_name, temp_path)
                break
            else:
                if not result["success"]:
                    error_info = result["error"]
                else:
                    error_info = f"模块执行成功但输出包含错误信息：\n{output}"
                print("执行失败或输出错误：", error_info[:200])
                logger.error(f"执行失败或输出错误: {error_info}")
                attempt += 1
                if attempt >= self.max_fix_attempts:
                    print("已达到最大修复次数，放弃。")
                    logger.warning(f"模块 {module_name} 修复失败，放弃")
                    self.add_to_history("assistant", f"模块 {module_name} 执行失败，已达最大修复次数。")
                    break

                print("正在请求LLM修复代码...")
                if using_temp and temp_path:
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        current_code = f.read()
                else:
                    with open(original_module.__file__, 'r', encoding='utf-8') as f:
                        current_code = f.read()

                full_error = error_info
                fixed_code = self.llm.fix_code(current_code, full_error)

                temp_path = self.module_manager.save_temp_module(module_name, fixed_code)
                try:
                    current_module = self.module_manager.load_temp_module(temp_path)
                    using_temp = True
                    logger.info("临时模块加载成功，准备重试")
                except Exception as e:
                    logger.error(f"加载临时模块失败: {e}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    temp_path = None
                    current_module = original_module
                    using_temp = False
                    print("临时代码无法加载，将基于原代码继续尝试。")