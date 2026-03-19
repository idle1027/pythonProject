@echo off
REM FaaS 系统快速启动脚本 (Windows)

echo 🚀 启动 FaaS 系统...

REM 检查 Docker 是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装，请先安装 Docker Desktop
    pause
    exit /b 1
)

REM 检查 Docker Compose 是否安装
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose 未安装，请先安装 Docker Compose
    pause
    exit /b 1
)

REM 检查 .env 文件
if not exist .env (
    echo 📝 创建 .env 文件...
    copy .env.example .env
    echo ✅ .env 文件已创建，请根据需要修改配置
)

REM 检查 Docker 是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)

REM 停止现有容器
echo 🛑 停止现有容器...
docker-compose down 2>nul

REM 构建镜像
echo 🔨 构建 Docker 镜像...
docker-compose build

REM 启动服务
echo 🎬 启动服务...
docker-compose up -d

REM 等待 MySQL 启动
echo ⏳ 等待 MySQL 启动...
timeout /t 10 /nobreak >nul

REM 初始化数据库
echo 🗄️ 初始化数据库...
docker-compose exec faas-app python init_db.py

echo.
echo ✅ FaaS 系统启动成功！
echo.
echo 📊 访问地址:
echo    - Web 界面: http://localhost:8000
echo    - API 文档: http://localhost:8000/docs
echo    - 健康检查: http://localhost:8000/health
echo.
echo 📝 查看日志:
echo    docker-compose logs -f faas-app
echo.
echo 🛑 停止服务:
echo    docker-compose down
echo.

pause