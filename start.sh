#!/bin/bash

# FaaS 系统快速启动脚本

set -e

echo "🚀 启动 FaaS 系统..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "📝 创建 .env 文件..."
    cp .env.example .env
    echo "✅ .env 文件已创建，请根据需要修改配置"
fi

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose down 2>/dev/null || true

# 构建镜像
echo "🔨 构建 Docker 镜像..."
docker-compose build

# 启动服务
echo "🎬 启动服务..."
docker-compose up -d

# 等待 MySQL 启动
echo "⏳ 等待 MySQL 启动..."
sleep 10

# 初始化数据库
echo "🗄️ 初始化数据库..."
docker-compose exec faas-app python init_db.py

echo ""
echo "✅ FaaS 系统启动成功！"
echo ""
echo "📊 访问地址:"
echo "   - Web 界面: http://localhost:8000"
echo "   - API 文档: http://localhost:8000/docs"
echo "   - 健康检查: http://localhost:8000/health"
echo ""
echo "📝 查看日志:"
echo "   docker-compose logs -f faas-app"
echo ""
echo "🛑 停止服务:"
echo "   docker-compose down"
echo ""