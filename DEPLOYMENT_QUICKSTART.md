# 🚀 FaaS 系统部署快速开始

## 📦 本地开发（推荐）

### 使用 Docker Compose（最简单）

**Windows:**
```bash
# 双击运行
start.bat
```

**Linux/Mac:**
```bash
# 添加执行权限
chmod +x start.sh

# 运行脚本
./start.sh
```

**手动启动:**
```bash
# 启动所有服务
docker-compose up -d

# 初始化数据库
docker-compose exec faas-app python init_db.py

# 查看日志
docker-compose logs -f faas-app

# 停止服务
docker-compose down
```

访问: http://localhost:8000

---

## ☁️ 云端部署

### 方案 1: Railway（推荐新手）

1. 访问 [Railway](https://railway.app/)
2. 点击 "New Project"
3. 连接 GitHub 仓库
4. Railway 会自动识别并配置
5. 添加 MySQL 服务
6. 部署！

✅ **优点**: 自动配置，免费额度充足

---

### 方案 2: Render

1. 访问 [Render](https://render.com/)
2. 点击 "New +"
3. 选择 "Web Service"
4. 连接 GitHub 仓库
5. 配置构建命令
6. 添加 MySQL 数据库
7. 部署！

✅ **优点**: 免费计划慷慨，部署快速

---

### 方案 3: Heroku

```bash
# 安装 Heroku CLI
# macOS
brew tap heroku/brew && brew install heroku

# 登录
heroku login

# 创建应用
heroku create your-faas-app

# 添加数据库
heroku addons:create jawsdb:kitefin

# 部署
git push heroku main
```

✅ **优点**: 成熟稳定，插件丰富

---

## 🔧 常见问题

### Q: Docker 部署失败？
A: 确保已安装 Docker 并正在运行

### Q: 数据库连接失败？
A: 检查环境变量配置，确认数据库服务已启动

### Q: 代码执行失败？
A: 云平台可能不支持 Docker-in-Docker，需要使用支持的平台

### Q: 内存不足？
A: 减小 Worker 数量和内存限制

---

## 📚 详细文档

完整的部署指南请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 🎯 推荐配置

### 本地开发
- Worker 数量: 3
- 内存限制: 256MB
- 数据库: MySQL 8.0

### 云端部署（免费计划）
- Worker 数量: 1-2
- 内存限制: 128-256MB
- 数据库: 云平台提供的 MySQL

### 生产环境
- Worker 数量: 5-10
- 内存限制: 512MB-1GB
- 数据库: 托管 MySQL 服务
- 负载均衡: Nginx / 云平台 LB

---

## 🆘 获取帮助

- 查看日志: `docker-compose logs -f faas-app`
- 健康检查: 访问 `http://your-domain/health`
- API 文档: 访问 `http://your-domain/docs`

---

祝部署顺利！🎉