"""
Workers package - Quản lý background tasks. 

Background tasks dùng để:
- Tạo scenes 2-6 mà KHÔNG BLOCK API response
- User nhận scene 1 ngay, các scene còn lại tạo sau
"""

from story_generator.workers.task_manager import task_manager

__all__ = ["task_manager"]