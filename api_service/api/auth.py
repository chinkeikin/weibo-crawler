"""
API 认证中间件
"""
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic_settings import BaseSettings
from typing import Optional
import os

# 定义 HTTPBearer 安全方案
security = HTTPBearer(
    scheme_name="Bearer Token",
    description="请输入 API Token（不需要加 Bearer 前缀）"
)


class APISettings(BaseSettings):
    """API 配置"""
    api_token: str = os.getenv("API_TOKEN", "change_me_in_production")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


api_settings = APISettings()


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    验证API Token
    
    Args:
        credentials: HTTP Bearer 认证凭据
        
    Raises:
        HTTPException: 认证失败
    """
    # 获取 token
    token = credentials.credentials
    
    # 验证 token
    if token != api_settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True

