#!/bin/bash

# AI智能告警系统启动脚本 - 简化版

set -e

echo "🚀 启动简化版AI智能告警系统..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python版本 $python_version 兼容"
else
    echo "❌ 错误: 需要Python 3.8+，但当前安装的是 $python_version"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装核心依赖
echo "📥 安装依赖包..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建必要目录
mkdir -p data/chroma_db
mkdir -p logs

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 未找到.env文件，从示例复制..."
    cp .env.example .env
    echo "请编辑.env文件设置您的配置后再运行系统。"
    echo "特别是需要设置OPENAI_API_KEY"
    exit 1
fi

# 启动系统
echo "🎯 启动AI智能告警系统..."
echo "按 Ctrl+C 停止系统"
echo "========================================"
python main.py
