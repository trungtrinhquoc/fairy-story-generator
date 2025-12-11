"""
Scene Worker - Worker tạo scenes trong background. 

NHIỆM VỤ: 
- Nhận scenes 2-6 từ API
- Tạo PARALLEL 3 scenes cùng lúc (batch processing)
- Upload lên storage
- Update database
- Update progress sau mỗi batch
"""

import asyncio
import logging
import time
from story_generator.database import Database
from story_generator.services.image_generator import ImageGenerator
from story_generator.services.voice_generator import VoiceGenerator 

logger = logging.getLogger(__name__)


async def generate_single_scene_worker(
    scene_data: dict,
    db_scene: dict,
    request_params: dict,
    character_design: str,
    background_design: str,
    story_id: str,
    image_gen: ImageGenerator,
    voice_gen: VoiceGenerator,
    db: Database
) -> dict:
    """
    Tạo MỘT scene (image + audio).
    
    Dùng trong worker để process parallel.
    
    Returns:
        dict với status ('completed' hoặc 'failed')
    """
    scene_num = db_scene["scene_order"]
    scene_id = db_scene["id"]
    
    try:
        logger.info(f"   🎨 Scene {scene_num} starting...")
        
        #1. Update status = generating
        await db.update_scene_status(scene_id, "generating")
        
        start_time = time.time()
        
        #2. Generate image + audio (parallel)
        image_task = image_gen.generate_image(
            prompt=db_scene["image_prompt_used"],
            style=request_params.get("image_style"),
            scene_number=scene_num,
            character_design=character_design,
            background_design=background_design
        )
        
        audio_task = voice_gen.generate_audio(
            text=db_scene["paragraph_text"],
            voice=request_params.get("voice")
        )
        
        image_bytes, (audio_bytes, audio_duration) = await asyncio.gather(
            image_task,
            audio_task
        )
        
        #3. Upload (parallel)
        image_path = f"{story_id}/scene_{scene_num}.png"
        audio_path = f"{story_id}/scene_{scene_num}.mp3"
        
        image_url, audio_url = await asyncio.gather(
            db.upload_file("story-images", image_path, image_bytes, "image/png"),
            db.upload_file("story-audio", audio_path, audio_bytes, "audio/mpeg")
        )
        
        #4. Update scene database and đánh dấu Success
        await db.update_scene(scene_id, {
            "image_url":  image_url,
            "audio_url": audio_url
        })
        
        # Update status = completed
        await db.update_scene_status(scene_id, "completed")
        
        duration = time.time() - start_time
        logger.info(f"   ✅ Scene {scene_num} OK ({duration:.2f}s)")
        
        return {
            "scene_number": scene_num,
            "scene_id": scene_id,
            "status": "completed",
            "duration": duration
        }
        
    except Exception as e:
        logger.error(f"   ❌ Scene {scene_num} FAILED: {e}")
        
        # Mark as failed
        await db.update_scene_status(
            scene_id, 
            "failed", 
            error_message=str(e)
        )
        
        return {
            "scene_number":  scene_num,
            "scene_id": scene_id,
            "status": "failed",
            "error":  str(e)
        }


