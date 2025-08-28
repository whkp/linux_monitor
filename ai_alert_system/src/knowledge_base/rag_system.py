"""
RAG知识库管理
使用ChromaDB存储和检索系统监控知识
"""
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document

from ..config import settings

logger = logging.getLogger(__name__)

class MonitoringKnowledgeBase:
    """监控系统知识库"""
    
    def __init__(self):
        self.persist_directory = settings.chroma_persist_directory
        self.collection_name = settings.chroma_collection_name
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        self.vectorstore: Optional[Chroma] = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def initialize(self):
        """初始化知识库"""
        try:
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            # 如果知识库为空，加载默认知识
            if self._is_empty():
                self._load_default_knowledge()
            
            logger.info("Knowledge base initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")
            raise
    
    def _is_empty(self) -> bool:
        """检查知识库是否为空"""
        try:
            result = self.vectorstore.similarity_search("test", k=1)
            return len(result) == 0
        except:
            return True
    
    def _load_default_knowledge(self):
        """加载默认监控知识"""
        default_knowledge = [
            {
                "content": """
                CPU使用率高的问题诊断和解决方案：
                
                1. 识别CPU密集型进程：
                   - 使用top、htop命令查看进程CPU占用
                   - 使用ps aux --sort=-%cpu查看CPU使用率排序
                
                2. 常见解决方案：
                   - 优化应用程序代码，减少CPU密集型操作
                   - 增加CPU核心数或升级CPU
                   - 使用负载均衡分散CPU压力
                   - 调整进程优先级（nice值）
                   - 限制进程CPU使用率（cpulimit工具）
                
                3. 临时缓解措施：
                   - 重启占用CPU较高的非关键进程
                   - 使用cgroup限制进程资源使用
                """,
                "metadata": {"category": "cpu", "issue": "high_usage"}
            },
            {
                "content": """
                内存使用率高的问题诊断和解决方案：
                
                1. 内存分析工具：
                   - free -h：查看总体内存使用情况
                   - ps aux --sort=-%mem：查看进程内存占用
                   - pmap -d <pid>：查看进程详细内存映射
                   - /proc/meminfo：详细内存信息
                
                2. 解决方案：
                   - 增加物理内存
                   - 优化应用程序内存使用
                   - 调整swap配置
                   - 清理page cache：echo 3 > /proc/sys/vm/drop_caches
                   - 重启内存泄漏的进程
                
                3. 预防措施：
                   - 设置进程内存限制
                   - 监控内存泄漏
                   - 合理配置swap大小
                """,
                "metadata": {"category": "memory", "issue": "high_usage"}
            },
            {
                "content": """
                系统负载高的问题诊断和解决方案：
                
                1. 负载分析：
                   - uptime：查看1、5、15分钟平均负载
                   - w：查看当前用户和负载
                   - 负载>CPU核心数表示系统繁忙
                
                2. 定位问题：
                   - iostat：检查I/O等待
                   - vmstat：查看系统整体状态
                   - sar：系统活动报告
                
                3. 解决方案：
                   - 如果是CPU负载：优化CPU密集型任务
                   - 如果是I/O负载：优化磁盘I/O操作
                   - 如果是内存负载：释放内存或增加内存
                   - 调整系统调度策略
                """,
                "metadata": {"category": "load", "issue": "high_load"}
            },
            {
                "content": """
                网络流量异常的问题诊断和解决方案：
                
                1. 网络监控工具：
                   - iftop：实时网络流量监控
                   - nethogs：按进程查看网络使用
                   - ss -tuln：查看网络连接状态
                   - netstat -i：查看网络接口统计
                
                2. 常见问题和解决方案：
                   - 异常流量：检查是否有恶意软件或DDoS攻击
                   - 网络拥塞：优化网络配置或增加带宽
                   - 连接数过多：调整系统连接限制
                   - 包丢失：检查网络硬件和配置
                
                3. 优化措施：
                   - 调整TCP/IP参数
                   - 使用流量控制工具
                   - 优化应用程序网络代码
                """,
                "metadata": {"category": "network", "issue": "traffic_anomaly"}
            }
        ]
        
        documents = []
        for item in default_knowledge:
            doc = Document(
                page_content=item["content"],
                metadata=item["metadata"]
            )
            documents.append(doc)
        
        # 分割文档
        split_docs = self.text_splitter.split_documents(documents)
        
        # 添加到向量数据库
        self.vectorstore.add_documents(split_docs)
        self.vectorstore.persist()
        
        logger.info(f"Loaded {len(split_docs)} knowledge chunks")
    
    def add_knowledge(self, content: str, metadata: Dict[str, Any]):
        """添加新的知识"""
        doc = Document(page_content=content, metadata=metadata)
        split_docs = self.text_splitter.split_documents([doc])
        self.vectorstore.add_documents(split_docs)
        self.vectorstore.persist()
        logger.info(f"Added new knowledge: {metadata}")
    
    def search_solutions(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """搜索解决方案"""
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            solutions = []
            
            for doc, score in results:
                solutions.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": score
                })
            
            logger.debug(f"Found {len(solutions)} solutions for query: {query}")
            return solutions
            
        except Exception as e:
            logger.error(f"Error searching solutions: {e}")
            return []
    
    def get_context_for_metric(self, metric_type: str, issue_type: str) -> str:
        """根据指标类型和问题类型获取上下文"""
        query = f"{metric_type} {issue_type} 问题 解决方案"
        solutions = self.search_solutions(query, k=3)
        
        context = []
        for solution in solutions:
            context.append(solution["content"])
        
        return "\n\n".join(context)
    
    def update_knowledge_from_feedback(self, query: str, solution: str, effectiveness: float):
        """根据反馈更新知识库"""
        if effectiveness > 0.8:  # 如果解决方案有效
            metadata = {
                "category": "feedback",
                "effectiveness": effectiveness,
                "query": query
            }
            self.add_knowledge(solution, metadata)
