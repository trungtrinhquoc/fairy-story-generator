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
                parent_path = os.path.join("..", self.credentials_path)
                if os.path.exists(parent_path):
                    self.credentials_path = parent_path
                else:
                    logger.error(f"❌ Credentials not found: {self.credentials_path}")
                    return
            
            logger.info("🔄 Initializing Vertex AI...")
            
            credentials = service_account.Credentials.from_service_account_file(self.credentials_path)
            vertexai.init(project=self.project_id, location=self.location, credentials=credentials)
            
            # Try models (FIXED: no spaces!)
            models = ["imagen-3.0-fast-generate-001", "imagegeneration@006"]
            
            for model_id in models:
                try:
                    logger.info(f"📡 Trying: {model_id}")
                    self.model = ImageGenerationModel.from_pretrained(model_id)
                    self.model_name = model_id
                    logger.info(f"✅ Connected to: {model_id}")
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
        Generate fairy tale image.
        
        Args:
            prompt: Main image prompt (should include char + bg + action)
            style: Optional style override
            scene_number: Scene number for logging
            character_design: Character description (for fallback)
            background_design: Background description (for fallback)
            
        Returns:
            Image bytes (PNG) or placeholder if failed
        """
        
        if not self.model:
            logger. error("❌ Model not ready")
            return await self._get_placeholder(scene_number)
        
        # ==========================================
        # PROMPT ENHANCEMENT FOR FAIRY TALES
        # ==========================================
        # Fairy tale atmosphere keywords
        fairytale_keywords = (
            "magical fairytale storybook illustration, "
            "enchanted children's book art, "
            "whimsical dreamlike atmosphere, "
            "vibrant cheerful colors, "
            "soft magical lighting, "
            "safe and friendly for children"
        )

        # Quality enhancement keywords
        quality_keywords = (
            "high quality 3D render, "
            "Pixar animation style, "
            "volumetric lighting, "
            "cinematic composition, "
            "highly detailed, "
            "professional children's illustration"
        )

        # Combine style
        base_style = style if style else "Pixar 3D style, cute and vibrant"

        # Build final prompt
        final_prompt = f"{prompt}. {fairytale_keywords}, {quality_keywords}, {base_style}"

        # ==========================================
        # FALLBACK PROMPTS (if main fails)
        # ==========================================
        
        fallback_prompts = [
            final_prompt,  # Full enhanced prompt
            
            # Fallback 1: Simplified with char+bg
            f"{prompt}.  Magical fairytale scene, Pixar 3D style, bright cheerful colors, safe for children.",
            
            # Fallback 2: Generic fairy tale
            "A cute magical fairytale scene with friendly characters.  Pixar 3D animation style, bright vibrant colors, whimsical enchanted atmosphere, safe and happy for children."
        ]
        
        # ==========================================
        # GENERATION WITH RETRY
        # ==========================================
        loop = asyncio.get_running_loop()
        
        for attempt, current_prompt in enumerate(fallback_prompts, 1):
            logger.info(f"🎨 Scene {scene_number} - Try {attempt}/{len(fallback_prompts)}")
            logger.info(f"   📝 {current_prompt[:150]}...")
            
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
                    logger.info(f"✅ Scene {scene_number} OK ({len(image_bytes)} bytes)")
                    return image_bytes
                else:
                    logger.warning(f"⚠️ Empty response")
            
            except Exception as e:
                logger.warning(f"⚠️ Failed: {str(e)[:150]}")
            
            # Wait before retry
            if attempt < len(fallback_prompts):
                await asyncio. sleep(1)
        
        # All attempts failed
        logger.error(f"❌ All attempts failed")
        return await self._get_placeholder(scene_number)
    
    async def _get_placeholder(self, scene_number: int = None) -> bytes:
        """Generate placeholder."""
        # Create 16:9 image
        img = Image.new('RGB', (1024, 576), color=(255, 250, 245))  # Soft cream
        draw = ImageDraw. Draw(img)
        
        # Draw decorative border
        draw.rectangle([30, 30, 994, 546], outline=(255, 182, 193), width=10)
        draw.rectangle([50, 50, 974, 526], outline=(200, 150, 200), width=5)
        
        # Load font
        try:
            font_large = ImageFont.truetype("arial.ttf", 56)
            font_small = ImageFont.truetype("arial.ttf", 32)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw text
        if scene_number:
            text_main = f"✨ Scene {scene_number} ✨"
            text_sub = "Image placeholder"
        else:
            text_main = "✨ Magic Loading ✨"
            text_sub = "Please wait..."
        
        # Center main text
        bbox = draw.textbbox((0, 0), text_main, font=font_large)
        x = (1024 - (bbox[2] - bbox[0])) // 2
        y = 220
        draw.text((x, y), text_main, fill=(200, 100, 150), font=font_large)
        
        # Center subtitle
        bbox_sub = draw.textbbox((0, 0), text_sub, font=font_small)
        x_sub = (1024 - (bbox_sub[2] - bbox_sub[0])) // 2
        y_sub = 300
        draw.text((x_sub, y_sub), text_sub, fill=(150, 150, 150), font=font_small)
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format='PNG')
        return output.getvalue()