import logging
from utils import execute_system_command as _execute

logger = logging.getLogger(__name__)

class SystemCommandExecutor:
    """执行系统命令，并返回结果"""
    @staticmethod
    def execute(command):
        success = _execute(command)
        return {
            "success": success,
            "command": command,
            "message": "执行成功" if success else "执行失败"
        }