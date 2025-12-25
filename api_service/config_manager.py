"""
配置管理器 - 读取和更新 config.json
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化配置管理器
        
        Args:
            config_path: config.json 文件路径
        """
        self.config_path = Path(config_path).expanduser().resolve()
        self._config: Optional[Dict[str, Any]] = None
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            
            logger.info(f"配置文件加载成功: {self.config_path}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取完整配置
        
        Returns:
            配置字典
        """
        if self._config is None:
            self._load_config()
        return self._config.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 "mysql_config.host"
            default: 默认值
            
        Returns:
            配置值
        """
        if self._config is None:
            self._load_config()
        
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置配置项
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
            
        Returns:
            是否成功
        """
        if self._config is None:
            self._load_config()
        
        keys = key.split('.')
        config = self._config
        
        # 导航到目标位置
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        
        return self._save_config()
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """
        批量更新配置
        
        Args:
            updates: 要更新的配置字典
            
        Returns:
            是否成功
        """
        if self._config is None:
            self._load_config()
        
        def deep_update(base: dict, updates: dict):
            """深度更新字典"""
            for key, value in updates.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    deep_update(base[key], value)
                else:
                    base[key] = value
        
        deep_update(self._config, updates)
        return self._save_config()
    
    def _save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            是否成功
        """
        try:
            # 创建备份
            backup_path = self.config_path.with_suffix('.json.bak')
            if self.config_path.exists():
                import shutil
                shutil.copy2(self.config_path, backup_path)
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=4)
            
            logger.info(f"配置文件已保存: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def reload(self):
        """重新加载配置文件"""
        self._load_config()


# 全局配置管理器实例
# 延迟初始化，避免模块导入时路径问题
_config_manager_instance = None

def _init_config_manager():
    """初始化配置管理器（延迟初始化）"""
    global _config_manager_instance
    if _config_manager_instance is None:
        import os
        # 尝试从环境变量获取路径，否则使用默认路径
        config_path = os.getenv("CONFIG_PATH", "config.json")
        _config_manager_instance = ConfigManager(config_path)
    return _config_manager_instance

# 创建一个延迟初始化的代理类
class _ConfigManagerProxy:
    """配置管理器代理，延迟初始化"""
    def __getattr__(self, name):
        return getattr(_init_config_manager(), name)
    
    def __call__(self, *args, **kwargs):
        return _init_config_manager()

# 全局实例（延迟初始化）
config_manager = _ConfigManagerProxy()

