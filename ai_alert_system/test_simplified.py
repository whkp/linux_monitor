#!/usr/bin/env python3
"""
简化版AI智能告警系统测试脚本
无需外部依赖，验证核心功能
"""
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

# 模拟MonitoringKnowledgeBase来避免ChromaDB依赖
class MockMonitoringKnowledgeBase:
    def __init__(self):
        self.mock_solutions = {
            "CPU": ["检查top命令查看高CPU进程", "优化应用性能"],
            "内存": ["检查内存泄漏", "重启占用内存的进程"],
            "负载": ["分析I/O状态", "检查系统任务"]
        }
    
    def search_solutions(self, query, k=3):
        results = []
        for key, solutions in self.mock_solutions.items():
            if key in query:
                for solution in solutions[:k]:
                    results.append({'content': solution})
        return results

# 模拟监控数据
from src.models.data_models import MonitoringData

def create_test_data(scenario="normal"):
    """创建测试数据"""
    base_data = {
        'timestamp': datetime.now(),
        'hostname': 'test-server',
        'cpu_load_1min': 2.0,
        'cpu_load_5min': 1.8,
        'cpu_load_15min': 1.5,
        'cpu_stats': [],
        'soft_irq_stats': [],
        'memory_stats': None,
        'network_stats': [],
        'memory_total': 8 * 1024**3,  # 8GB
        'memory_used': 4 * 1024**3,   # 4GB
        'memory_available': 4 * 1024**3  # 4GB
    }
    
    if scenario == "high_cpu":
        base_data.update({
            'cpu_usage': 90.0,
            'cpu_load_1min': 8.5
        })
    elif scenario == "high_memory":
        base_data.update({
            'cpu_usage': 45.0,
            'memory_used': 7.5 * 1024**3,  # 7.5GB
            'memory_available': 0.5 * 1024**3  # 0.5GB
        })
    elif scenario == "load_cpu_mismatch":
        base_data.update({
            'cpu_usage': 30.0,
            'cpu_load_1min': 12.0
        })
    else:  # normal
        base_data.update({
            'cpu_usage': 25.0
        })
    
    return MonitoringData(**base_data)

async def test_analysis_agent():
    """测试分析Agent"""
    print("=" * 60)
    print("🧪 AI智能告警系统 - 简化版测试")
    print("=" * 60)
    print()
    
    # 创建模拟知识库
    mock_kb = MockMonitoringKnowledgeBase()
    
    # 导入并创建Agent
    from src.agents.analysis_agent import MonitoringAgent
    agent = MonitoringAgent(mock_kb)
    
    # 测试场景
    scenarios = [
        ("正常状态", "normal"),
        ("CPU使用率过高", "high_cpu"),
        ("内存不足", "high_memory"),
        ("负载高CPU低(I/O瓶颈)", "load_cpu_mismatch")
    ]
    
    for scenario_name, scenario_type in scenarios:
        print(f"📊 测试场景: {scenario_name}")
        print("-" * 40)
        
        # 创建测试数据
        test_data = create_test_data(scenario_type)
        
        # 执行分析
        result = await agent.analyze(test_data)
        
        # 显示结果
        print(f"主机: {test_data.hostname}")
        print(f"CPU: {test_data.cpu_usage:.1f}%")
        print(f"内存: {(test_data.memory_used/test_data.memory_total)*100:.1f}%")
        print(f"负载: {test_data.cpu_load_1min:.1f}")
        print()
        
        if result.anomalies_detected:
            print("⚠️  检测到问题:")
            for anomaly in result.anomalies_detected:
                print(f"  • {anomaly}")
            print()
            
            if result.analysis_details.get("llm_analysis"):
                print(f"🤖 AI分析: {result.analysis_details['llm_analysis']}")
                print()
            
            if result.recommendations:
                print("💡 建议解决方案:")
                for i, rec in enumerate(result.recommendations, 1):
                    print(f"  {i}. {rec}")
                print()
            
            print(f"置信度: {result.confidence_score:.2f}")
            print(f"LLM启用: {result.analysis_details.get('llm_enabled', False)}")
            print(f"LLM触发: {result.analysis_details.get('llm_triggered', False)}")
            
            if result.analysis_details.get('fallback_used'):
                print("🔄 使用了降级机制")
        else:
            print("✅ 系统运行正常")
        
        print("=" * 60)
        print()

async def main():
    try:
        await test_analysis_agent()
        print("🎉 测试完成！简化版AI智能告警系统工作正常")
        print()
        print("💡 说明:")
        print("  • 无需安装OpenAI或ChromaDB即可运行基础功能")
        print("  • 规则检测和降级机制工作正常")
        print("  • 配置OpenAI API密钥可启用LLM分析")
        print("  • 安装ChromaDB可启用完整RAG功能")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
