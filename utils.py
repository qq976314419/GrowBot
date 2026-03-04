import os
import sys
import subprocess
import logging
import chardet
import shutil
import re

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

def ensure_utf8_encoding(filepath):
    """检查文件编码，如果不是 UTF-8，则转换为 UTF-8（备份原文件）"""
    if not os.path.exists(filepath):
        return True
    with open(filepath, 'rb') as f:
        raw_data = f.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    if encoding and encoding.lower() not in ('utf-8', 'ascii'):
        logger.warning(f"文件 {filepath} 编码为 {encoding}，将转换为 UTF-8")
        try:
            content = raw_data.decode(encoding)
        except Exception as e:
            logger.error(f"解码失败: {e}")
            return False
        backup_path = filepath + '.bak'
        shutil.copy2(filepath, backup_path)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已转换 {filepath} 为 UTF-8，原文件备份为 {backup_path}")
    return True

def extract_code_from_text(text):
    """从可能包含Markdown代码块或自然语言描述的文本中提取纯Python代码"""
    # 尝试匹配 ```python ... ``` 或 ``` ... ```
    pattern = r"```(?:python)?\s*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        # 返回最后一个代码块（通常最完整）
        return matches[-1].strip()
    # 如果没有代码块，则尝试去除末尾的自然语言说明
    lines = text.split('\n')
    code_lines = []
    in_code = False
    for line in lines:
        stripped = line.strip()
        if (stripped.startswith(('def ', 'class ', 'import ', 'from ', '#', '@', '"""', "'''")) or
            stripped == '' or
            line.startswith((' ', '\t'))):
            code_lines.append(line)
            in_code = True
        else:
            # 如果已经进入代码区，遇到非代码行可能表示开始说明，停止
            if in_code and stripped:
                break
            # 否则忽略前导说明
    if code_lines:
        return '\n'.join(code_lines)
    # 兜底：返回原文本
    return text

def check_syntax(filepath):
    """检查 Python 文件语法是否正确"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        compile(source, filepath, 'exec')
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def execute_system_command(command):
    """执行系统命令（如打开文件夹、启动应用等）"""
    logger.info(f"执行系统命令：{command}")
    print(f"执行系统命令：{command}")
    try:
        if sys.platform.startswith('win'):
            # Windows
            if command.lower().startswith("open "):
                path = command[5:].strip()
                # 使用 os.startfile 打开文件夹（更可靠）
                os.startfile(path)
                logger.info(f"使用 os.startfile 打开路径：{path}")
            else:
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