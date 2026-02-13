# Linux 部署指南

本文档介绍如何在 Linux 服务器上部署 Social Content Creator Platform (SCCP)。

## 📋 环境要求

### 系统要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **内存**: 至少 4GB RAM (推荐 8GB)
- **磁盘**: 至少 50GB 可用空间
- **网络**: 可访问互联网

### 软件依赖
- Docker 24.0+
- Docker Compose 2.20+
- Node.js 20+ (如不使用Docker)
- Python 3.10+ (如不使用Docker)
- Git

## 🚀 快速部署

### 方式一: Docker Compose 一键部署 (推荐)

#### 1. 安装 Docker 和 Docker Compose

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

#### 2. 克隆项目

```bash
git clone <repository-url>
cd social-content-creator
```

#### 3. 配置环境变量

```bash
# 创建环境变量文件
cat > .env << 'EOF'
# 应用配置
NODE_ENV=production
PORT=3000
API_PREFIX=/api/v1

# 数据库配置
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=sccp
POSTGRES_USER=sccp_user
POSTGRES_PASSWORD=your_secure_password_here

# MongoDB配置
MONGODB_URI=mongodb://mongodb:27017/sccp

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# JWT配置
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRES_IN=7d
JWT_REFRESH_SECRET=your-refresh-secret-key-change-this
JWT_REFRESH_EXPIRES_IN=30d

# AI服务配置
AI_SERVICE_URL=http://ai-service:8000
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# 爬虫配置
CRAWLER_TIMEOUT=30000
CRAWLER_CONCURRENT_LIMIT=3

# 日志配置
LOG_LEVEL=info

# 限流配置
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
EOF

# 设置权限
chmod 600 .env
```

#### 4. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 5. 初始化数据库

```bash
# 等待数据库启动完成
sleep 10

# 执行数据库初始化
docker-compose exec postgres psql -U sccp_user -d sccp -f /docker-entrypoint-initdb.d/init.sql
```

#### 6. 验证部署

```bash
# 检查健康状态
curl http://localhost:3000/api/v1/health

# 应该返回:
# {"success":true,"data":{"status":"healthy",...}}
```

### 方式二: 手动部署

#### 1. 安装依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 Python
sudo apt install -y python3 python3-pip python3-venv

# 安装 PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 安装 Redis
sudo apt install -y redis-server

# 安装 MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org

# 启动数据库服务
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl start mongod
sudo systemctl enable postgresql redis-server mongod
```

#### 2. 配置数据库

```bash
# 创建 PostgreSQL 用户和数据库
sudo -u postgres psql << 'EOF'
CREATE USER sccp_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE sccp OWNER sccp_user;
GRANT ALL PRIVILEGES ON DATABASE sccp TO sccp_user;
\q
EOF

# 执行初始化脚本
sudo -u postgres psql -d sccp -f db/init.sql
```

#### 3. 部署后端服务

```bash
cd src/backend

# 安装依赖
npm install --production

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库连接

# 启动服务
npm start
```

#### 4. 部署前端

```bash
cd src/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 使用 Nginx 或其他 Web 服务器部署 dist 目录
```

#### 5. 部署 AI 服务

```bash
cd src/ai

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

## 🔧 生产环境配置

### Nginx 反向代理配置

```nginx
# /etc/nginx/sites-available/sccp
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /var/www/sccp/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# 启用配置
sudo ln -s /etc/nginx/sites-available/sccp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL/TLS 配置 (Let's Encrypt)

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo systemctl enable certbot.timer
```

### 系统服务配置

创建 systemd 服务文件：

```bash
# /etc/systemd/system/sccp-backend.service
[Unit]
Description=SCCP Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=sccp
WorkingDirectory=/opt/sccp/src/backend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable sccp-backend
sudo systemctl start sccp-backend
```

## 📊 监控与日志

### 查看日志

```bash
# Docker 方式
docker-compose logs -f [service-name]

# 系统服务方式
sudo journalctl -u sccp-backend -f
```

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看系统资源
top
htop
```

### 备份策略

```bash
# 数据库备份脚本
#!/bin/bash
BACKUP_DIR="/backup/sccp"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL 备份
docker-compose exec -T postgres pg_dump -U sccp_user sccp > "$BACKUP_DIR/postgres_$DATE.sql"

# MongoDB 备份
docker-compose exec -T mongodb mongodump --out="$BACKUP_DIR/mongo_$DATE"

# Redis 备份
docker-compose exec -T redis redis-cli BGSAVE

# 压缩备份
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" -C "$BACKUP_DIR" "postgres_$DATE.sql" "mongo_$DATE"

# 清理旧备份 (保留7天)
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete
```

## 🔒 安全加固

### 1. 防火墙配置

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# 或 iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

### 2. 数据库安全

```bash
# 修改 PostgreSQL 监听地址
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/" /etc/postgresql/15/main/postgresql.conf

# 配置访问控制
sudo tee -a /etc/postgresql/15/main/pg_hba.conf << 'EOF'
# 只允许本地连接
host    sccp    sccp_user    127.0.0.1/32    scram-sha-256
host    sccp    sccp_user    ::1/128         scram-sha-256
EOF

sudo systemctl restart postgresql
```

### 3. 文件权限

```bash
# 设置项目目录权限
sudo chown -R sccp:sccp /opt/sccp
sudo chmod 600 /opt/sccp/.env
sudo chmod 600 /opt/sccp/src/backend/.env
```

## 🆘 故障排除

### 常见问题

#### 1. 数据库连接失败

```bash
# 检查 PostgreSQL 状态
sudo systemctl status postgresql

# 检查连接
psql -h localhost -U sccp_user -d sccp

# 查看日志
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

#### 2. 端口被占用

```bash
# 查看端口占用
sudo netstat -tulpn | grep :3000

# 终止进程
sudo kill -9 <PID>
```

#### 3. 内存不足

```bash
# 查看内存使用
free -h

# 添加 Swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. Docker 容器无法启动

```bash
# 查看容器日志
docker-compose logs [service-name]

# 重建容器
docker-compose down
docker-compose up -d --build
```

## 📈 扩容指南

### 水平扩展

```yaml
# docker-compose.yml 扩展配置
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### 数据库优化

```bash
# PostgreSQL 性能优化
sudo tee -a /etc/postgresql/15/main/postgresql.conf << 'EOF'
# 内存配置
shared_buffers = 1GB
effective_cache_size = 3GB
work_mem = 16MB
maintenance_work_mem = 256MB

# 连接配置
max_connections = 200

# WAL 配置
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB
EOF

sudo systemctl restart postgresql
```

## 🔄 更新部署

```bash
# 拉取最新代码
git pull origin main

# Docker 方式更新
docker-compose down
docker-compose pull
docker-compose up -d --build

# 手动方式更新
cd src/backend && git pull && npm install && pm2 restart backend
cd src/frontend && git pull && npm install && npm run build
```

## 📞 获取帮助

- 查看日志: `docker-compose logs -f`
- 检查健康: `curl http://localhost:3000/api/v1/health`
- 文档: https://docs.your-domain.com
- 问题反馈: https://github.com/your-org/sccp/issues

---

**版本**: v1.0  
**最后更新**: 2026-02-13
