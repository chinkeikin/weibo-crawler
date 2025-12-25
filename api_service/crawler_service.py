"""
爬虫服务 - 调用 weibo.py 的爬虫逻辑
"""
import logging
import threading
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import weibo
from .config_manager import config_manager

logger = logging.getLogger(__name__)


class CrawlerService:
    """爬虫服务"""
    
    def __init__(self, max_workers: int = 1):
        """
        初始化爬虫服务
        
        Args:
            max_workers: 最大并发爬取数（建议为1，避免被封）
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.current_task_id: Optional[str] = None
        self.task_lock = threading.Lock()
        self.tasks: Dict[str, Dict[str, Any]] = {}
    
    def crawl_users(self, user_ids: List[str], task_id: Optional[str] = None) -> str:
        """
        爬取指定用户的微博
        
        Args:
            user_ids: 用户ID列表
            task_id: 任务ID（可选，不提供则自动生成）
            
        Returns:
            任务ID
        """
        import uuid
        
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # 检查是否有正在运行的任务
        with self.task_lock:
            if self.current_task_id and self.current_task_id in self.tasks:
                task = self.tasks[self.current_task_id]
                if task['state'] in ['PENDING', 'PROGRESS']:
                    raise RuntimeError(f"已有任务正在运行: {self.current_task_id}")
            
            # 创建新任务
            self.tasks[task_id] = {
                'state': 'PENDING',
                'progress': 0,
                'user_ids': user_ids,
                'result': None,
                'error': None
            }
            self.current_task_id = task_id
        
        # 提交任务
        self.executor.submit(self._run_crawl_task, task_id, user_ids)
        
        return task_id
    
    def _run_crawl_task(self, task_id: str, user_ids: List[str]):
        """
        执行爬取任务
        
        Args:
            task_id: 任务ID
            user_ids: 用户ID列表
        """
        try:
            with self.task_lock:
                self.tasks[task_id]['state'] = 'PROGRESS'
                self.tasks[task_id]['progress'] = 0
            
            # 获取配置
            config = config_manager.get_config()
            
            # 更新 user_id_list
            # 如果配置中是文件路径，需要处理
            if isinstance(config.get('user_id_list'), str):
                # 是文件路径，需要写入文件
                user_id_file = config['user_id_list']
                with open(user_id_file, 'w', encoding='utf-8') as f:
                    for user_id in user_ids:
                        f.write(f"{user_id}\n")
                config['user_id_list'] = user_id_file
            else:
                # 直接是列表
                config['user_id_list'] = user_ids
            
            # 处理配置重命名（兼容性）
            # 如果 weibo 模块有 handle_config_renaming 函数则调用
            if hasattr(weibo, 'handle_config_renaming'):
                weibo.handle_config_renaming(config, oldName="filter", newName="only_crawl_original")
                weibo.handle_config_renaming(config, oldName="result_dir_name", newName="user_id_as_folder_name")
            
            # 创建爬虫实例
            wb = weibo.Weibo(config)
            
            with self.task_lock:
                self.tasks[task_id]['progress'] = 50
            
            # 开始爬取
            wb.start()
            
            with self.task_lock:
                self.tasks[task_id]['progress'] = 100
                self.tasks[task_id]['state'] = 'SUCCESS'
                self.tasks[task_id]['result'] = {
                    'message': f'成功爬取 {len(user_ids)} 个用户的微博',
                    'user_ids': user_ids
                }
                if self.current_task_id == task_id:
                    self.current_task_id = None
            
            logger.info(f"任务 {task_id} 完成")
        
        except Exception as e:
            logger.exception(f"任务 {task_id} 失败: {e}")
            with self.task_lock:
                self.tasks[task_id]['state'] = 'FAILED'
                self.tasks[task_id]['error'] = str(e)
                if self.current_task_id == task_id:
                    self.current_task_id = None
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态字典，如果任务不存在返回 None
        """
        return self.tasks.get(task_id)
    
    def get_running_task(self) -> Optional[Dict[str, Any]]:
        """
        获取当前运行的任务
        
        Returns:
            任务状态字典，如果没有运行的任务返回 None
        """
        with self.task_lock:
            if self.current_task_id and self.current_task_id in self.tasks:
                task = self.tasks[self.current_task_id]
                if task['state'] in ['PENDING', 'PROGRESS']:
                    return {
                        'task_id': self.current_task_id,
                        **task
                    }
        return None


# 全局爬虫服务实例
crawler_service = CrawlerService()

