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
    Tạo TRULY UNIQUE seed với UUID + timestamp microsecond. 
    """
    import uuid
    import random as rand
    
    # Combine UUID + timestamp + random
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")  
    random_num = str(rand.randint(10000, 99999))
    
    combined = f"{unique_id}-{timestamp}-{random_num}"
    hash_obj = hashlib.md5(combined.encode())
    
    return hash_obj.hexdigest()[:10]


# =================================
# ENHANCED SYSTEM PROMPT
# =================================

SYSTEM_PROMPT = """Fairy tale writer for kids 2-12. Create UNIQUE magical stories.

JSON:
{{
  "title": "Magical title ({title_style}{mythology_hint})",
  "character_design": "EXACT DETAILS:  [age]yo [gender], [skin color], [hair:  exact style+color], [outfit: item1 color1, item2 color2, item3 color3], [eyes: color+shape], [face: features], [build: body type]",
  "background_design":  "[place type], [magic element 1], [magic element 2], [lighting], [color palette]",
  "scenes": [{{"scene_number": 1, "text": "{words_min}-{words_max}w", "image_prompt": "{{{{CHAR}}}} [action], {{{{BG}}}} [location]"}}]
}}

CHARACTER (CRITICAL - MUST BE IDENTICAL IN ALL SCENES):
- Dragon→[COLOR]scales+[COLOR]wings+[SIZE]claws+[COLOR]eyes+[SIZE]body | Robot→[SHAPE]head+[COLOR]metal+[COLOR]lights+[SHAPE]antenna+[SIZE]
- MUST: SIZE(tiny/small/med/large), EXACT COLOR(emerald/ruby/silver/cyan), EXACT SHAPE(round/square/oval)
- Example: "small robot, round silver head, cyan glowing eyes, thin square antenna, orange chest panel"

TITLE (MUST be magical/whimsical, seed={seed} for uniqueness):
- AVOID boring: "Blinky's Skyward Leap","Zeep's Floating Lesson" ❌
- AVOID patterns: "Princess [Name] and the Crystal...","[Name] and the Staircase..." ❌
- AVOID: "Whispering","Emerald","Gentle Giant","Golden","Glowing","Crystal Staircase","Crystal Bridge"
- USE VARIED magical: "[Name] and the [Magical Noun]", "[Magical Adj] [Noun] of [Name]", "[Name]'s [Magical Quest]"
- Examples: "Rusty and the Singing Stars","The Sparkling Secret of Pip","Luna's Quest for the Rainbow Crystal"
- Add magic words: Crystal, Starlight, Rainbow, Enchanted, Secret, Quest, Adventure, Magic, Wonder
- NEVER repeat title patterns from previous stories

CONTENT:
- AVOID: "Deep in [place] lived","spent days","[Sound]! [Name]" (every scene)
- AVOID patterns: "High above the world, Princess...","Once upon a time in..." ❌
- VARY openings: action(50%), sound(20%), dialogue(20%), description(10%)
- NEVER start multiple scenes with same phrase

DESIGN (for 100% consistency):
- Robot: [shape]head(round/square/oval),[color]body(silver/gray/blue),[color]eyes(cyan/amber/green),[color]lights,[shape+size]antenna,[SIZE]overall
- Dragon: [color]scales(emerald/ruby/gold),[color]wings,[size]claws(small/large),[color]eyes,[SIZE]overall(tiny/small/med/large)
- Human: [skin],[hair:style+color],[3+outfit:item+color]
- EVERY feature needs: COLOR + SHAPE + SIZE

RULES:
- {num_scenes} scenes, {words_min}-{words_max}w each
- Numbers as words, happy end, safe

JSON only."""


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
    Generate CONCISE user prompt (target: <100 tokens).
    
    For mobile mode, user_input is already built by build_prompt_from_mobile_params().
    Just add scene requirements.
    """
    config = get_scene_config(story_length)
    
    # ✅ SIMPLE FORMAT: Just the story idea + scene requirements
    prompt = (
        f"{story_tone.capitalize()} story: {user_input}\n"
        f"{config['num_scenes']} scenes, {config['words_per_scene_min']}-{config['words_per_scene_max']}w/scene, JSON only"
    )
    
    return prompt


