import os
import sys
import yaml
import logging
from llm_client import LLMClient
from growbot import GrowBot

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('growbot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config(config_path="config.yaml"):
    """加载配置文件，只读取非敏感信息"""
    if not os.path.exists(config_path):
        print(f"配置文件 {config_path} 不存在，将使用默认配置。")
        return {
            "llm": {
                "provider": "openai",
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
    provider = llm_config.get("provider", "openai")
    model = llm_config.get("model")
    base_url = llm_config.get("base_url")

    # API 密钥从环境变量获取，不依赖配置文件
    try:
        llm = LLMClient(provider=provider, model=model, base_url=base_url)
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