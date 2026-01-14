"""
Story generation prompts - Enhanced với title uniqueness và mythology integration
Target: <900 tokens, chính xác words/scene, NO duplicate titles
"""

from typing import Optional, Dict
import logging
import random
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

# =================================
# STORY LENGTH CONFIGURATION (THEO BẢNG CHÍNH XÁC)
# =================================

STORY_CONFIG = {
    "short": {
        "num_scenes": 6,
        "words_per_scene": (25, 50),
        "total_words": (150, 300),
        "sentences_per_scene": (3, 5),
    },
    "medium": {
        "num_scenes": 10,
        "words_per_scene": (38, 50),
        "total_words": (380, 500),
        "sentences_per_scene": (4, 6),
    },
    "long": {
        "num_scenes": 14,
        "words_per_scene": (56, 60),
        "total_words": (784, 840),
        "sentences_per_scene": (5, 7),
    },
}

# =================================
# TITLE STYLE VARIATIONS (để tránh trùng lặp)
# =================================

TITLE_STYLES = [
    "classic",      # "The Princess and the Dragon"
    "modern",       # "When Dragons Meet Princesses"
    "whimsical",    # "A Dragon's Tale of Magic"
    "epic",         # "Legend of the Crystal Dragon"
    "poetic",       # "Where Starlight Meets the Sea"
]

# =================================
# MYTHOLOGY REGION KEYWORDS (tích hợp với character naming)
# =================================

MYTHOLOGY_HINTS = {
    "norse": ["viking warriors", "ancient runes", "frozen fjords", "northern lights"],
    "japanese": ["cherry blossoms", "sacred temples", "samurai honor", "zen gardens"],
    "greek": ["marble columns", "ancient olympus", "mediterranean shores", "mythic heroes"],
    "celtic": ["mystical druids", "emerald hills", "ancient forests", "fairy circles"],
    "egyptian": ["golden pyramids", "desert sands", "pharaoh's treasures", "nile rivers"],
    "fantasy": ["enchanted forests", "crystal caves", "magic spells", "floating islands"]
}


def get_scene_config(story_length: str) -> Dict:
    """Lấy cấu hình CHÍNH XÁC theo bảng."""
    config = STORY_CONFIG.get(story_length, STORY_CONFIG["short"])
    
    num_scenes = config["num_scenes"]
    words_min, words_max = config["words_per_scene"]
    avg_words_per_scene = (words_min + words_max) / 2
    target_words = int(num_scenes * avg_words_per_scene)
    
    return {
        "num_scenes": num_scenes,
        "words_per_scene_min": words_min,
        "words_per_scene_max": words_max,
        "target_words": target_words,
        "sentences_per_scene": config["sentences_per_scene"]
    }


def get_scene_count(story_length: str) -> int:
    """Get fixed scene count."""
    return STORY_CONFIG.get(story_length, STORY_CONFIG["short"])["num_scenes"]


def detect_mythology_region(user_input: str, theme: Optional[str] = None) -> str:
    """
    Phát hiện mythology region từ user input để inject hints.
    Tương đồng với CharacterNameExtractor.detect_mythology_region()
    """
    combined_text = f"{user_input} {theme or ''}".lower()
    
    if any(word in combined_text for word in ["viking", "norse", "rune", "fjord", "ice", "snow"]):
        return "norse"
    elif any(word in combined_text for word in ["samurai", "cherry", "temple", "zen", "kimono", "japan"]):
        return "japanese"
    elif any(word in combined_text for word in ["olympus", "toga", "marble", "greek", "sparta", "hero"]):
        return "greek"
    elif any(word in combined_text for word in ["druid", "clover", "mist", "celtic", "ireland", "fairy"]):
        return "celtic"
    elif any(word in combined_text for word in ["pyramid", "desert", "sphinx", "pharaoh", "egypt", "nile"]):
        return "egyptian"
    
    return "fantasy"


def generate_uniqueness_seed() -> str:
    """
    Tạo unique seed dựa trên timestamp để force AI generate title khác nhau.
    Returns: Short hash (6 chars)
    """
    timestamp = datetime.now().isoformat()
    hash_obj = hashlib.md5(timestamp.encode())
    return hash_obj.hexdigest()[:6]


# =================================
# ENHANCED SYSTEM PROMPT
# =================================

