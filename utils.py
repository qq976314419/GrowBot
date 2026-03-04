import os
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)

def install_package(package_name):
    """使用pip自动安装缺失的Python包"""
    logger.info(f"尝试安装缺失库：{package_name}")
    print(f"正在安装缺失的库：{package_name}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logger.info(f"成功安装 {package_name}")
        print(f"成功安装 {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"安装 {package_name} 失败：{e}")
        print(f"安装 {package_name} 失败：{e}")
        return False

def execute_system_command(command):
    """执行系统命令（如打开文件夹、启动应用等）"""
    logger.info(f"执行系统命令：{command}")
    print(f"执行系统命令：{command}")
    try:
        if sys.platform.startswith('win'):
            # Windows 系统
            if command.lower().startswith("open "):
                path = command[5:].strip()
                # 使用 os.startfile 打开文件夹（更可靠）
                os.startfile(path)
                logger.info(f"使用 os.startfile 打开路径：{path}")
            else:
                # 其他命令直接执行
                subprocess.run(command, shell=True)
        elif sys.platform.startswith('darwin'):
            # macOS
            if command.startswith("open "):
                subprocess.run(command, shell=True)
            else:
                subprocess.run(command, shell=True)
        else:
            # Linux
            if command.startswith("open "):
                subprocess.run(f"xdg-open {command[5:]}", shell=True)
            else:
                subprocess.run(command, shell=True)
        logger.info(f"系统命令执行完成：{command}")
        print(f"系统命令执行完成：{command}")
        return True
    except Exception as e:
        logger.error(f"执行系统命令失败：{e}")
        print(f"执行系统命令失败：{e}")
        return False