def create_system_prompt(
    story_length: str = "short",
    user_input: str = "",
    theme: Optional[str] = None
) -> str:
    """
    Generate system prompt with uniqueness seed.
    
    Args:
        story_length: "short" | "medium" | "long"
        user_input: Not used (kept for compatibility)
        theme: Not used (kept for compatibility)
    
    Returns:
        Optimized system prompt (~600 tokens)
    """
    config = get_scene_config(story_length)
    seed = generate_uniqueness_seed()
    
    return SYSTEM_PROMPT.format(
        num_scenes=config["num_scenes"],
        words_min=config["words_per_scene_min"],
        words_max=config["words_per_scene_max"],
        sentences=f"{config['sentences_per_scene'][0]}-{config['sentences_per_scene'][1]}",
        title_style=random.choice(TITLE_STYLES),
        mythology_hint="",  # Removed for simplicity
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
    
    # Check character_design có đủ keywords (chỉ check hair cho humans)
    char = response["character_design"].lower()
    
    # Detect character type
    non_human_types = ["robot", "dragon", "unicorn", "alien", "monster", "creature", "animal"]
    is_non_human = any(t in char for t in non_human_types)
    
    # Only require hair for humans
    if is_non_human:
        required_keywords = ["eyes"]  
    else:
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

# =================================
# MOBILE PARAMS BUILDER (NEW)
# =================================

def build_prompt_from_mobile_params(
    character: str,
    place: str,
    adventure: str,
    lesson:  str,
    child_name: Optional[str] = None
) -> str:
    """
    Build story prompt from mobile app parameters (OPTIMIZED).
    
    Mobile gửi 4 params chính:
    - character: "Princess", "Dragon", "Robot", etc.
    - place: "In a castle", "Under the sea", etc.
    - adventure: "Rescue a friend", "Find a hidden treasure", etc.
    - lesson: "Always help your friends", "Be brave", etc.
    
    Returns:
        Ngắn gọn prompt string (~50-80 tokens)
    """
    
    # Clean inputs
    character = character.strip()
    place = place.strip().lower()  
    adventure = adventure.strip().lower()
    lesson = lesson.strip().lower()
    
    # ✅ Validate child_name (skip nếu invalid)
    valid_child_name = None
    if child_name and child_name.strip() and child_name.strip().lower() not in ["string", "test", "null", "none"]:
        valid_child_name = child_name.strip()
    
    # ✅ Build character part (simple, no mapping needed)
    article = "An" if character[0].lower() in ['a', 'e', 'i', 'o', 'u'] else "A"
    
    if valid_child_name:
        char_part = f"{article} {character} named {valid_child_name}"
    else:
        char_part = f"{article} {character}"
    
    # ✅ Clean lesson format
    if lesson.startswith(("always ", "be ", "never ", "tell ", "listen ", "share ", "believe ")):
        lesson = "to " + lesson.replace("always ", "", 1)
    
    # ✅ Build CONCISE prompt (NO repetition)
    prompt = f"{char_part} {place} who {adventure} and learns {lesson}."
    
    logger.info(f"🔧 Mobile prompt: {prompt}")
    
    return prompt



def validate_mobile_params(
    character: Optional[str],
    place: Optional[str],
    adventure: Optional[str],
    lesson: Optional[str]
) -> tuple[bool, str]:
    """
    Validate that all 4 mobile params are provided and non-empty.
    
    Args:
        character: Character name
        place: Place description
        adventure: Adventure type
        lesson:  Moral lesson
    
    Returns:
        (is_valid, error_message)
        - (True, ""): All params valid
        - (False, "error message"): Missing or invalid params
    
    Examples:
        >>> validate_mobile_params("Princess", "In a castle", "Rescue a friend", "Always help")
        (True, "")
        
        >>> validate_mobile_params("Princess", None, "Rescue", "Help")
        (False, "Missing 'place' parameter")
    """
    
    if not character:
        return False, "Missing 'character' parameter"
    if not place:
        return False, "Missing 'place' parameter"
    if not adventure:
        return False, "Missing 'adventure' parameter"
    if not lesson:
        return False, "Missing 'lesson' parameter"
    
    # Check not empty after strip
    if not character.strip():
        return False, "'character' is empty"
    if not place. strip():
        return False, "'place' is empty"
    if not adventure.strip():
        return False, "'adventure' is empty"
    if not lesson.strip():
        return False, "'lesson' is empty"
    
    return True, ""