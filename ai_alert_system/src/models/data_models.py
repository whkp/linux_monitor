"""
数据模型定义
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import json

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class MetricType(Enum):
    """指标类型"""
    CPU_USAGE = "cpu_usage"
    CPU_LOAD = "cpu_load"
    MEMORY_USAGE = "memory_usage"
    NETWORK_TRAFFIC = "network_traffic"
    DISK_IO = "disk_io"
    PROCESS_COUNT = "process_count"

@dataclass
class MonitoringData:
    """监控数据模型"""
    timestamp: datetime
    hostname: str
    cpu_usage: float
    cpu_load_1min: float
    cpu_load_5min: float
    cpu_load_15min: float
    memory_total: int
    memory_used: int
    memory_available: int
    network_interfaces: Dict[str, Dict[str, int]]
    processes: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "hostname": self.hostname,
            "cpu_usage": self.cpu_usage,
            "cpu_load_1min": self.cpu_load_1min,
            "cpu_load_5min": self.cpu_load_5min,
            "cpu_load_15min": self.cpu_load_15min,
            "memory_total": self.memory_total,
            "memory_used": self.memory_used,
            "memory_available": self.memory_available,
            "memory_usage_percent": (self.memory_used / self.memory_total) * 100,
            "network_interfaces": self.network_interfaces,
            "processes": self.processes
        }

@dataclass
class Alert:
    """告警模型"""
    id: str
    timestamp: datetime
    level: AlertLevel
    metric_type: MetricType
    title: str
    description: str
    current_value: float
    threshold_value: float
    hostname: str
    suggested_actions: List[str]
    context: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "metric_type": self.metric_type.value,
            "title": self.title,
            "description": self.description,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "hostname": self.hostname,
            "suggested_actions": self.suggested_actions,
            "context": self.context,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }

@dataclass
class SystemContext:
    """系统上下文信息"""
    hostname: str
    os_version: str
    kernel_version: str
    cpu_cores: int
    total_memory: int
    architecture: str
    uptime: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "hostname": self.hostname,
            "os_version": self.os_version,
            "kernel_version": self.kernel_version,
            "cpu_cores": self.cpu_cores,
            "total_memory": self.total_memory,
            "architecture": self.architecture,
            "uptime": self.uptime
        }

@dataclass
class AnalysisResult:
    """分析结果模型"""
    timestamp: datetime
    hostname: str
    anomalies_detected: List[str]
    performance_issues: List[str]
    recommendations: List[str]
    confidence_score: float
    analysis_details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "hostname": self.hostname,
            "anomalies_detected": self.anomalies_detected,
            "performance_issues": self.performance_issues,
            "recommendations": self.recommendations,
            "confidence_score": self.confidence_score,
            "analysis_details": self.analysis_details
        }
