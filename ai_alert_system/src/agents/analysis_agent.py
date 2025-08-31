"""
基于LangChain的分析Agent实现
使用LangChain的链式处理、提示模板和输出解析器
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
    from langchain_core.runnables import RunnablePassthrough, RunnableLambda
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain.chains import LLMChain
    from pydantic import BaseModel, Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("警告: LangChain库未安装，将使用降级模式")

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from ..models.data_models import MonitoringData, Alert, AlertLevel, MetricType, AnalysisResult
from ..knowledge_base.rag_system import MonitoringKnowledgeBase

logger = logging.getLogger(__name__)

# Pydantic模型用于结构化输出
class IssueAnalysis(BaseModel):
    """问题分析结构化输出"""
    root_cause: str = Field(description="根本原因分析，1-2句话")
    severity: str = Field(description="严重程度：低/中/高")
    impact: str = Field(description="系统影响描述")

class SolutionRecommendation(BaseModel):
    """解决方案结构化输出"""
    immediate_actions: List[str] = Field(description="立即采取的行动")
    monitoring_steps: List[str] = Field(description="监控步骤")
    preventive_measures: List[str] = Field(description="预防措施")

@dataclass
class AnalysisContext:
    """分析上下文"""
    data: MonitoringData
    issues: List[str] = None
    llm_analysis: IssueAnalysis = None
    solutions: SolutionRecommendation = None
    confidence: float = 0.5
    fallback_used: bool = False

class LangChainMonitoringAgent:
    """基于LangChain的监控分析Agent"""
    
    def __init__(self, knowledge_base: MonitoringKnowledgeBase, mock_mode: bool = False):
        self.knowledge_base = knowledge_base
        self.mock_mode = mock_mode  # 新增模拟模式支持
        
        # 初始化LangChain组件
        if LANGCHAIN_AVAILABLE and (os.getenv("OPENAI_API_KEY") or mock_mode):
            if not mock_mode:
                self.llm = ChatOpenAI(
                    model="gpt-4-turbo-preview",
                    temperature=0,
                    api_key=os.getenv("OPENAI_API_KEY")
                )
            else:
                self.llm = None  # 模拟模式下不需要真实LLM
            self.use_langchain = True
            logger.info(f"LangChain组件已初始化 (模拟模式: {mock_mode})")
        else:
            self.llm = None
            self.use_langchain = False
            logger.warning("LangChain不可用，将使用降级模式")
            
        # 降级到直接OpenAI客户端（总是初始化）
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            self.openai_client = None
        
        # 设置LangChain链和解析器
        self._setup_langchain_components()
        
    def _setup_langchain_components(self):
        """设置LangChain组件"""
        if not self.use_langchain:
            return
            
        # 问题分析提示模板
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个Linux系统监控专家。基于检测到的问题进行深度分析。
请以JSON格式输出分析结果，包含root_cause（根本原因）、severity（严重程度）、impact（系统影响）。"""),
            ("human", """
主机: {hostname}
检测到的问题: {detected_issues}

详细指标：
CPU使用率: {cpu_usage}%
内存使用率: {memory_usage_percent:.1f}%
系统负载: {load_avg}
内存总量: {memory_total_gb:.1f}GB
内存已用: {memory_used_gb:.1f}GB

请分析根本原因和影响：
""")
        ])
        
        # 解决方案生成提示模板
        self.solution_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个Linux系统运维专家。基于问题分析和知识库信息生成具体的解决方案。
请以JSON格式输出解决方案，包含immediate_actions（立即行动）、monitoring_steps（监控步骤）、preventive_measures（预防措施）。"""),
            ("human", """
检测问题: {detected_issues}
根本原因分析: {root_cause_analysis}
知识库建议: {knowledge_base_results}

