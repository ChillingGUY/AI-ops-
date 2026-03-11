"""AI 告警分类器：根据告警摘要和指标名称识别问题类型，用于分类处置。"""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class AlertCategory:
    """告警分类结果"""
    category: str       # disk | cpu | memory | network | app_error | unknown
    label: str          # 中文标签
    confidence: float   # 0~1


def classify_alert(summary: str, metric_name: str | None, details: str | None = None) -> AlertCategory:
    """
    根据告警摘要、指标名称判断问题类型。
    Demo 版：规则匹配；生产可接 LLM 做语义分类。
    """
    text = " ".join(filter(None, [summary or "", metric_name or "", details or ""])).lower()

    # 存储 / 磁盘
    if any(k in text for k in ["disk", "disk_usage", "磁盘", "storage", "存储", "空间", "volume"]):
        return AlertCategory("disk", "存储问题", 0.95)

    # CPU
    if any(k in text for k in ["cpu", "cpu_usage", "cpu过载", "cpu 过载"]):
        return AlertCategory("cpu", "CPU 过载", 0.95)

    # 内存
    if any(k in text for k in ["mem", "memory", "mem_usage", "内存", "oom"]):
        return AlertCategory("memory", "内存不足", 0.95)

    # 网络
    if any(k in text for k in ["network", "net", "io_", "网络", "latency", "timeout"]):
        return AlertCategory("network", "网络/IO 异常", 0.9)

    # 应用错误
    if any(k in text for k in ["error", "exception", "fail", "错误", "异常", "超时"]):
        return AlertCategory("app_error", "应用错误", 0.85)

    # 按指标名兜底
    if metric_name:
        mn = metric_name.lower()
        if "disk" in mn or "storage" in mn:
            return AlertCategory("disk", "存储问题", 0.9)
        if "cpu" in mn:
            return AlertCategory("cpu", "CPU 过载", 0.9)
        if "mem" in mn or "memory" in mn:
            return AlertCategory("memory", "内存不足", 0.9)

    return AlertCategory("unknown", "未知类型", 0.5)
