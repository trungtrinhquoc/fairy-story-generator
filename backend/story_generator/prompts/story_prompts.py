# """
# Story generation prompts for Google Gemini.
# Simple version - focus on working, not perfect.
# """

# from typing import Optional
# import logging

# logger = logging.getLogger(__name__)

# # =================================
# # SYSTEM PROMPT
# # =================================

# SYSTEM_PROMPT = """You are an expert FAIRY TALE story writer for children aged 4-10 years old. 

# Your stories should be:
# - Magical and enchanting with clear beginning, middle, and end
# - Written in simple, engaging language (5-7 sentences per scene)
# - Safe, positive, and age-appropriate
# - Rich in visual descriptions for image generation

# OUTPUT FORMAT (JSON):
# {
#   "title": "Story Title",
#   "character_design": "Detailed visual description of main character.  Include: age, hair (color/style), clothing (colors/style), facial expression, distinctive features.  Example: 'A 6-year-old girl with curly red hair in pigtails, wearing a green t-shirt with flower pattern, blue denim overalls, white sneakers, bright curious green eyes, warm friendly smile'",
#   "background_design": "Detailed description of the fairy tale world setting that remains consistent.  Include: environment type, magical elements, lighting, atmosphere, colors, mood. Example: 'A whimsical enchanted forest with towering ancient trees covered in glowing purple moss, floating golden fireflies, sparkling crystal streams, soft magical mist at ground level, warm golden sunlight filtering through emerald leaves, rainbow-colored mushrooms, gentle fairy dust sparkles in the air'",
#   "scenes": [
#     {
#       "scene_number": 1,
#       "text": "Scene narrative text here (5-7 sentences)",
#       "image_prompt": "[EXACT CHARACTER DESIGN], [specific action/emotion for this scene], [EXACT BACKGROUND DESIGN with scene-specific location detail]",
#       "sentence_count": 6
#     }
#   ]
# }

# CRITICAL IMAGE PROMPT STRUCTURE:
# 1. START with EXACT text from 'character_design' field
# 2. ADD scene-specific action/emotion/pose
# 3. END with EXACT text from 'background_design' field + specific location detail

# EXAMPLE:
# {
#   "character_design": "A 5-year-old boy with short brown hair, wearing blue overalls, yellow t-shirt, red sneakers, curious brown eyes",
#   "background_design": "A magical garden with giant colorful flowers, glowing butterflies, rainbow waterfalls, golden sunbeams, floating fairy lanterns",
#   "scenes": [
#     {
#       "scene_number": 1,
#       "text": "Little Timmy discovered a mysterious glowing door hidden behind the old oak tree. The heavy wood shimmered with soft, magical light. Timmy pushed the door open, feeling a rush of wonder and excitement. Beyond the door was a path leading deeper into the garden. He stepped onto the path, knowing a great adventure had just begun.",
#       "image_prompt": "A 5-year-old boy with short brown hair, wearing blue overalls, yellow t-shirt, red sneakers, curious brown eyes, excitedly pointing at a sparkling wooden door, in a magical garden with giant colorful flowers, glowing butterflies, rainbow waterfalls, golden sunbeams, floating fairy lanterns, standing near an ancient oak tree with a glowing door in its trunk",
#       "sentence_count": 5
#     }
#   ]
# }

# FAIRY TALE ATMOSPHERE KEYWORDS (use liberally):
# - Environment: enchanted, magical, mystical, whimsical, dreamy, fantastical
# - Lighting: golden hour glow, sparkling starlight, soft magical radiance, twinkling lights
# - Elements: glowing, shimmering, sparkling, floating, dancing, swirling
# - Mood: wonder-filled, joyful, peaceful, adventurous, heartwarming
# - Settings: enchanted forests, fairy kingdoms, magical castles, crystal caves, rainbow meadows

# SAFETY REQUIREMENTS:
# - Use warm, friendly, gentle tone
# - NO violence, scary content, or dark themes
# - Bright, vibrant, colorful descriptions
# - Positive emotions and happy endings
# - Age-appropriate vocabulary
# """

# # =================================
# # USER PROMPT BUILDER
# # =================================

