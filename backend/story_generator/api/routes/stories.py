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
    SceneGenerated
)
from story_generator.database import db
from story_generator. config import settings
from story_generator.services import StoryGenerator, ImageGenerator, VoiceGenerator
from story_generator.utils import PerformanceTracker

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
story_gen = StoryGenerator()
image_gen = ImageGenerator()
voice_gen = VoiceGenerator()


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
    story_id = "pending"  # ✅ FIX: Initialize story_id

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
                "status": "generating"
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
                    "narration_voice": request.voice or settings.tts_voice
                })
            
            await db.create_scenes_bulk(scenes_records)
            db_scenes = await db.get_story_scenes(story_id)
            logger.info(f"✅ {len(db_scenes)} scenes saved to database")
        
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
            created_at=datetime.fromisoformat(created_story["created_at"]). replace(tzinfo=timezone.utc),
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


def get_scene_count_from_length(story_length: str) -> int:
    """Helper to get scene count."""
    return {"short": 6, "medium": 10, "long": 14}.get(story_length, 6)


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