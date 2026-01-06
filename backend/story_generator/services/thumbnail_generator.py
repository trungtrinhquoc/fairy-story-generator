import logging
import io, os
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import asyncio
from google.oauth2 import service_account
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

from story_generator.config import settings

logger = logging.getLogger(__name__)

class ThumbnailGenerator:
    """Generate story cover thumbnails (2:3 ratio)."""

    def __init__(self):
        """Initialize Vertex AI."""
        # Lấy thông tin cấu hình từ file settings
        self.credentials_path = settings.google_application_credentials
        self.project_id = settings.google_cloud_project
        self.location = settings.google_cloud_location
        self.model = None
        
        self._init_vertex_ai()

    def _init_vertex_ai(self):
        # Kiểm tra file chìa khóa có tồn tại không
        try:
            if not os.path.exists(self.credentials_path):
                logger.error(f"❌ Credentials not found")
                return
            
            # Đăng nhập vào Google Vertex AI
            credentials = service_account.Credentials.from_service_account_file(self.credentials_path)
            vertexai.init(project=self.project_id, location=self.location, credentials=credentials)
            
            # Thử nạp model Imagen 3 (mới nhất) hoặc model cũ hơn nếu lỗi
            for model_id in ["imagen-3.0-fast-generate-001", "imagegeneration@006"]:
                try:
                    self.model = ImageGenerationModel.from_pretrained(model_id)
                    break
                except Exception as e:
                        logger.warning(f"⚠️ Failed {model_id}: {e}")
        
        except Exception as e:
            logger.error(f"❌ Thumbnail init failed: {e}")

    
    # Hàm chính: Tạo ảnh bìa (600x900px).
    #Quy trình: Vẽ ảnh -> Cắt ảnh -> Thêm dải đen mờ -> Viết chữ -> Trả về dữ liệu.
    async def generate_thumbnail(
        self,
        title: str,
        short_title: str,
        character_design: str,
        background_design: str,
        story_tone: str = "gentle"
    ) -> Optional[bytes]:
        """
        Generate story cover thumbnail (2:3 ratio, 600x900px).
        
        Args:
            title: Full story title
            short_title:  Short title for display
            character_design: Character description
            background_design: Background description
            story_tone: Story tone (gentle/funny/adventurous)
        
        Returns:
            Image bytes (WEBP) or None
        """

        if not self.model:
            logger.error("❌ Model not ready")
            return await self._get_fallback_thumbnail(short_title)
        
        # Build thumbnail prompt
        # 1. Xây dựng câu lệnh (prompt) để họa sĩ AI hiểu ý đồ
        prompt = self._build_thumbnail_prompt(
            character_design,
            background_design,
            story_tone
        )
        
        logger.info(f"🎨 Generating thumbnail:  {short_title}")

        
        try:
            loop = asyncio.get_running_loop()
            # 2. Chạy lệnh vẽ ảnh trong một luồng riêng (asyncio) để không làm treo app
            def _gen():
                return self.model.generate_images(
                    prompt=prompt,
                    number_of_images=1,
                    aspect_ratio="9:16",  # Vẽ khổ dọc (tương đương 2:3)
                    safety_filter_level="block_only_high", # Lọc nội dung nhạy cảm
                    person_generation="allow_all"
                )
            
            response = await loop.run_in_executor(None, _gen)

            # Extract image
            if hasattr(response, 'images') and response.images:
                img = response.images[0]
                if hasattr(img, '_image_bytes'):
                    image_bytes = img._image_bytes
                    
                    # Resize to 600x900 and add title overlay
                    final_bytes = self._process_thumbnail(
                        image_bytes,
                        short_title
                    )
                    
                    logger.info(f"✅ Thumbnail generated: {len(final_bytes)} bytes")
                    return final_bytes
        except Exception as e: 
            logger.error(f"❌ Thumbnail generation failed: {e}")
        
        # Fallback
        return await self._get_fallback_thumbnail(short_title)   

    
    # Xây dựng câu lệnh (Prompt) tối ưu cho bìa sách.
    def _build_thumbnail_prompt(
        self,
        character_design: str,
        background_design: str,
        tone: str
    ) -> str:
        """Build optimized prompt for thumbnail."""
        
        tone_keywords = {
            "gentle": "soft, warm, peaceful, heartwarming",
            "funny":  "playful, cheerful, whimsical, joyful",
            "adventurous": "exciting, dynamic, epic, bold"
        }
        
        keywords = tone_keywords.get(tone, "magical, enchanting")
        
        prompt = (
            f"Book cover illustration, portrait orientation, "
            f"{character_design}, {background_design}, "
            f"{keywords}, storybook cover art, "
            f"professional children's book illustration, "
            f"Pixar style, vibrant colors, "
            f"cinematic lighting, high quality, "
            f"suitable for book cover thumbnail"
        )
        
        return prompt


    # Xử lý đồ họa: Resize, thêm Gradient đen mờ và chèn Tiêu đề.
    def _process_thumbnail(
        self,
        image_bytes: bytes,
        short_title: str
    ) -> bytes:
        """
        Process thumbnail: 
        1. Resize to 600x900 (2:3 ratio)
        2. Add gradient overlay at bottom
        3. Add title text
        4. Convert to WEBP
        """
        
        try:
            # Load image
            img = Image.open(io.BytesIO(image_bytes))
            
            # Resize to 600x900 (2:3 ratio)
            img = img.resize((600, 900), Image.LANCZOS)
            
            # Create gradient overlay for text
            overlay = Image.new('RGBA', (600, 900), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Draw gradient at bottom (for text contrast)
            for y in range(700, 900):
                alpha = int((y - 700) / 200 * 180)  # 0 to 180
                draw.rectangle(
                    [(0, y), (600, y+1)],
                    fill=(0, 0, 0, alpha)
                )
            
            # Composite overlay
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay)
            
            # Add title text
            draw = ImageDraw.Draw(img)
            
            # Try to load font
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            # Wrap text if too long
            lines = self._wrap_text(short_title, 20)
            
            # Draw text (bottom area)
            y_start = 820 - (len(lines) * 55)
            for i, line in enumerate(lines):
                # Get text bounding box
                bbox = draw. textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                
                # Center text
                x = (600 - text_width) // 2
                y = y_start + (i * 55)
                
                # Draw text with shadow
                draw.text((x+2, y+2), line, fill=(0, 0, 0, 200), font=font)
                draw.text((x, y), line, fill=(255, 255, 255, 255), font=font)
            
            # Convert to WEBP
            output = io.BytesIO()
            img = img.convert('RGB')
            img.save(output, format='WEBP', quality=90)
            
            return output. getvalue()
        
        except Exception as e: 
            logger.error(f"❌ Thumbnail processing failed: {e}")
            return image_bytes

    
    # Cắt tiêu đề thành nhiều dòng để không bị tràn bìa
    def _wrap_text(self, text: str, max_chars: int) -> list:
        """Wrap text into multiple lines."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_chars:
                current_line.append(word)
                current_length += len(word) + 1
            else: 
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    # Tạo bìa màu đơn giản nếu AI lỗi
    async def _get_fallback_thumbnail(self, short_title: str) -> bytes:
        """Generate fallback thumbnail with gradient."""
        
        # Create 600x900 gradient image
        img = Image.new('RGB', (600, 900), color=(138, 43, 226))  # Purple
        draw = ImageDraw.Draw(img)
        
        # Gradient from purple to pink
        for y in range(900):
            r = int(138 + (y / 900) * (255 - 138))
            g = int(43 + (y / 900) * (182 - 43))
            b = int(226 + (y / 900) * (193 - 226))
            draw.line([(0, y), (600, y)], fill=(r, g, b))
        
        # Add decorative elements
        draw.ellipse([50, 100, 150, 200], fill=(255, 255, 255, 50))
        draw.ellipse([450, 300, 550, 400], fill=(255, 255, 255, 30))
        
        # Add title
        try:
            font = ImageFont. truetype("arial.ttf", 52)
        except:
            font = ImageFont.load_default()
        
        lines = self._wrap_text(short_title, 18)
        y_start = 400
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (600 - text_width) // 2
            y = y_start + (i * 60)
            
            # Shadow
            draw.text((x+3, y+3), line, fill=(0, 0, 0), font=font)
            # Text
            draw.text((x, y), line, fill=(255, 255, 255), font=font)
        
        # Convert to WEBP
        output = io.BytesIO()
        img. save(output, format='WEBP', quality=85)
        
        return output. getvalue()
