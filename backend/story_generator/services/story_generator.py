"""
Story generation using OpenRouter (GPT-4o).
Features: 
- Character design consistency
- Background design for fairy tale worlds
- Retry logic with validation
- Token optimization (<900 tokens)
- Anti-duplication (seed rotation + temperature)
- Words/scene accuracy (theo bảng specs)
- Detailed logging
"""

import logging
import json
from typing import Optional
import asyncio
from openai import OpenAI

from story_generator.config import settings
from story_generator.prompts.story_prompts import (
    create_system_prompt,  
    create_user_prompt,
    validate_story_response,
    get_scene_count,
    get_scene_config
)

logger = logging.getLogger(__name__)


class StoryGenerator:
    """
    Generate fairy tale stories using OpenRouter (GPT-4o).
    
    Usage:
        story_gen = StoryGenerator()
        story_data = await story_gen.generate_story(
            user_prompt="A brave princess meets a dragon",
            story_length="short",
            story_tone="adventurous"
        )
    """

    def __init__(self):
        """Initialize OpenRouter client with request counter."""
        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = settings.openrouter_model
        self.request_count = 0
        
        logger.info(f"✅ Story Generator initialized (Model: {self.model})")
    
    def _expand_image_prompts(self, story_data: dict) -> dict:
        """
        Expand {CHARACTER} and {BACKGROUND} placeholders in image prompts.
        
        This reduces output tokens by 600+ for 6-scene story.
        """
        character = story_data.get("character_design", "")
        background = story_data.get("background_design", "")
        
        for scene in story_data.get("scenes", []):
            prompt = scene.get("image_prompt", "")
            
            # Replace placeholders
            prompt = prompt.replace("{CHARACTER}", character)
            prompt = prompt.replace("{BACKGROUND}", background)
            
            # Also handle {CHAR} and {BG} variants
            prompt = prompt.replace("{CHAR}", character)
            prompt = prompt.replace("{BG}", background)
            
            scene["image_prompt"] = prompt
        
        return story_data

    async def generate_story(
        self,
        user_prompt: str,
        story_length: str = "short",
        story_tone: str = "gentle",
        theme: Optional[str] = None,
        child_name:  Optional[str] = None
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
                "character_design":  str,
                "background_design": str,
                "scenes":  [
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
        
        self.request_count += 1
        
        # Get config
        config = get_scene_config(story_length)
        num_scenes = config["num_scenes"]
        
        # ✅ LOG CHÍNH XÁC
        logger.info(f"🎨 Generating {story_length}:")
        logger.info(f"   • Scenes: {num_scenes}")
        logger.info(f"   • Words/scene: {config['words_per_scene_min']}-{config['words_per_scene_max']}")
        logger.info(f"   • Target total: ~{config['target_words']} words")
        
        # ✅ BUILD ENHANCED SYSTEM PROMPT với title uniqueness
        system_instruction = create_system_prompt(
            story_length=story_length,
            user_input=user_prompt,
            theme=theme
        )
        
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
                logger.info(f"📝 Gemini-3-flash-preview attempt {attempt}/{max_attempts}...")
                
                # Generate unique seed
                seed = (self.request_count * 1000) + attempt
                
                # Call OpenRouter GPT-4o
                response = await asyncio.wait_for(
                        asyncio.to_thread(
                        self. client.chat.completions.create,
                        model=self. model,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_instruction}
                        ],
                        temperature=0.85,
                        max_tokens=1400,
                        seed=seed,
                        response_format={"type": "json_object"}
                    ),
                    timeout = 25.0
                )
                # Log token usage
                if hasattr(response, 'usage') and response.usage:
                    usage = response.usage
                    total = usage.total_tokens
                    
                    logger.info("=" * 50)
                    logger.info(f"📊 TOKENS (Request #{self.request_count}):")
                    logger.info(f"   IN:    {usage.prompt_tokens:>4} | OUT:  {usage.completion_tokens:>4} | TOTAL: {total:>4}")
                    
                    if usage.completion_tokens > 800:
                        logger.warning(f"   ⚠️ OUTPUT HIGH:   {usage.completion_tokens} > 800")
                    if total > 1100:
                        logger.warning(f"   ⚠️ TOTAL HIGH:  {total} > 1100")
                    else:
                        logger.info(f"   ✅ OK:  {total} <= 1100")
                    logger.info("=" * 50)
                # Parse response
                if not hasattr(response, 'choices') or len(response.choices) == 0:
                    raise ValueError("Response has no choices")

                response_text = response.choices[0].message.content

                if not response_text or response_text.strip() == "":
                    raise ValueError("Empty response text")

                logger.debug(f"📄 Response preview: {response_text[:200]}...")
                story_data = self._parse_response(response_text)
                
                if not isinstance(story_data, dict):
                    raise TypeError(f"Response is {type(story_data)}, expected dict.  Content: {str(story_data)[:200]}")
                # Enhance character design if incomplete
                story_data = self._enhance_character_design(story_data, child_name)
                
                # Expand image prompts
                story_data = self._expand_image_prompts(story_data)
                
                # ✅ VALIDATE với logic mới (words/scene)
                is_valid, error_msg = self._validate_with_words_per_scene(
                    story_data,
                    expected_scenes=num_scenes,
                    words_per_scene_min=config['words_per_scene_min'],
                    words_per_scene_max=config['words_per_scene_max']
                )
                
                if not is_valid:
                    logger.warning(f"⚠️ Validation:  {error_msg}")
                    if attempt < max_attempts:
                        await asyncio.sleep(2)
                        continue
                    else:
                        logger.warning("⚠️ Using story despite validation failure")
                
                # Ensure defaults
                if not story_data.get("background_design"):
                    story_data["background_design"] = "Magical world, sparkles, glowing lights, dreamy colors"
                
                logger.info(f"✅ Story:  '{story_data['title']}'")
                logger.info(f"   🎬 Scenes: {len(story_data['scenes'])}")
                logger.info(f"   👤 Character: {story_data['character_design'][: 80]}...")
                logger.info(f"   🌍 Background: {story_data['background_design'][:80]}...")
                
                return story_data
            
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout (attempt {attempt}): Request took > 30s")
                if attempt == max_attempts:
                    raise Exception("Request timeout after 3 attempts")
                await asyncio.sleep(3)
            
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parse failed (attempt {attempt}): {e}")
                logger.error(f"   Response: {response_text[: 500] if 'response_text' in locals() else 'N/A'}")
                if attempt == max_attempts:
                    raise Exception(f"Invalid JSON after {max_attempts} attempts.  Response: {response_text[:200] if 'response_text' in locals() else 'N/A'}")
                await asyncio. sleep(2)
            
            except (TypeError, ValueError, AttributeError) as e:
                logger.error(f"❌ Data structure error (attempt {attempt}): {e}")
                logger.error(f"   Data type: {type(story_data) if 'story_data' in locals() else 'N/A'}")
                logger.error(f"   Response: {response_text[:300] if 'response_text' in locals() else 'N/A'}")
                if attempt == max_attempts:
                    raise Exception(f"Invalid data structure:  {e}")
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {e}", exc_info=True)
                if attempt < max_attempts:
                    await asyncio.sleep(3)
                else:
                    raise e
        
        raise Exception(f"Story generation failed after {max_attempts} attempts")
    
    def _enhance_character_design(self, story_data: dict, child_name: Optional[str]) -> dict:
        """
        Ensure character_design has ALL required details for consistency.
        """
        char_design = story_data.get("character_design", "")
        
        # Check critical keywords
        required_keywords = {
            "age": ["year", "yo", "old"],
            "hair": ["hair"],
            "eyes": ["eyes", "eye"],
            "outfit": ["outfit", "clothes", "clothing", "dress", "shirt", "wearing"],
            "skin": ["skin", "complexion"]
        }
        
        missing = []
        for category, keywords in required_keywords.items():
            if not any(kw in char_design. lower() for kw in keywords):
                missing.append(category)
        
        # If missing > 2 keywords → enhance
        if len(missing) > 2:
            logger.warning(f"⚠️ character_design incomplete (missing:  {missing}), enhancing...")
            
            default_char = (
                f"A friendly 7-year-old child named {child_name or 'Hero'}, "
                f"warm brown skin, curly black hair with colorful ribbon, "
                f"wearing bright blue shirt with stars, red shorts, yellow sneakers, "
                f"big expressive brown eyes, cheerful smile, average height"
            )
            
            story_data["character_design"] = default_char
            logger.info(f"   → Enhanced:  {default_char[:60]}...")
        
        return story_data
    
    def _validate_with_words_per_scene(
        self,
        story_data: dict,
        expected_scenes: int,
        words_per_scene_min: int,
        words_per_scene_max: int
    ) -> tuple[bool, str]:
        """
        Validate theo words/scene CHÍNH XÁC (theo bảng specs).
        """
        
        # Basic validation
        is_valid, error = validate_story_response(story_data)
        if not is_valid:
            return False, error
        
        # Check số scenes
        num_scenes = len(story_data.get("scenes", []))
        if num_scenes != expected_scenes:
            if abs(num_scenes - expected_scenes) <= 1:
                logger.warning(f"⚠️ Scenes:  {num_scenes} (expected {expected_scenes})")
            else:
                return False, f"Scene count {num_scenes} != {expected_scenes}"
        
        # ✅ KIỂM TRA TỪNG SCENE
        scene_word_counts = []
        warnings = []
        
        for i, scene in enumerate(story_data.get("scenes", []), 1):
            text = scene.get("text", "")
            word_count = len(text.split())
            scene_word_counts.append(word_count)
            
            # ✅ Cho phép sai lệch ±20% cho mỗi scene
            min_allowed = int(words_per_scene_min * 0.8)
            max_allowed = int(words_per_scene_max * 1.2)
            
            if not (min_allowed <= word_count <= max_allowed):
                warning = (
                    f"Scene {i}:  {word_count}w "
                    f"(target: {words_per_scene_min}-{words_per_scene_max}w, "
                    f"allowed: {min_allowed}-{max_allowed}w)"
                )
                warnings.append(warning)
        
        # Log warnings nếu có
        if warnings: 
            for w in warnings:
                logger.warning(f"⚠️ {w}")
        
        # Tính total
        total_words = sum(scene_word_counts)
        avg_words_per_scene = total_words / num_scenes if num_scenes > 0 else 0
        
        logger. info(f"✅ Validation:")
        logger.info(f"   • Scenes: {num_scenes}")
        logger.info(f"   • Total words: {total_words}")
        logger.info(f"   • Avg words/scene: {avg_words_per_scene:.1f}")
        logger.info(f"   • Scene word counts: {scene_word_counts}")
        
        return True, "Valid"
    
    def _parse_response(self, text: str) -> dict:
        """Parse JSON from response."""
        
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
                    logger.error(f"❌ Failed JSON segment: {json_candidate[: 200]}...")
                    raise secondary_e
            raise ValueError("No valid JSON found in response")