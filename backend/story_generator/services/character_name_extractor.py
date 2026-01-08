"""
Character Name Extractor - Trích xuất và tạo tên nhân vật duy nhất với hệ thống fantasy name bank.
"""

import logging
import re
import random
from typing import Optional, List
from story_generator.database import Database

logger = logging.getLogger(__name__)

class CharacterNameExtractor:
    """
    Lớp xử lý việc tạo tên nhân vật fantasy với các tính năng:
    - Hỗ trợ mythology theo vùng miền (Bắc Âu, Nhật Bản, Hy Lạp, Celtic...)
    - Name bank phân loại theo region và giới tính
    - Tạo tên 2 âm tiết dựa trên character design và environment
    - Đảm bảo tính duy nhất trong database
    """
    
    # Fantasy Name Banks by Mythology Region
    NAME_BANKS = {
        "norse": {  # Thần thoại Bắc Âu (Viking)
            "male": ["Bjorn", "Leif", "Thor", "Odin", "Ragnar", "Erik", "Sven", "Magnus"],
            "female": ["Freya", "Astrid", "Sigrid", "Ingrid", "Helga", "Thyra", "Runa", "Solveig"]
        },
        "japanese": {  # Thần thoại Nhật Bản
            "male": ["Hiro", "Kenji", "Ryu", "Satoshi", "Yuki", "Kaito", "Haruto", "Akira"],
            "female": ["Yuki", "Sakura", "Hana", "Aiko", "Hikari", "Miyu", "Sora", "Rina"]
        },
        "greek": {  # Thần thoại Hy Lạp
            "male": ["Atlas", "Perseus", "Orion", "Damon", "Zane", "Leon", "Theron", "Kyros"],
            "female": ["Iris", "Luna", "Lyra", "Athena", "Selene", "Chloe", "Zara", "Thea"]
        },
        "celtic": {  # Thần thoại Celtic (Ireland/Scotland)
            "male": ["Finn", "Ronan", "Cian", "Declan", "Liam", "Aiden", "Eamon", "Oran"],
            "female": ["Aisling", "Niamh", "Saoirse", "Maeve", "Ciara", "Fiona", "Roisin", "Brigid"]
        },
        "egyptian": {  # Thần thoại Ai Cập
            "male": ["Amun", "Osiris", "Horus", "Anubis", "Khepri", "Seth", "Thoth", "Ra"],
            "female": ["Bastet", "Nefret", "Cleopatra", "Nefertari", "Isis", "Hathor", "Sekhmet", "Maat"]
        },
        "fantasy": {  # Generic Fantasy (default)
            "male": ["Arlo", "Finn", "Zane", "Ronan", "Kai", "Ren", "Leo", "Ezra"],
            "female": ["Aria", "Luna", "Nova", "Lyra", "Stella", "Zara", "Maya", "Nyla"]
        }
    }
    
    # Syllable components cho 2-syllable name generation
    SYLLABLE_PREFIX = {
        "nature": ["Wil", "Glen", "Thorn", "Rain", "Storm", "Leaf", "Sky", "Star"],
        "ocean": ["Mar", "Cor", "Nep", "Thal", "Pearl", "Wave", "Tide", "Reef"],
        "fire": ["Bla", "Ember", "Flare", "Ash", "Pyr", "Ignis", "Scorch", "Flame"],
        "magic": ["Lumi", "Mystic", "Rune", "Spell", "Mage", "Arcane", "Fae", "Starlight"],
        "royal": ["Rex", "Regina", "Crown", "Royal", "Noble", "Prince", "Duchess", "Sire"]
    }
    
    SYLLABLE_SUFFIX = {
        "nature": ["wood", "leaf", "brook", "vale", "grove", "wind", "meadow", "fern"],
        "ocean": ["ia", "ine", "issa", "ara", "ella", "wave", "tide", "shell"],
        "fire": ["wyn", "ra", "is", "en", "fire", "burn", "glow", "spark"],
        "magic": ["belle", "nix", "dore", "mir", "spell", "luna", "star", "dawn"],
        "royal": ["ton", "wick", "ford", "ridge", "mont", "castle", "crown", "heir"]
    }
    
    def __init__(self, db: Database):
        self.db = db
    
    def detect_mythology_region(self, character_design: str, background_design: str = "") -> str:
        """
        Phát hiện vùng mythology dựa trên character design và background.
        
        Keywords mapping:
        - Norse: viking, norse, runes, fjord, ice
        - Japanese: samurai, cherry blossom, temple, zen, kimono
        - Greek: olympus, toga, marble, mediterranean
        - Celtic: druid, clover, mist, highland
        - Egyptian: pyramid, desert, sphinx, pharaoh
        """
        combined_text = f"{character_design} {background_design}".lower()
        
        # Norse/Viking
        if any(word in combined_text for word in ["viking", "norse", "rune", "fjord", "ice", "snow", "nordic"]):
            return "norse"
        
        # Japanese
        if any(word in combined_text for word in ["samurai", "cherry", "temple", "zen", "kimono", "pagoda", "manga", "anime"]):
            return "japanese"
        
        # Greek
        if any(word in combined_text for word in ["olympus", "toga", "marble", "mediterranean", "greek", "sparta"]):
            return "greek"
        
        # Celtic
        if any(word in combined_text for word in ["druid", "clover", "mist", "highland", "celtic", "ireland", "fairy"]):
            return "celtic"
        
        # Egyptian
        if any(word in combined_text for word in ["pyramid", "desert", "sphinx", "pharaoh", "egypt", "nile"]):
            return "egyptian"
        
        # Default to fantasy
        return "fantasy"
    
    def detect_gender(self, character_design: str) -> str:
        """Phát hiện giới tính từ character design."""
        design_lower = character_design.lower()
        
        if any(word in design_lower for word in ["female", "girl", "princess", "she", "her", "woman"]):
            return "female"
        elif any(word in design_lower for word in ["male", "boy", "prince", "he", "him", "man"]):
            return "male"
        
        # Random nếu không xác định được
        return random.choice(["male", "female"])
    
    def detect_theme(self, character_design: str, background_design: str = "") -> str:
        """Phát hiện theme để chọn syllables phù hợp."""
        combined_text = f"{character_design} {background_design}".lower()
        
        if any(word in combined_text for word in ["ocean", "sea", "water", "mermaid", "wave", "coral"]):
            return "ocean"
        elif any(word in combined_text for word in ["fire", "flame", "dragon", "lava", "phoenix", "burn"]):
            return "fire"
        elif any(word in combined_text for word in ["magic", "wizard", "spell", "fairy", "enchant", "mystic"]):
            return "magic"
        elif any(word in combined_text for word in ["king", "queen", "prince", "princess", "royal", "castle", "crown"]):
            return "royal"
        else:
            return "nature"  # Default
    
    def generate_two_syllable_name(self, theme: str, gender: str) -> str:
        """
        Tạo tên 2 âm tiết dựa trên theme.
        
        Example:
        - Ocean theme: "Marina", "Coralina"
        - Fire theme: "Blazewyn", "Emberra"
        - Nature theme: "Willow", "Thornbrook"
        """
        prefix_list = self.SYLLABLE_PREFIX.get(theme, self.SYLLABLE_PREFIX["nature"])
        suffix_list = self.SYLLABLE_SUFFIX.get(theme, self.SYLLABLE_SUFFIX["nature"])
        
        prefix = random.choice(prefix_list)
        suffix = random.choice(suffix_list)
        
        # Combine and capitalize properly
        name = f"{prefix}{suffix}"
        
        # Make sure it's capitalized and between 4-10 characters
        if len(name) > 10:
            # Use just prefix if too long
            name = prefix
        
        return name.capitalize()
    
    def extract_name_from_design(
        self, 
        character_design: str,
        background_design: str = ""
    ) -> Optional[str]:
        """
        Tạo tên nhân vật fantasy dựa trên:
        1. Phát hiện mythology region
        2. Chọn tên từ name bank tương ứng
        3. Hoặc generate 2-syllable name nếu muốn unique hơn
        
        Flow:
        - 70% chance: Chọn từ name bank (đảm bảo phù hợp văn hóa)
        - 30% chance: Generate 2-syllable name (unique, creative)
        """
        
        if not character_design:
            logger.warning("⚠️ Empty character_design")
            return None
        
        # Detect mythology region và gender
        region = self.detect_mythology_region(character_design, background_design)
        gender = self.detect_gender(character_design)
        theme = self.detect_theme(character_design, background_design)
        
        logger.info(f"🌍 Detected region={region}, gender={gender}, theme={theme}")
        
        # 70% chance chọn từ name bank
        if random.random() < 0.7:
            name_bank = self.NAME_BANKS.get(region, self.NAME_BANKS["fantasy"])
            names = name_bank.get(gender, name_bank["female"])
            name = random.choice(names)
            logger.info(f"✅ Selected name from {region} bank: {name}")
        else:
            # 30% chance generate 2-syllable name
            name = self.generate_two_syllable_name(theme, gender)
            logger.info(f"✅ Generated 2-syllable name: {name}")
        
        return name
    
    async def check_name_uniqueness(
        self,
        name: str,
        user_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Kiểm tra xem tên đã được dùng chưa.
        
        Returns:
            (is_unique, suggested_name)
            - (True, None): Tên chưa tồn tại, dùng được
            - (False, "Name2"): Tên đã tồn tại, gợi ý thêm suffix số
        """
        
        if not name:
            return True, None
        
        try:
            response = self.db.client.table("stories")\
                .select("character_name")\
                .eq("user_id", user_id)\
                .eq("character_name", name)\
                .execute()
            
            if response.data and len(response.data) > 0:
                # Tên đã tồn tại → gợi ý tên mới với suffix số
                count = len(response.data)
                suggested_name = f"{name}{count + 1}"
                logger.info(f"⚠️ Name '{name}' exists ({count} times), suggesting '{suggested_name}'")
                return False, suggested_name
            
            # Tên chưa tồn tại
            logger.info(f"✅ Name '{name}' is unique")
            return True, None
            
        except Exception as e:
            logger.error(f"❌ Failed to check name uniqueness: {e}")
            # Nếu lỗi DB → vẫn cho phép dùng tên gốc
            return True, None