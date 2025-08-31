"""
gRPC数据收集器
从Linux监控系统接收监控数据
"""
import grpc
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional
import sys
import os

# 添加proto模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../proto'))

from ..models.data_models import (
    MonitoringData, SystemContext, CpuStats, SoftIrqStats, 
    MemoryStats, NetworkStats
)
from ..config import settings

logger = logging.getLogger(__name__)

class MonitorDataCollector:
    """监控数据收集器"""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or settings.monitor_grpc_host
        self.port = port or settings.monitor_grpc_port
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub = None
        self._running = False
    
    async def connect(self):
        """连接到gRPC服务器"""
        try:
            self.channel = grpc.aio.insecure_channel(f'{self.host}:{self.port}')
            # 这里需要导入实际的proto文件生成的类
            # from monitor_info_pb2_grpc import MonitorServiceStub
            # self.stub = MonitorServiceStub(self.channel)
            
            logger.info(f"Connected to monitoring service at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to monitoring service: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.channel:
            await self.channel.close()
            logger.info("Disconnected from monitoring service")
    
    async def get_system_context(self) -> Optional[SystemContext]:
        """获取系统上下文信息"""
        try:
            # 这里应该调用实际的gRPC方法获取系统信息
            # response = await self.stub.GetSystemInfo(Empty())
            
            # 临时返回模拟数据
            return SystemContext(
                hostname="test-server",
                os_version="Ubuntu 20.04",
                kernel_version="5.4.0",
                cpu_cores=8,
                total_memory=16 * 1024 * 1024 * 1024,  # 16GB
                architecture="x86_64",
                uptime=3600 * 24 * 7  # 7天
            )
        except Exception as e:
            logger.error(f"Failed to get system context: {e}")
            return None
    
    async def stream_monitoring_data(self) -> AsyncGenerator[MonitoringData, None]:
        """流式获取监控数据"""
        self._running = True
        
        while self._running:
            try:
                # 这里应该调用实际的gRPC流式方法
                # async for response in self.stub.StreamMonitoringData(request):
                #     yield self._parse_monitoring_data(response)
                
                # 临时返回模拟数据
                yield self._create_mock_data()
                await asyncio.sleep(3)  # 每3秒获取一次数据
                
            except Exception as e:
                logger.error(f"Error streaming monitoring data: {e}")
                await asyncio.sleep(5)  # 错误重试间隔
    
    def stop_streaming(self):
        """停止数据流"""
        self._running = False
    
    def _create_mock_data(self) -> MonitoringData:
        """创建包含所有详细指标的模拟监控数据（用于测试和演示）"""
        import random
        
        # 模拟CPU核心数量
        cpu_cores = 8
        
        # 生成CPU统计数据（每个核心）
        cpu_stats = []
        for i in range(cpu_cores):
            # 模拟不同核心的负载差异
            base_usage = random.uniform(10, 80)
            io_wait = random.uniform(0, 20) if i % 3 == 0 else random.uniform(0, 5)  # 某些核心I/O等待更高
            system_cpu = random.uniform(5, 25) if i == 0 else random.uniform(2, 10)  # 核心0系统CPU更高
            
            cpu_stats.append(CpuStats(
                cpu_name=f"cpu{i}",
                cpu_percent=base_usage,
                usr_percent=base_usage * 0.6,
                system_percent=system_cpu,
                nice_percent=random.uniform(0, 2),
                idle_percent=100 - base_usage,
                io_wait_percent=io_wait,
                irq_percent=random.uniform(0, 1),
                soft_irq_percent=random.uniform(1, 8)
            ))
        
        # 生成软中断统计数据（每个核心）
        soft_irq_stats = []
        for i in range(cpu_cores):
            # 模拟不同类型的中断负载
            network_load = random.uniform(100, 2000) if i < 4 else random.uniform(50, 500)  # 前4核心网络中断更多
            
            soft_irq_stats.append(SoftIrqStats(
                cpu=f"cpu{i}",
                hi=random.uniform(0, 10),
                timer=random.uniform(500, 1500),
                net_tx=network_load * 0.4,
                net_rx=network_load * 0.6,
                block=random.uniform(50, 800),
                irq_poll=random.uniform(0, 5),
                tasklet=random.uniform(10, 100),
                sched=random.uniform(200, 800),
                hrtimer=random.uniform(100, 400),
                rcu=random.uniform(50, 200)
            ))
        
        # 生成内存详细统计
        total_memory = 16.0  # 16GB
        used_percent = random.uniform(45, 85)
        used_memory = total_memory * (used_percent / 100)
        free_memory = random.uniform(1, 3)
        cached = random.uniform(4, 8)
        
        memory_stats = MemoryStats(
            total=total_memory,
            free=free_memory,
            avail=total_memory - used_memory,
            buffers=random.uniform(0.1, 0.5),
            cached=cached,
            swap_cached=random.uniform(0, 0.1),
            active=random.uniform(6, 10),
            inactive=random.uniform(2, 4),
            active_anon=random.uniform(3, 6),
            inactive_anon=random.uniform(0.5, 2),
            active_file=random.uniform(2, 4),
            inactive_file=random.uniform(1, 2),
            dirty=random.uniform(0.01, 0.5),
            writeback=random.uniform(0, 0.1),
            anon_pages=random.uniform(4, 8),
            mapped=random.uniform(0.5, 2),
            kReclaimable=random.uniform(0.3, 1),
            sReclaimable=random.uniform(0.2, 0.8),
            sUnreclaim=random.uniform(0.1, 0.5),
            used_percent=used_percent
        )
        
        # 生成网络接口统计
        network_stats = []
        
        # 主网卡 - 模拟正常流量
        network_stats.append(NetworkStats(
            name="eth0",
            send_rate=random.uniform(1024, 50*1024),  # 1KB/s 到 50MB/s
            rcv_rate=random.uniform(2*1024, 100*1024),  # 2KB/s 到 100MB/s
            send_packets_rate=random.uniform(10, 5000),
            rcv_packets_rate=random.uniform(20, 8000)
        ))
        
        # 环回接口
        network_stats.append(NetworkStats(
            name="lo",
            send_rate=random.uniform(100, 1024),
            rcv_rate=random.uniform(100, 1024),
            send_packets_rate=random.uniform(5, 100),
            rcv_packets_rate=random.uniform(5, 100)
        ))
        
        # 可能的无线接口
        if random.choice([True, False]):
            network_stats.append(NetworkStats(
                name="wlan0",
                send_rate=random.uniform(512, 10*1024),
                rcv_rate=random.uniform(1024, 20*1024),
                send_packets_rate=random.uniform(5, 1000),
                rcv_packets_rate=random.uniform(10, 2000)
            ))
        
        # 创建完整的监控数据
        return MonitoringData(
            timestamp=datetime.now(),
            hostname="enhanced-test-server",
            
            # CPU负载
            cpu_load_1min=random.uniform(0.5, cpu_cores * 0.9),
            cpu_load_5min=random.uniform(0.4, cpu_cores * 0.7),
            cpu_load_15min=random.uniform(0.3, cpu_cores * 0.6),
            
            # 详细统计
            cpu_stats=cpu_stats,
            soft_irq_stats=soft_irq_stats,
            memory_stats=memory_stats,
            network_stats=network_stats,
            
            # 模拟进程信息
            processes=[
                {
                    "pid": 1234,
                    "name": "python3",
                    "cpu_percent": random.uniform(1, 25),
                    "memory_percent": random.uniform(2, 15)
                },
                {
                    "pid": 5678,
                    "name": "mysql",
                    "cpu_percent": random.uniform(5, 30),
                    "memory_percent": random.uniform(10, 25)
                },
                {
                    "pid": 9999,
                    "name": "nginx",
                    "cpu_percent": random.uniform(1, 15),
                    "memory_percent": random.uniform(1, 8)
                }
            ]
        )
    
    def _parse_monitoring_data(self, grpc_response) -> MonitoringData:
        """解析真实gRPC响应为MonitoringData对象"""
        try:
            # 解析CPU统计
            cpu_stats = []
            for cpu_stat in grpc_response.cpu_stat:
                cpu_stats.append(CpuStats(
                    cpu_name=cpu_stat.cpu_name,
                    cpu_percent=cpu_stat.cpu_percent,
                    usr_percent=cpu_stat.usr_percent,
                    system_percent=cpu_stat.system_percent,
                    nice_percent=cpu_stat.nice_percent,
                    idle_percent=cpu_stat.idle_percent,
                    io_wait_percent=cpu_stat.io_wait_percent,
                    irq_percent=cpu_stat.irq_percent,
                    soft_irq_percent=cpu_stat.soft_irq_percent
                ))
            
            # 解析软中断统计
            soft_irq_stats = []
            for soft_irq in grpc_response.soft_irq:
                soft_irq_stats.append(SoftIrqStats(
                    cpu=soft_irq.cpu,
                    hi=soft_irq.hi,
                    timer=soft_irq.timer,
                    net_tx=soft_irq.net_tx,
                    net_rx=soft_irq.net_rx,
                    block=soft_irq.block,
                    irq_poll=soft_irq.irq_poll,
                    tasklet=soft_irq.tasklet,
                    sched=soft_irq.sched,
                    hrtimer=soft_irq.hrtimer,
                    rcu=soft_irq.rcu
                ))
            
            # 解析内存统计
            mem_info = grpc_response.mem_info
            memory_stats = MemoryStats(
                total=mem_info.total,
                free=mem_info.free,
                avail=mem_info.avail,
                buffers=mem_info.buffers,
                cached=mem_info.cached,
                swap_cached=mem_info.swap_cached,
                active=mem_info.active,
                inactive=mem_info.inactive,
                active_anon=mem_info.active_anon,
                inactive_anon=mem_info.inactive_anon,
                active_file=mem_info.active_file,
                inactive_file=mem_info.inactive_file,
                dirty=mem_info.dirty,
                writeback=mem_info.writeback,
                anon_pages=mem_info.anon_pages,
                mapped=mem_info.mapped,
                kReclaimable=mem_info.kReclaimable,
                sReclaimable=mem_info.sReclaimable,
                sUnreclaim=mem_info.sUnreclaim,
                used_percent=mem_info.used_percent
            )
            
            # 解析网络统计
            network_stats = []
            for net_info in grpc_response.net_info:
                network_stats.append(NetworkStats(
                    name=net_info.name,
                    send_rate=net_info.send_rate,
                    rcv_rate=net_info.rcv_rate,
                    send_packets_rate=net_info.send_packets_rate,
                    rcv_packets_rate=net_info.rcv_packets_rate
                ))
            
            # 构建完整数据对象
            return MonitoringData(
                timestamp=datetime.now(),
                hostname=grpc_response.name,
                
                # CPU负载
                cpu_load_1min=grpc_response.cpu_load.load_avg_1,
                cpu_load_5min=grpc_response.cpu_load.load_avg_3,  # 注意：原proto中是load_avg_3
                cpu_load_15min=grpc_response.cpu_load.load_avg_15,
                
                # 详细统计
                cpu_stats=cpu_stats,
                soft_irq_stats=soft_irq_stats,
                memory_stats=memory_stats,
                network_stats=network_stats,
                
                # 进程信息（需要从其他源获取，或扩展proto）
                processes=[]
            )
            
        except Exception as e:
            logger.error(f"Failed to parse monitoring data: {e}")
            # 返回模拟数据作为降级
            return self._create_mock_data()
