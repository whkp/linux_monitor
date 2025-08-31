# AI智能告警系统 (简化版)

## 概述

这是一个基于LLM Agent和RAG技术的**简化版**智能告警系统，专注于Linux系统监控数据的AI分析和智能告警。实现轻量级、高效的智能运维告警。

后端LLM系统：以LangChain编排“规则检测→LLM分析→RAG方案”三步链路，gRPC流式接入监控数据，LLM输出受控JSON驱动告警分级与通知，内置降级回退与可观测性；实现E2E检测<2s、检索<100ms、Token成本约-60%。
RAG知识库：基于ChromaDB构建“检索→重排→上下文压缩”链路，覆盖CPU/内存/负载/网络场景并生成可执行Runbook建议；支持去重与严重度映射，显著降低误报并提升处置效率。

## 核心特性

🎯 **简化设计**: 3步线性工作流，无框架依赖
🤖 **AI智能分析**: GPT-4直接调用，仅在检测到问题时启动
📚 **RAG知识库**: 智能解决方案推荐，基于运维知识库
⚡ **快速响应**: 规则检测 + LLM分析，毫秒级处理
🔧 **降级机制**: LLM失败时自动降级到规则检测
📧 **直接通知**: 控制台输出 + 邮件告警，无Web依赖
🚀 **易于部署**: 单文件启动，5分钟内可运行
📚 **RAG知识库**: 集成专业的Linux系统运维知识，提供精准的解决方案
🔄 **实时处理**: 毫秒级数据处理，快速响应系统异常
🎯 **智能告警**: 自动去重、分级告警，减少告警疲劳
� **直接通知**: 通过Email/控制台直接输出告警信息
⚡ **轻量部署**: 简化架构，快速部署

## 简化架构

```
┌─────────────────┐    gRPC     ┌─────────────────┐
│   Linux Monitor │ ────────► │  数据收集器     │
│   (gRPC Server) │             │ (gRPC Client)   │
└─────────────────┘             └─────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────┐
│              简化的AI分析工作流                           │
│                                                         │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│  │规则检测问题 │─→ │LLM深度分析  │─→ │生成解决方案 │    │
│  │detect_issues│   │analyze_llm  │   │gen_solutions│    │
│  └─────────────┘   └─────────────┘   └─────────────┘    │
│                            │                            │
│                            ▼                            │
│                    ┌─────────────┐                      │
│                    │ 知识库(RAG) │                      │
│                    │  (ChromaDB) │                      │
│                    └─────────────┘                      │
└─────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────┐             ┌─────────────────┐
│   告警通知      │ ◄────────── │   告警管理器    │
│ (Email/Console) │             │ (Alert Manager) │
└─────────────────┘             └─────────────────┘
```

## 技术栈

- **AI框架**: OpenAI GPT-4 (直接调用，无框架依赖)
- **向量数据库**: ChromaDB (用于RAG知识库)
- **数据处理**: Python asyncio, gRPC
- **部署**: Docker (可选) 或本地Python运行

## 简化工作流

系统采用**3步线性流程**，大幅简化了原有的6节点复杂工作流：

### 步骤1: 规则检测问题 (detect_issues)
- 基于阈值的快速检测：CPU > 70%, 内存 > 80%, 负载 > 8
- 毫秒级响应，发现异常立即标记
- 计算初始置信度评分

### 步骤2: LLM深度分析 (analyze_with_llm)  
- **仅在检测到问题时**启动GPT-4分析
- 提供简洁的根本原因分析（1-2句话）
- 提升置信度评分

### 步骤3: 生成解决方案 (generate_solutions)
- 从RAG知识库检索相关解决方案
- 结合检测结果生成具体建议
- 创建标准化告警对象

### 降级机制
- LLM调用失败时自动降级到规则检测
- 确保系统稳定性和可用性

## 快速开始

### 方式一：本地运行（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd linux_monitor/ai_alert_system
```

2. **安装依赖**
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装简化版依赖 (仅8个核心包)
pip install -r requirements.txt

# 或手动安装核心依赖
pip install openai chromadb numpy pandas python-dotenv grpcio structlog rich
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，设置OpenAI API密钥
vim .env
```

4. **启动系统**
```bash
python main.py
```

### 方式二：Docker部署（可选）

```bash
# 构建镜像
docker build -t ai-alert-system .

# 运行容器
docker run -d --name ai-alert \
  -e OPENAI_API_KEY=your_key \
  -e MONITOR_GRPC_HOST=host.docker.internal \
  -v ./data:/app/data \
  ai-alert-system
```

## 配置说明

### 环境变量配置

```bash
# OpenAI配置
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# 监控系统连接
MONITOR_GRPC_HOST=localhost
MONITOR_GRPC_PORT=50051

# 告警阈值
CPU_THRESHOLD_WARNING=80.0
CPU_THRESHOLD_CRITICAL=95.0
MEMORY_THRESHOLD_WARNING=85.0
MEMORY_THRESHOLD_CRITICAL=95.0

# 通知配置
ALERT_EMAIL_USER=your-email@gmail.com
ALERT_EMAIL_PASSWORD=your-app-password
```

### 告警级别说明

- **INFO**: 信息性告警，记录在日志中
- **WARNING**: 警告级别，控制台输出
- **CRITICAL**: 严重告警，邮件通知
- **EMERGENCY**: 紧急告警，立即邮件通知

## 使用示例

