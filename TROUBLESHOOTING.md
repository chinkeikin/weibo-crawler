# 故障排查指南

## 服务启动失败

### 查看详细错误日志

在 Ubuntu 服务器上执行：

```bash
# 1. 查看 systemd 日志（最详细）
sudo journalctl -u weibo-crawler-api -n 50 --no-pager

# 2. 查看最近的服务日志
sudo journalctl -u weibo-crawler-api --since "10 minutes ago"

# 3. 实时查看日志
sudo journalctl -u weibo-crawler-api -f
```

### 手动测试启动

```bash
cd /home/jayden/weibo-crawler

# 激活虚拟环境
source venv/bin/activate

# 手动启动（查看详细错误）
python run_api.py
```

### 运行诊断脚本

```bash
cd /home/jayden/weibo-crawler
bash diagnose.sh
```

## 常见错误及解决方案

### 错误1: ModuleNotFoundError: No module named 'api_service'

**原因**：Python 路径问题

**解决方案**：

```bash
# 确保在项目根目录
cd /home/jayden/weibo-crawler

# 检查 run_api.py 是否正确设置了路径
cat run_api.py

# 手动测试导入
source venv/bin/activate
python -c "import sys; sys.path.insert(0, '.'); import api_service"
```

### 错误2: FileNotFoundError: 配置文件不存在

**原因**：config.json 文件不存在或路径不对

**解决方案**：

```bash
# 检查文件是否存在
ls -la /home/jayden/weibo-crawler/config.json

# 如果不存在，从示例创建
# 或者确保 config.json 在项目根目录
```

### 错误3: ImportError: cannot import name 'xxx' from 'weibo'

**原因**：weibo.py 模块导入失败或依赖缺失

**解决方案**：

```bash
# 检查 weibo.py 是否存在
ls -la /home/jayden/weibo-crawler/weibo.py

# 检查依赖是否安装完整
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-api.txt

# 测试导入
python -c "import weibo; print('OK')"
```

### 错误4: Permission denied

**原因**：文件权限问题

**解决方案**：

```bash
# 确保文件有执行权限
chmod +x /home/jayden/weibo-crawler/run_api.py

# 确保目录权限正确
sudo chown -R jayden:jayden /home/jayden/weibo-crawler
```

### 错误5: Address already in use

**原因**：端口被占用

**解决方案**：

```bash
# 检查端口占用
sudo lsof -i :8000
# 或
sudo netstat -tulpn | grep 8000

# 修改端口（在 .env 或 systemd 服务文件中）
echo "APP_PORT=9000" >> .env
sudo systemctl restart weibo-crawler-api
```

## 调试步骤

### 步骤1: 检查基本环境

```bash
cd /home/jayden/weibo-crawler

# 检查 Python
source venv/bin/activate
python --version

# 检查依赖
pip list | grep fastapi
pip list | grep uvicorn
```

### 步骤2: 测试模块导入

```bash
source venv/bin/activate
python -c "
import sys
sys.path.insert(0, '/home/jayden/weibo-crawler')
try:
    import api_service
    print('✓ api_service OK')
except Exception as e:
    print(f'✗ api_service: {e}')
    import traceback
    traceback.print_exc()
"
```

### 步骤3: 测试配置文件

```bash
source venv/bin/activate
python -c "
import sys
sys.path.insert(0, '/home/jayden/weibo-crawler')
from api_service.config_manager import get_config_manager
try:
    cm = get_config_manager()
    print('✓ Config loaded:', cm.get_config().get('user_id_list'))
except Exception as e:
    print(f'✗ Config error: {e}')
    import traceback
    traceback.print_exc()
"
```

### 步骤4: 测试完整启动

```bash
cd /home/jayden/weibo-crawler
source venv/bin/activate
python run_api.py
```

## 获取帮助

如果以上方法都无法解决，请提供以下信息：

1. **完整错误日志**：
   ```bash
   sudo journalctl -u weibo-crawler-api -n 100 > error.log
   ```

2. **诊断脚本输出**：
   ```bash
   bash diagnose.sh > diagnose.log
   ```

3. **手动启动输出**：
   ```bash
   source venv/bin/activate
   python run_api.py 2>&1 | tee manual_start.log
   ```

4. **环境信息**：
   ```bash
   python --version
   pip list
   ls -la
   ```

