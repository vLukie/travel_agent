"""
配置文件模块
优先级：环境变量 > config.json > 默认值
支持多 Provider：DeepSeek / 通义千问 / GLM / OpenAI / SiliconFlow
"""

import json
import os
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"

# ===== Provider 配置表 =====
PROVIDER_CONFIG = {
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "default_model": "deepseek-chat",
    },
    "qwen": {
        "label": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-long"],
        "default_model": "qwen-plus",
    },
    "glm": {
        "label": "GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4-plus", "glm-4-air", "glm-4-flash"],
        "default_model": "glm-4-flash",
    },
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini"],
        "default_model": "gpt-4o-mini",
    },
    "siliconflow": {
        "label": "SiliconFlow",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": ["deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1", "Qwen/Qwen2.5-72B-Instruct"],
        "default_model": "deepseek-ai/DeepSeek-V3",
    },
}

PROVIDER_NAMES = list(PROVIDER_CONFIG.keys())
PROVIDER_LABELS = [p["label"] for p in PROVIDER_CONFIG.values()]

# label → key 映射
LABEL_TO_KEY = {p["label"]: key for key, p in PROVIDER_CONFIG.items()}
KEY_TO_LABEL = {key: p["label"] for key, p in PROVIDER_CONFIG.items()}


def load_config():
    """加载配置，合并 config.json 和环境变量"""
    config = {
        "llm": {
            "provider": "deepseek",
            "api_key": "",
            "base_url": PROVIDER_CONFIG["deepseek"]["base_url"],
            "model": PROVIDER_CONFIG["deepseek"]["default_model"],
        },
        "agent": {
            "max_iterations": 12,
            "system_prompt": "你是小林，23岁的女生，性格活泼热情开朗。你是我的旅行规划助手，精通国内各城市的旅游信息。查询城市信息时优先使用 search_city_info（本地已收录23个城市），只有 search_city_info 查不到时才用 web_search。你可以查询景点、估算预算、推荐目的地、换算货币。回答问题时请提供清晰有条理的行程建议，说话语气像朋友聊天一样轻松活泼，多用语气词和表情符号。主动给出具体方案，比如 Day1 上午去哪里、下午去哪里这样的结构化行程。你也能执行常规的计算、搜索和待办管理。",
        },
        "knowledge": {
            "embedding_model": "BAAI/bge-small-zh-v1.5",
            "chroma_db_path": str(Path(__file__).parent / "chroma_db"),
            "knowledge_dir": str(Path(__file__).parent / "knowledge"),
        },
    }

    # 从 config.json 加载
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                file_config = json.load(f)
            _deep_merge(config, file_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  config.json 加载失败: {e}")

    # 确保路径用绝对路径（防止 config.json 的相对路径覆盖）
    config["knowledge"]["chroma_db_path"] = str(Path(__file__).parent / "chroma_db")
    config["knowledge"]["knowledge_dir"] = str(Path(__file__).parent / "knowledge")

    # 环境变量覆盖（优先级最高）
    env_overrides = {
        ("llm", "api_key"): "LLM_API_KEY",
        ("llm", "base_url"): "LLM_BASE_URL",
        ("llm", "model"): "LLM_MODEL",
        ("llm", "provider"): "LLM_PROVIDER",
    }
    for (section, key), env_var in env_overrides.items():
        if env_var in os.environ:
            config[section][key] = os.environ[env_var]

    # 根据 provider 解析 base_url
    _resolve_provider(config)

    return config


def _resolve_provider(config):
    """
    根据 provider 名称填充 base_url 和 model 默认值
    如果用户在 config.json 里指定了 base_url，保留手动覆盖
    """
    provider = config["llm"].get("provider", "deepseek")
    provider_key = provider

    # 兼容中文 label
    if provider in LABEL_TO_KEY:
        provider_key = LABEL_TO_KEY[provider]

    if provider_key not in PROVIDER_CONFIG:
        print(f"⚠️  未知 provider '{provider}'，使用 deepseek")
        provider_key = "deepseek"
        config["llm"]["provider"] = "deepseek"

    info = PROVIDER_CONFIG[provider_key]

    # 只有未设置 base_url 时才用默认值
    if not config["llm"].get("base_url"):
        config["llm"]["base_url"] = info["base_url"]

    # 标准化 provider 字段为 key
    config["llm"]["provider"] = provider_key


def save_config(config):
    """保存配置到 config.json"""
    # 保存时确保 provider 用 key 形式
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def _deep_merge(base, overlay):
    """递归合并字典"""
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


# 单例配置
CONFIG = load_config()
