import os
import sys
import yaml
import logging
from llm_client import LLMClient
from growbot import GrowBot  # 导入更名后的类

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('growbot.log', encoding='utf-8'),  # 添加 encoding
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config(config_path="config.yaml"):
    if not os.path.exists(config_path):
        print(f"配置文件 {config_path} 不存在，将使用默认配置。")
        return {
            "llm": {
                "provider": "openai",
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "model": "gpt-4"
            },
            "app": {
                "max_fix_attempts": 3,
                "module_dir": "modules"
            }
        }
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("GrowBot 启动")

    config = load_config()
    llm_config = config.get("llm", {})
    if not llm_config.get("api_key"):
        logger.error("未提供API密钥")
        print("错误：配置文件中未提供API密钥。")
        sys.exit(1)

    try:
        llm = LLMClient(llm_config)
    except Exception as e:
        logger.error(f"初始化LLM客户端失败：{e}")
        print(f"初始化LLM客户端失败：{e}")
        sys.exit(1)

    bot = GrowBot(llm, config)

    print("=" * 50)
    print("GrowBot 已启动 — 一个能够自我进化的智能助手")
    print("=" * 50)
    print("输入 'exit' 或 'quit' 退出。")

    while True:
        try:
            cmd = input(">>> ").strip()
            if cmd.lower() in ("exit", "quit"):
                break
            bot.handle_user_request(cmd)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.exception("未处理的异常")
            print(f"发生错误：{e}")

if __name__ == "__main__":
    main()