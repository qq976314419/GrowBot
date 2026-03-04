import logging
from history_manager import HistoryManager
from intent_parser import IntentParser
from module_executor import ModuleExecutor
from system_command import SystemCommandExecutor
from module_manager import ModuleManager
from utils import extract_code_from_text

logger = logging.getLogger(__name__)

class GrowBot:
    def __init__(self, llm_client, config):
        self.llm = llm_client
        self.max_fix_attempts = config.get("app", {}).get("max_fix_attempts", 3)
        module_dir = config.get("app", {}).get("module_dir", "modules")

        # 初始化各个组件
        self.module_manager = ModuleManager(module_dir, llm_client=self.llm)
        self.module_manager.scan_and_load()

        self.history = HistoryManager(max_history=20)
        self.intent_parser = IntentParser(self.llm, self.module_manager)
        self.module_executor = ModuleExecutor(self.llm, self.module_manager, self.max_fix_attempts)
        self.system_executor = SystemCommandExecutor()

        logger.info("GrowBot 初始化完成，当前能力：\n" + self.module_manager.get_capabilities_summary())

    def handle_user_request(self, user_input):
        if not user_input.strip():
            return
        logger.info(f"用户输入: {user_input}")
        self.history.add_message("user", user_input)

        # 获取历史消息用于意图解析
        recent_history = self.history.get_recent_messages(10)
        intent, params = self.intent_parser.parse(user_input, recent_history)
        logger.info(f"解析意图: {intent}, 参数: {params}")
        print(f"[调试] 意图: {intent}, 参数: {params}")

        if intent == "create_module":
            description = params.get("description")
            if description:
                self._create_module(description)
            else:
                self._reply("无法理解要创建的模块描述。")
        elif intent == "run_module":
            module_name = params.get("module_name")
            args = params.get("args", [])
            if module_name:
                if module_name not in self.module_manager.modules:
                    self._reply(f"模块 {module_name} 不存在，正在尝试自动创建...")
                    self._create_module(f"创建一个名为 {module_name} 的模块，功能：{user_input}")
                else:
                    self._run_module(module_name, args)
            else:
                self._reply("未指定要运行的模块名。")
        elif intent == "system_command":
            command = params.get("command")
            if command:
                self._run_system_command(command)
            else:
                self._reply("无法理解要执行的系统命令。")
        elif intent == "chat":
            response = params.get("response", "抱歉，我无法理解您的请求。")
            self._reply(response)
        else:
            self._reply("无法识别您的意图，请稍后再试。")

    def _create_module(self, description):
        logger.info(f"开始生成模块，描述：{description}")
        print(f"正在根据需求生成模块：{description}")

        attempt = 0
        code = None
        module_name = None

        while attempt < self.max_fix_attempts:
            try:
                if attempt == 0:
                    code = self.llm.generate_code(description)
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
                        base = '_'.join(words[:3]).lower() if words else 'module'
                        module_name = f"{base}_{attempt+1}"

                self.module_manager.create_module(module_name, code)
                logger.info(f"模块 {module_name} 创建成功")
                print(f"模块 {module_name} 创建成功，已加载。")
                print(f"正在自动运行模块 {module_name}...")
                self._run_module(module_name, [])
                return

            except SyntaxError as e:
                error_msg = str(e)
                logger.error(f"模块 {module_name} 语法错误: {error_msg}")
                print(f"创建模块时发生语法错误：{error_msg}")
                attempt += 1
                if attempt >= self.max_fix_attempts:
                    self._reply(f"创建模块 {module_name} 失败，已达最大修复次数。")
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
                    self._reply(f"创建模块 {module_name} 失败，已达最大修复次数。")
                    return
                if code is not None:
                    print("正在请求LLM修复代码...")
                    fixed_code = self.llm.fix_code(code, error_msg)
                    code = fixed_code
                else:
                    code = self.llm.generate_code(description)

    def _run_module(self, module_name, args):
        result = self.module_executor.run(module_name, args)
        if result.get("need_args"):
            # 需要用户输入参数
            print("模块需要参数，请提供：")
            args_input = input("请输入参数（空格分隔）：").strip()
            args = args_input.split() if args_input else []
            # 重新运行，不计数
            self._run_module(module_name, args)
            return

        if result["success"]:
            output = result.get("output", "")
            ret_val = result.get("result")
            print("执行成功！")
            if output:
                print("输出：", output)
            if ret_val is not None:
                print("返回值：", ret_val)
            # 记录到历史
            summary = f"模块 {module_name} 执行成功"
            if output:
                summary += f"\n输出：{output[:200]}..."
            if ret_val is not None:
                summary += f"\n返回值：{str(ret_val)[:200]}..."
            self.history.add_message("assistant", summary)
        else:
            error = result.get("error", "未知错误")
            print("执行失败：", error)
            self.history.add_message("assistant", f"模块 {module_name} 执行失败：{error}")

    def _run_system_command(self, command):
        result = self.system_executor.execute(command)
        if result["success"]:
            msg = f"系统命令执行成功：{command}"
        else:
            msg = f"系统命令执行失败：{command}"
        print(msg)
        self.history.add_message("assistant", msg)

    def _reply(self, message):
        print(f"GrowBot: {message}")
        self.history.add_message("assistant", message)