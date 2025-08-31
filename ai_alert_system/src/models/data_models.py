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
    """指标类型 - 增强版"""
    CPU_USAGE = "cpu_usage"
    CPU_LOAD = "cpu_load"
    CPU_IO_WAIT = "cpu_io_wait"
    CPU_SYSTEM = "cpu_system"
    CPU_SOFTIRQ = "cpu_softirq"
    MEMORY_USAGE = "memory_usage"
    MEMORY_CACHE = "memory_cache"
    MEMORY_BUFFER = "memory_buffer"
    MEMORY_SWAP = "memory_swap"
    NETWORK_TRAFFIC = "network_traffic"
    NETWORK_IO = "network_io"
    NETWORK_PACKETS = "network_packets"
    DISK_IO = "disk_io"
    SOFTIRQ_HI = "softirq_hi"
    SOFTIRQ_TIMER = "softirq_timer"
    SOFTIRQ_NET = "softirq_net"
    SOFTIRQ_BLOCK = "softirq_block"
    SOFTIRQ_SCHED = "softirq_sched"
    PROCESS_COUNT = "process_count"

@dataclass
class CpuStats:
    """CPU详细统计"""
    cpu_name: str
    cpu_percent: float
    usr_percent: float
    system_percent: float
    nice_percent: float
    idle_percent: float
    io_wait_percent: float
    irq_percent: float
    soft_irq_percent: float

@dataclass
class SoftIrqStats:
    """软中断统计"""
    cpu: str
    hi: float           # 高优先级中断
    timer: float        # 定时器中断
    net_tx: float       # 网络发送
    net_rx: float       # 网络接收
    block: float        # 块设备I/O
    irq_poll: float     # IRQ轮询
    tasklet: float      # 小任务
    sched: float        # 调度器
    hrtimer: float      # 高分辨率定时器
    rcu: float          # RCU (Read-Copy-Update)

@dataclass
class MemoryStats:
    """内存详细统计"""
    total: float
    free: float
    avail: float
    buffers: float
    cached: float
    swap_cached: float
    active: float
    inactive: float
    active_anon: float
    inactive_anon: float
    active_file: float
    inactive_file: float
    dirty: float
    writeback: float
    anon_pages: float
    mapped: float
    kReclaimable: float
    sReclaimable: float
    sUnreclaim: float
    used_percent: float

@dataclass
class NetworkStats:
    """网络接口统计"""
    name: str
    send_rate: float        # KB/s
    rcv_rate: float         # KB/s
    send_packets_rate: float
    rcv_packets_rate: float

