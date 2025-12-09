"""
Background Task Manager. 

Quản lý các async tasks chạy trong background. 

CÔNG DỤNG:
- Khi API 1 trả về scene 1, task manager sẽ chạy worker tạo scenes 2-6
- Task chạy KHÔNG ĐỒNG BỘ (async) → không block API
- Có thể cancel task nếu cần
"""

import asyncio
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """
    Quản lý background tasks. 
    
    CÁCH DÙNG:
    ```python
    # Bắt đầu task
    task_manager. start_task("story-123", my_async_function())
    
    # Kiểm tra task
    if task_manager.is_running("story-123"):
        print("Đang chạy...")
    
    # Hủy task
    task_manager.cancel_task("story-123")
    ```
    """
    
    def __init__(self):
        """Khởi tạo manager với dictionary rỗng để lưu tasks."""
        self.tasks: Dict[str, asyncio.Task] = {}
        logger.info("🚀 Background Task Manager initialized")
    
    
    def start_task(self, story_id: str, coroutine) -> asyncio.Task:
        """
        Bắt đầu một background task.
        
        FLOW:
        1. Hủy task cũ nếu có (tránh duplicate)
        2. Tạo task mới từ coroutine
        3.  Lưu task vào dictionary
        4. Add callback để cleanup khi done
        
        Args:
            story_id: ID của story (dùng làm key)
            coroutine: Async function cần chạy (ví dụ: generate_scenes())
        
        Returns:
            asyncio.Task object
        
        Example:
            async def my_worker():
                await asyncio.sleep(10)
                print("Done!")
            
            task = task_manager.start_task("story-123", my_worker())
        """
        # Hủy task cũ nếu đang chạy (tránh duplicate)
        self.cancel_task(story_id)
        
        # Tạo task mới từ coroutine
        task = asyncio.create_task(coroutine)
        
        # Lưu vào dictionary (key = story_id)
        self.tasks[story_id] = task
        
        logger.info(f"🚀 Started background task: {story_id}")
        
        # Thêm callback để cleanup khi task xong
        task.add_done_callback(lambda t: self._on_task_done(story_id, t))
        
        return task
    
    
    def get_task(self, story_id: str) -> Optional[asyncio.Task]:
        """
        Lấy task theo story_id.
        
        DÙNG ĐỂ:
        - Kiểm tra task có tồn tại không
        - Check status của task (done/running/cancelled)
        
        Args:
            story_id: ID của story
        
        Returns:
            Task object hoặc None nếu không tìm thấy
        """
        return self.tasks.get(story_id)
    
    
    def cancel_task(self, story_id: str) -> bool:
        """
        Hủy một task đang chạy.
        
        DÙNG KHI:
        - User muốn cancel generation
        - Cần restart generation
        - Cleanup resources
        
        Args:
            story_id: ID của story
        
        Returns:
            True nếu cancel thành công, False nếu task không tồn tại
        """
        task = self.tasks.get(story_id)
        
        # Nếu task tồn tại VÀ chưa done
        if task and not task.done():
            task.cancel()
            logger.info(f"❌ Cancelled task: {story_id}")
            return True
        
        return False
    
    
    def is_running(self, story_id: str) -> bool:
        """
        Kiểm tra task có đang chạy không.
        
        Returns:
            True = đang chạy, False = không chạy/không tồn tại
        """
        task = self.tasks.get(story_id)
        return task is not None and not task.done()
    
    
    def _on_task_done(self, story_id: str, task: asyncio.Task):
        """
        Callback khi task hoàn thành (internal function).
        
        TỰ ĐỘNG GỌI khi:
        - Task chạy xong (success)
        - Task bị cancel
        - Task raise exception
        
        NHIỆM VỤ:
        - Log kết quả
        - Cleanup task khỏi dictionary
        """
        try:
            # Kiểm tra có exception không
            exception = task.exception()
            if exception:
                logger.error(f"❌ Task failed [{story_id}]: {exception}")
            else:
                logger. info(f"✅ Task completed [{story_id}]")
                
        except asyncio.CancelledError:
            logger.info(f"⚠️ Task cancelled [{story_id}]")
            
        finally:
            # Cleanup: Xóa task khỏi dictionary
            if story_id in self.tasks:
                del self.tasks[story_id]
    
    
    def cleanup_done_tasks(self):
        """
        Xóa tất cả tasks đã hoàn thành (để tiết kiệm memory).
        
        GỌI ĐỊNH KỲ (ví dụ: mỗi giờ) để cleanup.
        """
        # Tìm các tasks đã done
        done_stories = [
            sid for sid, task in self.tasks.items() 
            if task.done()
        ]
        
        # Xóa khỏi dictionary
        for sid in done_stories:
            del self.tasks[sid]
        
        if done_stories:
            logger.info(f"🧹 Cleaned up {len(done_stories)} done tasks")
    
    
    def get_stats(self) -> dict:
        """
        Lấy thống kê về tasks (để monitoring).
        
        Returns:
            {
                'total': 5,      # Tổng số tasks đang track
                'running': 3,    # Số tasks đang chạy
                'done': 2        # Số tasks đã xong (chưa cleanup)
            }
        """
        total = len(self.tasks)
        running = sum(1 for t in self.tasks.values() if not t.done())
        done = total - running
        
        return {
            'total': total,
            'running': running,
            'done': done
        }


# ========================================
# GLOBAL INSTANCE
# Import từ đây: from workers import task_manager
# ========================================
task_manager = BackgroundTaskManager()