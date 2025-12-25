#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动 API 服务
"""
import uvicorn
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    # 获取项目根目录
    project_root = Path(__file__).parent.absolute()
    
    # 确保项目根目录在 Python 路径中
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 切换到项目根目录
    os.chdir(project_root)
    
    # 设置环境变量（如果未设置）
    if "CONFIG_PATH" not in os.environ:
        config_path = project_root / "config.json"
        if config_path.exists():
            os.environ["CONFIG_PATH"] = str(config_path)
    
    host = os.getenv("APP_HOST", "::")
    port = int(os.getenv("APP_PORT", "8000"))
    
    try:
        uvicorn.run(
            "api_service.main:app",
            host=host,
            port=port,
            reload=False
        )
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

