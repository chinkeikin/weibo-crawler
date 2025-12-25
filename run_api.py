#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动 API 服务
"""
import uvicorn
import os
import sys

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "::")
    port = int(os.getenv("APP_PORT", "8000"))
    
    # 添加当前目录到 Python 路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    uvicorn.run(
        "api_service.main:app",
        host=host,
        port=port,
        reload=False
    )