请提供结构化的解决方案：
""")
        ])
        
        # 输出解析器
        self.analysis_parser = PydanticOutputParser(pydantic_object=IssueAnalysis)
        self.solution_parser = PydanticOutputParser(pydantic_object=SolutionRecommendation)
        
        # 仅在非模拟模式下创建真实的链
        if not self.mock_mode and self.llm:
            # 创建分析链
            self.analysis_chain = (
                self.analysis_prompt 
                | self.llm 
                | self.analysis_parser
            )
            
            # 创建解决方案链
            self.solution_chain = (
                self.solution_prompt 
                | self.llm 
                | self.solution_parser
            )
            
            logger.info("LangChain真实链组件设置完成")
        else:
            # 模拟模式下不需要真实的链
            self.analysis_chain = None
            self.solution_chain = None
            logger.info("LangChain模拟模式组件设置完成")

    async def analyze(self, data: MonitoringData) -> AnalysisResult:
        """主分析方法 - 基于LangChain的3步工作流"""
        context = AnalysisContext(data=data)
        
        try:
            # 第1步: 规则检测问题（无需LLM）
            context.issues = self._detect_issues_locally(data)
            context.confidence = 0.6
            
            if not context.issues:
                logger.info("未检测到问题，跳过后续分析")
                return self._create_analysis_result(context)
            
            logger.info(f"检测到问题: {context.issues}")
            
            # 第2步: 使用LangChain进行问题分析
            if self.use_langchain and self._should_use_llm(context.issues):
                context = await self._perform_langchain_analysis(context)
                context.confidence = 0.9
            else:
                logger.info("跳过LangChain分析（不可用或简单问题）")
                context = await self._fallback_analysis_mode(context)
                context.confidence = 0.7
            
            # 第3步: 使用LangChain生成结构化解决方案
            context = await self._generate_langchain_solutions(context)
            
            return self._create_analysis_result(context)
            
        except Exception as e:
            logger.error(f"分析过程出错: {e}")
            return self._fallback_analysis(data)

    def _detect_issues_locally(self, data: MonitoringData) -> List[str]:
        """本地规则检测（无需LLM）"""
        issues = []
        
        # CPU检测
        if data.cpu_usage > 95:
            issues.append("CPU使用率严重过高")
        elif data.cpu_usage > 80:
            issues.append("CPU使用率偏高")
            
        # 内存检测
        memory_usage_percent = (data.memory_used / data.memory_total) * 100
        if memory_usage_percent > 95:
            issues.append("内存严重不足")
        elif memory_usage_percent > 85:
            issues.append("内存使用率偏高")
            
        # 负载检测
        if data.cpu_load_1min > 10:
            issues.append("系统负载严重过高")
        elif data.cpu_load_1min > 8:
            issues.append("系统负载偏高")
            
        # 复合问题检测
        if data.cpu_load_1min > 5 and data.cpu_usage < 50:
            issues.append("负载高但CPU低，可能存在I/O瓶颈")
        
        return issues

    def _should_use_llm(self, issues: List[str]) -> bool:
        """智能判断是否需要LLM分析（成本优化）"""
        complex_keywords = ["严重", "瓶颈", "不足"]
        
        has_complex_issue = any(
            any(keyword in issue for keyword in complex_keywords) 
            for issue in issues
        )
        
        if has_complex_issue:
            logger.info("检测到复杂问题，启动LangChain分析")
            return True
        else:
            logger.info("仅检测到简单问题，使用规则处理")
            return False

    async def _perform_langchain_analysis(self, context: AnalysisContext) -> AnalysisContext:
        """使用LangChain执行结构化分析"""
        if not self.use_langchain:
            return await self._fallback_analysis_mode(context)
            
        try:
            # 准备分析输入
            memory_usage_percent = (context.data.memory_used / context.data.memory_total) * 100
            memory_total_gb = context.data.memory_total / (1024**3)
            memory_used_gb = context.data.memory_used / (1024**3)
            
            analysis_input = {
                "hostname": context.data.hostname,
                "detected_issues": ", ".join(context.issues),
                "cpu_usage": context.data.cpu_usage,
                "memory_usage_percent": memory_usage_percent,
                "load_avg": context.data.cpu_load_1min,
                "memory_total_gb": memory_total_gb,
                "memory_used_gb": memory_used_gb
            }
            
            if self.mock_mode:
                # 模拟LangChain分析结果
                analysis_result = self._mock_langchain_analysis(context.issues, analysis_input)
                context.llm_analysis = analysis_result
                logger.info(f"LangChain模拟分析完成: {analysis_result.root_cause}")
            else:
                # 使用真实LangChain分析链
                analysis_result = await asyncio.wait_for(
                    self.analysis_chain.ainvoke(analysis_input),
                    timeout=30.0
                )
                
                context.llm_analysis = analysis_result
                logger.info(f"LangChain分析完成: {analysis_result.root_cause}")
            
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"LangChain分析失败，启用降级: {e}")
            context = await self._fallback_analysis_mode(context)
            context.fallback_used = True
            
        return context

    async def _generate_langchain_solutions(self, context: AnalysisContext) -> AnalysisContext:
        """使用LangChain生成结构化解决方案"""
        try:
            # 从知识库检索相关解决方案
            knowledge_results = []
            for issue in context.issues:
                results = self.knowledge_base.search_solutions(issue, k=2)
                knowledge_results.extend([r['content'] for r in results])
            
            knowledge_text = "\n".join(knowledge_results) if knowledge_results else "暂无相关知识库信息"
            
            if self.use_langchain and context.llm_analysis:
                # 使用LangChain解决方案链
                solution_input = {
                    "detected_issues": ", ".join(context.issues),
                    "root_cause_analysis": context.llm_analysis.root_cause,
                    "knowledge_base_results": knowledge_text
                }
                
                try:
                    if self.mock_mode:
                        # 模拟LangChain解决方案生成
                        solution_result = self._mock_langchain_solutions(context.issues, solution_input)
                        context.solutions = solution_result
                        logger.info("LangChain模拟解决方案生成完成")
                    else:
                        # 真实LangChain解决方案链
                        solution_result = await asyncio.wait_for(
                            self.solution_chain.ainvoke(solution_input),
                            timeout=30.0
                        )
                        
                        context.solutions = solution_result
                        logger.info("LangChain解决方案生成完成")
                    
                except Exception as e:
                    logger.warning(f"LangChain解决方案生成失败: {e}")
                    context.solutions = self._get_fallback_solutions(context.issues, knowledge_results)
            else:
                # 降级模式解决方案
                context.solutions = self._get_fallback_solutions(context.issues, knowledge_results)
                
        except Exception as e:
            logger.error(f"解决方案生成失败: {e}")
            context.solutions = self._get_fallback_solutions(context.issues, [])
            
        return context

    async def _fallback_analysis_mode(self, context: AnalysisContext) -> AnalysisContext:
        """降级分析模式"""
        if self.openai_client:
            # 使用直接OpenAI客户端
            try:
                prompt = f"""
