"""AI 异常分析：告警根因诊断与处置建议，可接入 LLM 增强。"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.llm_client import llm_alert_diagnosis, _is_llm_configured


@dataclass(frozen=True)
class AIAnalysis:
    anomaly: bool
    summary: str
    probable_causes: list[str]
    suggestions: list[str]
    source: str = "rule"  # rule | llm


def analyze_alert(
    alert_summary: str,
    alert_details: str | None,
    recent_logs: list[str],
    metric_name: str | None = None,
) -> AIAnalysis:
    """分析告警，优先使用 LLM，未配置时使用规则兜底。"""
    if _is_llm_configured():
        result = llm_alert_diagnosis(
            alert_summary, alert_details, metric_name, recent_logs
        )
        if result:
            return AIAnalysis(
                anomaly=True,
                summary=result.get("summary", "LLM 诊断完成"),
                probable_causes=result.get("probable_causes", []),
                suggestions=result.get("suggestions", []),
                source="llm",
            )
    return AIAnalysis(
        anomaly=True,
        summary="检测到异常事件，建议结合 LLM 做进一步根因分析。",
        probable_causes=[
            "资源饱和（CPU/内存/磁盘 IO）",
            "应用程序错误或部署变更",
            "外部依赖（DB/网络）延迟升高",
        ],
        suggestions=[
            "检查近期变更与部署记录",
            "查看同时间窗的 error 日志与流量峰值",
            "如为资源瓶颈，考虑水平扩展或调整限额",
        ],
        source="rule",
    )
