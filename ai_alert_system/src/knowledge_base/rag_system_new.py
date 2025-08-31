"""
RAG知识库管理
使用ChromaDB存储和检索系统监控知识（可选依赖）
"""
import logging
from typing import List, Dict, Any, Optional

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

try:
    from ..config import settings
except ImportError:
    # 如果config不可用，使用默认设置
    class Settings:
        log_level = "INFO"
        chroma_persist_directory = "./data/chroma_db"
        chroma_collection_name = "linux_monitoring_kb"
    settings = Settings()

logger = logging.getLogger(__name__)

class MonitoringKnowledgeBase:
    """监控系统知识库（简化版，支持降级到内存模式）"""
    
    def __init__(self):
        self.persist_directory = getattr(settings, 'chroma_persist_directory', './data/chroma_db')
        self.collection_name = getattr(settings, 'chroma_collection_name', 'linux_monitoring_kb')
        self.vectorstore = None
        self.in_memory_kb = self._get_default_knowledge()
        self.use_chroma = CHROMADB_AVAILABLE
    
    def initialize(self):
        """初始化知识库"""
        if CHROMADB_AVAILABLE:
            try:
                # 创建ChromaDB客户端
                self.client = chromadb.PersistentClient(path=self.persist_directory)
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                
                # 如果知识库为空，加载默认知识
                if self.collection.count() == 0:
                    self._load_default_knowledge()
                
                logger.info("ChromaDB知识库初始化成功")
                return True
            except Exception as e:
                logger.warning(f"ChromaDB初始化失败，将使用内存知识库: {e}")
                self.use_chroma = False
        else:
            logger.info("ChromaDB不可用，使用内存知识库")
        
        return True
    
    def search_solutions(self, problem_description: str, k: int = 3) -> List[Dict[str, Any]]:
        """搜索解决方案"""
        if self.use_chroma and hasattr(self, 'collection'):
            try:
                results = self.collection.query(
                    query_texts=[problem_description],
                    n_results=k
                )
                
                solutions = []
                if results['documents'] and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        solutions.append({
                            'content': doc,
                            'score': 1.0 - results['distances'][0][i] if results['distances'] else 0.8,
                            'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                        })
                return solutions
            except Exception as e:
                logger.warning(f"ChromaDB查询失败，使用内存搜索: {e}")
        
        # 内存搜索（简单匹配）
        solutions = []
        problem_lower = problem_description.lower()
        for item in self.in_memory_kb:
            score = 0.0
            content_lower = item['content'].lower()
            
            # 简单关键词匹配计分
            if 'cpu' in problem_lower and 'cpu' in content_lower:
                score += 0.8
            if '内存' in problem_lower and '内存' in content_lower:
                score += 0.8
            if '负载' in problem_lower and '负载' in content_lower:
                score += 0.8
            if 'i/o' in problem_lower and 'i/o' in content_lower:
                score += 0.8
            
            if score > 0:
                solutions.append({
                    'content': item['content'],
                    'score': score,
                    'metadata': item['metadata']
                })
        
        # 按分数排序并返回前k个
        solutions.sort(key=lambda x: x['score'], reverse=True)
        return solutions[:k]
    
    def _load_default_knowledge(self):
        """加载默认知识到ChromaDB"""
        if not self.use_chroma or not hasattr(self, 'collection'):
            return
        
        try:
            documents = []
            metadatas = []
            ids = []
            
            for i, item in enumerate(self.in_memory_kb):
                documents.append(item['content'])
                metadatas.append(item['metadata'])
                ids.append(f"doc_{i}")
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"已加载 {len(documents)} 条知识到ChromaDB")
        except Exception as e:
            logger.error(f"加载默认知识失败: {e}")
    
    def _get_default_knowledge(self) -> List[Dict[str, Any]]:
        """获取默认监控知识"""
        return [
            {
                "content": """CPU使用率高的问题诊断和解决方案：
1. 使用top、htop命令查看进程CPU占用
2. 优化应用程序代码，减少CPU密集型操作
3. 增加CPU核心数或升级CPU
4. 使用负载均衡分散CPU压力
5. 调整进程优先级（nice值）""",
                "metadata": {"category": "cpu", "issue": "high_usage"}
            },
            {
                "content": """内存使用率高的问题诊断和解决方案：
1. 使用free -h查看总体内存使用情况
2. 使用ps aux --sort=-%mem查看进程内存占用
3. 检查是否存在内存泄漏
4. 重启占用内存较高的进程
5. 增加物理内存或配置swap""",
                "metadata": {"category": "memory", "issue": "high_usage"}
            },
            {
                "content": """系统负载高的问题诊断和解决方案：
1. 使用uptime查看系统负载
2. 检查CPU使用率和进程状态
3. 分析I/O等待时间
4. 查看网络连接状态
5. 优化系统任务调度""",
                "metadata": {"category": "load", "issue": "high_load"}
            },
            {
                "content": """I/O瓶颈问题诊断和解决方案：
1. 使用iostat查看磁盘I/O状态
2. 使用iotop查看进程I/O占用
3. 检查磁盘空间使用情况
4. 优化数据库查询
5. 使用SSD替换传统硬盘""",
                "metadata": {"category": "io", "issue": "bottleneck"}
            }
        ]

    def add_knowledge(self, content: str, metadata: Dict[str, Any]):
        """添加新的知识条目"""
        if self.use_chroma and hasattr(self, 'collection'):
            try:
                import uuid
                doc_id = str(uuid.uuid4())
                self.collection.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
                logger.info("新知识已添加到ChromaDB")
            except Exception as e:
                logger.error(f"添加知识到ChromaDB失败: {e}")
        
        # 同时添加到内存知识库
        self.in_memory_kb.append({
            'content': content,
            'metadata': metadata
        })

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        stats = {
            'use_chroma': self.use_chroma,
            'memory_kb_size': len(self.in_memory_kb)
        }
        
        if self.use_chroma and hasattr(self, 'collection'):
            try:
                stats['chroma_collection_size'] = self.collection.count()
            except Exception as e:
                stats['chroma_error'] = str(e)
        
        return stats
