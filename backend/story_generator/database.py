"""
Supabase database client and operations. 
Handles connection to Supabase and provides helper methods. 
FIXED: SSL errors, timeouts, retry logic. 
"""

from supabase import create_client, Client
from story_generator. config import settings
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import httpx

logger = logging.getLogger(__name__)


class Database:
    """Supabase database manager with enhanced error handling."""
    
    def __init__(self):
        """Initialize Supabase client with optimized HTTP settings."""
        
        # Create custom HTTP client with better timeout and connection settings
        # This fixes SSL and timeout errors
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,    # Connection timeout
                read=30.0,       # Read timeout (increased for large files)
                write=30.0,      # Write timeout (increased for uploads)
                pool=5.0
            ),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=50
            ),
            # Retry on connection errors
            transport=httpx.AsyncHTTPTransport(retries=2)
        )
        
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        
        logger.info("✅ Supabase client initialized with enhanced settings")
    
    # =================================
    # STORIES TABLE
    # =================================
    
    async def create_story(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new story record."""
        try:
            response = self.client.table("stories").insert(story_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Story created: {response.data[0]['id']}")
                return response. data[0]
            
            raise Exception("No data returned from insert")
            
        except Exception as e:
            logger.error(f"❌ Error creating story: {e}")
            raise
    
    async def get_story(self, story_id: str) -> Optional[Dict[str, Any]]:
        """Get story by ID."""
        try:
            response = self.client.table("stories")\
                .select("*")\
                .eq("id", story_id)\
                .execute()
            
            if response. data and len(response.data) > 0:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger. error(f"❌ Error fetching story {story_id}: {e}")
            return None
    
    async def update_story_status(
        self, 
        story_id: str, 
        status: str,
        cover_image_url: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Update story status and optional fields."""
        try:
            update_data = {
                "status": status, 
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if cover_image_url:
                update_data["cover_image_url"] = cover_image_url
            
            update_data. update(kwargs)
            
            self.client.table("stories")\
                .update(update_data)\
                .eq("id", story_id)\
                . execute()
            
            logger. info(f"✅ Story {story_id} status updated to: {status}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating story status: {e}")
            return False
    
    async def get_user_stories(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get all stories for a user."""
        try:
            response = self.client.table("stories")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"❌ Error fetching user stories: {e}")
            return []
    
    # =================================
    # SCENES TABLE
    # =================================
    # Lưu hàng loạt cảnh (scenes) vào cơ sở dữ liệu cùng một lúc.
    async def create_scenes_bulk(self, scenes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk insert scenes and return created records."""
        try:
            response = self.client.table("scenes").insert(scenes_data).execute()
            logger.info(f"✅ {len(scenes_data)} scenes created")
            return response.data or []
            
        except Exception as e:
            logger.error(f"❌ Error creating scenes: {e}")
            raise
    
    async def update_scene(self, scene_id: str, data: dict):
        """
        Update scene with image, audio URLs, and transcript. 
        
        Args:
            scene_id: Scene ID
            data: Dict with keys:  image_url, audio_url, transcript
        
        Returns:
            Updated scene record
        """
        update_data = {}
        
        # Add fields conditionally
        if data.get("image_url"):
            update_data["image_url"] = data["image_url"]
        
        if data.get("audio_url"):
            update_data["audio_url"] = data["audio_url"]
        
        if "audio_duration" in data:  
            update_data["audio_duration"] = data["audio_duration"]

        if "transcript" in data:  
            update_data["transcript"] = data["transcript"]
        
        if not update_data:
            logger.warning(f"⚠️ No data to update for scene {scene_id}")
            return None
        
        # Update (NO updated_at - not in scenes table)
        try:
            result = self.client.table("scenes").update(
                update_data
            ).eq("id", scene_id).execute()
            
            if result. data:
                logger.info(f"✅ Scene {scene_id} updated: {list(update_data.keys())}")
                return result.data[0]
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Error updating scene {scene_id}: {e}")
            return None
    
    async def get_story_scenes(self, story_id: str) -> List[Dict[str, Any]]:
        """Get all scenes for a story, ordered by scene_order."""
        try:
            response = self.client.table("scenes")\
                .select("*")\
                .eq("story_id", story_id)\
                .order("scene_order", desc=False)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"❌ Error fetching scenes for story {story_id}: {e}")
            return []
    
    # =================================
    # STORAGE (WITH RETRY LOGIC)
    # =================================
    
    async def upload_file(
        self, 
        bucket: str, 
        path: str, 
        file_data: bytes,
        content_type: str = "image/png",
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Upload file to Supabase Storage with retry logic.
        
        Args:
            bucket: Storage bucket name
            path: File path in bucket
            file_data: File bytes
            content_type: MIME type
            max_retries: Maximum retry attempts
        
        Returns:
            Public URL if successful, None if all retries failed
        """
        
        for attempt in range(1, max_retries + 1):
            try:
                # Upload file with upsert (overwrite if exists)
                upload_response = self.client.storage.from_(bucket).upload(
                    path=path,
                    file=file_data,
                    file_options={
                        "content-type": content_type,
                        "upsert": "true"  # Overwrite if file exists
                    }
                )
                
                # Get public URL
                public_url = self.client.storage.from_(bucket).get_public_url(path)
                
                if attempt > 1:
                    logger.info(f"✅ File uploaded on retry {attempt}: {path}")
                else:
                    logger.info(f"✅ File uploaded: {path}")
                
                return public_url
            
            except Exception as e:
                error_msg = str(e). lower()
                
                # Check error type
                is_ssl_error = any(keyword in error_msg for keyword in [
                    "ssl", "eof", "connection", "timeout", "reset"
                ])
                
                if is_ssl_error and attempt < max_retries:
                    # SSL/Connection error - retry with exponential backoff
                    wait_time = 2 ** attempt  # 2s, 4s, 8s
                    logger.warning(
                        f"⚠️ Upload error (attempt {attempt}/{max_retries}) for {path}: "
                        f"{str(e)[:100]}.  Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # Non-retryable error or last attempt
                    logger.error(
                        f"❌ Upload failed (attempt {attempt}/{max_retries}) for {path}: {e}"
                    )
                    
                    if attempt >= max_retries:
                        break
                    
                    # Short delay before next attempt
                    await asyncio. sleep(1)
        
        logger.error(f"❌ Upload failed after {max_retries} attempts: {path}")
        return None
    
    async def delete_file(self, bucket: str, path: str) -> bool:
        """Delete file from storage."""
        try:
            self.client.storage.from_(bucket).remove([path])
            logger.info(f"✅ File deleted: {path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting file {path}: {e}")
            return False
    
    async def list_files(self, bucket: str, folder: str = "") -> List[Dict[str, Any]]:
        """List files in a bucket folder."""
        try:
            response = self.client.storage.from_(bucket).list(folder)
            return response or []
            
        except Exception as e:
            logger.error(f"❌ Error listing files in {bucket}/{folder}: {e}")
            return []
    
    async def get_file_url(self, bucket: str, path: str) -> Optional[str]:
        """Get public URL for a file."""
        try:
            url = self.client.storage.from_(bucket).get_public_url(path)
            return url
            
        except Exception as e:
            logger.error(f"❌ Error getting URL for {path}: {e}")
            return None
    
    # =================================
    # HEALTH CHECK
    # =================================
    
    async def health_check(self) -> bool:
        """Check database connection."""
        try:
            # Simple query to test connection
            response = self.client.table("stories").select("id").limit(1).execute()
            logger.info("✅ Database health check passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False
    
    async def close(self):
        """Close HTTP client connections."""
        try:
            if hasattr(self, 'http_client'):
                await self.http_client.aclose()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"⚠️ Error closing connections: {e}")


    # =================================
    # PROGRESS TRACKING FUNCTIONS
    # Các functions để track progress của story generation
    # =================================
    async def update_story_progress(self, story_id: str, completed: int, total: int):
        """
        Cập nhật progress của story. 
        
        Args:
            story_id: ID của story
            completed: Số scenes đã hoàn thành
            total: Tổng số scenes
        """
        response = self.client.table("stories").update({
            "scenes_completed": completed,
            "scenes_total": total,
            #"updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", story_id).execute()
        
        logger.info(f"✅ Story {story_id} progress: {completed}/{total}")
        return response. data[0] if response.data else None


    async def update_scene_status(
        self, 
        scene_id: str, 
        status: str, 
        error_message: str = None
    ):
        """
        Cập nhật status của scene.
        
        Args:
            scene_id: ID của scene
            status: 'pending' | 'generating' | 'completed' | 'failed'
            error_message: Lỗi nếu có
        """
        update_data = {
            "status": status,
            #"updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if status == "generating":
            update_data["started_at"] = datetime.now(timezone.utc).isoformat()
        elif status == "completed":
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        if error_message:
            update_data["error_message"] = error_message
        
        response = self.client.table("scenes").update(
            update_data
        ).eq("id", scene_id).execute()
        
        logger.info(f"✅ Scene {scene_id} status: {status}")
        return response.data[0] if response. data else None

    
    async def get_completed_scenes(self, story_id: str):
        """
        Lấy tất cả scenes đã hoàn thành. 
        
        Returns:
            List các scenes có status='completed'
        """
        response = self.client.table("scenes") \
            .select("*") \
            .eq("story_id", story_id) \
            .eq("status", "completed") \
            .order("scene_order") \
            .execute()
        
        return response.data if response.data else []


    async def get_scene_by_order(self, story_id: str, scene_order: int):
        """
        Lấy scene theo số thứ tự.
        
        Args:
            story_id: ID của story
            scene_order: Thứ tự scene (1-6)
        """
        response = self.client.table("scenes") \
            .select("*") \
            .eq("story_id", story_id) \
            .eq("scene_order", scene_order) \
            .execute()
        
        return response. data[0] if response.data else None

    
    async def get_story_with_progress(self, story_id: str) -> Optional[dict]:
        """
        Lấy story KÈM THEO thông tin progress.
        
        TRẢ VỀ:
        - Tất cả fields của story
        - Thêm field "progress_percentage" (tính từ scenes_completed/scenes_total)
        
        DÙNG CHO:
        - API 2: Cần trả về % để frontend hiển thị progress bar
        
        VÍ DỤ OUTPUT:
        {
            "id": "story-123",
            "title": "Max và Rừng Phép Thuật",
            "status": "generating",
            "scenes_completed": 3,
            "scenes_total": 6,
            "progress_percentage": 50.0  ← Field này được TÍNH thêm
        }
        
        Args:
            story_id: ID của story
        
        Returns:
            Story record + progress_percentage
        """
        try:
            # Lấy story bình thường
            story = await self.get_story(story_id)
            
            if not story:
                return None
            
            # Tính progress percentage
            completed = story. get("scenes_completed", 0)
            total = story.get("scenes_total", 6)
            percentage = (completed / total * 100) if total > 0 else 0
            
            # Thêm field mới vào story
            story["progress_percentage"] = round(percentage, 1)
            
            return story
            
        except Exception as e:
            logger.error(f"❌ Failed to get story with progress: {e}")
            return None
# Global database instance
db = Database()