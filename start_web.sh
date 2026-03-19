#!/bin/bash

# OpenClaw Drug Web 启动脚本

echo "🚀 启动 OpenClaw Drug Web 界面..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "🔧 安装依赖..."
pip install -r web/requirements.txt
pip install -r requirements.txt

# 设置环境变量
export PYTHONPATH=$(pwd)
export FLASK_APP=web/app.py

echo ""
echo "🌐 服务即将启动，请访问: http://localhost:7890"
echo "🧪 功能模块:"
echo "   • 文献分析 - 自动搜索和分析学术文献"
echo "   • ADMET预测 - 预测化合物成药性"
echo "   • 虚拟筛选 - 自动化分子对接和化合物筛选"
echo ""
echo "⚠️  首次启动会自动下载AI模型，可能需要几分钟时间。"
echo "按 Ctrl+C 停止服务。"
echo ""

# 启动服务
python web/app.py --host 0.0.0.0 --port 7890