"""LLM 接入：支持 OpenAI 兼容 API（千问/智谱/DeepSeek/OpenAI），用于告警诊断、优化建议、自动化评估。"""
from __future__ import annotations

import json
from typing import Any

import httpx

from app.llm_config import get_llm_effective_config


def _is_llm_configured() -> bool:
    cfg = get_llm_effective_config()
    return bool(cfg.get("provider") and cfg["provider"] != "none" and cfg.get("api_base"))


def _call_chat(messages: list[dict[str, str]]) -> str | None:
    """调用 OpenAI 兼容的 chat/completions 接口，返回回复内容。"""
    cfg = get_llm_effective_config()
    if not _is_llm_configured():
        return None
    api_base = cfg.get("api_base", "").rstrip("/")
    url = f"{api_base}/chat/completions"
    headers = {"Content-Type": "application/json"}
    api_key = cfg.get("api_key")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    model = cfg.get("model", "gpt-3.5-turbo")
    payload = {"model": model, "messages": messages, "temperature": 0.3}
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            return content
    except Exception:
        return None


def llm_alert_diagnosis(
    alert_summary: str,
    alert_details: str | None,
    metric_name: str | None,
    recent_logs: list[str],
) -> dict[str, Any] | None:
    """
    告警诊断：分析根因并给出解决建议。
    返回 {summary, probable_causes, suggestions, diagnosis} 或 None。
    """
    logs_text = "\n".join((recent_logs or [])[:20])[:1500]
    prompt = f"""你是一名资深运维工程师。请针对以下告警进行诊断分析。

## 告警信息
- 摘要：{alert_summary}
- 指标：{metric_name or "未知"}
- 详情：{alert_details or "无"}

## 近期日志（节选）
{logs_text or "无"}

## 输出要求（严格按以下 JSON 格式输出，不要其他内容）
{{
  "summary": "一句话诊断结论",
  "probable_causes": ["可能原因1", "可能原因2"],
  "suggestions": ["处置建议1", "处置建议2", "处置建议3"]
}}"""
    content = _call_chat([{"role": "user", "content": prompt}])
    if not content:
        return None
    try:
        # 尝试提取 JSON（模型可能包裹在 ```json 中）
        text = content.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {"summary": content[:500], "probable_causes": [], "suggestions": []}


def llm_server_optimization(
    hostname: str,
    metrics: dict[str, float],
    recent_alerts: list[str],
) -> dict[str, Any] | None:
    """
    服务器优化建议：基于指标与告警历史给出优化方案。
    返回 {summary, optimizations, risks} 或 None。
    """
    metrics_str = json.dumps(metrics, ensure_ascii=False)
    alerts_str = "\n".join((recent_alerts or [])[:10]) or "无"
    prompt = f"""你是一名资深运维架构师。请针对以下服务器资源使用情况给出优化建议。

## 服务器
{hostname}

## 当前指标（0-1 表示使用率）
{metrics_str}

## 近期告警
{alerts_str}

## 输出要求（严格按以下 JSON 格式输出，不要其他内容）
{{
  "summary": "一句话整体评估",
  "optimizations": ["优化建议1", "优化建议2"],
  "risks": ["潜在风险1"]
}}"""
    content = _call_chat([{"role": "user", "content": prompt}])
    if not content:
        return None
    try:
        text = content.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {"summary": content[:500], "optimizations": [], "risks": []}


def llm_automation_evaluation(
    alert_category: str,
    actions_taken: list[str],
    outcome: str,
    context: str,
) -> dict[str, Any] | None:
    """
    自动化运维评估：评估本次自动处置的效果与改进建议。
    返回 {score, evaluation, improvements} 或 None。
    """
    actions_str = "\n".join(actions_taken or ["无"])
    prompt = f"""你是一名运维自动化专家。请评估以下自动化处置的效果。

## 告警类型
{alert_category}

## 已执行动作
{actions_str}

## 处置结果
{outcome}

## 上下文
{context}

## 输出要求（严格按以下 JSON 格式输出，不要其他内容）
{{
  "score": 85,
  "evaluation": "评估说明（100字内）",
  "improvements": ["改进建议1", "改进建议2"]
}}
score 为 0-100 的整数。"""
    content = _call_chat([{"role": "user", "content": prompt}])
    if not content:
        return None
    try:
        text = content.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        data = json.loads(text)
        if "score" not in data:
            data["score"] = 70
        return data
    except json.JSONDecodeError:
        return {"score": 70, "evaluation": content[:300], "improvements": []}
