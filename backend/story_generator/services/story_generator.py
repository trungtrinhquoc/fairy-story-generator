"""
Story generation using Google Gemini. 
Features:
- Character design consistency
- Background design for fairy tale worlds
- Retry logic with validation
- Detailed logging
"""

import logging
import json
from typing import Optional
import google.generativeai as genai
from openai import OpenAI
import asyncio

from story_generator.config import settings
from story_generator.prompts.story_prompts import (
    SYSTEM_PROMPT,
    create_user_prompt,
    validate_story_response,
    get_scene_count
)   

logger = logging.getLogger(__name__)


class StoryGenerator:
    """
    Generate fairy tale stories using Google Gemini.
    
    Usage:
        story_gen = StoryGenerator()
        story_data = await story_gen.generate_story(
            user_prompt="A brave princess meets a dragon",
            story_length="short",
            story_tone="adventurous"
        )
    """

    # Gemini
    # def __init__(self):
    #     """Initialize Gemini."""
    #     genai.configure(api_key=settings.gemini_api_key)
        
    #     self.model = genai.GenerativeModel(
    #         model_name="gemini-2.5-flash-lite",
    #         generation_config={
    #             "temperature": 0.9,
    #             "top_p": 0.95,
    #             "max_output_tokens": 8192,
    #         }
    #     )

    # OpenRouter
    def __init__(self):
        """Initialize OpenRouter client."""
        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = settings.openrouter_model
        logger.info(f"✅ Story Generator initialized (OpenRouter: {self.model})")
    
    def _expand_image_prompts(self, story_data: dict) -> dict:
        """
        Expand {CHARACTER} and {BACKGROUND} placeholders in image prompts.
        
        This reduces output tokens by 600+ for 6-scene story.
        """
        character = story_data.get("character_design", "")
        background = story_data.get("background_design", "")
        
        for scene in story_data. get("scenes", []):
            prompt = scene.get("image_prompt", "")
            
            # Replace placeholders
            prompt = prompt.replace("{CHARACTER}", character)
            prompt = prompt.replace("{BACKGROUND}", background)
            
            scene["image_prompt"] = prompt
        
        return story_data

    async def generate_story(
        self,
        user_prompt: str,
        story_length: str = "short",
        story_tone: str = "gentle",
        theme: Optional[str] = None,
        child_name: Optional[str] = None
    ) -> dict:
        """
        Generate complete story with character and background design.
        
        Args:
            user_prompt: User's story idea
            story_length: "short" (6), "medium" (10), or "long" (14) scenes
            story_tone: "gentle", "funny", or "adventurous"
            theme: Optional theme (princess, dragon, etc.)
            child_name: Optional name to include in story
            
        Returns:
            dict with:
            {
                "title": str,
                "character_design": str,
                "background_design": str,
                "scenes": [
                    {
                        "scene_number": int,
                        "text": str,
                        "image_prompt": str,
                        "word_count": int
                    }
                ]
            }
            
        Raises:
            Exception: If generation fails after max attempts
        """
        
        num_scenes = get_scene_count(story_length)
        logger.info(f"🎨 Generating {story_length} story with {num_scenes} scenes...")
        
        # Build prompt
        system_instruction = SYSTEM_PROMPT
        user_instruction = create_user_prompt(
            user_input=user_prompt,
            story_length=story_length,
            story_tone=story_tone,
            theme=theme,
            child_name=child_name,
            num_scenes=num_scenes
        )
        
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"📝 ChatGPT-4o attempt {attempt}/{max_attempts}...")
                
                # Call Gemini
                # response = await asyncio.to_thread(
                #     self.model.generate_content,
                #     [system_instruction, user_instruction]
                # )

                # if hasattr(response, 'usage_metadata'):
                #     usage = response.usage_metadata
                #     logger.info("=" * 30)
                #     logger.info(f"📊 GEMINI TOKEN USAGE:")
                #     logger.info(f"   • Prompt Tokens (Input): {usage.prompt_token_count}")
                #     logger.info(f"   • Candidates Tokens (Output): {usage.candidates_token_count}")
                #     logger.info(f"   • Total Tokens: {usage.total_token_count}")
                #     logger.info("=" * 30)

                # response_text = response.text
                # story_data = self._parse_response(response_text)

                # Call gpt-4o
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_instruction}
                    ],
                    temperature=0.9,
                    max_tokens=4000,
                    response_format={"type": "json_object"} 
                )
                if hasattr(response, 'usage') and response.usage:
                    usage = response.usage
                    logger.info("=" * 30)
                    logger.info(f"📊 OPENROUTER TOKEN USAGE:")
                    logger.info(f"   • Prompt Tokens (Input): {usage.prompt_tokens}")
                    logger.info(f"   • Completion Tokens (Output): {usage.completion_tokens}")
                    logger.info(f"   • Total Tokens: {usage.total_tokens}")
                    logger.info("=" * 30)
                # Extract content from OpenAI response
                response_text = response.choices[0].message.content
                # Parse response
                story_data = self._parse_response(response_text)
                story_data = self._expand_image_prompts(story_data)
                is_valid, error_msg = validate_story_response(story_data)
                if not is_valid:
                    logger. warning(f"⚠️ Validation failed: {error_msg}")
                    if attempt < max_attempts:
                        await asyncio.sleep(2)
                        continue
                    else:
                        raise ValueError(f"Validation failed: {error_msg}")
                
                # Đảm bảo character_design tồn tại
                if "character_design" not in story_data or not story_data["character_design"]:
                    default_char = f"A friendly {child_name or 'child'} with bright eyes and a warm smile, wearing colorful magical clothing"
                    story_data["character_design"] = default_char
                    logger.warning(f"⚠️ Missing character_design. Set to default: {default_char}")
                
                # Đảm bảo background_design tồn tại
                if "background_design" not in story_data or not story_data["background_design"]:
                    default_bg = "A whimsical enchanted world filled with sparkling magic, glowing lights, vibrant colorful nature, floating fairy dust, and a dreamy fairytale atmosphere"
                    story_data["background_design"] = default_bg
                    logger.warning(f"⚠️ Missing background_design. Set to default: {default_bg}")
                
                # Success! 
                logger.info(f"✅ Story generated: '{story_data['title']}'")
                logger.info(f"   🎬 Scenes: {len(story_data['scenes'])}")
                logger. info(f"   👤 Character: {story_data['character_design'][:70]}...")
                logger.info(f"   🌍 Background: {story_data['background_design'][:70]}...")
                
                return story_data
            
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parsing failed (attempt {attempt}): {e}")
                if attempt == max_attempts:
                    raise Exception(f"Failed to parse Gemini response after {max_attempts} attempts")
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {e}")
                if attempt < max_attempts:
                    # Tính thời gian chờ tăng dần: 5s, 10s.
                    # Lỗi 429 cần chờ lâu hơn lỗi mạng bình thường.
                    wait_time = 5 * attempt 
                    
                    logger.warning(f"⏳ Waiting {wait_time}s before retrying due to error...")
                    await asyncio.sleep(wait_time) # 👈 Dòng này giúp Google reset quota cho bạn
                else:
                    # Hết lượt thử mới throw lỗi ra ngoài
                    raise e
        
        raise Exception("Story generation failed after {max_attempts} attempts")
    
    def _parse_response(self, text: str) -> dict:
        """Parse JSON from Gemini response."""
        
        cleaned = text.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        try:
            return json. loads(cleaned)
        except json.JSONDecodeError:
            # Try to find JSON in text
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start != -1 and end > start:
                json_candidate = cleaned[start:end]
                try:
                    return json.loads(json_candidate)
                except json.JSONDecodeError as secondary_e:
                    logger.error(f"❌ Secondary JSON decode failed: {secondary_e}")
                    logger.error(f"❌ Failed JSON segment: {json_candidate[:200]}...")
                    raise secondary_e
            raise ValueError("No valid JSON found in response")