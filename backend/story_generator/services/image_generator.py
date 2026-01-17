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
        Generate fairy tale image with STRONG CHARACTER CONSISTENCY.
        
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
        # BUILD PROMPT WITH STRONG CHARACTER CONSISTENCY
        # ==========================================
        
        # Extract action from prompt
        action = prompt
        if character_design:
            action = action.replace(character_design, "").strip()
        if background_design:
            action = action.replace(background_design, "").strip()
        
        # Remove common words
        action = action.replace(", at ", " ").replace(", in ", " ").strip()
        
        # ✅ NEW: Build DETAILED character prompt with EXACT features
        if character_design:
            # Extract key features to enforce
            char_lower = character_design.lower()
            
            # Build consistency enforcement
            consistency_details = []
            
            # Add character design verbatim
            consistency_details.append(f"Character MUST BE EXACTLY: {character_design}")
            
            # ✅ Extract and enforce specific colors
            color_keywords = ["red", "blue", "green", "yellow", "orange", "purple", "pink", "black", "white", 
                            "gray", "grey", "brown", "silver", "gold", "emerald", "cyan", "teal", "ruby", 
                            "sapphire", "amber", "crimson", "violet", "turquoise"]
            found_colors = [color for color in color_keywords if color in char_lower]
            if found_colors:
                consistency_details.append(f"EXACT COLORS: {', '.join(found_colors)} - NEVER change these colors in ANY scene")
            
            # ✅ Extract and enforce specific shapes
            shape_keywords = ["round", "square", "cylindrical", "oval", "rectangular", "triangular", 
                            "spherical", "cubic", "flat", "curved", "pointed", "angular"]
            found_shapes = [shape for shape in shape_keywords if shape in char_lower]
            if found_shapes:
                consistency_details.append(f"EXACT SHAPES: {', '.join(found_shapes)} - NEVER change these shapes in ANY scene")
            
            # ✅ Extract and enforce sizes
            size_keywords = ["tiny", "small", "medium", "large", "huge", "big", "little", "short", "tall", "long"]
            found_sizes = [size for size in size_keywords if size in char_lower]
            if found_sizes:
                consistency_details.append(f"EXACT SIZES: {', '.join(found_sizes)} - NEVER change these sizes in ANY scene")
            
            # Add explicit "SAME" enforcement with measurements
            consistency_details.append("CRITICAL: This is the EXACT SAME character from scene 1")
            consistency_details.append("MAINTAIN 100% IDENTICAL in ALL scenes: face shape, body proportions, ALL colors, ALL shapes, ALL sizes, clothing, accessories, hairstyle")
            
            # ✅ Enhanced negative prompts with specifics
            negative_prompts = [
                "NEVER change: face shape",
                "NEVER change: body size or proportions",
                "NEVER change: ANY colors",
                "NEVER change: ANY shapes",
                "NEVER change: outfit or clothing",
                "NEVER change: hair style or color",
                "NEVER change: species or character type"
            ]
            consistency_details.append(" | ".join(negative_prompts))
            
            # ✅ Add reference instruction with emphasis
            consistency_details.append("Scene 2-6: Character MUST be PIXEL-PERFECT identical to scene 1. Same face, same body, same colors, same everything")
            
            char_consistency = ". ".join(consistency_details)
        else:
            char_consistency = ""
        
        # Rebuild với thứ tự CỐ ĐỊNH: CHARACTER → ACTION → BACKGROUND
        if character_design and background_design:
            base_prompt = f"{action}, {background_design}"
        else:
            base_prompt = prompt
        
        # Fairy tale atmosphere keywords (simplified)
        fairytale_keywords = (
            "magical storybook illustration, "
            "vibrant colors, soft lighting, "
            "child-friendly, whimsical atmosphere"
        )

        # Quality keywords (reduced)
        quality_keywords = "Pixar 3D style, high quality"

        # Combine style
        base_style = style if style else ""

        # ✅ NEW: Build final prompt with CHARACTER FIRST
        if char_consistency:
            final_prompt = (
                f"{char_consistency}. "
                f"Scene: {base_prompt}. "
                f"{fairytale_keywords}, {quality_keywords}"
            )
        else:
            final_prompt = (
                f"{base_prompt}. "
                f"{fairytale_keywords}, {quality_keywords}"
            )
        
        if base_style:
            final_prompt += f", {base_style}"

        # Trim if too long
        if len(final_prompt) > 1500:
            final_prompt = final_prompt[:1500]
        
        # ==========================================
        # FALLBACK PROMPTS
        # ==========================================
        
        fallback_prompts = [
            final_prompt,
            f"SAME character: {character_design}. {base_prompt}. Magical fairytale, Pixar style, consistent character."
        ]
        
        # ==========================================
        # GENERATION WITH RETRY + SEED CONSISTENCY
        # ==========================================
        loop = asyncio.get_running_loop()
        
        # ✅ Use FIXED SEED for character consistency
        # Same seed = more consistent character appearance
        character_seed = hash(character_design) % 2147483647 if character_design else None
        
        for attempt, current_prompt in enumerate(fallback_prompts, 1):
            try:
                def _gen():
                    gen_params = {
                        "prompt": current_prompt,
                        "number_of_images": 1,
                        "aspect_ratio": "16:9",
                        "safety_filter_level": "block_only_high",
                        "person_generation": "allow_all"
                    }
                    
                    # ✅ FIX: Disable watermark to enable seed
                    # Seed requires add_watermark=False
                    if character_seed:
                        try:
                            gen_params["seed"] = character_seed
                            gen_params["add_watermark"] = False  # Required for seed
                            logger.debug(f"Using seed={character_seed} with watermark disabled")
                        except Exception as e:
                            # If seed fails, continue without it
                            logger.debug(f"Seed not supported: {e}")
                            gen_params.pop("seed", None)
                            gen_params.pop("add_watermark", None)
                    
                    return self.model.generate_images(**gen_params)
                
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
                    if character_seed:
                        logger.info(f"✅ Scene {scene_number}: Generated with seed={character_seed}")
                    else:
                        logger.info(f"✅ Scene {scene_number}: Generated (no seed)")
                    return compressed_bytes
                else:
                    logger.warning(f"⚠️ Empty response")
            
            except Exception as e: 
                error_msg = str(e)
                logger.warning(f"⚠️ Attempt {attempt} failed: {error_msg[:150]}")
                
                # ✅ If seed error, retry without seed
                if "seed" in error_msg.lower() or "watermark" in error_msg.lower():
                    logger.info("🔄 Retrying without seed...")
                    character_seed = None  # Disable seed for next attempt
            
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