# def create_user_prompt(
#     user_input: str,
#     story_length: str = "short",
#     story_tone: str = "gentle",
#     theme: Optional[str] = None,
#     child_name: Optional[str] = None,
#     num_scenes: int = 6
# ) -> str:
#     """Build simple user prompt."""
    
#     prompt = f"Create a {story_tone} children's story.\n\n"
#     prompt += f"**Topic:** {user_input}\n"
    
#     if child_name:
#         prompt += f"**Main character name:** {child_name}\n"
#     if theme:
#         prompt += f"**Theme:** {theme}\n"
    
#     prompt += f"**Number of scenes:** {num_scenes}\n"
#     prompt += f"**Sentences per scene:** 5-7\n"
#     prompt += f"**Style:** Magical fairy tale with enchanted atmosphere\n\n"
    
#     prompt += """**STEP-BY-STEP INSTRUCTIONS:**

# 1. **Create Character Design:**
#    - Describe the main character in detail
#    - Include: age, hair (color/style), clothing (colors/items), facial features, expression
#    - Be specific with colors and visual details
#    - This description will be used EXACTLY in every scene's image

# 2. **Create Background Design:**
#    - Describe the fairy tale world setting
#    - Include: environment type, magical elements, lighting, colors, atmosphere
#    - Make it enchanting and whimsical
#    - This description will be used EXACTLY in every scene's image

# 3.  **Write Each Scene:**
#    - Scene text: 5-7 sentences, simple language, engaging narrative
#    - Image prompt format: [EXACT character_design] + [scene action] + [EXACT background_design + location detail]

# 4. **Ensure Consistency:**
#    - Every scene's image_prompt MUST start with the EXACT character_design
#    - Every scene's image_prompt MUST include the EXACT background_design
#    - Only the middle part (action/location) changes per scene

# 5. **Add Fairy Tale Magic:**
#    - Use magical keywords: enchanted, sparkling, glowing, mystical
#    - Create wonder and delight
#    - Keep tone positive and warm

# 6. **Output Valid JSON:**
#    - Follow the exact structure shown in the system prompt
#    - Include all required fields
#    - Ensure proper JSON formatting

# **QUALITY CHECKLIST:**
# ✓ Character design is detailed and visual
# ✓ Background design creates fairy tale atmosphere
# ✓ Each scene text is 5-7 sentences
# ✓ Each image_prompt uses EXACT character + background designs
# ✓ Story has clear beginning, middle, end
# ✓ Language is age-appropriate (4-10 years)
# ✓ Tone is warm, safe, and magical

# Generate the fairy tale story now following all instructions above. 
# """
    
#     return prompt


# # =================================
# # VALIDATION
# # =================================

# def validate_story_response(response: dict) -> tuple[bool, str]:
#     """
#     Validate Gemini response structure.
    
#     Args:
#         response: Parsed JSON response from Gemini
        
#     Returns:
#         (is_valid, error_message)
#     """
    
#     # Check title
#     if "title" not in response or not response["title"]:
#         return False, "Missing or empty title"
    
#     # Check character_design
#     if "character_design" not in response or not response["character_design"]:
#         return False, "Missing or empty character_design"
    
#     # Check background_design (warn but don't fail)
#     if "background_design" not in response or not response["background_design"]:
#         logger.warning("⚠️ Missing background_design - will use default")
    
#     # Check scenes
#     if "scenes" not in response:
#         return False, "Missing scenes field"
    
#     if not isinstance(response["scenes"], list):
#         return False, "Scenes must be a list"
    
#     if len(response["scenes"]) == 0:
#         return False, "No scenes generated"
    
#     # Validate each scene
#     for i, scene in enumerate(response["scenes"], 1):
#         # Check scene_number
#         if "scene_number" not in scene:
#             return False, f"Scene {i}: missing scene_number"
        
#         # Check text
#         if "text" not in scene:
#             return False, f"Scene {i}: missing text"
        
#         if len(scene["text"].strip()) < 50:
#              # Đây là kiểm tra HEURISTIC (ước tính) vì đếm câu chính xác rất phức tạp.
#              return False, f"Scene {i}: text is too short. Expected 5-7 sentences, got less than 50 characters."
        
