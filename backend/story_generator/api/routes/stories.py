"""
Story API routes with performance tracking and optimization. 

Key features:
- Detailed performance metrics
- Parallel scene generation (3 concurrent)
- Parallel upload (image + audio)
- Enhanced fairy tale prompts
"""

import logging
import asyncio
import time
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone

from story_generator.models.story import (
    StoryRequest,
    StoryResponse,
    StoryListItem,
    SceneGenerated,
    StoryGenerationStartResponse,
    StoryProgressResponse,
    ProgressInfo,
    SceneWithStatus,
    SceneStatus
)
from story_generator.database import db
from story_generator.config import settings
from story_generator.services import StoryGenerator, ImageGenerator, VoiceGenerator
from story_generator.utils import PerformanceTracker
from story_generator.workers import task_manager
from story_generator.workers.scene_worker import generate_remaining_scenes

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
story_gen = StoryGenerator()
image_gen = ImageGenerator()
voice_gen = VoiceGenerator()

# ========================================
# HELPER FUNCTION: Tạo một scene
# ========================================
async def generate_single_scene(
    scene_data: dict,
    db_scene: dict,
    image_style: Optional[str],
    voice: Optional[str],
    character_design: str,
    background_design: str,
    story_id: str,
    tracker: PerformanceTracker
) -> dict:
    """
    Tạo image + audio cho MỘT scene. 
    
    DÙNG CHO:
    - API 1: Tạo scene 1
    - Worker: Tạo scenes 2-6
    
    FLOW:
    1. Generate image + audio (parallel)
    2. Upload lên storage
    3. Update database
    
    Args:
        scene_data: Data từ Gemini
        db_scene: Scene record từ DB
        image_style: Style cho image
        voice: Voice cho TTS
        character_design: Character description
        background_design: Background description
        story_id: ID của story
        tracker: Performance tracker
    
    Returns:
        Scene dict với image_url, audio_url
    """
    scene_num = db_scene["scene_order"]
    scene_id = db_scene["id"]
    scene_metrics = tracker.get_scene_metrics(scene_num)
    scene_metrics. text_ready_at = time.time()
    
    logger.info(f"🎨 Generating scene {scene_num}...")
    
    try:
        # ==========================================
        # Update status = generating
        # ==========================================
        await db.update_scene_status(scene_id, "generating")
        
        # ==========================================
        # Generate image + audio (PARALLEL)
        # ==========================================
        scene_metrics.image_start = time.time()
        scene_metrics.audio_start = time.time()
        
        image_task = image_gen.generate_image(
            prompt=db_scene["image_prompt_used"],
            style=image_style,
            scene_number=scene_num,
            character_design=character_design,
            background_design=background_design
        )
        
        audio_task = voice_gen.generate_audio(
            text=db_scene["paragraph_text"],
            voice=voice or settings.tts_voice
        )
        
        # Wait for both
        image_bytes, (audio_bytes, audio_duration) = await asyncio.gather(
            image_task,
            audio_task
        )
        
        scene_metrics.image_end = time.time()
        scene_metrics.audio_end = time.time()
        
        image_time = scene_metrics.image_end - scene_metrics.image_start
        audio_time = scene_metrics.audio_end - scene_metrics.audio_start
        
        logger.info(
            f"   ✅ Scene {scene_num} assets: "
            f"Image={image_time:.2f}s, Audio={audio_time:.2f}s"
        )
        
        # ==========================================
        # Upload (PARALLEL)
        # ==========================================
        scene_metrics.upload_start = time.time()
        
        image_path = f"{story_id}/scene_{scene_num}.png"
        audio_path = f"{story_id}/scene_{scene_num}.mp3"
        
        image_url, audio_url = await asyncio. gather(
            db.upload_file("story-images", image_path, image_bytes, "image/png"),
            db.upload_file("story-audio", audio_path, audio_bytes, "audio/mpeg")
        )
        
        scene_metrics.upload_end = time.time()
        upload_time = scene_metrics.upload_end - scene_metrics.upload_start
        
        if not image_url or not audio_url:
            raise Exception(f"Upload failed: image={image_url}, audio={audio_url}")
        
        # ==========================================
        # Update database
        # ==========================================
        await db.update_scene(scene_id, {
            "image_url": image_url,
            "audio_url": audio_url
        })
        
        # Update status = completed
        await db.update_scene_status(scene_id, "completed")
        
        # Calculate total duration
        scene_metrics.total_duration = time.time() - scene_metrics.text_ready_at
        
        logger.info(
            f"✅ Scene {scene_num} COMPLETE in {scene_metrics.total_duration:.2f}s "
            f"(Upload={upload_time:.2f}s)"
        )
        
        # ==========================================
        # Return complete scene data
        # ==========================================
        return {
            **db_scene,
            "image_url": image_url,
            "audio_url": audio_url,
            "audio_duration": audio_duration,
            "word_count": len(db_scene["paragraph_text"].split()),
            "status": "completed"
        }
        
    except Exception as e:
        logger. error(f"❌ Scene {scene_num} failed: {e}")
        
        # Update status = failed
        await db. update_scene_status(scene_id, "failed", error_message=str(e))
        
        # Still calculate duration
        if scene_metrics.text_ready_at:
            scene_metrics.total_duration = time.time() - scene_metrics.text_ready_at
        
        raise

