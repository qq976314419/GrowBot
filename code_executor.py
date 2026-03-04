import sys
import traceback
import importlib
import re
from io import StringIO
import logging
from utils import install_package

logger = logging.getLogger(__name__)

class CodeExecutor:
    @staticmethod
    def run_function(module, func_name="main", args=None):
        if args is None:
            args = []
        old_stdout = sys.stdout
        redirected_output = StringIO()
        sys.stdout = redirected_output

        try:
            func = getattr(module, func_name, None)
            if not func:
                raise AttributeError(f"模块中没有 {func_name} 函数")
            result = func(*args)
            output = redirected_output.getvalue()
            logger.info(f"函数执行成功，输出：{output[:200]}...")
            return {"success": True, "output": output, "result": result, "error": None}
        except ModuleNotFoundError as e:
            match = re.search(r"no module named '?([a-zA-Z0-9_\-]+)'?", str(e).lower())
            if match:
                package = match.group(1)
                logger.warning(f"检测到缺失库：{package}")
                print(f"检测到缺失库：{package}，尝试自动安装...")
                if install_package(package):
                    try:
                        importlib.reload(module)
                        return CodeExecutor.run_function(module, func_name, args)
                    except Exception as e2:
                        logger.error(f"安装后重新执行失败：{e2}")
                        return {"success": False, "output": "", "result": None, "error": traceback.format_exc()}
                else:
                    return {"success": False, "output": "", "result": None, "error": f"无法安装 {package}"}
            else:
                error_trace = traceback.format_exc()
                logger.error(f"执行出错：{error_trace}")
                return {"success": False, "output": redirected_output.getvalue(), "result": None, "error": error_trace}
        except SyntaxError as e:
            # 捕获语法错误
            error_trace = traceback.format_exc()
            logger.error(f"语法错误：{error_trace}")
            return {"success": False, "output": redirected_output.getvalue(), "result": None, "error": error_trace}
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"执行出错：{error_trace}")
            return {"success": False, "output": redirected_output.getvalue(), "result": None, "error": error_trace}
        finally:
            sys.stdout = old_stdout