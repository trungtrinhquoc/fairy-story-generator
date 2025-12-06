"""
Performance tracking and metrics collection for story generation.
"""

import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class StepMetric:
    """Metric cho một bước xử lý."""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict = field(default_factory=dict)
    
    def finish(self) -> float:
        """Đánh dấu hoàn thành và tính duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return self.duration


@dataclass
class SceneMetrics:
    """Metrics chi tiết cho một scene."""
    scene_number: int
    text_ready_at: Optional[float] = None
    image_start: Optional[float] = None
    image_end: Optional[float] = None
    audio_start: Optional[float] = None
    audio_end: Optional[float] = None
    upload_start: Optional[float] = None
    upload_end: Optional[float] = None
    total_duration: Optional[float] = None
    
    def get_summary(self) -> Dict:
        """Tạo summary report cho scene."""
        return {
            "scene": self.scene_number,
            "image_gen": round(self.image_end - self.image_start, 2) if (self.image_end and self.image_start) else None,
            "audio_gen": round(self.audio_end - self.audio_start, 2) if (self.audio_end and self.audio_start) else None,
            "upload": round(self.upload_end - self.upload_start, 2) if (self.upload_end and self.upload_start) else None,
            "total": round(self.total_duration, 2) if self.total_duration else None
        }


class PerformanceTracker:
    """Track performance of story generation."""
    
    def __init__(self, story_id: str):
        self.story_id = story_id
        self. start_time = time.time()
        self.steps: List[StepMetric] = []
        self.scene_metrics: Dict[int, SceneMetrics] = {}
        self.current_step: Optional[StepMetric] = None
    
    @contextmanager
    def track_step(self, name: str, **metadata):
        """Context manager để track một bước xử lý."""
        step = StepMetric(name=name, start_time=time.time(), metadata=metadata)
        self.current_step = step
        
        metadata_str = ", ".join(f"{k}={v}" for k, v in metadata.items())
        logger.info(f"⏱️  [{name}] Started...   {metadata_str}")
        
        try:
            yield step
        finally:
            duration = step.finish()
            self.steps.append(step)
            logger.info(f"✅ [{name}] Completed in {duration:.2f}s")
            self.current_step = None
    
    def get_scene_metrics(self, scene_number: int) -> SceneMetrics:
        """Get hoặc tạo SceneMetrics cho một scene."""
        if scene_number not in self.scene_metrics:
            self.scene_metrics[scene_number] = SceneMetrics(scene_number=scene_number)
        return self. scene_metrics[scene_number]
    
    def get_summary(self) -> Dict:
        """Tạo summary report đầy đủ."""
        total_duration = time.time() - self.start_time
        
        # Group steps by name
        step_times = {}
        for step in self.steps:
            if step.duration:
                step_times[step.name] = step_times.get(step.name, 0) + step.duration
        
        # Scene summaries
        scene_summaries = []
        for metrics in sorted(self.scene_metrics.values(), key=lambda x: x. scene_number):
            summary = metrics.get_summary()
            scene_summaries.append({
                "scene": summary.get("scene"),
                "image_gen": summary.get("image_gen"),
                "audio_gen": summary.get("audio_gen"),
                "upload": summary.get("upload"),
                "total": summary.get("total")
            })
        
        # Calculate averages
        if scene_summaries:
            image_times = [s["image_gen"] for s in scene_summaries if s.get("image_gen") is not None]
            audio_times = [s["audio_gen"] for s in scene_summaries if s. get("audio_gen") is not None]
            upload_times = [s["upload"] for s in scene_summaries if s.get("upload") is not None]
            
            avg_image = sum(image_times) / len(image_times) if image_times else 0
            avg_audio = sum(audio_times) / len(audio_times) if audio_times else 0
            avg_upload = sum(upload_times) / len(upload_times) if upload_times else 0
        else:
            avg_image = avg_audio = avg_upload = 0
        
        return {
            "story_id": self.story_id,
            "total_duration": round(total_duration, 2),
            "step_times": {k: round(v, 2) for k, v in step_times. items()},
            "scene_count": len(self.scene_metrics),
            "scenes": scene_summaries,
            "averages": {
                "image_gen": round(avg_image, 2),
                "audio_gen": round(avg_audio, 2),
                "upload": round(avg_upload, 2)
            },
            "timestamp": datetime.utcnow(). isoformat()
        }
    
    def log_summary(self):
        """Log formatted summary ra console."""
        summary = self.get_summary()
        
        logger.info("=" * 70)
        logger.info(f"📊 PERFORMANCE SUMMARY - Story: {self.story_id}")
        logger.info("=" * 70)
        logger.info(f"⏱️  Total Duration: {summary['total_duration']}s")
        logger.info(f"🎬 Scenes Generated: {summary['scene_count']}")
        logger.info("")
        
        # Step Breakdown
        logger.info("⚡ Step Breakdown:")
        if summary['step_times']:
            for step, duration in summary['step_times'].items():
                percentage = (duration / summary['total_duration']) * 100 if summary['total_duration'] > 0 else 0
                logger.info(f"   • {step:<40} {duration:>6.2f}s ({percentage:>5.1f}%)")
        else:
            logger.info("   (No steps recorded)")
        logger.info("")
        
        # Averages
        logger.info("📈 Average Timing per Scene:")
        if summary.get('averages'):
            logger.info(f"   • Image Generation: {summary['averages'].get('image_gen', 0):.2f}s")
            logger. info(f"   • Audio Generation: {summary['averages'].get('audio_gen', 0):.2f}s")
            logger.info(f"   • Upload (both):    {summary['averages'].get('upload', 0):.2f}s")
        else:
            logger.info("   (No scene data available)")
        logger.info("")
        
        # Scene details with NULL safety
        logger.info("🎬 Scene-by-Scene Details:")
        if summary.get('scenes'):
            for scene in summary['scenes']:
                # Safe extraction with defaults
                scene_num = scene.get('scene', '?')
                img_time = scene. get('image_gen') or 0
                aud_time = scene.get('audio_gen') or 0
                upl_time = scene.get('upload') or 0
                tot_time = scene.get('total') or 0
                
                # Format with scene number handling
                if scene_num != '?' and scene_num is not None:
                    logger.info(
                        f"   Scene {scene_num:>2}: "
                        f"Image={img_time:>5.2f}s, "
                        f"Audio={aud_time:>5.2f}s, "
                        f"Upload={upl_time:>5.2f}s, "
                        f"Total={tot_time:>5.2f}s"
                    )
                else:
                    logger.info(
                        f"   Scene  ?: "
                        f"Image={img_time:>5. 2f}s, "
                        f"Audio={aud_time:>5.2f}s, "
                        f"Upload={upl_time:>5.2f}s, "
                        f"Total={tot_time:>5.2f}s"
                    )
        else:
            logger.info("   (No scenes completed)")
        logger.info("=" * 70)
        logger.info("")