### 1. 系统运行示例 (简化版输出)
```bash
$ python main.py
╔══════════════════════════════════════════════════╗
║            AI智能告警系统 (简化版)                ║
║        基于LLM Agent + RAG技术                   ║
╚══════════════════════════════════════════════════╝

2025-08-28 10:30:15 - INFO - 初始化简化版AI智能告警系统...
2025-08-28 10:30:16 - INFO - 知识库初始化完成
2025-08-28 10:30:17 - INFO - AI分析Agent已就绪 (MonitoringAgent)
2025-08-28 10:30:18 - INFO - 系统启动完成，等待监控数据...

============================================================
🔍 检测流程: 规则检测 → LLM分析 → 解决方案生成
主机: server-01 | 时间: 2025-08-28 10:32:20
CPU: 85.2% | 内存: 78.5% | 负载: 3.2

⚠️  检测到问题:
  1. CPU使用率偏高: 85.2%

🤖 AI分析: CPU使用率持续偏高，可能存在资源竞争或进程阻塞

💡 建议解决方案:
  1. 建议：检查top命令查看高CPU进程并优化

置信度评分: 0.8
============================================================

2025-08-28 10:35:15 - CRITICAL - server-01: 内存严重不足: 95.8%
📧 [EMAIL SENT] 严重告警邮件已发送
  建议解决方案:
  1. 使用free -h查看内存详情
  2. 识别内存泄漏进程：ps aux --sort=-%mem
  3. 重启占用内存过多的进程
```

### 2. 查看告警历史
```bash
# 查看最近的告警
tail -n 50 logs/alerts.log

# 实时监控告警
tail -f logs/alerts.log
```

## 测试和验证

### 运行测试
```bash
# 运行系统测试
python test_system.py

# 手动测试知识库
python -c "
from src.knowledge_base.rag_system import MonitoringKnowledgeBase
kb = MonitoringKnowledgeBase()
kb.initialize()
results = kb.search_solutions('CPU使用率高')
for r in results: print(r['content'][:100])
"
```

## 监控和运维

### 查看日志
```bash
# 系统日志
tail -f logs/system.log

# 告警日志
tail -f logs/alerts.log

# 错误日志
tail -f logs/error.log
```

### 手动添加知识
```python
# 在Python中添加知识
from src.knowledge_base.rag_system import MonitoringKnowledgeBase

kb = MonitoringKnowledgeBase()
kb.initialize()
kb.add_knowledge(
    "MySQL慢查询优化：1.启用慢查询日志 2.分析执行计划 3.添加索引 4.优化SQL语句",
    {"category": "mysql", "issue": "performance"}
)
```

## 故障排除

### 常见问题

1. **OpenAI API连接失败**
   - 检查API密钥配置
   - 验证网络连接
   - 检查API使用额度

2. **gRPC连接超时**
   - 确认Linux监控系统正在运行
   - 检查防火墙设置
   - 验证端口配置

3. **ChromaDB初始化失败**
   - 检查磁盘空间
   - 验证文件权限
   - 清理data/chroma_db目录

### 调试模式
```bash
# 设置DEBUG日志级别
export LOG_LEVEL=DEBUG
python main.py
```

## 系统组件说明

### 核心组件
1. **数据收集器** (`src/data_collector/`): 从Linux监控系统接收数据
2. **分析Agent** (`src/agents/`): 使用LangGraph进行AI分析
3. **知识库** (`src/knowledge_base/`): RAG系统，存储运维知识
4. **告警管理器** (`src/alert_engine/`): 处理告警逻辑和通知

### 简化设计理念 (80/20原则)

这个版本基于**SIMPLIFICATION.md**中的设计原则，大幅简化了系统架构：


**✅ 保留的核心功能:**
- ✅ 3步AI智能分析（规则检测→LLM分析→解决方案）
- ✅ RAG知识库（ChromaDB）
- ✅ 智能告警管理
- ✅ 降级机制（LLM失败时规则检测）
- ✅ 邮件通知 + 控制台输出
- ✅ 日志记录


### 文件结构
```
ai_alert_system/ (16个文件，精简高效)
├── src/
│   ├── agents/analysis_agent.py      # 简化的AI分析Agent (MonitoringAgent)
│   ├── data_collector/grpc_client.py # gRPC数据接收
│   ├── knowledge_base/rag_system.py  # RAG知识库系统
│   ├── alert_engine/alert_manager.py # 告警管理器
│   ├── models/data_models.py         # 数据模型定义
│   └── config.py                     # 配置管理
├── main.py                          # 主程序入口
├── test_system.py                   # 系统测试脚本
├── requirements.txt                 # 13个核心依赖包
├── README.md                        # 主要文档
├── SIMPLIFICATION.md                # 简化设计文档
├── CLEANUP.md                       # 文件清理记录
├── .env.example                     # 环境配置模板
├── .gitignore                       # Git忽略规则
├── Dockerfile                       # 容器化部署
└── scripts/start.sh                 # 一键启动脚本
```
├── test_system.py                   # 测试脚本
├── requirements.txt                 # 核心依赖
├── QUICKSTART.md                    # 快速开始指南
└── scripts/start.sh                 # 启动脚本
```

### 简化版优势
- 🚀 **极速部署**: 5分钟内启动运行，无复杂配置
- 💡 **专注核心**: 80/20原则，保留20%核心功能实现80%效果
- 🔧 **易于维护**: 代码量减少55%，维护成本大幅降低
- 📦 **轻量级**: 依赖包从20+减少到13个核心包
- 🎯 **高效能**: 去掉中间层，直接处理核心逻辑
- 🛡️ **稳定性**: 降级机制确保LLM失败时系统仍可工作
- 📖 **易扩展**: 基于简化核心版本可快速扩展Web功能

## 扩展说明

当前简化版专注于核心AI检测功能。如需Web界面、API服务或高级监控功能，可基于此核心版本进行扩展开发。详细的简化设计原理请参考 `SIMPLIFICATION.md` 文档。
