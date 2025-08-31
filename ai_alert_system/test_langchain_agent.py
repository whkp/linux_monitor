#!/usr/bin/env python3
"""
测试基于LangChain的分析Agent
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.analysis_agent import LangChainMonitoringAgent
from src.knowledge_base.rag_system import MonitoringKnowledgeBase
from src.models.data_models import MonitoringData, CpuStats, SoftIrqStats, MemoryStats, NetworkStats
from datetime import datetime

def create_test_data(hostname, cpu_usage, memory_total_gb, memory_used_gb, cpu_load_1min):
    """创建测试数据"""
    # 创建基础CPU统计（假设4核心）
    cpu_stats = [
        CpuStats(
            cpu_name=f"cpu{i}",
            cpu_percent=cpu_usage + (i * 2),  # 略微变化
            usr_percent=cpu_usage * 0.7,
            system_percent=cpu_usage * 0.2,
            nice_percent=0.0,
            idle_percent=100 - cpu_usage,
            io_wait_percent=cpu_usage * 0.05,
            irq_percent=cpu_usage * 0.03,
            soft_irq_percent=cpu_usage * 0.02
        ) for i in range(4)
    ]
    
    # 创建软中断统计
    soft_irq_stats = [
        SoftIrqStats(
            cpu=f"cpu{i}",
            hi=0.1, timer=0.5, net_tx=0.2, net_rx=0.3,
            block=0.1, irq_poll=0.0, tasklet=0.1,
            sched=0.2, hrtimer=0.1, rcu=0.1
        ) for i in range(4)
    ]
    
    # 创建内存统计 (关键：avail决定了实际的memory_used计算)
    memory_avail = memory_total_gb - memory_used_gb  # 可用内存
    memory_stats = MemoryStats(
        total=memory_total_gb,
        free=memory_avail * 0.5,  # 部分空闲内存
        avail=memory_avail,       # 这个值决定了最终的memory_used计算
        buffers=0.2,
        cached=1.0,
        swap_cached=0.0,
        active=memory_used_gb * 0.6,
        inactive=memory_used_gb * 0.3,
        active_anon=memory_used_gb * 0.4,
        inactive_anon=memory_used_gb * 0.2,
        active_file=memory_used_gb * 0.2,
        inactive_file=memory_used_gb * 0.1,
        dirty=0.01,
        writeback=0.0,
        anon_pages=memory_used_gb * 0.5,
        mapped=memory_used_gb * 0.1,
        kReclaimable=0.3,
        sReclaimable=0.5,
        sUnreclaim=0.2,
        used_percent=(memory_used_gb / memory_total_gb) * 100
    )
    
    # 创建网络统计
    network_stats = [
        NetworkStats(
            name="eth0",
            send_rate=100.0,  # KB/s
            rcv_rate=200.0,
            send_packets_rate=50.0,
            rcv_packets_rate=80.0
        )
    ]
    
    return MonitoringData(
        timestamp=datetime.now(),
        hostname=hostname,
        cpu_load_1min=cpu_load_1min,
        cpu_load_5min=cpu_load_1min * 0.9,
        cpu_load_15min=cpu_load_1min * 0.8,
        cpu_stats=cpu_stats,
        soft_irq_stats=soft_irq_stats,
        memory_stats=memory_stats,
        network_stats=network_stats
    )

async def test_langchain_agent():
    """测试LangChain Agent的各种场景"""
    print("=== 测试基于LangChain的监控分析Agent ===\n")
    
    # 初始化知识库
    print("1. 初始化知识库...")
    knowledge_base = MonitoringKnowledgeBase()
    
    # 初始化LangChain Agent（启用模拟模式）
    print("2. 初始化LangChain Agent（模拟模式）...")
    agent = LangChainMonitoringAgent(knowledge_base, mock_mode=True)
    print(f"LangChain可用: {agent.use_langchain}")
    print(f"模拟模式: {agent.mock_mode}")
    print()
    
    # 测试场景1: 正常状态
    print("=== 场景1: 正常系统状态 ===")
    normal_data = create_test_data(
        hostname="server-01",
        cpu_usage=15.2,
        memory_total_gb=16.0,
        memory_used_gb=4.0,
        cpu_load_1min=0.8
    )
    
    result = await agent.analyze(normal_data)
    print(f"检测到的问题: {result.anomalies_detected}")
    print(f"推荐方案: {result.recommendations}")
    print(f"置信度: {result.confidence_score}")
    print(f"LangChain分析详情: {result.analysis_details}")
    print()
    
    # 测试场景2: 高CPU使用率（简单问题）
    print("=== 场景2: 高CPU使用率（简单问题） ===")
    high_cpu_data = create_test_data(
        hostname="server-02",
        cpu_usage=85.5,
        memory_total_gb=16.0,
        memory_used_gb=6.0,
        cpu_load_1min=3.2
    )
    
    result = await agent.analyze(high_cpu_data)
    print(f"检测到的问题: {result.anomalies_detected}")
    print(f"推荐方案数量: {len(result.recommendations)}")
    print(f"置信度: {result.confidence_score}")
    print(f"LangChain详情: {result.analysis_details.get('langchain_enabled', 'N/A')}")
    print()
    
    # 测试场景3: 严重内存不足（复杂问题，触发LangChain）
    print("=== 场景3: 严重内存不足（复杂问题） ===")
    memory_critical_data = create_test_data(
        hostname="server-03",
        cpu_usage=75.0,
        memory_total_gb=8.0,
        memory_used_gb=7.9,  # 98.75% - 应该触发严重告警
        cpu_load_1min=6.5
    )
    
    result = await agent.analyze(memory_critical_data)
    print(f"检测到的问题: {result.anomalies_detected}")
    print(f"推荐方案: {result.recommendations[:3]}...")  # 显示前3个建议
    print(f"置信度: {result.confidence_score}")
    if 'root_cause' in result.analysis_details:
        print(f"根本原因: {result.analysis_details['root_cause']}")
    if 'severity' in result.analysis_details:
        print(f"严重程度: {result.analysis_details['severity']}")
    print()
    
    # 测试场景4: I/O瓶颈（复杂场景）
    print("=== 场景4: I/O瓶颈检测 ===")
    io_bottleneck_data = create_test_data(
        hostname="server-04",
        cpu_usage=45.0,    # CPU不高
        memory_total_gb=32.0,
        memory_used_gb=12.0,
        cpu_load_1min=8.5  # 但负载很高
    )
    
    result = await agent.analyze(io_bottleneck_data)
    print(f"检测到的问题: {result.anomalies_detected}")
    print(f"推荐方案数量: {len(result.recommendations)}")
    print(f"置信度: {result.confidence_score}")
    print(f"分析方法: {result.analysis_details.get('detection_method', 'unknown')}")
    print()
    
    print("=== LangChain Agent测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_langchain_agent())
