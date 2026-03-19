# FaaS 系统云部署指南

## 🚀 支持的云平台

本项目支持部署到以下云平台：

- [Heroku](#heroku-部署)
- [Railway](#railway-部署)
- [Render](#render-部署)
- [Fly.io](#flyio-部署)
- [自建服务器](#自建服务器部署)

---

## 🔑 前置要求

### 必需服务

1. **MySQL 数据库**（云平台提供或自建）
2. **Docker**（代码执行需要）
3. **Python 3.10+**

### 环境变量

确保配置以下环境变量：

```bash
# MySQL 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=faas_system

# FaaS 系统配置
WORKER_COUNT=3
MAX_USER_CONCURRENT=5

# Docker 配置
DOCKER_IMAGE=python:3.10-alpine
DOCKER_CPU_LIMIT=1
DOCKER_MEMORY_LIMIT=256m

# 代码执行配置
MAX_CODE_SIZE=10240
DEFAULT_TIMEOUT=10
MAX_TIMEOUT=300

# CORS 配置
CORS_ORIGINS=*
```

---

## 📦 Heroku 部署

### 1. 安装 Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows
# 下载: https://devcenter.heroku.com/articles/heroku-cli

# Linux
curl https://cli-assets.heroku.com/install.sh | sh
```

### 2. 登录 Heroku

```bash
heroku login
```

### 3. 创建应用

```bash
heroku create your-faas-app
```

### 4. 添加 MySQL 插件

```bash
heroku addons:create jawsdb:kitefin
```

### 5. 配置环境变量

```bash
heroku config:set WORKER_COUNT=3
heroku config:set MAX_USER_CONCURRENT=5
heroku config:set CORS_ORIGINS=*
```

### 6. 部署

```bash
git push heroku main
```

### 7. 查看日志

```bash
heroku logs --tail
```

---

## 🚂 Railway 部署

### 1. 登录 Railway

```bash
npm install -g @railway/cli
railway login
```

### 2. 创建项目

```bash
railway init
```

### 3. 添加 MySQL 服务

```bash
railway add mysql
```

### 4. 部署

```bash
railway up
```

### 5. 查看日志

```bash
railway logs
```

**注意**：Railway 会自动提供以下环境变量：
- `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`

---

## 🎨 Render 部署

### 1. 准备项目

```bash
# 确保 .gitignore 不包含 .env
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. 登录 Render

访问 [Render Dashboard](https://dashboard.render.com/)

### 3. 创建 Web Service

1. 点击 "New +"
2. 选择 "Web Service"
3. 连接 GitHub 仓库
4. 配置构建和启动命令

### 4. 配置环境变量

在 Render Dashboard 中添加环境变量

### 5. 添加 PostgreSQL/MySQL

创建一个新的数据库服务

---

## ✈️ Fly.io 部署

### 1. 安装 Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
```

### 2. 登录

```bash
flyctl auth login
```

### 3. 初始化应用

```bash
flyctl init
```

### 4. 创建 fly.toml

```toml
app = "your-faas-app"
primary_region = "iad"

[env]
  PORT = "8000"
  WORKER_COUNT = "3"
  MAX_USER_CONCURRENT = "5"

[build]
  dockerfile = "Dockerfile"

[[services]]
  protocol = "tcp"
  internal_port = 8000

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [services.concurrency]
    type = "connections"
    hard_limit = 25
    soft_limit = 20
```

### 5. 部署

```bash
flyctl deploy
```

---

## 🖥️ 自建服务器部署

### 1. 系统要求

- Ubuntu 20.04+ / CentOS 8+
- Python 3.10+
- Docker
- MySQL 8.0+

### 2. 安装依赖

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 安装 Python 3.10
sudo apt update
sudo apt install python3.10 python3.10-venv

# 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
nano .env
```

### 4. 初始化数据库

```bash
python init_db.py
```

### 5. 使用 Gunicorn 启动

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 300
```

### 6. 使用 Systemd（推荐）

创建 `/etc/systemd/system/faas.service`：

```ini
[Unit]
Description=FaaS System
After=network.target mysql.service

[Service]
Type=simple
User=faas
WorkingDirectory=/opt/faas-system
Environment="PATH=/opt/faas-system/venv/bin"
ExecStart=/opt/faas-system/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 300
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable faas
sudo systemctl start faas
sudo systemctl status faas
```

---

## 🔧 Docker 部署

### 1. 创建 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    docker.io \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建 runtime 目录
RUN mkdir -p /app/runtime

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 构建镜像

```bash
docker build -t faas-system .
```

### 3. 运行容器

```bash
docker run -d \
  --name faas-system \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --env-file .env \
  faas-system
```

---

## 🔍 健康检查

添加健康检查端点到 `app/main.py`：

```python
@app.get("/health")
async def health():
    """健康检查"""
    try:
        # 检查数据库连接
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        # 检查 Docker
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        
        return {
            "status": "healthy",
            "database": "connected",
            "docker": "available"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

---

## 📊 监控和日志

### Heroku

```bash
# 查看日志
heroku logs --tail

# 查看指标
heroku ps
```

### Railway

```bash
# 查看日志
railway logs

# 查看指标
railway status
```

### Render

- 访问 Render Dashboard 查看日志和指标

---

## ⚠️ 注意事项

### 1. Docker 权限

云平台通常不支持在容器内运行 Docker，需要：
- 使用支持 Docker-in-Docker 的平台（如 Fly.io）
- 或者使用无 Docker 执行方式

### 2. 资源限制

根据云平台调整配置：

```bash
# 低配云平台
WORKER_COUNT=1
MAX_USER_CONCURRENT=2
DOCKER_MEMORY_LIMIT=128m

# 高配云平台
WORKER_COUNT=5
MAX_USER_CONCURRENT=10
DOCKER_MEMORY_LIMIT=512m
```

### 3. 数据库连接池

云平台可能需要调整连接池配置：

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,  # 减小连接池大小
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

---

## 🚀 快速部署推荐

### 最简单：Railway
- 自动数据库配置
- 免费额度充足
- 支持环境变量自动注入

### 最稳定：Heroku
- 成熟稳定
- 丰富的插件生态
- 良好的文档支持

### 最便宜：Render
- 免费计划慷慨
- 支持持久化存储
- 部署速度快

---

## 📞 故障排查

### 常见问题

1. **数据库连接失败**
   - 检查环境变量配置
   - 确认数据库服务已启动
   - 检查防火墙规则

2. **Docker 执行失败**
   - 确认云平台支持 Docker-in-Docker
   - 检查 Docker 守护进程状态
   - 验证权限配置

3. **内存不足**
   - 减小 Worker 数量
   - 降低 Docker 内存限制
   - 升级云服务计划

---

## 🔐 安全建议

1. **使用环境变量**：不要在代码中硬编码密码
2. **启用 HTTPS**：使用云平台提供的 SSL 证书
3. **配置 CORS**：限制跨域请求来源
4. **定期更新**：及时更新依赖包和系统
5. **监控日志**：定期检查异常日志

---

部署完成后，访问您的云平台提供的 URL 即可使用 FaaS 系统！🎉