SYSTEM_PROMPT = """⚠️ IMPORTANT: You are a professional children's fairy tale writer for ages 2-12. Generate UNIQUE, creative stories.

⚠️ CRITICAL JSON FORMAT - MUST FOLLOW EXACTLY:
{{
  "title": "UNIQUE creative title (never repeat, use {title_style} style{mythology_hint})",
  "character_design": "EXACT DETAILS:  [age]yo [gender], [skin color], [hair:  exact style+color], [outfit: item1 color1, item2 color2, item3 color3], [eyes: color+shape], [face: features], [build: body type]",
  "background_design":  "[place type], [magic element 1], [magic element 2], [lighting], [color palette]",
  "scenes": [{{
    "scene_number": 1,
    "text": "Story text here.   {words_min}-{words_max} words.   {sentences} sentences.",
    "image_prompt":  "{{{{CHAR}}}} [specific action with details], {{{{BG}}}} at [exact location]"
  }}]
}}

⚠️ IMPORTANT - GRAMMAR RULES:
1. Write ALL numbers as WORDS: 
   - "one sunny morning" NOT "1 sunny morning"
   - "three friends" NOT "3 friends"
   - "five minutes" NOT "5 minutes"
2. Perfect English grammar and spelling
3. No contractions in narration (use "cannot" not "can't")
4. Proper capitalization

⚠️ IMPORTANT - CHARACTER DESIGN MUST INCLUDE:
- Age (written as word:  "7-year-old" not "7yo")
- Gender
- Skin color (specific:  "light brown" not just "brown")
- Hair (exact style AND color:  "short curly rainbow mohawk with green base")
- Outfit (3 items with colors: "yellow overalls with star patches, blue gloves, red sneakers")
- Eyes (color AND shape: "big curious brown eyes")
- Face features ("round cheerful face with freckles")
- Build ("slim" or "sturdy")

⚠️ IMPORTANT - IMAGE PROMPT RULES:
- Use {{{{CHAR}}}} and {{{{BG}}}} placeholders
- Describe SPECIFIC actions:  "walking nervously" not just "walking"
- Include emotional expressions: "with worried face" 
- Specify exact locations: "in the enchanted forest clearing" not "in forest"

⚠️ IMPORTANT - SCENE REQUIREMENTS:
- EXACTLY {num_scenes} scenes
- Each scene:  {words_min}-{words_max} words, {sentences} sentences
- Write numbers as WORDS throughout the story
- No spelling errors
- No grammatical mistakes

⚠️ IMPORTANT - STORY QUALITY:
- Unique title (never repeat)
- Happy ending
- Safe for children
- Emotionally engaging
- Clear narrative arc

⚠️ RETURN ONLY VALID JSON.  NO MARKDOWN.  NO EXTRA TEXT."""


# =================================
# ENHANCED USER PROMPT
# =================================

OPENERS = [
    "{tone} tale:",
    "{tone} story:",
    "{tone} adventure:",
    "{tone} journey:",
]


def create_user_prompt(
    user_input: str,
    story_length: str = "short",
    story_tone: str = "gentle",
    theme: Optional[str] = None,
    child_name: Optional[str] = None,
    num_scenes: int = 6
) -> str:
    """
    Generate enhanced prompt với:
    - Title uniqueness enforcement
    - Mythology region hints
    - Random style variations
    """
    config = get_scene_config(story_length)
    
    # Detect mythology region
    region = detect_mythology_region(user_input, theme)
    
    # Random opener và title style
    opener = random.choice(OPENERS).format(tone=story_tone.capitalize())
    title_style = random.choice(TITLE_STYLES)
    
    # Build prompt
    prompt = f"{opener} {user_input}\n"
    
    if child_name:
        prompt += f"Hero: {child_name}\n"
    
    if theme:
        prompt += f"Theme: {theme}\n"
    
    # ✅ INJECT MYTHOLOGY HINTS (subtle, không quá explicit)
    if region and region != "fantasy":
        hint = random.choice(MYTHOLOGY_HINTS[region])
        prompt += f"Inspiration: {hint}\n"
    
    # ✅ TITLE STYLE REQUIREMENT
    prompt += f"Title style: {title_style}\n"
    
    # Scene requirements
    prompt += f"\n{config['num_scenes']} scenes, {config['words_per_scene_min']}-{config['words_per_scene_max']}w/scene, numbers→words, JSON only"
    
    return prompt


def create_system_prompt(
    story_length: str = "short",
    user_input: str = "",
    theme: Optional[str] = None
) -> str:
    """
    Generate system prompt với uniqueness hints.
    
    Args:
        story_length: "short" | "medium" | "long"
        user_input: User's story idea (for region detection)
        theme: Optional theme
    
    Returns:
        Enhanced system prompt với title style và mythology hints
    """
    config = get_scene_config(story_length)
    
    # Detect region và generate hints
    region = detect_mythology_region(user_input, theme)
    title_style = random.choice(TITLE_STYLES)
    seed = generate_uniqueness_seed()
    
    # Mythology hint cho title (optional)
    mythology_hint = ""
    if region and region != "fantasy":
        mythology_hint = f", {region} inspired"
    
    return SYSTEM_PROMPT.format(
        num_scenes=config["num_scenes"],
        words_min=config["words_per_scene_min"],
        words_max=config["words_per_scene_max"],
        sentences=f"{config['sentences_per_scene'][0]}-{config['sentences_per_scene'][1]}",
        title_style=title_style,
        mythology_hint=mythology_hint,
        seed=seed
    )


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
    char = response["character_design"].lower()
    required_keywords = ["hair", "eyes"]
    missing = [k for k in required_keywords if k not in char]
    
    if missing:
        logger.warning(f"⚠️ character_design missing: {missing}")
    
    # Validate title không quá ngắn
    if len(response["title"]) < 5:
        return False, "Title too short"
    
    scenes = response["scenes"]
    if not isinstance(scenes, list) or len(scenes) == 0:
        return False, "Invalid scenes"
    
    for i, scene in enumerate(scenes, 1):
        if "scene_number" not in scene:
            return False, f"Scene {i}: missing scene_number"
        if "text" not in scene or len(scene["text"]) < 15:
            return False, f"Scene {i}: text too short"
        if "image_prompt" not in scene:
            return False, f"Scene {i}: missing image_prompt"
    
    return True, "Valid"