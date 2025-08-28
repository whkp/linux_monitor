"""
主应用程序
简化版AI智能告警系统，专注于核心功能
"""
import asyncio
import logging
import signal
import sys
from typing import Optional
from datetime import datetime

from src.config import settings
from src.models.data_models import MonitoringData
from src.data_collector.grpc_client import MonitorDataCollector
from src.knowledge_base.rag_system import MonitoringKnowledgeBase
from src.agents.analysis_agent import MonitoringAgent
from src.alert_engine.alert_manager import AlertManager

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/system.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class SimpleAIAlertSystem:
    """简化版AI智能告警系统"""
    
    def __init__(self):
        self.data_collector: Optional[MonitorDataCollector] = None
        self.knowledge_base: Optional[MonitoringKnowledgeBase] = None
        self.analysis_agent: Optional[MonitoringAgent] = None
        self.alert_manager: Optional[AlertManager] = None
        self.running = False
    
    async def initialize(self):
        """初始化系统组件"""
        logger.info("正在初始化AI智能告警系统...")
        
        try:
            # 创建日志目录
            import os
            os.makedirs('logs', exist_ok=True)
            os.makedirs('data', exist_ok=True)
            
            # 初始化知识库
            logger.info("初始化知识库...")
            self.knowledge_base = MonitoringKnowledgeBase()
            self.knowledge_base.initialize()
            
            # 初始化分析Agent
            logger.info("初始化分析Agent...")
            self.analysis_agent = MonitoringAgent(self.knowledge_base)
            
            # 初始化告警管理器
            logger.info("初始化告警管理器...")
            self.alert_manager = AlertManager()
            
            # 初始化数据收集器
            logger.info("初始化数据收集器...")
            self.data_collector = MonitorDataCollector()
            connected = await self.data_collector.connect()
            
            if not connected:
                logger.warning("无法连接到监控系统，将使用模拟数据进行演示")
            
            logger.info("AI智能告警系统初始化完成")
            
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            raise
    
    async def start(self):
        """启动系统"""
        if not all([self.data_collector, self.knowledge_base, self.analysis_agent, self.alert_manager]):
            raise RuntimeError("系统未正确初始化")
        
        logger.info("启动AI智能告警系统...")
        self.running = True
        
        try:
            # 启动数据处理循环
            await self._data_processing_loop()
            
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭系统...")
        except Exception as e:
            logger.error(f"系统运行错误: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def _data_processing_loop(self):
        """数据处理主循环"""
        logger.info("开始数据处理循环...")
        
        async for monitoring_data in self.data_collector.stream_monitoring_data():
            if not self.running:
                break
            
            try:
                # 记录接收到的数据
                logger.debug(f"收到来自 {monitoring_data.hostname} 的监控数据")
                
                # AI分析
                analysis_result = await self.analysis_agent.analyze(monitoring_data)
                
                # 打印分析结果到控制台
                await self._print_analysis_result(monitoring_data, analysis_result)
                
                # 处理告警
                await self._handle_alerts(monitoring_data, analysis_result)
                
            except Exception as e:
                logger.error(f"处理监控数据时出错: {e}")
                # 继续处理下一个数据，不中断系统
                continue
    
    async def _print_analysis_result(self, monitoring_data, analysis_result):
        """打印分析结果到控制台"""
        print(f"\n{'='*60}")
        print(f"主机: {monitoring_data.hostname}")
        print(f"时间: {monitoring_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"CPU使用率: {monitoring_data.cpu_usage:.1f}%")
        print(f"内存使用率: {(monitoring_data.memory_used/monitoring_data.memory_total)*100:.1f}%")
        print(f"系统负载: {monitoring_data.cpu_load_1min}")
        
        if analysis_result.anomalies_detected:
            print(f"\n🚨 检测到异常:")
            for anomaly in analysis_result.anomalies_detected:
                print(f"  • {anomaly}")
        
        if analysis_result.recommendations:
            print(f"\n💡 建议解决方案:")
            for i, rec in enumerate(analysis_result.recommendations[:3], 1):
                print(f"  {i}. {rec}")
        
        print(f"\n置信度评分: {analysis_result.confidence_score:.2f}")
        print(f"{'='*60}")
    
    async def _handle_alerts(self, monitoring_data, analysis_result):
        """处理告警"""
        # 根据异常生成告警
        if analysis_result.anomalies_detected:
            from src.models.data_models import Alert, AlertLevel, MetricType
            
            for anomaly in analysis_result.anomalies_detected:
                # 确定告警级别
                if "Critical" in anomaly or "Extremely" in anomaly:
                    level = AlertLevel.CRITICAL
                elif "High" in anomaly:
                    level = AlertLevel.WARNING
                else:
                    level = AlertLevel.INFO
                
                # 确定指标类型
                if "CPU" in anomaly:
                    metric_type = MetricType.CPU_USAGE
                    current_value = monitoring_data.cpu_usage
                    threshold = settings.cpu_threshold_warning
                elif "memory" in anomaly:
                    metric_type = MetricType.MEMORY_USAGE
                    current_value = (monitoring_data.memory_used / monitoring_data.memory_total) * 100
                    threshold = settings.memory_threshold_warning
                elif "load" in anomaly:
                    metric_type = MetricType.CPU_LOAD
                    current_value = monitoring_data.cpu_load_1min
                    threshold = settings.load_threshold_warning
                else:
                    metric_type = MetricType.CPU_USAGE
                    current_value = 0
                    threshold = 0
                
                alert = Alert(
                    id=f"{monitoring_data.hostname}_{metric_type.value}_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    level=level,
                    metric_type=metric_type,
                    title=f"{monitoring_data.hostname}: {anomaly}",
                    description=f"在 {monitoring_data.hostname} 上检测到: {anomaly}",
                    current_value=current_value,
                    threshold_value=threshold,
                    hostname=monitoring_data.hostname,
                    suggested_actions=analysis_result.recommendations[:3],
                    context={"analysis": analysis_result.to_dict()}
                )
                
                await self.alert_manager.process_alert(alert)
    
    async def shutdown(self):
        """关闭系统"""
        logger.info("正在关闭AI智能告警系统...")
        self.running = False
        
        if self.data_collector:
            self.data_collector.stop_streaming()
            await self.data_collector.disconnect()
        
        logger.info("AI智能告警系统已关闭")

async def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║              AI智能告警系统                      ║
    ║         基于LLM Agent + RAG技术                  ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    system = SimpleAIAlertSystem()
    
    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}")
        system.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 初始化并启动系统
        await system.initialize()
        await system.start()
        
    except Exception as e:
        logger.error(f"系统运行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 运行主程序
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("用户中断应用程序")
    except Exception as e:
        logger.error(f"应用程序失败: {e}")
        sys.exit(1)
