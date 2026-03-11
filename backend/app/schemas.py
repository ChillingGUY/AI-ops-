from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServerUpsert(BaseModel):
    """服务器信息（上报时使用）"""

    model_config = ConfigDict(title="服务器信息", description="Agent 上报时携带的服务器元数据")
    hostname: str = Field(description="主机名")
    os: str | None = Field(None, description="操作系统")
    tags: dict = Field(default_factory=dict, description="标签")


class ServerOut(BaseModel):
    """服务器输出"""

    model_config = ConfigDict(title="服务器", description="已注册的服务器资产")
    id: int = Field(description="服务器 ID")
    hostname: str = Field(description="主机名")
    os: str | None = Field(None, description="操作系统")
    tags: dict = Field(description="标签")
    last_seen_at: datetime | None = Field(None, description="最后上线时间")


class MetricPointIn(BaseModel):
    """单条指标数据"""

    model_config = ConfigDict(title="指标点", description="单条监控指标")
    ts: datetime = Field(description="时间戳")
    name: str = Field(description="指标名称，如 cpu_usage、mem_usage、disk_usage")
    value: float = Field(description="指标值")
    labels: dict = Field(default_factory=dict, description="标签")


class MetricsIngestIn(BaseModel):
    """指标上报请求体"""

    model_config = ConfigDict(title="指标上报", description="Agent 上报一批监控指标")
    server: ServerUpsert = Field(description="服务器信息")
    points: list[MetricPointIn] = Field(description="指标点列表")


class LogEventIn(BaseModel):
    """单条日志事件"""

    model_config = ConfigDict(title="日志事件", description="单条结构化日志")
    ts: datetime = Field(description="时间戳")
    level: str = Field("INFO", description="日志级别：INFO/WARN/ERROR")
    message: str = Field(description="日志内容")
    source: str = Field("agent", description="来源")
    fields: dict = Field(default_factory=dict, description="附加字段")


class LogsIngestIn(BaseModel):
    """日志上报请求体"""

    model_config = ConfigDict(title="日志上报", description="Agent 上报一批日志")
    server: ServerUpsert = Field(description="服务器信息")
    events: list[LogEventIn] = Field(description="日志事件列表")


class AlertRuleIn(BaseModel):
    """告警规则（新建）"""

    model_config = ConfigDict(title="告警规则", description="指标阈值告警规则")
    name: str = Field(description="规则名称")
    enabled: bool = Field(True, description="是否启用")
    metric_name: str = Field(description="指标名称")
    comparator: str = Field(">", description="比较符：>、>=、<、<=、==")
    threshold: float = Field(description="阈值")
    for_seconds: int = Field(60, description="持续秒数")
    severity: str = Field("warning", description="严重程度：warning、critical")
    labels: dict = Field(default_factory=dict, description="标签")


class AlertRuleOut(AlertRuleIn):
    """告警规则（含 ID）"""

    model_config = ConfigDict(title="告警规则（含ID）", description="创建后的告警规则")
    id: int = Field(description="规则 ID")


class AlertEventOut(BaseModel):
    """告警事件"""

    model_config = ConfigDict(title="告警事件", description="已触发的告警事件")
    id: int = Field(description="事件 ID")
    rule_id: int = Field(description="规则 ID")
    server_id: int = Field(description="服务器 ID")
    ts: datetime = Field(description="发生时间")
    status: str = Field(description="状态：firing/resolved")
    severity: str = Field(description="严重程度")
    summary: str = Field(description="摘要")
    details: str | None = Field(None, description="详情")
    context: dict = Field(description="上下文")


class RepairActionOut(BaseModel):
    """处置记录"""

    model_config = ConfigDict(title="处置记录", description="自动化处置动作")
    id: int = Field(description="记录 ID")
    alert_event_id: int = Field(description="告警事件 ID")
    ts: datetime = Field(description="执行时间")
    action_type: str = Field(description="动作类型")
    target: str = Field(description="目标")
    status: str = Field(description="状态：queued/running/succeeded/failed")
    output: str | None = Field(None, description="执行输出")


class AlertCategoryOut(BaseModel):
    """告警分类结果"""

    model_config = ConfigDict(title="告警分类", description="AI 分类结果")
    category: str = Field(description="分类：disk/cpu/memory/network/app_error/unknown")
    label: str = Field(description="中文标签")
    confidence: float = Field(description="置信度 0~1")

