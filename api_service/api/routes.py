"""
API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel, Field
import sqlite3
import json
import os
from datetime import datetime
from ..config_manager import config_manager
from ..crawler_service import crawler_service
from .auth import verify_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 数据库路径（从 weibo.py 中获取默认路径）
DEFAULT_DB_PATH = "./weibo/weibodata.db"


# Pydantic 模型
class AddUserRequest(BaseModel):
    """添加用户请求"""
    user_ids: List[str] = Field(min_length=1, description="用户ID列表")


class DeleteUserRequest(BaseModel):
    """删除用户请求"""
    user_id: str = Field(description="用户ID")


class UpdateConfigRequest(BaseModel):
    """更新配置请求"""
    only_crawl_original: Optional[int] = Field(None, ge=0, le=1, description="是否只爬取原创微博")
    since_date: Optional[int] = Field(None, description="爬取天数（整数）或日期（yyyy-mm-dd）")
    cookie: Optional[str] = Field(None, description="Cookie")
    original_pic_download: Optional[int] = Field(None, ge=0, le=1)
    retweet_pic_download: Optional[int] = Field(None, ge=0, le=1)
    original_video_download: Optional[int] = Field(None, ge=0, le=1)
    retweet_video_download: Optional[int] = Field(None, ge=0, le=1)
    download_comment: Optional[int] = Field(None, ge=0, le=1)
    download_repost: Optional[int] = Field(None, ge=0, le=1)


class ApiResponse(BaseModel):
    """统一响应格式"""
    success: bool
    message: str
    data: Optional[dict] = None


def get_db_path() -> str:
    """获取数据库路径"""
    config = config_manager.get_config()
    # 从配置中获取数据库路径（如果有的话）
    # 默认使用 weibo/weibodata.db
    return DEFAULT_DB_PATH


# ========== 查询接口（无需认证） ==========

@router.get("/weibos", summary="查询微博内容")
async def get_weibos(
    user_ids: Optional[str] = Query(None, description="用户ID列表，逗号分隔"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="返回数量限制")
):
    """
    查询微博内容
    
    Args:
        user_ids: 用户ID列表，逗号分隔，为空则查询所有
        limit: 返回数量限制
        
    Returns:
        微博内容列表
    """
    try:
        db_path = get_db_path()
        
        if not os.path.exists(db_path):
            return ApiResponse(
                success=True,
                message="数据库不存在，暂无数据",
                data={"weibos": []}
            )
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询
        query = "SELECT * FROM weibo WHERE 1=1"
        params = []
        
        if user_ids:
            user_id_list = [uid.strip() for uid in user_ids.split(",") if uid.strip()]
            if user_id_list:
                placeholders = ",".join(["?"] * len(user_id_list))
                query += f" AND user_id IN ({placeholders})"
                params.extend(user_id_list)
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        weibos = []
        for row in rows:
            weibo_dict = dict(row)
            # 处理日期时间字段
            for key, value in weibo_dict.items():
                if isinstance(value, str) and 'T' in value:
                    try:
                        # 尝试解析日期时间
                        pass
                    except:
                        pass
            weibos.append(weibo_dict)
        
        return ApiResponse(
            success=True,
            message="查询成功",
            data={"weibos": weibos, "count": len(weibos)}
        )
    
    except Exception as e:
        logger.error(f"查询微博失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.get("/users", summary="查询用户列表")
async def get_users():
    """
    查询已配置的用户列表
    
    Returns:
        用户列表
    """
    try:
        config = config_manager.get_config()
        user_id_list = config.get('user_id_list', [])
        
        # 如果是文件路径，读取文件
        if isinstance(user_id_list, str):
            if os.path.exists(user_id_list):
                with open(user_id_list, 'r', encoding='utf-8') as f:
                    user_ids = [line.strip() for line in f if line.strip()]
            else:
                user_ids = []
        else:
            user_ids = user_id_list if isinstance(user_id_list, list) else []
        
        return ApiResponse(
            success=True,
            message="查询成功",
            data={"users": user_ids, "count": len(user_ids)}
        )
    
    except Exception as e:
        logger.error(f"查询用户列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.get("/config", summary="查询系统配置")
async def get_config():
    """
    查询系统配置
    
    Returns:
        系统配置
    """
    try:
        config = config_manager.get_config()
        # 隐藏敏感信息
        safe_config = config.copy()
        if 'cookie' in safe_config:
            cookie = safe_config['cookie']
            if cookie and cookie != "your cookie":
                safe_config['cookie'] = cookie[:10] + "..." if len(cookie) > 10 else "***"
        
        return ApiResponse(
            success=True,
            message="查询成功",
            data={"config": safe_config}
        )
    
    except Exception as e:
        logger.error(f"查询配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


# ========== 管理接口（需要认证） ==========

@router.post("/users/add", summary="添加用户", dependencies=[Depends(verify_token)])
async def add_users(request: AddUserRequest):
    """
    添加微博用户并立即爬取
    
    Args:
        request: 用户ID列表
        
    Returns:
        添加结果
    """
    try:
        # 获取当前配置
        config = config_manager.get_config()
        current_user_ids = config.get('user_id_list', [])
        
        # 如果是文件路径，读取文件
        if isinstance(current_user_ids, str):
            user_id_file = current_user_ids
            if os.path.exists(user_id_file):
                with open(user_id_file, 'r', encoding='utf-8') as f:
                    existing_ids = [line.strip() for line in f if line.strip()]
            else:
                existing_ids = []
                # 确保目录存在
                os.makedirs(os.path.dirname(user_id_file) if os.path.dirname(user_id_file) else '.', exist_ok=True)
        else:
            existing_ids = current_user_ids if isinstance(current_user_ids, list) else []
            user_id_file = None
        
        # 添加新用户（去重）
        new_ids = []
        for user_id in request.user_ids:
            if user_id not in existing_ids:
                existing_ids.append(user_id)
                new_ids.append(user_id)
        
        # 更新配置
        if user_id_file:
            with open(user_id_file, 'w', encoding='utf-8') as f:
                for user_id in existing_ids:
                    f.write(f"{user_id}\n")
        else:
            config_manager.update({'user_id_list': existing_ids})
        
        # 立即触发爬取
        task_id = crawler_service.crawl_users(request.user_ids)
        
        logger.info(f"添加用户成功: {request.user_ids}")
        
        return ApiResponse(
            success=True,
            message=f"成功添加 {len(new_ids)} 个用户，已开始爬取",
            data={
                "user_ids": request.user_ids,
                "task_id": task_id,
                "new_users": new_ids
            }
        )
    
    except Exception as e:
        logger.error(f"添加用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加失败: {str(e)}"
        )


@router.post("/users/delete", summary="删除用户", dependencies=[Depends(verify_token)])
async def delete_user(request: DeleteUserRequest):
    """
    删除微博用户
    
    Args:
        request: 用户ID
        
    Returns:
        删除结果
    """
    try:
        config = config_manager.get_config()
        current_user_ids = config.get('user_id_list', [])
        
        # 如果是文件路径，读取文件
        if isinstance(current_user_ids, str):
            user_id_file = current_user_ids
            if os.path.exists(user_id_file):
                with open(user_id_file, 'r', encoding='utf-8') as f:
                    user_ids = [line.strip() for line in f if line.strip()]
            else:
                user_ids = []
        else:
            user_ids = current_user_ids if isinstance(current_user_ids, list) else []
            user_id_file = None
        
        # 删除用户
        if request.user_id in user_ids:
            user_ids.remove(request.user_id)
            
            # 更新配置
            if user_id_file:
                with open(user_id_file, 'w', encoding='utf-8') as f:
                    for user_id in user_ids:
                        f.write(f"{user_id}\n")
            else:
                config_manager.update({'user_id_list': user_ids})
            
            logger.info(f"删除用户成功: {request.user_id}")
            
            return ApiResponse(
                success=True,
                message=f"成功删除用户 {request.user_id}",
                data={"user_id": request.user_id}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用户 {request.user_id} 不存在"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


@router.post("/config/update", summary="更新配置", dependencies=[Depends(verify_token)])
async def update_config(request: UpdateConfigRequest):
    """
    更新系统配置
    
    Args:
        request: 配置更新请求
        
    Returns:
        更新结果
    """
    try:
        updates = {}
        
        # 构建更新字典
        if request.only_crawl_original is not None:
            updates['only_crawl_original'] = request.only_crawl_original
        if request.since_date is not None:
            updates['since_date'] = request.since_date
        if request.cookie is not None:
            updates['cookie'] = request.cookie
        if request.original_pic_download is not None:
            updates['original_pic_download'] = request.original_pic_download
        if request.retweet_pic_download is not None:
            updates['retweet_pic_download'] = request.retweet_pic_download
        if request.original_video_download is not None:
            updates['original_video_download'] = request.original_video_download
        if request.retweet_video_download is not None:
            updates['retweet_video_download'] = request.retweet_video_download
        if request.download_comment is not None:
            updates['download_comment'] = request.download_comment
        if request.download_repost is not None:
            updates['download_repost'] = request.download_repost
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供要更新的配置项"
            )
        
        # 更新配置
        success = config_manager.update(updates)
        
        if success:
            logger.info(f"配置更新成功: {list(updates.keys())}")
            return ApiResponse(
                success=True,
                message=f"配置更新成功: {', '.join(updates.keys())}",
                data={"updated": updates}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="配置更新失败"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.post("/crawl/trigger", summary="手动触发爬取", dependencies=[Depends(verify_token)])
async def trigger_crawl(user_ids: Optional[str] = Query(None, description="用户ID列表，逗号分隔")):
    """
    手动触发爬取任务
    
    Args:
        user_ids: 用户ID列表，逗号分隔，为空则爬取所有用户
        
    Returns:
        触发结果
    """
    try:
        if user_ids:
            # 爬取指定用户
            user_id_list = [uid.strip() for uid in user_ids.split(",") if uid.strip()]
            if not user_id_list:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户ID列表为空"
                )
        else:
            # 爬取所有用户
            config = config_manager.get_config()
            current_user_ids = config.get('user_id_list', [])
            
            if isinstance(current_user_ids, str):
                if os.path.exists(current_user_ids):
                    with open(current_user_ids, 'r', encoding='utf-8') as f:
                        user_id_list = [line.strip() for line in f if line.strip()]
                else:
                    user_id_list = []
            else:
                user_id_list = current_user_ids if isinstance(current_user_ids, list) else []
            
            if not user_id_list:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="没有配置用户ID"
                )
        
        # 检查是否有正在运行的任务
        running_task = crawler_service.get_running_task()
        if running_task:
            return ApiResponse(
                success=False,
                message="已有任务正在运行",
                data={"running_task": running_task}
            )
        
        # 触发爬取
        task_id = crawler_service.crawl_users(user_id_list)
        
        return ApiResponse(
            success=True,
            message=f"成功触发爬取任务",
            data={
                "task_id": task_id,
                "user_ids": user_id_list
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"触发爬取失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发失败: {str(e)}"
        )


@router.get("/task/{task_id}", summary="查询任务状态")
async def get_task_status(task_id: str):
    """
    查询爬取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态
    """
    task = crawler_service.get_task_status(task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return ApiResponse(
        success=True,
        message="查询成功",
        data={"task": task}
    )


@router.get("/health", summary="健康检查")
async def health_check():
    """健康检查接口"""
    try:
        config = config_manager.get_config()
        running_task = crawler_service.get_running_task()
        
        return {
            "status": "healthy",
            "config_loaded": True,
            "has_running_task": running_task is not None,
            "running_task": running_task
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

