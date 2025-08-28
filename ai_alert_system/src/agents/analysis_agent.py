"""
简化的LangGraph智能分析Agent
专注于核心检测功能：规则检测 -> LLM分析 -> 解决方案
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.data_models import MonitoringData, Alert, AlertLevel, MetricType, AnalysisResult
from ..knowledge_base.rag_system import MonitoringKnowledgeBase
from ..config import settings

logger = logging.getLogger(__name__)

class AnalysisState:
    """简化的分析状态"""
    def __init__(self):
        self.data: Optional[MonitoringData] = None
        self.issues: List[str] = []
        self.alerts: List[Alert] = []
        self.solutions: List[str] = []
        self.confidence: float = 0.0

class MonitoringAgent:
    """简化的监控分析Agent - 专注核心功能"""
    
    def __init__(self, knowledge_base: MonitoringKnowledgeBase):
        self.knowledge_base = knowledge_base
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,
            openai_api_key=settings.openai_api_key
        )
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建简化的3步工作流：检测 -> 分析 -> 解决"""
        workflow = StateGraph(AnalysisState)
        
        # 只保留核心3个节点
        workflow.add_node("detect_issues", self._detect_issues)
        workflow.add_node("analyze_with_llm", self._analyze_with_llm)
        workflow.add_node("generate_solutions", self._generate_solutions)
        
        # 简化的线性流程
        workflow.set_entry_point("detect_issues")
        workflow.add_edge("detect_issues", "analyze_with_llm")
        workflow.add_edge("analyze_with_llm", "generate_solutions")
        workflow.add_edge("generate_solutions", END)
        
        return workflow.compile()
    
    async def analyze(self, data: MonitoringData) -> AnalysisResult:
        """主分析入口"""
        state = AnalysisState()
        state.data = data
        
        try:
            result = await self.workflow.ainvoke(state)
            
            return AnalysisResult(
                timestamp=datetime.now(),
                hostname=data.hostname,
                anomalies_detected=result.issues,
                performance_issues=result.issues,  # 简化：合并为一个列表
                recommendations=result.solutions,
                confidence_score=result.confidence,
                analysis_details={"simplified": True}
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # 降级到基础规则检测
            return self._fallback_analysis(data)
    
    def _detect_issues(self, state: AnalysisState) -> AnalysisState:
        """步骤1：基于阈值的问题检测"""
        data = state.data
        issues = []
        
        # CPU检测
        if data.cpu_usage > 90:
            issues.append(f"CPU严重过载: {data.cpu_usage:.1f}%")
        elif data.cpu_usage > 70:
            issues.append(f"CPU使用率偏高: {data.cpu_usage:.1f}%")
        
        # 内存检测
        memory_percent = (data.memory_used / data.memory_total) * 100
        if memory_percent > 90:
            issues.append(f"内存严重不足: {memory_percent:.1f}%")
        elif memory_percent > 80:
            issues.append(f"内存使用率偏高: {memory_percent:.1f}%")
        
        # 负载检测
        if data.cpu_load_1min > 8:  # 假设8核
            issues.append(f"系统负载过高: {data.cpu_load_1min}")
        
        state.issues = issues
        state.confidence = 0.8 if issues else 0.3
        return state
    
    def _analyze_with_llm(self, state: AnalysisState) -> AnalysisState:
        """步骤2：LLM深度分析（仅在有问题时）"""
        if not state.issues:
            return state
        
        try:
            prompt = f"""分析Linux系统状况：
CPU: {state.data.cpu_usage}%, 负载: {state.data.cpu_load_1min}
内存: {(state.data.memory_used/state.data.memory_total)*100:.1f}%
问题: {'; '.join(state.issues)}

简要分析根本原因（1-2句话）："""
            
            response = self.llm.invoke([{"role": "user", "content": prompt}])
            if hasattr(response, 'content'):
                # 添加LLM分析结果
                state.issues.append(f"AI分析: {response.content.strip()}")
                state.confidence = min(state.confidence + 0.2, 1.0)
                
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")
            
        return state
    
    def _generate_solutions(self, state: AnalysisState) -> AnalysisState:
        """步骤3：生成解决方案"""
        if not state.issues:
            return state
        
        # 从知识库检索解决方案
        query = " ".join(state.issues[:2])  # 使用前2个问题作为查询
        solutions = self.knowledge_base.search_solutions(query, k=2)
        
        # 提取解决方案
        state.solutions = []
        for solution in solutions:
            content = solution.get("content", "")
            if content:
                # 简单提取前100字作为建议
                state.solutions.append(content[:100] + "...")
        
        # 如果没有找到，使用默认建议
        if not state.solutions:
            if any("CPU" in issue for issue in state.issues):
                state.solutions.append("建议：检查top命令查看高CPU进程并优化")
            if any("内存" in issue for issue in state.issues):
                state.solutions.append("建议：清理缓存或增加内存容量")
        
        # 生成告警
        if state.issues:
            alert = Alert(
                id=f"{state.data.hostname}_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                level=AlertLevel.CRITICAL if any("严重" in issue for issue in state.issues) else AlertLevel.WARNING,
                metric_type=MetricType.CPU_USAGE,  # 简化：默认CPU类型
                title=f"{state.data.hostname}: 系统性能告警",
                description="; ".join(state.issues),
                current_value=state.data.cpu_usage,
                threshold_value=70,
                hostname=state.data.hostname,
                suggested_actions=state.solutions,
                context={}
            )
            state.alerts = [alert]
        
        return state
    
    def _fallback_analysis(self, data: MonitoringData) -> AnalysisResult:
        """降级分析（当LLM失败时）"""
        issues = []
        if data.cpu_usage > 80:
            issues.append("CPU使用率过高")
        if (data.memory_used / data.memory_total) > 0.8:
            issues.append("内存使用率过高")
        
        return AnalysisResult(
            timestamp=datetime.now(),
            hostname=data.hostname,
            anomalies_detected=issues,
            performance_issues=issues,
            recommendations=["建议进行系统优化"],
            confidence_score=0.5,
            analysis_details={"fallback": True}
        )
