import os
import logging
from code_executor import CodeExecutor
from utils import extract_code_from_text

logger = logging.getLogger(__name__)

class ModuleExecutor:
    """负责运行模块、检测错误、触发修复"""
    def __init__(self, llm_client, module_manager, max_fix_attempts=3):
        self.llm = llm_client
        self.module_manager = module_manager
        self.max_fix_attempts = max_fix_attempts
        self.executor = CodeExecutor()

    def run(self, module_name, args=None):
        if module_name not in self.module_manager.modules:
            return {"success": False, "error": f"模块 {module_name} 不存在"}

        original_module = self.module_manager.modules[module_name]
        if args is None:
            args = []

        attempt = 0
        current_module = original_module
        using_temp = False
        temp_path = None

        while attempt < self.max_fix_attempts:
            logger.info(f"运行模块 {module_name} (尝试 {attempt+1}, 使用临时: {using_temp})")
            result = self.executor.run_function(current_module, args=args)

            # 检查是否因参数不足而失败
            if not result["success"] and "takes 0 positional arguments" in result.get("error", ""):
                # 参数不足的情况应由上层处理，这里返回特殊信号
                return {"success": False, "need_args": True, "error": result["error"]}

            error_keywords = ["错误", "失败", "无法获取", "网络请求错误", "Error", "Failed", "Exception", "not found", "timeout", "连接"]
            output = result.get("output", "")
            output_has_error = any(keyword in output for keyword in error_keywords)

            if result["success"] and not output_has_error:
                # 成功
                if using_temp and temp_path:
                    # 提升为永久
                    self.module_manager.promote_temp_to_permanent(module_name, temp_path)
                return {
                    "success": True,
                    "output": output,
                    "result": result["result"],
                    "module_name": module_name
                }
            else:
                # 失败
                if not result["success"]:
                    error_info = result["error"]
                else:
                    error_info = f"模块执行成功但输出包含错误信息：\n{output}"

                attempt += 1
                if attempt >= self.max_fix_attempts:
                    return {"success": False, "error": f"已达到最大修复次数，放弃。最后错误：{error_info}"}

                # 请求修复
                if using_temp and temp_path:
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        current_code = f.read()
                else:
                    with open(original_module.__file__, 'r', encoding='utf-8') as f:
                        current_code = f.read()

                fixed_code = self.llm.fix_code(current_code, error_info)

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
        # 循环外
        return {"success": False, "error": "未知错误"}