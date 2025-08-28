"""
测试脚本
用于测试AI智能告警系统的各个组件
"""
import asyncio
import logging
from datetime import datetime
import json

from src.models.data_models import MonitoringData, AlertLevel, MetricType
from src.knowledge_base.rag_system import MonitoringKnowledgeBase
from src.agents.analysis_agent import MonitoringAgent
from src.alert_engine.alert_manager import AlertManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_monitoring_data():
    """创建测试监控数据"""
    return MonitoringData(
        timestamp=datetime.now(),
        hostname="test-server-01",
        cpu_usage=95.5,  # 高CPU使用率
        cpu_load_1min=8.2,  # 高负载
        cpu_load_5min=7.8,
        cpu_load_15min=6.5,
        memory_total=16 * 1024 * 1024 * 1024,  # 16GB
        memory_used=15 * 1024 * 1024 * 1024,   # 15GB (93.75%)
        memory_available=1 * 1024 * 1024 * 1024,  # 1GB
        network_interfaces={
            "eth0": {
                "rx_bytes": 1024 * 1024 * 100,  # 100MB
                "tx_bytes": 1024 * 1024 * 50,   # 50MB
                "rx_packets": 10000,
                "tx_packets": 5000
            }
        },
        processes=[
            {
                "pid": 1234,
                "name": "python3",
                "cpu_percent": 45.2,
                "memory_percent": 25.8
            },
            {
                "pid": 5678,
                "name": "mysql",
                "cpu_percent": 30.1,
                "memory_percent": 35.5
            }
        ]
    )

async def test_knowledge_base():
    """测试知识库功能"""
    logger.info("Testing Knowledge Base...")
    
    try:
        kb = MonitoringKnowledgeBase()
        kb.initialize()
        
        # 测试搜索
        results = kb.search_solutions("CPU使用率高", k=3)
        logger.info(f"Found {len(results)} solutions for high CPU usage")
        
        for i, result in enumerate(results):
            logger.info(f"Solution {i+1}: {result['content'][:100]}...")
        
        # 测试添加知识
        kb.add_knowledge(
            "测试知识：当MySQL进程占用过多CPU时，可以优化查询语句和索引",
            {"category": "mysql", "issue": "high_cpu", "test": True}
        )
        logger.info("Knowledge base test completed successfully")
        
    except Exception as e:
        logger.error(f"Knowledge base test failed: {e}")

async def test_analysis_agent():
    """测试分析Agent"""
    logger.info("Testing Analysis Agent...")
    
    try:
        # 初始化组件
        kb = MonitoringKnowledgeBase()
        kb.initialize()
        
        agent = MonitoringAgent(kb)
        
        # 创建测试数据
        test_data = create_test_monitoring_data()
        
        # 执行分析
        result = await agent.analyze(test_data)
        
        logger.info("Analysis Result:")
        logger.info(f"  Anomalies: {len(result.anomalies_detected)}")
        for anomaly in result.anomalies_detected:
            logger.info(f"    - {anomaly}")
        
        logger.info(f"  Performance Issues: {len(result.performance_issues)}")
        for issue in result.performance_issues:
            logger.info(f"    - {issue}")
        
        logger.info(f"  Recommendations: {len(result.recommendations)}")
        for rec in result.recommendations[:3]:  # 只显示前3个
            logger.info(f"    - {rec}")
        
        logger.info(f"  Confidence Score: {result.confidence_score:.2f}")
        
        logger.info("Analysis agent test completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis agent test failed: {e}")

async def test_alert_manager():
    """测试告警管理器"""
    logger.info("Testing Alert Manager...")
    
    try:
        manager = AlertManager()
        
        # 创建测试告警
        from src.models.data_models import Alert
        test_alert = Alert(
            id="test_alert_001",
            timestamp=datetime.now(),
            level=AlertLevel.WARNING,
            metric_type=MetricType.CPU_USAGE,
            title="Test High CPU Alert",
            description="测试高CPU使用率告警",
            current_value=95.5,
            threshold_value=80.0,
            hostname="test-server-01",
            suggested_actions=[
                "检查CPU密集型进程",
                "优化应用程序性能",
                "考虑扩容或升级硬件"
            ],
            context={"test": True}
        )
        
        # 处理告警
        await manager.process_alert(test_alert)
        
        # 获取活跃告警
        active_alerts = manager.get_active_alerts()
        logger.info(f"Active alerts: {len(active_alerts)}")
        
        # 获取统计信息
        stats = manager.get_alert_statistics()
        logger.info(f"Alert statistics: {json.dumps(stats, indent=2)}")
        
        # 解决告警
        manager.resolve_alert(test_alert.id)
        
        logger.info("Alert manager test completed successfully")
        
    except Exception as e:
        logger.error(f"Alert manager test failed: {e}")

async def test_full_system():
    """测试完整系统流程"""
    logger.info("Testing Full System Integration...")
    
    try:
        # 初始化所有组件
        kb = MonitoringKnowledgeBase()
        kb.initialize()
        
        agent = MonitoringAgent(kb)
        manager = AlertManager()
        
        # 创建测试数据
        test_data = create_test_monitoring_data()
        
        # 执行分析
        analysis_result = await agent.analyze(test_data)
        
        # 手动创建告警（因为当前分析器不直接生成告警对象）
        if analysis_result.anomalies_detected:
            from src.models.data_models import Alert
            alert = Alert(
                id=f"system_test_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                level=AlertLevel.CRITICAL,
                metric_type=MetricType.CPU_USAGE,
                title=f"System Integration Test: {analysis_result.anomalies_detected[0]}",
                description=f"检测到系统异常：{analysis_result.anomalies_detected[0]}",
                current_value=test_data.cpu_usage,
                threshold_value=80.0,
                hostname=test_data.hostname,
                suggested_actions=analysis_result.recommendations[:3],
                context=analysis_result.analysis_details
            )
            
            # 处理告警
            await manager.process_alert(alert)
        
        logger.info("Full system integration test completed successfully")
        
    except Exception as e:
        logger.error(f"Full system test failed: {e}")

async def main():
    """运行所有测试"""
    logger.info("Starting AI Alert System Tests...")
    
    # 运行各项测试
    await test_knowledge_base()
    print("-" * 50)
    
    await test_analysis_agent()
    print("-" * 50)
    
    await test_alert_manager()
    print("-" * 50)
    
    await test_full_system()
    print("-" * 50)
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
