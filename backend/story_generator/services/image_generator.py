"""
Image generation using Google Vertex AI Imagen. 
Features:
- Fairytale-optimized prompts
- Character + Background consistency
- Retry logic with fallbacks
- Quality enhancement keywords
"""

import logging
import asyncio
import io
import os
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

from google.oauth2 import service_account
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

from story_generator.config import settings

logger = logging.getLogger(__name__)


class ImageGenerator:
    """
    Generate images using Vertex AI Imagen. 
    
    Optimized for: 
    - Fairy tale storybook illustrations
    - Consistent character/background
    - Child-friendly content
    """
    
    def __init__(self):
        """Initialize Vertex AI."""
        self.credentials_path = settings.credentials_path or settings.google_application_credentials or ""
        self.project_id = settings.google_cloud_project or ""
        self.location = settings.google_cloud_location
        self.model = None
        self.model_name = None
        
        self._init_vertex_ai()
    
    def _init_vertex_ai(self):
        """Initialize Vertex AI."""
        try:
            # Check credentials path
            if not os.path.exists(self.credentials_path):
                parent_path = os.path.join(". .", self.credentials_path)
                if os.path.exists(parent_path):
                    self.credentials_path = parent_path
                else:
                    logger.error(f"❌ Credentials not found:  {self.credentials_path}")
                    return
            
            logger.info("🔄 Initializing Vertex AI...")
            
            credentials = service_account.Credentials. from_service_account_file(self.credentials_path)
            vertexai.init(project=self.project_id, location=self.location, credentials=credentials)
            
            # Try models
            models = ["imagen-3.0-fast-generate-001", "imagegeneration@006"]
            
            for model_id in models:
                try: 
                    logger.info(f"📡 Trying:  {model_id}")
                    self.model = ImageGenerationModel.from_pretrained(model_id)
                    self.model_name = model_id
                    logger.info(f"✅ Connected to:  {model_id}")
                    break
                except Exception as e: 
                    logger.warning(f"⚠️ Failed {model_id}: {e}")
            
            if not self.model:
                logger.error("❌ No model available")
        
        except Exception as e: 
            logger.error(f"❌ Init failed: {e}", exc_info=True)
    
    async def generate_image(
        self,
        prompt: str,
        style: str = None,
        scene_number: int = None,
        character_design: str = None,
        background_design: str = None
    ) -> Optional[bytes]:
        """
        Generate fairy tale image with CHARACTER CONSISTENCY.
        
        Args:
            prompt: Main image prompt (should include char + bg + action)
            style: Optional style override
            scene_number: Scene number for logging
            character_design: Character description (for consistency)
            background_design: Background description (for consistency)
            
        Returns:
            Image bytes (WEBP) or placeholder if failed
        """
        
        if not self.model:
            logger.error("❌ Model not ready")
            return await self._get_placeholder(scene_number)
        
        # ==========================================
        # BUILD PROMPT WITH CHARACTER CONSISTENCY
        # ==========================================
        
        # Extract action from prompt
        action = prompt
        if character_design:
            action = action.replace(character_design, "").strip()
        if background_design:
            action = action.replace(background_design, "").strip()
        
        # Remove common words
        action = action.replace(", at ", " ").replace(", in ", " ").strip()
        
        # Rebuild với thứ tự CỐ ĐỊNH:  CHARACTER → ACTION → BACKGROUND
        if character_design and background_design:
            base_prompt = f"{character_design}, {action}, {background_design}"
        else:
            base_prompt = prompt
        
        # Consistency keywords
        consistency_keywords = (
            "SAME character throughout story, "
            "consistent character design, "
            "character continuity, "
            "exact same appearance"
        )
        
        # Fairy tale atmosphere keywords
        fairytale_keywords = (
            "magical fairytale storybook illustration, "
            "enchanted children's book art, "
            "whimsical dreamlike atmosphere, "
            "vibrant cheerful colors, "
            "soft magical lighting, "
            "safe and friendly for children"
        )

        # Quality keywords (reduced)
        quality_keywords = "Pixar 3D style, high quality, detailed"

        # Combine style
        base_style = style if style else ""

        # Build final prompt
        final_prompt = (
            f"{base_prompt}. "
            f"{consistency_keywords}, "
            f"{fairytale_keywords}, "
            f"{quality_keywords}"
        )
        
        if base_style:
            final_prompt += f", {base_style}"

        # ==========================================
        # FALLBACK PROMPTS
        # ==========================================
        
        fallback_prompts = [
            final_prompt,
            f"{base_prompt}.  Magical fairytale scene, Pixar style, bright colors, safe for children."
        ]
        
        # ==========================================
        # GENERATION WITH RETRY
        # ==========================================
        loop = asyncio.get_running_loop()
        
        for attempt, current_prompt in enumerate(fallback_prompts, 1):
            try:
                def _gen():
                    return self.model. generate_images(
                        prompt=current_prompt,
                        number_of_images=1,
                        aspect_ratio="16:9",
                        safety_filter_level="block_only_high",
                        person_generation="allow_all"
                    )
                
                response = await loop.run_in_executor(None, _gen)
                
                # Extract image bytes
                image_bytes = None
                if hasattr(response, 'images') and response.images and len(response.images) > 0:
                    img = response.images[0]
                    if hasattr(img, '_image_bytes'):
                        image_bytes = img._image_bytes
                
                # Validate image
                if image_bytes and len(image_bytes) > 100:
                    compressed_bytes = self._compress_image(image_bytes)
                    return compressed_bytes
                else:
                    logger.warning(f"⚠️ Empty response")
            
            except Exception as e: 
                logger.warning(f"⚠️ Failed:  {str(e)[:150]}")
            
            # Wait before retry
            if attempt < len(fallback_prompts):
                await asyncio.sleep(1)
        
        # All attempts failed
        logger.error(f"❌ All attempts failed")
        return await self._get_placeholder(scene_number)
    
    def _compress_image(self, image_bytes: bytes) -> bytes:
        """Nén và chuyển đổi PNG sang WebP để tăng tốc độ upload."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            output = io.BytesIO()
            
            img.save(output, format='WEBP', quality=85, method=6)
            
            compressed_bytes = output.getvalue()
            
            return compressed_bytes
        except Exception as e:
            logger.warning(f"⚠️ Compression failed, using original bytes: {e}")
            return image_bytes

    async def _get_placeholder(self, scene_number: int = None) -> bytes:
        """Generate placeholder."""
        img = Image.new('RGB', (1024, 576), color=(255, 250, 245))
        draw = ImageDraw.Draw(img)
        
        draw.rectangle([30, 30, 994, 546], outline=(255, 182, 193), width=10)
        draw.rectangle([50, 50, 974, 526], outline=(200, 150, 200), width=5)
        
        try:
            font_large = ImageFont.truetype("arial.ttf", 56)
            font_small = ImageFont.truetype("arial.ttf", 32)
        except: 
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        if scene_number:
            text_main = f"✨ Scene {scene_number} ✨"
            text_sub = "Image placeholder"
        else:
            text_main = "✨ Magic Loading ✨"
            text_sub = "Please wait..."
        
        bbox = draw.textbbox((0, 0), text_main, font=font_large)
        x = (1024 - (bbox[2] - bbox[0])) // 2
        y = 220
        draw.text((x, y), text_main, fill=(200, 100, 150), font=font_large)
        
        bbox_sub = draw.textbbox((0, 0), text_sub, font=font_small)
        x_sub = (1024 - (bbox_sub[2] - bbox_sub[0])) // 2
        y_sub = 300
        draw.text((x_sub, y_sub), text_sub, fill=(150, 150, 150), font=font_small)
        
        output = io.BytesIO()
        img.save(output, format='PNG')
        return output.getvalue()