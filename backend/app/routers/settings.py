"""LLM 与平台设置 API。"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.llm_config import LLM_PRESETS, get_llm_effective_config, load_llm_config, save_llm_config

router = APIRouter(prefix="/settings", tags=["平台设置"])


class LLMConfigOut(BaseModel):
    """LLM 配置（读取）"""
    provider: str = Field(description="供应商：openai/qwen/zhipu/deepseek/none")
    api_base: str | None = Field(None, description="API 地址")
    api_key: str | None = Field(None, description="API Key（脱敏返回）")
    model: str = Field(description="模型名称")
    presets: dict = Field(description="可选预设列表")


class LLMConfigIn(BaseModel):
    """LLM 配置（保存）"""
    provider: str = Field(description="供应商：openai/qwen/zhipu/deepseek/none")
    api_base: str | None = Field(None, description="API 地址，留空则用预设默认")
    api_key: str | None = Field(None, description="API Key，留空则不修改原有")
    model: str | None = Field(None, description="模型名称，留空则用预设默认")


@router.get(
    "/llm",
    response_model=LLMConfigOut,
    summary="获取 LLM 配置",
    description="返回当前 LLM 配置及可选供应商预设（千问/智谱/DeepSeek/OpenAI）。",
)
def get_llm_config() -> LLMConfigOut:
    cfg = get_llm_effective_config()
    api_key = cfg.get("api_key")
    masked = (api_key[:8] + "***" + api_key[-4:]) if api_key and len(api_key) > 12 else ("***" if api_key else None)
    return LLMConfigOut(
        provider=cfg.get("provider", "none"),
        api_base=cfg.get("api_base"),
        api_key=masked,
        model=cfg.get("model", "gpt-3.5-turbo"),
        presets={
            k: {"label": v["label"], "api_base": v["api_base"], "model": v["model"]}
            for k, v in LLM_PRESETS.items()
        },
    )


@router.post(
    "/llm",
    summary="保存 LLM 配置",
    description="保存用户选择的 LLM 供应商及 API 信息。",
)
def save_llm(cfg_in: LLMConfigIn) -> dict:
    file_cfg = load_llm_config()
    preset = LLM_PRESETS.get(cfg_in.provider, {})

    file_cfg["provider"] = cfg_in.provider
    if cfg_in.provider == "none":
        file_cfg["api_base"] = None
        file_cfg["model"] = "gpt-3.5-turbo"
    else:
        file_cfg["api_base"] = cfg_in.api_base if cfg_in.api_base else preset.get("api_base")
        file_cfg["model"] = cfg_in.model if cfg_in.model else preset.get("model", "gpt-3.5-turbo")
    if cfg_in.api_key is not None and cfg_in.api_key != "":
        file_cfg["api_key"] = cfg_in.api_key

    save_llm_config(file_cfg)
    return {"ok": True, "message": "LLM 配置已保存"}
