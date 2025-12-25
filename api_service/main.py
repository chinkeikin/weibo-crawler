"""
FastAPI 应用主入口
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .api.routes import router
from .scheduler import scheduler
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

__version__ = "1.0.0"


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

