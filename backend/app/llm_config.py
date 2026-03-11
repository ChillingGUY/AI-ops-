"""LLM 配置：预设供应商与文件持久化。用户可从千问、智谱、DeepSeek、OpenAI 中选择。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# 预设供应商（千问、智谱、DeepSeek、OpenAI）
LLM_PRESETS: dict[str, dict[str, str]] = {
    "openai": {
        "label": "OpenAI",
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo",
    },
    "qwen": {
        "label": "通义千问（阿里云）",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-turbo",
    },
    "zhipu": {
        "label": "智谱 GLM",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
    },
    "deepseek": {
        "label": "DeepSeek",
        "api_base": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
}

CONFIG_FILE = Path(__file__).resolve().parent.parent / "data" / "llm_config.json"


def _ensure_dir() -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_llm_config() -> dict[str, Any]:
    """从文件加载 LLM 配置，无则返回空。"""
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_llm_config(data: dict[str, Any]) -> None:
    """保存 LLM 配置到文件。"""
    _ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_llm_effective_config() -> dict[str, str | None]:
    """
    获取当前生效的 LLM 配置。优先级：文件 > 环境变量。
    返回 provider, api_base, api_key, model。
    """
    from app.config import get_settings

    file_cfg = load_llm_config()
    s = get_settings()

    provider = file_cfg.get("provider") or s.llm_provider or "none"
    if provider == "none":
        return {"provider": "none", "api_base": None, "api_key": None, "model": s.llm_model}

    preset = LLM_PRESETS.get(provider, {})
    api_base = file_cfg.get("api_base") or s.llm_api_base or preset.get("api_base")
    api_key = file_cfg.get("api_key") or s.llm_api_key
    model = file_cfg.get("model") or s.llm_model or preset.get("model", "gpt-3.5-turbo")

    return {"provider": provider, "api_base": api_base, "api_key": api_key, "model": model}
