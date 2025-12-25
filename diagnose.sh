#!/bin/bash

# 诊断脚本 - 在 Ubuntu 服务器上运行

echo "================================"
echo "API 服务诊断脚本"
echo "================================"
echo ""

PROJECT_DIR="/home/jayden/weibo-crawler"
cd "$PROJECT_DIR" || exit 1

echo "1. 检查项目目录..."
echo "   当前目录: $(pwd)"
echo ""

echo "2. 检查虚拟环境..."
if [ -d "venv" ]; then
    echo "   ✓ 虚拟环境存在"
    echo "   Python 版本: $(venv/bin/python --version)"
else
    echo "   ✗ 虚拟环境不存在"
    exit 1
fi
echo ""

echo "3. 检查依赖..."
venv/bin/pip list | grep -E "(fastapi|uvicorn|weibo)" || echo "   部分依赖可能缺失"
echo ""

echo "4. 检查配置文件..."
if [ -f "config.json" ]; then
    echo "   ✓ config.json 存在"
    echo "   文件大小: $(stat -f%z config.json 2>/dev/null || stat -c%s config.json) 字节"
else
    echo "   ✗ config.json 不存在"
    echo "   请确保配置文件存在"
fi
echo ""

echo "5. 检查 Python 模块导入..."
venv/bin/python -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')

print('   测试导入模块...')
try:
    import api_service
    print('   ✓ api_service 导入成功')
except Exception as e:
    print(f'   ✗ api_service 导入失败: {e}')
    import traceback
    traceback.print_exc()

try:
    from api_service import main
    print('   ✓ api_service.main 导入成功')
except Exception as e:
    print(f'   ✗ api_service.main 导入失败: {e}')
    import traceback
    traceback.print_exc()

try:
    import weibo
    print('   ✓ weibo 导入成功')
except Exception as e:
    print(f'   ✗ weibo 导入失败: {e}')
    import traceback
    traceback.print_exc()

try:
    from api_service.config_manager import config_manager
    print('   ✓ config_manager 导入成功')
except Exception as e:
    print(f'   ✗ config_manager 导入失败: {e}')
    import traceback
    traceback.print_exc()
"
echo ""

echo "6. 检查服务日志..."
if [ -f "/var/log/syslog" ]; then
    echo "   最近的服务日志:"
    sudo journalctl -u weibo-crawler-api -n 20 --no-pager || echo "   无法读取日志"
else
    echo "   检查本地日志..."
    if [ -f "log/api_service.log" ]; then
        tail -20 log/api_service.log
    else
        echo "   日志文件不存在"
    fi
fi
echo ""

echo "7. 尝试手动启动（查看详细错误）..."
echo "   执行: cd $PROJECT_DIR && source venv/bin/activate && python run_api.py"
echo ""

echo "================================"
echo "诊断完成"
echo "================================"

