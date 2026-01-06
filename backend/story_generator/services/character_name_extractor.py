"""
Character Name Extractor - Trích xuất và đảm bảo tên nhân vật là duy nhất.
Mục đích: Tìm tên trong mô tả của AI, kiểm tra xem tên đó đã dùng chưa, 
nếu trùng thì gợi ý tên mới.
"""

import logging
import re
from typing import Optional, List
from story_generator.database import Database

logger = logging.getLogger(__name__)

class CharacterNameExtractor:
    """Lớp xử lý việc nhặt tên nhân vật và đảm bảo tính duy nhất."""
    
    def __init__(self, db: Database):
        # Kết nối với Database để kiểm tra dữ liệu cũ
        self.db = db
    
    def extract_name_from_design(self, character_design: str) -> Optional[str]:
        """
        Sử dụng biểu thức chính quy (Regex) để tìm tên trong mô tả nhân vật.
        
        Ví dụ AI trả về: "A 7-year-old girl named Lily..." -> Trích xuất: "Lily"
        """
        
        # Mẫu 1: Tìm tên đứng sau chữ "named " (Ví dụ: named Lily)
        # [A-Z][a-z]+ nghĩa là tìm một chữ viết hoa rồi đến các chữ viết thường
        match = re.search(r'named\s+([A-Z][a-z]+)', character_design)
        if match:
            return match.group(1)
        
        # Mẫu 2: Tìm tên ở ngay đầu câu và có dấu phẩy theo sau (Ví dụ: Mochi, a ...)
        match = re.search(r'^([A-Z][a-z]+),\s+a\s+', character_design)
        if match:
            return match.group(1)
        
        # Mẫu 3: Tìm tên đứng sau chữ "called " (Ví dụ: called Max)
        match = re.search(r'called\s+([A-Z][a-z]+)', character_design)
        if match:
            return match.group(1)
        
        # Nếu không tìm thấy theo các mẫu trên, trả về None
        return None
    
    async def check_name_uniqueness(
        self,
        name: str,
        user_id: str
    ) -> tuple[bool, Optional[str]]: 
        """
        Kiểm tra xem tên này đã được User này sử dụng trong truyện nào trước đó chưa.
        Trả về: (Có duy nhất không?, Tên gợi ý mới nếu bị trùng)
        """
        
        if not name:
            return True, None
        
        try:
            # Truy vấn bảng 'stories' tìm các truyện có cùng user_id và character_name
            response = self.db.client.table("stories")\
                .select("character_name")\
                .eq("user_id", user_id)\
                .eq("character_name", name)\
                .execute()
            
            # Nếu tìm thấy dữ liệu (nghĩa là tên đã tồn tại)
            if response.data and len(response.data) > 0:
                # Gọi hàm sáng tạo tên mới để tránh trùng lặp
                suggested = self._suggest_unique_name(name, response.data)
                return False, suggested
            
            # Tên này chưa dùng, hoàn toàn hợp lệ
            return True, None
        
        except Exception as e: 
            logger.error(f"❌ Kiểm tra trùng tên thất bại: {e}")
            return True, None
    
    def _suggest_unique_name(
        self,
        base_name: str,
        existing_names: List[dict]
    ) -> str:
        """
        Hàm sáng tạo: Thêm tiền tố hoặc hậu tố để tạo ra một cái tên mới từ tên gốc.
        Ví dụ: Lily -> Lily the Brave hoặc Little Lily
        """
        
        # Danh sách các hậu tố (tính cách/danh hiệu)
        suffixes = [
            "Jr.", "the Brave", "the Wise", "the Kind", "the Clever", "the Swift"
        ]
        
        # Danh sách các tiền tố
        prefixes = [
            "Little", "Young", "Brave", "Sweet"
        ]
        
        # 1. Thử ghép hậu tố trước (Ví dụ: Lily the Brave)
        for suffix in suffixes:
            candidate = f"{base_name} {suffix}"
            # Kiểm tra xem cái tên mới ghép này có trùng nữa không
            if not any(d.get("character_name") == candidate for d in existing_names):
                return candidate
        
        # 2. Nếu vẫn trùng, thử ghép tiền tố (Ví dụ: Little Lily)
        for prefix in prefixes:
            candidate = f"{prefix} {base_name}"
            if not any(d.get("character_name") == candidate for d in existing_names):
                return candidate
        
        # 3. Cuối cùng, nếu vẫn trùng thì đánh số thứ tự (Ví dụ: Lily 2, Lily 3...)
        for i in range(2, 100):
            candidate = f"{base_name} {i}"
            if not any(d.get("character_name") == candidate for d in existing_names):
                return candidate
        
        return base_name