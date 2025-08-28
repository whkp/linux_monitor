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

from ..models.data_models import MonitoringData, SystemContext
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
        """创建模拟监控数据（用于测试）"""
        import random
        
        return MonitoringData(
            timestamp=datetime.now(),
            hostname="test-server",
            cpu_usage=random.uniform(20, 90),
            cpu_load_1min=random.uniform(0.5, 4.0),
            cpu_load_5min=random.uniform(0.5, 3.5),
            cpu_load_15min=random.uniform(0.5, 3.0),
            memory_total=16 * 1024 * 1024 * 1024,
            memory_used=int(random.uniform(8, 14) * 1024 * 1024 * 1024),
            memory_available=int(random.uniform(2, 8) * 1024 * 1024 * 1024),
            network_interfaces={
                "eth0": {
                    "rx_bytes": random.randint(1000000, 10000000),
                    "tx_bytes": random.randint(500000, 5000000),
                    "rx_packets": random.randint(1000, 10000),
                    "tx_packets": random.randint(500, 5000)
                }
            },
            processes=[
                {
                    "pid": 1234,
                    "name": "python3",
                    "cpu_percent": random.uniform(1, 20),
                    "memory_percent": random.uniform(1, 10)
                }
            ]
        )
    
    def _parse_monitoring_data(self, response) -> MonitoringData:
        """解析gRPC响应为MonitoringData"""
        # 这里实现实际的gRPC响应解析逻辑
        pass