# ========================================
# API 1: POST /generate
# Tạo story, trả về scene 1 ngay
# ========================================
@router.post("/generate", response_model=StoryResponse)
async def generate_story(request: StoryRequest):
    """Generate complete story with images and audio."""
    
    logger.info("=" * 70)
    logger.info(f"📚 NEW STORY REQUEST")
    logger.info(f"   Prompt: {request.prompt[:60]}...")
    logger.info(f"   Length: {request.story_length. value} ({get_scene_count_from_length(request.story_length.value)} scenes)")
    logger.info(f"   Tone: {request.story_tone.value}")
    logger.info("=" * 70)
    
    # Initialize performance tracker
    tracker = PerformanceTracker(story_id="pending")
    story_id = "pending" 

    try:
        # ========================================
        # STEP 1: Generate Story Text
        # ========================================
        with tracker.track_step("story_text_generation", length=request.story_length.value):
            story_data = await story_gen.generate_story(
                user_prompt=request.prompt,
                story_length=request.story_length.value,
                story_tone=request.story_tone.value,
                theme=request.theme.value if request.theme else None,
                child_name=request.child_name
            )
        
        # Extract designs for later use
        character_design = story_data.get("character_design", "")
        background_design = story_data.get("background_design", "")
        total_scenes = len(story_data["scenes"])
        
        # ========================================
        # STEP 2: Save Story to Database
        # ========================================
        with tracker.track_step("story_save_database"):
            story_record = {
                "user_id": settings.default_user_id,
                "title": story_data["title"],
                "story_length": request.story_length.value,
                "story_tone": request. story_tone.value,
                "theme_selected": request.theme.value if request.theme else "custom",
                "status": "generating",
                "scenes_completed": 0,   # ← Chưa có scene nào xong
                "scenes_total": total_scenes
            }
        
            created_story = await db.create_story(story_record)
            story_id = created_story["id"]
            tracker.story_id = story_id  # ✅ FIX: Update tracker
            logger.info(f"✅ Story saved: {story_id}")
        
        # ========================================
        # STEP 3: Save Scenes to Database
        # ========================================
        with tracker.track_step("scenes_save_database", count=len(story_data["scenes"])):
            scenes_records = []
            for scene in story_data["scenes"]:
                scenes_records.append({
                    "story_id": story_id,
                    "user_id": settings.default_user_id,
                    "scene_order": scene["scene_number"],
                    "paragraph_text": scene["text"],
                    "image_prompt_used": scene["image_prompt"],
                    "image_url": "",
                    "audio_url": "",
                    "image_style": request.image_style or "Pixar style, 3D render, cute, vibrant colors",
                    "narration_voice": request.voice or settings.tts_voice,
                    "status": "pending" 
                })
            
            await db.create_scenes_bulk(scenes_records)
            db_scenes = await db.get_story_scenes(story_id)
            logger.info(f"✅ {len(db_scenes)} scenes saved to database (status=pending)")
        

        # ========================================
        # STEP 4: Generate SCENE 1 ONLY (sync)
        # ========================================
        with tracker.track_step("scene_1_generation"):
            scene_1_data = story_data["scenes"][0]
            db_scene_1 = db_scenes[0]
            
            # Tạo scene 1 (đợi xong)
            scene_1_complete = await generate_single_scene(
                scene_1_data,
                db_scene_1,
                request.image_style,
                request.voice,
                character_design,
                background_design,
                story_id,
                tracker
            )
            
            # Update story progress: 1/6
            await db.update_story_progress(story_id, 1, total_scenes)


        # ========================================
        # STEP 5: Start Background Worker
        # ========================================
        logger.info("🚀 Starting background worker for scenes 2-6...")
        
        # Request params để worker dùng
        request_params = {
            "image_style": request.image_style,
            "voice": request.voice
        }
        
        # Tạo coroutine cho worker
        worker_coro = generate_remaining_scenes(
            story_id=story_id,
            scenes_data=story_data["scenes"],
            db_scenes=db_scenes,
            request_params=request_params,
            character_design=character_design,
            background_design=background_design,
            image_gen=image_gen,
            voice_gen=voice_gen,
            db=db
        )
        
        # Start task (KHÔNG ĐỢI - background)
        task_manager.start_task(story_id, worker_coro)
        
        logger.info("✅ Background worker started")
        
        # ========================================
        # STEP 6: Log Performance
        # ========================================
        logger.info("")
        tracker.log_summary()
        
        # ========================================
        # STEP 7: Return Response (Scene 1 only)
        # ========================================
        return StoryGenerationStartResponse(
            story_id=story_id,
            title=story_data["title"],
            status="generating",
            progress=ProgressInfo(
                completed=1,
                total=total_scenes,
                percentage=round((1 / total_scenes) * 100, 1)
            ),
            scenes=[
                SceneGenerated(
                    id=scene_1_complete["id"],
                    story_id=story_id,
                    scene_order=1,
                    paragraph_text=scene_1_complete["paragraph_text"],
                    image_prompt_used=scene_1_complete["image_prompt_used"],
                    image_url=scene_1_complete["image_url"],
                    audio_url=scene_1_complete["audio_url"],
                    audio_duration=scene_1_complete. get("audio_duration"),
                    image_style=scene_1_complete.get("image_style"),
                    narration_voice=scene_1_complete.get("narration_voice"),
                    word_count=scene_1_complete.get("word_count")
                )
            ],
            message=f"Scene 1/{total_scenes} hoàn thành. Đang tạo các scenes còn lại.. .",
            poll_url=f"/api/v1/stories/{story_id}/progress"
        )
        
    except Exception as e:
        logger.error("=" * 70)
        logger. error(f"❌ ERROR: {e}", exc_info=True)
        logger.error("=" * 70)
        
        # Update story status = failed
        if story_id and story_id != "pending":
            try:
                await db.update_story_status(story_id, "failed")
                await db.client.table("stories").update({
                    "error_message": str(e)
                }).eq("id", story_id).execute()
            except:
                pass
        
        # Log partial metrics
        if tracker:
            tracker.log_summary()
        
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# API 2: GET /{story_id}/progress
# Lấy progress + scenes đã hoàn thành
# ========================================
@router. get("/{story_id}/progress", response_model=StoryProgressResponse)
async def get_story_progress(story_id: str):
    """
    API 2: Lấy progress của story đang tạo. 
    
    FRONTEND POLL API NÀY mỗi 2 giây để:
    - Cập nhật progress bar
    - Lấy scenes mới hoàn thành
    - Biết khi nào dừng polling (status='completed')
    
    FLOW:
    1. Lấy story info
    2. Lấy tất cả scenes đã COMPLETED
    3. Tính progress %
    4. Estimate thời gian còn lại
    5. Return data
    
    RESPONSE:
    - status: 'generating' | 'completed' | 'failed'
    - progress: {completed: 3, total: 6, percentage: 50}
    - scenes: [scene_1, scene_2, scene_3] (chỉ completed)
    - estimated_time_remaining: 15 (seconds)
    
    FRONTEND LOGIC:
    ```javascript
    const poll = setInterval(async () => {
        const data = await fetch('/api/stories/{id}/progress')
        
        if (data.status === 'completed') {
            clearInterval(poll) // Dừng polling
            showAllScenes(data.scenes)
        } else {
            updateProgress(data. progress)
            showScenes(data.scenes) // Show scenes available
        }
    }, 2000) // Poll mỗi 2s
    ```
    
    Args:
        story_id: ID của story
    
    Returns:
        StoryProgressResponse
    """
    
    try:
        # ==========================================
        # 1. Lấy story với progress
        # ==========================================
        story = await db.get_story_with_progress(story_id)
        
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        # ==========================================
        # 2.  Lấy completed scenes
        # ==========================================
        completed_scenes = await db.get_completed_scenes(story_id)
        
        # ==========================================
        # 3. Calculate progress
        # ==========================================
        total = story.get("scenes_total", 6)
        completed_count = len(completed_scenes)
        percentage = (completed_count / total * 100) if total > 0 else 0
        
        # ==========================================
        # 4. Estimate remaining time
        # ==========================================
        # Giả sử mỗi scene mất ~8s (average)
        # Nếu còn 3 scenes → ~24s
        remaining_scenes = total - completed_count
        estimated_time = remaining_scenes * 8 if story["status"] == "generating" else 0
        
        # ==========================================
        # 5. Convert scenes to SceneWithStatus
        # ==========================================
        scenes_with_status = []
        for scene in completed_scenes:
            scenes_with_status.append(
                SceneWithStatus(
                    id=scene["id"],
                    story_id=scene["story_id"],
                    scene_order=scene["scene_order"],
                    paragraph_text=scene["paragraph_text"],
                    image_prompt_used=scene["image_prompt_used"],
                    image_url=scene["image_url"],
                    audio_url=scene["audio_url"],
                    image_style=scene. get("image_style"),
                    narration_voice=scene. get("narration_voice"),
                    status=SceneStatus(scene. get("status", "completed")),
                    error_message=scene.get("error_message"),
                    started_at=scene.get("started_at"),
                    completed_at=scene.get("completed_at")
                )
            )
        
        # ==========================================
        # 6. Return response
        # ==========================================
        return StoryProgressResponse(
            story_id=story_id,
            title=story["title"],
            status=story["status"],
            progress=ProgressInfo(
                completed=completed_count,
                total=total,
                percentage=round(percentage, 1)
            ),
            scenes=scenes_with_status,
            estimated_time_remaining=estimated_time if estimated_time > 0 else None,
            error_message=story.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger. error(f"❌ Failed to get progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# READ ENDPOINTS
# ========================================

@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(story_id: str):
    """Get story by ID."""
    story = await db.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    scenes = await db.get_story_scenes(story_id)
    
    return StoryResponse(
        id=story["id"],
        user_id=story["user_id"],
        title=story["title"],
        story_length=story["story_length"],
        story_tone=story["story_tone"],
        theme_selected=story["theme_selected"],
        status=story["status"],
        cover_image_url=story.get("cover_image_url"),
        created_at=datetime.fromisoformat(story["created_at"]).replace(tzinfo=timezone.utc),
        updated_at=datetime.fromisoformat(story["updated_at"]).replace(tzinfo=timezone.utc),
        scenes=[
            SceneGenerated(
                id=scene["id"],
                story_id=scene["story_id"],
                scene_order=scene["scene_order"],
                paragraph_text=scene["paragraph_text"],
                image_prompt_used=scene["image_prompt_used"],
                image_url=scene["image_url"],
                audio_url=scene["audio_url"],
                image_style=scene.get("image_style"),
                narration_voice=scene.get("narration_voice")
            )
            for scene in scenes
        ]
    )


@router.get("/", response_model=List[StoryListItem])
async def list_stories(limit: int = 10):
    """List stories."""
    stories = await db.get_user_stories(settings.default_user_id, limit)
    
    result = []
    for story in stories:
        scenes = await db.get_story_scenes(story["id"])
        result.append(
            StoryListItem(
                id=story["id"],
                title=story["title"],
                theme_selected=story["theme_selected"],
                status=story["status"],
                cover_image_url=story.get("cover_image_url"),
                created_at=datetime.fromisoformat(story["created_at"]).replace(tzinfo=timezone.utc),
                scene_count=len(scenes)
            )
        )
    
    return result


def get_scene_count_from_length(story_length: str) -> int:
    """Helper to get scene count."""
    return {"short": 6, "medium": 10, "long": 14}.get(story_length, 6)

'''
       # ========================================
        # STEP 4: Generate Assets in Parallel
        # ========================================
        async def generate_scene_assets(scene_data: dict, db_scene: dict):
            """
            Generate image and audio for a single scene.
            
            Process:
            1. Generate image + audio in parallel
            2. Upload both in parallel
            3. Update database
            
            Returns complete scene data. 
            """
            scene_num = db_scene["scene_order"]
            scene_metrics = tracker.get_scene_metrics(scene_num)
            scene_metrics.text_ready_at = time.time()
            
            logger.info(f"🎨 Scene {scene_num}: Starting asset generation...")
            
            try:
                # ----------------------------------
                # Parallel: Image + Audio Generation
                # ----------------------------------
                scene_metrics.image_start = time.time()
                scene_metrics.audio_start = time.time()

                # Image và Audio chạy SONG SONG
                image_task = image_gen.generate_image(
                    prompt=db_scene["image_prompt_used"],
                    style=request.image_style,
                    scene_number=scene_num,
                    character_design=character_design,
                    background_design=background_design
                )
                
                audio_task = voice_gen. generate_audio(
                    text=db_scene["paragraph_text"],
                    voice=request. voice or settings.tts_voice
                )
                
                # Đợi cả 2 xong cùng lúc
                image_bytes, (audio_bytes, audio_duration) = await asyncio.gather(
                    image_task, 
                    audio_task
                )
                
                scene_metrics.image_end = time.time()
                scene_metrics.audio_end = time.time()
                
                image_time = scene_metrics.image_end - scene_metrics.image_start
                audio_time = scene_metrics.audio_end - scene_metrics.audio_start
                
                logger.info(
                    f"   ✅ Scene {scene_num} assets generated: "
                    f"Image={image_time:.2f}s, Audio={audio_time:.2f}s"
                )

                # ----------------------------------
                # Parallel: Upload Image + Audio
                # ----------------------------------
                scene_metrics.upload_start = time.time()

                image_path = f"{story_id}/scene_{scene_num}.png"
                audio_path = f"{story_id}/scene_{scene_num}.mp3"
                
                # ✅ Upload song song
                image_url, audio_url = await asyncio. gather(
                    upload_with_retry("story-images", image_path, image_bytes, "image/png"),
                    upload_with_retry("story-audio", audio_path, audio_bytes, "audio/mpeg")
                )

                scene_metrics.upload_end = time.time()
                upload_time = scene_metrics.upload_end - scene_metrics.upload_start

                if not image_url or not audio_url:
                    raise Exception(
                        f"Upload failed for scene {scene_num}: "
                        f"image_url={image_url}, audio_url={audio_url}"
                    )
                
                # ----------------------------------
                # Update Database
                # ----------------------------------
                await db.update_scene(db_scene["id"], {
                    "image_url": image_url,
                    "audio_url": audio_url,
                })
                
                # ✅ FIX: Calculate total_duration BEFORE logging
                scene_metrics.total_duration = time.time() - scene_metrics. text_ready_at
                
                logger.info(
                    f"✅ Scene {scene_num} COMPLETE in {scene_metrics. total_duration:.2f}s "
                    f"(Upload={upload_time:.2f}s)"
                )
                
                return {
                    **db_scene,
                    "image_url": image_url,
                    "audio_url": audio_url,
                    "audio_duration": audio_duration,
                    "word_count": len(db_scene["paragraph_text"].split())
                }
            
            except Exception as e:
                logger.error(f"❌ Scene {scene_num} failed: {e}")
                # ✅ FIX: Still calculate duration even on error
                if scene_metrics.text_ready_at:
                    scene_metrics.total_duration = time.time() - scene_metrics.text_ready_at
                raise
        
        # ----------------------------------
        # Process All Scenes in Parallel
        # ----------------------------------
        with tracker.track_step("asset_generation_parallel", scenes=len(db_scenes)):
            semaphore = asyncio.Semaphore(3)
            
            async def generate_with_limit(scene_data, db_scene):
                async with semaphore:
                    return await generate_scene_assets(scene_data, db_scene)
            
            tasks = [
                generate_with_limit(scene_data, db_scene)
                for scene_data, db_scene in zip(story_data["scenes"], db_scenes)
            ]
            
            completed_scenes = await asyncio.gather(*tasks)
        
        # ========================================
        # STEP 5: Update Story Status
        # ========================================
        with tracker.track_step("database_update_status"):
            await db.update_story_status(
                story_id=story_id,
                status="completed",
                cover_image_url=completed_scenes[0]["image_url"]
            )
        
        # ========================================
        # FINAL: Log Performance Summary
        # ========================================
        logger.info("")
        tracker.log_summary()
        logger.info(f"🎉 Story '{story_data['title']}' completed successfully!")
        logger.info("")

        # ========================================
        # STEP 6: Return Response
        # ========================================
        return StoryResponse(
            id=story_id,
            user_id=settings.default_user_id,
            title=story_data["title"],
            story_length=request.story_length.value,
            story_tone=request. story_tone.value,
            theme_selected=request.theme. value if request.theme else "custom",
            status="completed",
            cover_image_url=completed_scenes[0]["image_url"],
            created_at=datetime.fromisoformat(created_story["created_at"]).replace(tzinfo=timezone.utc),
            updated_at=datetime.now(timezone.utc),
            scenes=[
                SceneGenerated(
                    id=scene["id"],
                    story_id=scene["story_id"],
                    scene_order=scene["scene_order"],
                    paragraph_text=scene["paragraph_text"],
                    image_prompt_used=scene["image_prompt_used"],
                    image_url=scene["image_url"],
                    audio_url=scene["audio_url"],
                    audio_duration=scene. get("audio_duration"),
                    image_style=scene.get("image_style"),
                    narration_voice=scene.get("narration_voice"),
                    word_count=scene.get("word_count")
                )
                for scene in completed_scenes
            ]
        )
    
    except Exception as e:
        logger.error("=" * 70)
        logger. error(f"❌ ERROR OCCURRED: {e}", exc_info=True)
        logger.error("=" * 70)
        
        # Update story status to failed
        if story_id and story_id != "pending":
            try:
                await db.update_story_status(story_id, "failed")
            except:
                pass
        
        # Log partial metrics
        if tracker:
            logger.info("📊 Partial performance data:")
            tracker.log_summary()
        
        raise HTTPException(status_code=500, detail=str(e))


async def upload_with_retry(
    bucket: str, 
    path: str, 
    file_data: bytes, 
    content_type: str, 
    max_retries: int = 3
) -> Optional[str]:
    """
    Upload file to storage with exponential backoff retry.
    
    Args:
        bucket: Storage bucket name
        path: File path in bucket
        file_data: File bytes
        content_type: MIME type
        max_retries: Maximum retry attempts
        
    Returns:
        Public URL if successful, None if failed
    """
    for attempt in range(1, max_retries + 1):
        try:
            url = await db.upload_file(bucket, path, file_data, content_type)
            if url:
                return url
            else:
                logger.warning(f"⚠️ Upload returned None for {path}")
        except Exception as e:
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(
                    f"⚠️ Upload failed (attempt {attempt}/{max_retries}): {path}. "
                    f"Retrying in {wait_time}s...  Error: {str(e)[:100]}"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Upload failed after {max_retries} attempts: {path}. Error: {str(e)}")
    
    return None

'''