分析以下系统问题：{', '.join(context.issues)}

主机: {context.data.hostname}
CPU: {context.data.cpu_usage}%
内存: {(context.data.memory_used / context.data.memory_total) * 100:.1f}%
负载: {context.data.cpu_load_1min}

请简要分析根本原因：
"""
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=200
                )
                
                analysis_text = response.choices[0].message.content.strip()
                context.llm_analysis = IssueAnalysis(
                    root_cause=analysis_text,
                    severity="中",
                    impact="可能影响系统性能"
                )
                
            except Exception as e:
                logger.warning(f"OpenAI降级分析失败: {e}")
                context.llm_analysis = self._get_rule_based_analysis(context.issues)
        else:
            # 完全规则分析
            context.llm_analysis = self._get_rule_based_analysis(context.issues)
            
        context.fallback_used = True
        return context

    def _get_rule_based_analysis(self, issues: List[str]) -> IssueAnalysis:
        """基于规则的分析"""
        if any("严重" in issue for issue in issues):
            severity = "高"
            impact = "严重影响系统稳定性"
        elif any("瓶颈" in issue for issue in issues):
            severity = "中"
            impact = "影响系统响应性能"
        else:
            severity = "低"
            impact = "轻微影响系统运行"
            
        root_cause = "基于规则检测: " + "; ".join(issues)
        
        return IssueAnalysis(
            root_cause=root_cause,
            severity=severity,
            impact=impact
        )

    def _mock_langchain_analysis(self, issues: List[str], analysis_input: dict) -> IssueAnalysis:
        """模拟LangChain分析结果"""
        # 基于问题类型生成智能分析
        if any("严重" in issue for issue in issues):
            if "内存" in " ".join(issues):
                root_cause = f"系统内存资源严重不足，当前使用率{analysis_input['memory_usage_percent']:.1f}%，可能导致OOM killer激活"
                severity = "高"
                impact = "可能引发应用程序崩溃和系统不稳定"
            elif "CPU" in " ".join(issues):
                root_cause = f"CPU资源严重过载，使用率{analysis_input['cpu_usage']:.1f}%，系统响应严重延迟"
                severity = "高"
                impact = "严重影响系统响应时间和用户体验"
            else:
                root_cause = f"系统负载{analysis_input['load_avg']:.1f}严重超标，可能存在资源争用"
                severity = "高"
                impact = "系统整体性能严重下降"
        elif "瓶颈" in " ".join(issues):
            root_cause = f"检测到I/O瓶颈：负载{analysis_input['load_avg']:.1f}高但CPU使用率{analysis_input['cpu_usage']:.1f}%相对较低，表明存在磁盘或网络I/O等待"
            severity = "中"
            impact = "影响应用程序I/O操作效率"
        else:
            root_cause = f"系统性能指标偏高：CPU {analysis_input['cpu_usage']:.1f}%，内存 {analysis_input['memory_usage_percent']:.1f}%，需要关注"
            severity = "低"
            impact = "轻微影响系统性能表现"
        
        return IssueAnalysis(
            root_cause=root_cause,
            severity=severity,
            impact=impact
        )

    def _mock_langchain_solutions(self, issues: List[str], solution_input: dict) -> SolutionRecommendation:
        """模拟LangChain解决方案生成"""
        immediate_actions = []
        monitoring_steps = []
        preventive_measures = []
        
        # 基于问题类型和根本原因分析生成解决方案
        if "内存" in " ".join(issues):
            immediate_actions.extend([
                "立即使用 free -h 和 ps aux --sort=-%mem 检查内存使用详情",
                "识别并重启占用内存最高的非关键进程",
                "清理系统缓存: echo 3 > /proc/sys/vm/drop_caches"
            ])
            monitoring_steps.extend([
                "设置内存使用率监控告警阈值为85%",
                "定期检查内存泄漏趋势"
            ])
            preventive_measures.extend([
                "评估是否需要增加物理内存",
                "优化应用程序内存使用模式"
            ])
        
        if "CPU" in " ".join(issues):
            immediate_actions.extend([
                "使用 top 和 htop 定位高CPU消耗进程",
                "检查是否存在CPU密集型任务可以调度到非高峰时段"
            ])
            monitoring_steps.extend([
                "监控CPU使用率变化趋势",
                "设置CPU负载告警"
            ])
            preventive_measures.extend([
                "考虑CPU升级或负载均衡",
                "优化高消耗应用程序算法"
            ])
        
        if "I/O瓶颈" in " ".join(issues):
            immediate_actions.extend([
                "使用 iostat -x 1 检查磁盘I/O性能",
                "使用 iotop 识别高I/O进程",
                "检查网络I/O状态: netstat -i"
            ])
            monitoring_steps.extend([
                "监控磁盘I/O等待时间",
                "跟踪网络带宽使用情况"
            ])
            preventive_measures.extend([
                "考虑SSD升级或I/O优化",
                "实施数据库查询优化"
            ])
        
        # 通用建议
        if not immediate_actions:
            immediate_actions.append("执行系统健康检查")
        
        return SolutionRecommendation(
            immediate_actions=immediate_actions[:5],
            monitoring_steps=monitoring_steps[:3],
            preventive_measures=preventive_measures[:3]
        )

    def _get_fallback_solutions(self, issues: List[str], knowledge_results: List[str]) -> SolutionRecommendation:
        """获取降级解决方案"""
        immediate_actions = []
        monitoring_steps = []
        preventive_measures = []
        
        # 基于问题类型生成建议
        for issue in issues:
            if "CPU" in issue:
                immediate_actions.append("使用top命令查看高CPU进程")
                monitoring_steps.append("监控CPU使用率趋势")
                preventive_measures.append("优化高消耗进程或增加CPU资源")
            elif "内存" in issue:
                immediate_actions.append("使用free -h检查内存详情")
                monitoring_steps.append("监控内存使用模式")
                preventive_measures.append("检查内存泄漏或增加内存容量")
            elif "负载" in issue:
                immediate_actions.append("检查系统负载和等待队列")
                monitoring_steps.append("持续监控系统负载")
                preventive_measures.append("分析负载来源并进行优化")
            elif "I/O瓶颈" in issue:
                immediate_actions.append("使用iostat检查磁盘I/O")
                monitoring_steps.append("监控I/O性能指标")
                preventive_measures.append("优化I/O操作或升级存储")
        
        # 添加知识库建议
        if knowledge_results:
            immediate_actions.extend(knowledge_results[:2])
        
        # 去重并限制数量
        immediate_actions = list(dict.fromkeys(immediate_actions))[:5]
        monitoring_steps = list(dict.fromkeys(monitoring_steps))[:3]
        preventive_measures = list(dict.fromkeys(preventive_measures))[:3]
        
        return SolutionRecommendation(
            immediate_actions=immediate_actions,
            monitoring_steps=monitoring_steps,
            preventive_measures=preventive_measures
        )

    def _create_analysis_result(self, context: AnalysisContext) -> AnalysisResult:
        """创建分析结果对象"""
        # 整合解决方案
        recommendations = []
        if context.solutions:
            if hasattr(context.solutions, 'immediate_actions'):
                recommendations.extend(context.solutions.immediate_actions)
            if hasattr(context.solutions, 'monitoring_steps'):
                recommendations.extend(context.solutions.monitoring_steps)
            if hasattr(context.solutions, 'preventive_measures'):
                recommendations.extend(context.solutions.preventive_measures)
        
        # 分析详情
        analysis_details = {
            "detection_method": "langchain_agent",
            "langchain_enabled": self.use_langchain,
            "fallback_used": context.fallback_used
        }
        
        if context.llm_analysis:
            analysis_details.update({
                "root_cause": context.llm_analysis.root_cause,
                "severity": context.llm_analysis.severity,
                "impact": context.llm_analysis.impact
            })
        
        return AnalysisResult(
            timestamp=datetime.now(),
            hostname=context.data.hostname,
            anomalies_detected=context.issues or [],
            performance_issues=context.issues or [],
            recommendations=recommendations,
            confidence_score=min(context.confidence, 1.0),
            analysis_details=analysis_details
        )

    def _fallback_analysis(self, data: MonitoringData) -> AnalysisResult:
        """完全降级分析"""
        return AnalysisResult(
            timestamp=datetime.now(),
            hostname=data.hostname,
            anomalies_detected=["系统检测异常"],
            performance_issues=["分析流程失败"],
            recommendations=["建议人工检查系统状态和日志"],
            confidence_score=0.3,
            analysis_details={"fallback": True, "error": "complete_fallback"}
        )

# 兼容性别名
MonitoringAgent = LangChainMonitoringAgent