@dataclass
class MonitoringData:
    """监控数据模型 - 增强版本支持所有指标"""
    timestamp: datetime
    hostname: str
    
    # CPU负载
    cpu_load_1min: float
    cpu_load_5min: float
    cpu_load_15min: float
    
    # CPU详细统计（每个核心）
    cpu_stats: List[CpuStats]
    
    # 软中断统计（每个核心）
    soft_irq_stats: List[SoftIrqStats]
    
    # 内存详细统计
    memory_stats: MemoryStats
    
    # 网络接口统计
    network_stats: List[NetworkStats]
    
    # 保留原有字段以兼容现有代码
    cpu_usage: float = 0.0  # 从cpu_stats计算得出
    memory_total: int = 0
    memory_used: int = 0
    memory_available: int = 0
    network_interfaces: Dict[str, Dict[str, int]] = None
    processes: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        """初始化后处理，计算兼容字段"""
        # 计算总体CPU使用率
        if self.cpu_stats:
            self.cpu_usage = sum(stat.cpu_percent for stat in self.cpu_stats) / len(self.cpu_stats)
        
        # 转换内存单位（假设原始数据是GB）
        if self.memory_stats:
            self.memory_total = int(self.memory_stats.total * 1024**3)  # 转换为字节
            self.memory_used = int((self.memory_stats.total - self.memory_stats.avail) * 1024**3)
            self.memory_available = int(self.memory_stats.avail * 1024**3)
        
        # 转换网络接口格式
        if self.network_stats and not self.network_interfaces:
            self.network_interfaces = {}
            for net in self.network_stats:
                self.network_interfaces[net.name] = {
                    'rx_bytes': int(net.rcv_rate * 1024),  # 转换为字节/秒
                    'tx_bytes': int(net.send_rate * 1024),
                    'rx_packets': int(net.rcv_packets_rate),
                    'tx_packets': int(net.send_packets_rate)
                }
        
        # 如果没有进程数据，创建空列表
        if self.processes is None:
            self.processes = []
    
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式 - 包含所有详细指标"""
        result = {
            "timestamp": self.timestamp.isoformat(),
            "hostname": self.hostname,
            
            # CPU负载信息
            "cpu_load_1min": self.cpu_load_1min,
            "cpu_load_5min": self.cpu_load_5min,
            "cpu_load_15min": self.cpu_load_15min,
            
            # CPU统计信息
            "cpu_stats": [
                {
                    "cpu_name": stat.cpu_name,
                    "cpu_percent": stat.cpu_percent,
                    "usr_percent": stat.usr_percent,
                    "system_percent": stat.system_percent,
                    "nice_percent": stat.nice_percent,
                    "idle_percent": stat.idle_percent,
                    "io_wait_percent": stat.io_wait_percent,
                    "irq_percent": stat.irq_percent,
                    "soft_irq_percent": stat.soft_irq_percent
                } for stat in self.cpu_stats
            ],
            
            # 软中断统计
            "soft_irq_stats": [
                {
                    "cpu": irq.cpu,
                    "hi": irq.hi,
                    "timer": irq.timer,
                    "net_tx": irq.net_tx,
                    "net_rx": irq.net_rx,
                    "block": irq.block,
                    "irq_poll": irq.irq_poll,
                    "tasklet": irq.tasklet,
                    "sched": irq.sched,
                    "hrtimer": irq.hrtimer,
                    "rcu": irq.rcu
                } for irq in self.soft_irq_stats
            ],
            
            # 内存详细统计
            "memory_stats": {
                "total": self.memory_stats.total,
                "free": self.memory_stats.free,
                "avail": self.memory_stats.avail,
                "buffers": self.memory_stats.buffers,
                "cached": self.memory_stats.cached,
                "swap_cached": self.memory_stats.swap_cached,
                "active": self.memory_stats.active,
                "inactive": self.memory_stats.inactive,
                "active_anon": self.memory_stats.active_anon,
                "inactive_anon": self.memory_stats.inactive_anon,
                "active_file": self.memory_stats.active_file,
                "inactive_file": self.memory_stats.inactive_file,
                "dirty": self.memory_stats.dirty,
                "writeback": self.memory_stats.writeback,
                "anon_pages": self.memory_stats.anon_pages,
                "mapped": self.memory_stats.mapped,
                "kReclaimable": self.memory_stats.kReclaimable,
                "sReclaimable": self.memory_stats.sReclaimable,
                "sUnreclaim": self.memory_stats.sUnreclaim,
                "used_percent": self.memory_stats.used_percent
            },
            
            # 网络统计
            "network_stats": [
                {
                    "name": net.name,
                    "send_rate": net.send_rate,
                    "rcv_rate": net.rcv_rate,
                    "send_packets_rate": net.send_packets_rate,
                    "rcv_packets_rate": net.rcv_packets_rate
                } for net in self.network_stats
            ],
            
            # 兼容字段
            "cpu_usage": self.cpu_usage,
            "memory_total": self.memory_total,
            "memory_used": self.memory_used,
            "memory_available": self.memory_available,
            "memory_usage_percent": (self.memory_used / self.memory_total) * 100 if self.memory_total > 0 else 0,
            "network_interfaces": self.network_interfaces,
            "processes": self.processes
        }
        
        return result

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
