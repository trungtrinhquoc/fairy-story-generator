"""
Story generation prompts - THEO ĐÚNG BẢNG SPECS
Target: <900 tokens, chính xác words/scene
"""

from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# =================================
# STORY LENGTH CONFIGURATION (THEO BẢNG CHÍNH XÁC)
# =================================

STORY_CONFIG = {
    "short": {
        # ✅ THEO BẢNG:  1-3 mins, 100-300 words, 4-6 scenes, 25-50 words/scene
        "num_scenes": 6,                # CỐ ĐỊNH 6 scenes (trung bình của 4-6)
        "words_per_scene":  (25, 50),    # CHÍNH XÁC từ bảng
        "total_words": (150, 300),      # 6 scenes × 25-50 = 150-300 words
        "sentences_per_scene": (3, 5),  # 25-50 words ≈ 3-5 sentences
    },
    "medium": {
        # ✅ THEO BẢNG:  4-6 mins, 300-600 words, 8-12 scenes, 37.5-50 words/scene
        "num_scenes": 10,               # CỐ ĐỊNH 10 scenes
        "words_per_scene":  (38, 50),    # Làm tròn 37.5 → 38
        "total_words": (380, 500),      # 10 scenes × 38-50 = 380-500 words
        "sentences_per_scene": (4, 6),
    },
    "long": {
        # ✅ THEO BẢNG: 7-10 mins, 600-900 words, 10-16 scenes, 56-60 words/scene
        "num_scenes": 14,               # CỐ ĐỊNH 14 scenes (trung bình 10-16)
        "words_per_scene": (56, 60),    # CHÍNH XÁC từ bảng
        "total_words": (784, 840),      # 14 scenes × 56-60 = 784-840 words
        "sentences_per_scene": (5, 7),
    },
}


def get_scene_config(story_length: str) -> Dict:
    """
    Lấy cấu hình CHÍNH XÁC theo bảng. 
    
    Returns:
        {
            "num_scenes": 6,
            "words_per_scene_min": 25,
            "words_per_scene_max":  50,
            "target_words": 225,  # Trung bình:  6 × 37.5
            "sentences_per_scene":  (3, 5)
        }
    """
    config = STORY_CONFIG. get(story_length, STORY_CONFIG["short"])
    
    # ✅ TÍNH target_words CHÍNH XÁC
    num_scenes = config["num_scenes"]
    words_min, words_max = config["words_per_scene"]
    
    # Target = trung bình words/scene × số scenes
    avg_words_per_scene = (words_min + words_max) / 2
    target_words = int(num_scenes * avg_words_per_scene)
    
    return {
        "num_scenes":  num_scenes,
        "words_per_scene_min": words_min,
        "words_per_scene_max": words_max,
        "target_words": target_words,
        "sentences_per_scene": config["sentences_per_scene"]
    }


def get_scene_count(story_length: str) -> int:
    """
    Get fixed scene count. 
    - "short" → 6 scenes
    - "medium" → 10 scenes
    - "long" → 14 scenes
    """
    return STORY_CONFIG. get(story_length, STORY_CONFIG["short"])["num_scenes"]


# =================================
# SYSTEM PROMPT (ULTRA-COMPACT:  ~120 tokens)
# =================================

SYSTEM_PROMPT = """Kids fairy tale writer. 

JSON:
{{
  "title": "creative title",
  "character_design":  "EXACT:  [age]yo [gender], [skin], [hair:  style+color], [outfit: 3 items+colors], [eyes: color], [build]",
  "background_design":  "[place], [2 magic elements], [lighting], [colors]",
  "scenes": [{{
    "scene_number": 1,
    "text": "{words_min}-{words_max} words, {sentences} sentences",
    "image_prompt": "{{CHAR}} [action], {{BG}} at [spot]"
  }}]
}}

CRITICAL: 
- EXACTLY {num_scenes} scenes
- Each scene: {words_min}-{words_max} words, {sentences} sentences
- character_design: Complete details (age, gender, skin, hair, outfit, eyes, build)
- Unique title each time
- Happy ending

JSON only."""


# =================================
# USER PROMPT (MINIMAL: ~80 tokens)
# =================================

OPENERS = [
    "{tone} tale:",
    "{tone} story:",
    "{tone} adventure:",
]


def create_user_prompt(
    user_input: str,
    story_length: str = "short",
    story_tone: str = "gentle",
    theme:  Optional[str] = None,
    child_name: Optional[str] = None,
    num_scenes: int = 6
) -> str:
    """Generate prompt với words/scene CHÍNH XÁC."""
    
    config = get_scene_config(story_length)
    
    # Bỏ random để ổn định
    opener = OPENERS[0]. format(tone=story_tone. capitalize())
    
    prompt = f"{opener} {user_input}\n"
    
    if child_name:
        prompt += f"Hero: {child_name}\n"
    if theme:
        prompt += f"Theme: {theme}\n"
    
    # ✅ YÊU CẦU CHÍNH XÁC
    prompt += (
        f"{config['num_scenes']} scenes.  "
        f"Each:  {config['words_per_scene_min']}-{config['words_per_scene_max']}w, "
        f"{config['sentences_per_scene'][0]}-{config['sentences_per_scene'][1]}s."
    )
    
    return prompt


# =================================
# VALIDATION
# =================================

def validate_story_response(response: dict) -> tuple[bool, str]:
    """Fast validation."""
    
    required = ["title", "character_design", "background_design", "scenes"]
    for field in required:
        if field not in response or not response[field]:
            return False, f"Missing {field}"
    
    # Check character_design có đủ keywords
    char = response["character_design"]. lower()
    required_keywords = ["hair", "eyes"]
    missing = [k for k in required_keywords if k not in char]
    
    if missing:
        logger.warning(f"⚠️ character_design missing:  {missing}")
    
    scenes = response["scenes"]
    if not isinstance(scenes, list) or len(scenes) == 0:
        return False, "Invalid scenes"
    
    for i, scene in enumerate(scenes, 1):
        if "scene_number" not in scene: 
            return False, f"Scene {i}:  missing scene_number"
        if "text" not in scene or len(scene["text"]) < 15:
            return False, f"Scene {i}: text too short"
        if "image_prompt" not in scene:
            return False, f"Scene {i}: missing image_prompt"
    
    return True, "Valid"