async def generate_remaining_scenes(
    story_id: str,
    scenes_data: list,
    db_scenes: list,
    request_params: dict,
    character_design: str,
    background_design: str,
    image_gen: ImageGenerator,
    voice_gen: VoiceGenerator,
    db: Database
):
    """
    Worker function - Tạo scenes 2-6 với PARALLEL PROCESSING.
    
    STRATEGY:
    - Tạo 3 scenes cùng lúc (batch)
    - Batch 1: scenes 2, 3, 4
    - Batch 2: scenes 5, 6
    
    BENEFITS:
    - Giảm thời gian từ ~30s xuống ~15s cho 6 scenes
    - Tận dụng I/O concurrency
    - API calls song song
    
    Args:
        story_id: ID của story
        scenes_data: List data từ Gemini
        db_scenes: List scene records từ DB
        request_params: Parameters (image_style, voice)
        character_design: Character description
        background_design: Background description
        image_gen: ImageGenerator instance
        voice_gen: VoiceGenerator instance
        db: Database instance
    """
    
    logger.info(f"🚀 Worker started: {story_id}")
    logger.info(f"   Strategy:  Parallel batch processing (3 scenes per batch)")
    
    total_scenes = len(db_scenes)
    completed_count = 1  # Scene 1 đã xong
    
    try:
        # Skip scene 1 (đã tạo trong API 1)
        remaining = list(zip(scenes_data[1:], db_scenes[1:]))
        
        if not remaining:
            logger.warning("⚠️ No remaining scenes to generate")
            return
        
        # ==========================================
        # PARALLEL BATCH PROCESSING
        # ==========================================
        BATCH_SIZE = 5  # Tạo 3 scenes cùng lúc
        
        # Chia thành batches
        batches = [
            remaining[i:i + BATCH_SIZE] 
            for i in range(0, len(remaining), BATCH_SIZE)
        ]
        
        logger.info(f"   📦 Total batches:   {len(batches)}")
        
        for batch_idx, batch in enumerate(batches, 1):
            batch_size = len(batch)
            scene_numbers = [db_scene["scene_order"] for _, db_scene in batch]
            
            logger.info(f"")
            logger.info(f"📦 BATCH {batch_idx}/{len(batches)}: Scenes {scene_numbers}")
            logger.info(f"   Processing {batch_size} scenes in parallel...")
            
            batch_start = time.time()
            
            # ==========================================
            # TẠO TẤT CẢ SCENES TRONG BATCH SONG SONG
            # ==========================================
            tasks = []
            for scene_data, db_scene in batch: 
                task = generate_single_scene_worker(
                    scene_data=scene_data,
                    db_scene=db_scene,
                    request_params=request_params,
                    character_design=character_design,
                    background_design=background_design,
                    story_id=story_id,
                    image_gen=image_gen,
                    voice_gen=voice_gen,
                    db=db
                )
                tasks.append(task)
            
            # Đợi TẤT CẢ scenes trong batch hoàn thành
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            batch_duration = time.time() - batch_start
            
            # ==========================================
            # PROCESS RESULTS
            # ==========================================
            completed_in_batch = 0
            failed_in_batch = 0
            
            for result in results: 
                if isinstance(result, Exception):
                    logger.error(f"   ❌ Task exception: {result}")
                    failed_in_batch += 1
                elif result["status"] == "completed":
                    completed_in_batch += 1
                else:
                    failed_in_batch += 1
            
            # Update total completed count
            completed_count += completed_in_batch + failed_in_batch
            
            # ==========================================
            # UPDATE STORY PROGRESS
            # ==========================================
            await db.update_story_progress(story_id, completed_count, total_scenes)
            
            logger.info(f"")
            logger.info(f"✅ BATCH {batch_idx} DONE in {batch_duration:.2f}s")
            logger.info(f"   Completed: {completed_in_batch}/{batch_size}")
            logger.info(f"   Failed: {failed_in_batch}/{batch_size}")
            logger.info(f"   Overall progress: {completed_count}/{total_scenes}")
        
        # ==========================================
        # ALL BATCHES COMPLETED
        # ==========================================
        await db.update_story_status(story_id, "completed")
        
        logger.info(f"")
        logger.info(f"🎉 Story {story_id} FULLY COMPLETED!")
        logger.info(f"   Total scenes: {completed_count}/{total_scenes}")
        
    except Exception as e:
        logger.error(f"❌ Worker CRITICAL FAILURE [{story_id}]: {e}", exc_info=True)
        
        # Mark story as failed
        await db.update_story_status(story_id, "failed")
        
        try:
            await db.client. table("stories").update({
                "error_message": str(e)
            }).eq("id", story_id).execute()
        except:
            pass