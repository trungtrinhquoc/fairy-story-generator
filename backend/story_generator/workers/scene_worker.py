"""
Scene Worker - Worker tạo scenes trong background. 

NHIỆM VỤ:
- Nhận scenes 2-6 từ API
- Tạo image + audio cho từng scene
- Upload lên storage
- Update database
- Update progress sau mỗi scene
"""

import asyncio
import logging
import time
from datetime import datetime
from story_generator.database import Database
from story_generator.services.image_generator import ImageGenerator
from story_generator.services.voice_generator import VoiceGenerator 

logger = logging.getLogger(__name__)


async def generate_remaining_scenes(
    story_id: str,
    scenes_data: list,      # Data từ Gemini (text + prompt)
    db_scenes: list,        # Scene records từ database
    request_params: dict,   # Parameters từ request (image_style, voice...)
    character_design: str,  # Character design từ Gemini
    background_design: str, # Background design từ Gemini
    image_gen: ImageGenerator,       # ImageGenerator instance
    voice_gen: VoiceGenerator,             # VoiceGenerator instance
    db: Database                 # Database instance
):
    """
    Worker function chạy trong background để tạo scenes 2-N.
    
    FLOW HOÀN CHỈNH:
    1. Loop qua scenes từ 2 đến 6
    2. Với mỗi scene:
       a. Update status = 'generating'
       b.  Generate image (Imagen API) - ~5s
       c. Generate audio (TTS API) - ~3s (PARALLEL với image)
       d. Upload image + audio lên Supabase Storage
       e. Update scene với URLs
       f. Update status = 'completed'
       g. Update story progress (3/6, 4/6, 5/6...)
    3. Nếu scene nào lỗi:
       - Log error
       - Mark scene status = 'failed'
       - TIẾP TỤC scene tiếp theo (không dừng toàn bộ)
    4. Sau khi hết:
       - Update story status = 'completed'
    
    PARTIAL SUCCESS:
    - Nếu scene 3 fail → vẫn tiếp tục tạo 4, 5, 6
    - User vẫn có scenes 1, 2, 4, 5, 6 (thiếu scene 3)
    - Better than losing everything! 
    
    Args:
        story_id: ID của story
        scenes_data: List data từ Gemini (text, image_prompt)
        db_scenes: List scene records từ DB (có id, scene_order...)
        request_params: Dict {image_style, voice, ...}
        character_design: Character description từ Gemini
        background_design: Background description từ Gemini
        image_gen: ImageGenerator service
        voice_gen: VoiceGenerator service
        db: Database client
    """
    
    logger.info(f"🎨 Background worker started: {story_id}")
    
    total_scenes = len(db_scenes)
    completed = 1  # Scene 1 đã tạo xong rồi (trong API 1)
    
    try:
        # Skip scene 1 (đã tạo trong API 1)
        # Chỉ tạo scenes từ 2 trở đi
        remaining = list(zip(scenes_data[1:], db_scenes[1:]))
        
        # Loop qua từng scene
        for scene_data, db_scene in remaining:
            scene_num = db_scene["scene_order"]
            scene_id = db_scene["id"]
            
            try:
                logger.info(f"🎨 Generating scene {scene_num}/{total_scenes}")
                
                # ==========================================
                # BƯỚC 1: Update status = 'generating'
                # ==========================================
                await db.update_scene_status(scene_id, "generating")
                
                # ==========================================
                # BƯỚC 2: Generate image + audio (PARALLEL)
                # ==========================================
                start_time = time.time()
                
                # Tạo image task
                image_task = image_gen.generate_image(
                    prompt=db_scene["image_prompt_used"],
                    style=request_params.get("image_style"),
                    scene_number=scene_num,
                    character_design=character_design,
                    background_design=background_design
                )
                
                # Tạo audio task
                audio_task = voice_gen.generate_audio(
                    text=db_scene["paragraph_text"],
                    voice=request_params.get("voice")
                )
                
                # Chạy CẢ HAI cùng lúc (parallel)
                # image_bytes: bytes của ảnh PNG
                # audio_bytes: bytes của file MP3
                # audio_duration: độ dài audio (seconds)
                image_bytes, (audio_bytes, audio_duration) = await asyncio.gather(
                    image_task,
                    audio_task
                )
                
                duration = time.time() - start_time
                logger.info(f"   ✅ Assets generated in {duration:.2f}s")
                
                # ==========================================
                # BƯỚC 3: Upload lên Supabase Storage
                # ==========================================
                image_path = f"{story_id}/scene_{scene_num}.png"
                audio_path = f"{story_id}/scene_{scene_num}.mp3"
                
                # Upload cả hai (parallel)
                image_url, audio_url = await asyncio.gather(
                    db.upload_file("story-images", image_path, image_bytes, "image/png"),
                    db.upload_file("story-audio", audio_path, audio_bytes, "audio/mpeg")
                )
                
                # ==========================================
                # BƯỚC 4: Update scene với URLs
                # ==========================================
                await db.update_scene(scene_id, {
                    "image_url": image_url,
                    "audio_url": audio_url
                })
                
                # ==========================================
                # BƯỚC 5: Update status = 'completed'
                # ==========================================
                await db.update_scene_status(scene_id, "completed")
                
                # ==========================================
                # BƯỚC 6: Update story progress
                # ==========================================
                completed += 1
                await db.update_story_progress(story_id, completed, total_scenes)
                
                logger.info(
                    f"✅ Scene {scene_num}/{total_scenes} completed "
                    f"(Progress: {completed}/{total_scenes})"
                )
                
            except Exception as e:
                # ==========================================
                # XỬ LÝ LỖI: Scene này fail
                # ==========================================
                logger.error(f"❌ Scene {scene_num} failed: {e}")
                
                # Mark scene as failed (lưu error message)
                await db.update_scene_status(
                    scene_id, 
                    "failed", 
                    error_message=str(e)
                )
                
                # Vẫn tăng completed (để progress tiếp tục)
                # User sẽ thấy scene này có status='failed'
                completed += 1
                await db.update_story_progress(story_id, completed, total_scenes)
                
                # TIẾP TỤC scene tiếp theo (không raise exception)
                continue
        
        # ==========================================
        # TẤT CẢ SCENES ĐÃ PROCESS
        # ==========================================
        # Update story status = 'completed'
        await db.update_story_status(story_id, "completed")
        
        logger.info(
            f"🎉 Story {story_id} fully completed! "
            f"({completed}/{total_scenes} scenes)"
        )
        
    except Exception as e:
        # ==========================================
        # LỖI CRITICAL (toàn bộ worker fail)
        # ==========================================
        logger.error(f"❌ Background worker CRITICAL FAIL [{story_id}]: {e}")
        
        # Mark story as failed
        await db.update_story_status(story_id, "failed")
        
        # Lưu error message vào story
        try:
            await db.client.table("stories").update({
                "error_message": str(e)
            }).eq("id", story_id).execute()
        except:
            pass