#         # ---------------------------------------------
#         # ✅ SỬA ĐỔI CHÍNH: Kiểm tra trường sentence_count
#         # ---------------------------------------------
#         SENTENCE_COUNT_KEY = "sentence_count"
        
#         if SENTENCE_COUNT_KEY not in scene:
#             return False, f"Scene {i}: missing {SENTENCE_COUNT_KEY} field"
            
#         count = scene[SENTENCE_COUNT_KEY]
#         if not isinstance(count, int) or not (5 <= count <= 7):
#              return False, f"Scene {i}: {SENTENCE_COUNT_KEY} must be an integer between 5 and 7."
        
#         # Check image_prompt
#         if "image_prompt" not in scene:
#             return False, f"Scene {i}: missing image_prompt"
        
#         if len(scene["image_prompt"].strip()) < 20:
#             return False, f"Scene {i}: image_prompt too short"
    
#     return True, "Valid"


# def get_scene_count(story_length: str) -> int:
#     """
#     Get number of scenes based on story length.
    
#     Args:
#         story_length: "short" | "medium" | "long"
        
#     Returns:
#         Number of scenes (6, 10, or 14)
#     """
#     scene_counts = {
#         "short": 6,
#         "medium": 10,
#         "long": 14
#     }
#     return scene_counts.get(story_length, 6)

"""
Story generation prompts - Ultra-optimized for minimal tokens
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)

# =================================
# SYSTEM PROMPT (ULTRA-COMPACT)
# =================================

SYSTEM_PROMPT = """Fairy tale writer for kids 4-10.

OUTPUT JSON:
{
  "title":  "string",
  "character_design": "age, hair, clothes, eyes, expression",
  "background_design": "environment, magic, lighting, colors",
  "scenes": [
    {
      "scene_number": 1,
      "text": "5-7 sentences",
      "image_prompt": "{CHARACTER} + action, {BACKGROUND} + location"
    }
  ]
}

IMAGE PROMPT FORMAT:
- Use placeholders: {CHARACTER} = character_design, {BACKGROUND} = background_design
- Add only:  action + specific location
- Example: "{CHARACTER} jumping over rainbow bridge, {BACKGROUND} in crystal valley"

RULES:
- Magical, safe, positive
- 5-7 sentences per scene
- Happy ending
- No violence

Return JSON only."""

# =================================
# USER PROMPT (MINIMAL)
# =================================

def create_user_prompt(
    user_input: str,
    story_length: str = "short",
    story_tone: str = "gentle",
    theme:  Optional[str] = None,
    child_name: Optional[str] = None,
    num_scenes: int = 6
) -> str:
    """Minimal prompt."""
    
    prompt = f"{story_tone} fairy tale:  {user_input}\n"
    
    if child_name:
        prompt += f"Character: {child_name}\n"
    if theme:
        prompt += f"Theme: {theme}\n"
    
    prompt += f"Scenes: {num_scenes}, each 5-7 sentences.\n\n"
    prompt += "JSON with title, character_design, background_design, scenes.\n"
    prompt += "Image prompts use {CHARACTER} and {BACKGROUND} placeholders."
    
    return prompt


# =================================
# VALIDATION (RELAXED)
# =================================

def validate_story_response(response:  dict) -> tuple[bool, str]:
    """Fast validation."""
    
    required = ["title", "character_design", "background_design", "scenes"]
    for field in required:
        if field not in response or not response[field]:
            return False, f"Missing {field}"
    
    scenes = response["scenes"]
    if not isinstance(scenes, list) or len(scenes) == 0:
        return False, "Invalid scenes"
    
    for i, scene in enumerate(scenes, 1):
        if "scene_number" not in scene:
            return False, f"Scene {i}: missing scene_number"
        if "text" not in scene or len(scene["text"]) < 30:
            return False, f"Scene {i}: text too short"
        if "image_prompt" not in scene:
            return False, f"Scene {i}: missing image_prompt"
    
    return True, "Valid"


def get_scene_count(story_length: str) -> int:
    """Scene count."""
    return {"short": 6, "medium": 10, "long": 14}.get(story_length, 6)