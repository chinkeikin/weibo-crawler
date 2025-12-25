"""
定时任务调度器
"""
import logging
import threading
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Optional
from .config_manager import config_manager
from .crawler_service import crawler_service

logger = logging.getLogger(__name__)


class CrawlerScheduler:
    """爬虫调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.job_id = "weibo_crawler_job"
        self.is_running = False
    
    def start(self):
        """启动调度器"""
        if not self.is_running:
            try:
                # 从配置读取间隔（如果有的话）
                # 默认30分钟
                interval = 30  # 分钟
                
                # 添加定时任务
                self.scheduler.add_job(
                    self._crawl_all_users,
                    trigger=IntervalTrigger(minutes=interval),
                    id=self.job_id,
                    replace_existing=True,
                    max_instances=1,
                )
                
                self.scheduler.start()
                self.is_running = True
                logger.info(f"调度器已启动，爬取间隔: {interval} 分钟")
            except Exception as e:
                logger.error(f"启动调度器失败: {e}")
                # 调度器启动失败不影响 API 服务
    
    def stop(self):
        """停止调度器"""
        if self.is_running:
            try:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("调度器已停止")
            except Exception as e:
                logger.error(f"停止调度器失败: {e}")
    
    def update_interval(self, interval: int):
        """
        更新爬取间隔
        
        Args:
            interval: 新的间隔时间（分钟）
        """
        if self.is_running:
            try:
                self.scheduler.reschedule_job(
                    self.job_id,
                    trigger=IntervalTrigger(minutes=interval)
                )
                logger.info(f"爬取间隔已更新为: {interval} 分钟")
            except Exception as e:
                logger.error(f"更新爬取间隔失败: {e}")
    
    def _crawl_all_users(self):
        """爬取所有用户的微博（在后台线程中执行）"""
        def run_crawl():
            try:
                # 检查是否有正在运行的任务
                running_task = crawler_service.get_running_task()
                if running_task:
                    logger.info("已有任务正在运行，跳过本次定时任务")
                    return
                
                # 获取所有用户
                config = config_manager.get_config()
                user_id_list = config.get('user_id_list', [])
                
                # 如果是文件路径，读取文件
                if isinstance(user_id_list, str):
                    import os
                    if os.path.exists(user_id_list):
                        with open(user_id_list, 'r', encoding='utf-8') as f:
                            user_ids = [line.strip() for line in f if line.strip()]
                    else:
                        user_ids = []
                else:
                    user_ids = user_id_list if isinstance(user_id_list, list) else []
                
                if not user_ids:
                    logger.info("没有需要爬取的用户")
                    return
                
                logger.info(f"定时任务开始爬取 {len(user_ids)} 个用户")
                
                # 触发爬取
                task_id = crawler_service.crawl_users(user_ids)
                logger.info(f"定时任务已提交，任务ID: {task_id}")
            
            except Exception as e:
                logger.error(f"定时任务执行失败: {e}")
        
        # 在后台线程中执行
        thread = threading.Thread(target=run_crawl, daemon=True)
        thread.start()


# 全局调度器实例
scheduler = CrawlerScheduler()

