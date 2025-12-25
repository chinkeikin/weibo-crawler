"""
FastAPI 应用主入口
"""
import os
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

__version__ = "1.0.0"

# 延迟导入，避免初始化时出错
try:
    from .api.routes import router
    from .scheduler import scheduler
except Exception as e:
    logger.error(f"导入模块失败: {e}")
    import traceback
    traceback.print_exc()
    raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("=" * 50)
    logger.info(f"微博爬虫 API 服务启动 v{__version__}")
    logger.info("=" * 50)
    
    # 启动调度器（如果配置了定时任务）
    scheduler.start()
    
    yield
    
    # 关闭时
    logger.info("微博爬虫 API 服务关闭")
    scheduler.stop()


# 创建FastAPI应用
app = FastAPI(
    title="微博爬虫 API 服务",
    description="基于 weibo-crawler 的 HTTP API 服务",
    version=__version__,
    lifespan=lifespan
)

# 注册路由
app.include_router(router, prefix="/api", tags=["微博爬虫"])


@app.get("/", summary="根路径")
async def root():
    """根路径"""
    return {
        "service": "微博爬虫 API 服务",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    import os
    
    host = os.getenv("APP_HOST", "::")
    port = int(os.getenv("APP_PORT", "8000"))
    
    uvicorn.run(
        "api_service.main:app",
        host=host,
        port=port,
        reload=False
    )

