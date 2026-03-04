import os
import sys
import importlib.util
import shutil
import logging
import chardet
import re
import subprocess

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
    # 寻找最后一个 def 或 class 或 if __name__ 之后的内容
    lines = text.split('\n')
    code_lines = []
    in_code = False
    for line in lines:
        # 简单的启发式：如果行以 def、class、import、from、#、空格开头，或空行，则可能是代码
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

class ModuleManager:
    def __init__(self, module_dir="modules", llm_client=None):
        self.module_dir = module_dir
        os.makedirs(self.module_dir, exist_ok=True)
        self.modules = {}
        self.capabilities = {}
        self.llm = llm_client

    def scan_and_load(self):
        """扫描目录，加载所有模块，并尝试修复语法错误的模块"""
        for filename in os.listdir(self.module_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                name = filename[:-3]
                filepath = os.path.join(self.module_dir, filename)
                try:
                    self.load_module(name)
                except Exception as e:
                    logger.error(f"加载模块 {name} 失败: {e}")
                    if self.llm:
                        print(f"模块 {name} 存在错误，尝试自动修复...")
                        self.fix_module_syntax(name, filepath)
                    else:
                        print(f"模块 {name} 加载失败，请手动修复。")

    def fix_module_syntax(self, name, filepath):
        """使用LLM修复模块的语法错误"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            logger.error(f"读取模块 {name} 失败: {e}")
            return

        prompt = f"以下Python代码存在错误，请修正并返回完整的正确代码：\n\n{code}"
        try:
            fixed_code = self.llm.generate_code(prompt)
            # 提取代码（防止LLM返回额外文本）
            fixed_code = extract_code_from_text(fixed_code)
            self.create_module(name, fixed_code, overwrite=True)
            logger.info(f"模块 {name} 修复成功")
            print(f"模块 {name} 已自动修复并重新加载。")
        except Exception as e:
            logger.error(f"修复模块 {name} 失败: {e}")
            print(f"自动修复模块 {name} 失败，请手动检查。")

    def load_module(self, name, retry_count=0):
        """动态加载或重新加载指定模块，并更新能力描述。支持自动安装依赖后重试。"""
        filepath = os.path.join(self.module_dir, f"{name}.py")

        if not ensure_utf8_encoding(filepath):
            logger.error(f"无法处理文件编码，跳过模块 {name}")
            return None

        # 读取文件内容并尝试提取代码
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        clean_code = extract_code_from_text(content)

        # 如果提取后的代码与原内容不同，则写回文件
        if clean_code != content:
            logger.info(f"模块 {name} 包含额外文本，已自动清理")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(clean_code)

        valid, error_msg = check_syntax(filepath)
        if not valid:
            raise SyntaxError(f"模块 {name} 语法错误: {error_msg}")

        spec = importlib.util.spec_from_file_location(name, filepath)
        module = importlib.util.module_from_spec(spec)

        if name in sys.modules:
            del sys.modules[name]

        try:
            spec.loader.exec_module(module)
            sys.modules[name] = module
            self.modules[name] = module
        except ModuleNotFoundError as e:
            match = re.search(r"no module named '?([a-zA-Z0-9_\-]+)'?", str(e).lower())
            if match and retry_count < 2:
                package = match.group(1)
                logger.info(f"检测到缺失库：{package}，尝试自动安装...")
                print(f"检测到缺失库：{package}，尝试自动安装...")
                if install_package(package):
                    return self.load_module(name, retry_count + 1)
                else:
                    raise Exception(f"无法自动安装 {package}")
            else:
                raise
        except Exception as e:
            raise

        description = module.__doc__
        if not description:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith('# description:'):
                            description = line.split(':', 1)[1].strip()
                            break
            except Exception as e:
                logger.error(f"读取文件 {filepath} 失败: {e}")
        if not description:
            description = f"模块 {name}，无详细描述。"
        self.capabilities[name] = description

        logger.info(f"模块 {name} 加载成功，描述：{description}")
        return module

    def create_module(self, name, code, overwrite=False):
        """将代码写入文件并加载，可选覆盖已存在文件"""
        filepath = os.path.join(self.module_dir, f"{name}.py")
        if os.path.exists(filepath) and not overwrite:
            raise FileExistsError(f"模块 {name} 已存在，如需覆盖请设置 overwrite=True")
        # 写入前确保代码是纯净的
        clean_code = extract_code_from_text(code)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(clean_code)
        logger.info(f"模块 {name} 代码写入文件")
        return self.load_module(name)

    def update_module(self, name, code):
        """更新已存在模块的代码并重新加载"""
        filepath = os.path.join(self.module_dir, f"{name}.py")
        clean_code = extract_code_from_text(code)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(clean_code)
        logger.info(f"模块 {name} 代码更新")
        return self.load_module(name)

    def save_temp_module(self, name, code):
        """保存临时代码到临时文件，返回临时文件路径"""
        temp_filename = f"{name}.tmp.py"
        temp_path = os.path.join(self.module_dir, temp_filename)
        clean_code = extract_code_from_text(code)
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(clean_code)
        logger.info(f"临时代码保存至 {temp_path}")
        return temp_path

    def load_temp_module(self, temp_path, retry_count=0):
        """加载临时文件为模块，返回模块对象，支持自动安装依赖"""
        ensure_utf8_encoding(temp_path)
        # 读取并清理临时文件
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        clean_code = extract_code_from_text(content)
        if clean_code != content:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(clean_code)

        valid, error_msg = check_syntax(temp_path)
        if not valid:
            raise SyntaxError(f"临时模块语法错误: {error_msg}")
        spec = importlib.util.spec_from_file_location("temp_module", temp_path)
        temp_module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(temp_module)
        except ModuleNotFoundError as e:
            match = re.search(r"no module named '?([a-zA-Z0-9_\-]+)'?", str(e).lower())
            if match and retry_count < 2:
                package = match.group(1)
                logger.info(f"临时模块检测到缺失库：{package}，尝试自动安装...")
                print(f"检测到缺失库：{package}，尝试自动安装...")
                if install_package(package):
                    return self.load_temp_module(temp_path, retry_count + 1)
                else:
                    raise
            else:
                raise
        logger.info(f"临时代码模块加载成功")
        return temp_module

    def promote_temp_to_permanent(self, name, temp_path):
        """将临时文件提升为永久模块，覆盖原文件并重新加载"""
        permanent_path = os.path.join(self.module_dir, f"{name}.py")
        shutil.copy2(temp_path, permanent_path)
        os.remove(temp_path)
        logger.info(f"临时代码提升为永久模块 {name}")
        return self.load_module(name)

    def get_capabilities_summary(self):
        """返回所有能力摘要，格式：模块名: 描述"""
        if not self.capabilities:
            return "当前无任何能力模块。"
        return "\n".join([f"- {name}: {desc}" for name, desc in self.capabilities.items()])