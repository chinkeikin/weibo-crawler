#!/bin/bash

# 微博爬虫 API 服务 - Ubuntu 22 安装脚本

set -e  # 遇到错误立即退出

echo "================================"
echo "微博爬虫 API 服务安装程序"
echo "================================"
echo ""

# 检查是否为 root 或 sudo
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 获取实际用户（即使使用 sudo）
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(eval echo ~$REAL_USER)

# 项目目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="weibo-crawler-api"

echo "项目目录: $PROJECT_DIR"
echo "运行用户: $REAL_USER"
echo ""

# 1. 安装系统依赖
echo ">>> 1. 安装系统依赖..."
apt-get update
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    gcc \
    curl \
    sqlite3

echo "✓ 系统依赖安装完成"
echo ""

# 2. 创建虚拟环境
echo ">>> 2. 创建 Python 虚拟环境..."
cd "$PROJECT_DIR"

if [ -d "venv" ]; then
    echo "虚拟环境已存在，跳过创建"
else
    sudo -u $REAL_USER python3.11 -m venv venv
    echo "✓ 虚拟环境创建完成"
fi
echo ""

# 3. 安装 Python 依赖
echo ">>> 3. 安装 Python 依赖..."
sudo -u $REAL_USER venv/bin/pip install --upgrade pip

# 先安装原项目的依赖
echo "安装爬虫核心依赖..."
sudo -u $REAL_USER venv/bin/pip install -r requirements.txt

# 再安装 API 服务依赖
if [ -f "$PROJECT_DIR/requirements-api.txt" ]; then
    echo "安装 API 服务依赖..."
    sudo -u $REAL_USER venv/bin/pip install -r requirements-api.txt
fi

echo "✓ Python 依赖安装完成"
echo ""

# 4. 创建必要的目录
echo ">>> 4. 创建数据目录..."
mkdir -p "$PROJECT_DIR/weibo"
mkdir -p "$PROJECT_DIR/log"
chown -R $REAL_USER:$REAL_USER "$PROJECT_DIR/weibo"
chown -R $REAL_USER:$REAL_USER "$PROJECT_DIR/log"
echo "✓ 数据目录创建完成"
echo ""

# 5. 检查配置文件
echo ">>> 5. 检查配置文件..."
if [ ! -f "$PROJECT_DIR/config.json" ]; then
    echo "⚠️  未找到 config.json，请手动创建配置文件"
else
    echo "config.json 配置文件已存在"
fi
echo ""

# 6. 创建 systemd 服务文件
echo ">>> 6. 创建 systemd 服务..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Weibo Crawler API Service
After=network.target

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
Environment="APP_HOST=\${APP_HOST:-::}"
Environment="APP_PORT=\${APP_PORT:-8000}"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/run_api.py
Restart=always
RestartSec=10

# 日志配置
StandardOutput=append:$PROJECT_DIR/log/api_service.log
StandardError=append:$PROJECT_DIR/log/api_service.log

[Install]
WantedBy=multi-user.target
EOF

echo "✓ systemd 服务文件创建完成"
echo ""

# 7. 重载 systemd
echo ">>> 7. 重载 systemd..."
systemctl daemon-reload
echo "✓ systemd 重载完成"
echo ""

# 8. 设置权限
echo ">>> 8. 设置文件权限..."
chown -R $REAL_USER:$REAL_USER "$PROJECT_DIR"
chmod +x "$PROJECT_DIR/run_api.py" 2>/dev/null || true
chmod +x "$PROJECT_DIR/install.sh" 2>/dev/null || true
echo "✓ 权限设置完成"
echo ""

# 安装完成
echo "================================"
echo "✅ 安装完成！"
echo "================================"
echo ""
echo "下一步操作："
echo ""
echo "1. 配置 API Token（可选，创建 .env 文件）："
echo "   echo 'API_TOKEN=your_secret_token_here' > $PROJECT_DIR/.env"
echo ""
echo "2. 配置 config.json（如果还没有）："
echo "   nano $PROJECT_DIR/config.json"
echo ""
echo "3. 启动服务："
echo "   sudo systemctl start $SERVICE_NAME"
echo ""
echo "4. 查看服务状态："
echo "   sudo systemctl status $SERVICE_NAME"
echo ""
echo "5. 设置开机自启："
echo "   sudo systemctl enable $SERVICE_NAME"
echo ""
echo "6. 查看日志："
echo "   sudo journalctl -u $SERVICE_NAME -f"
echo "   或"
echo "   tail -f $PROJECT_DIR/log/api_service.log"
echo ""
echo "7. 访问服务："
echo "   http://localhost:8000/docs"
echo ""
echo "常用命令："
echo "  启动: sudo systemctl start $SERVICE_NAME"
echo "  停止: sudo systemctl stop $SERVICE_NAME"
echo "  重启: sudo systemctl restart $SERVICE_NAME"
echo "  状态: sudo systemctl status $SERVICE_NAME"
echo ""

