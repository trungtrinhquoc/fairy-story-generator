"""
Pydantic models for Story and Scene data structures.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Literal, Dict
from datetime import datetime
from enum import Enum


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase"""
    components = string.split('_')
    return components[0] + ''.join(x. title() for x in components[1:])


class StoryStatus(str, Enum):
    """Story generation status."""
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class StoryLength(str, Enum):
    """Story length options."""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class StoryTone(str, Enum):
    """Story tone options."""
    FUNNY = "funny"
    ADVENTUROUS = "adventurous"
    GENTLE = "gentle"


class Theme(str, Enum):
    """Available story themes."""
    PRINCESS = "princess"
    DRAGON = "dragon"
    FOREST = "forest"
    OCEAN = "ocean"
    SPACE = "space"
    MAGICAL_FOREST = "magical_forest"
    CASTLE = "castle"
    ADVENTURE = "adventure"

    # Modern & Daily Life (MỚI - Dễ vẽ, không bị chặn)
    SCHOOL = "school_life"       # Chuyện trường lớp
    FRIENDSHIP = "friendship"    # Tình bạn
    ANIMALS = "cute_animals"     # Thú cưng
    SUPERHERO = "superhero"      # Siêu anh hùng (nhí)
    FAMILY = "family"            # Gia đình
    ROBOT = "robot"              # Robot/Công nghệ
    
# =================================
# REQUEST MODELS
# =================================

class StoryRequest(BaseModel):
    """Request model for story generation."""
    
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=500,
        # SỬA: Mô tả và ví dụ bằng Tiếng Anh
        description="Story prompt in English (e.g., about a robot, a fairy, etc.)",
        examples=["Mia turns into a mermaid and hosts a tea party at the bottom of the ocean. Her guests are a polite octopus and a glowing seahorse. They drink sea-foam tea out of seashell cups while sitting on a table made of bright pink coral."]
    )
    
    story_length: StoryLength = Field(
        default=StoryLength.SHORT,
        description="Story length (short=6 scenes, medium=10, long=14)"
    )
    
    story_tone: StoryTone = Field(
        default=StoryTone.GENTLE,
        description="Story tone/mood"
    )
    
    theme: Optional[Theme] = Field(
        default=None,
        description="Story theme (optional, auto-detected if not provided)"
    )
    
    child_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Child's name to include in story (optional)"
    )
    
    # SỬA: Đổi style mặc định sang 3D/Pixar cho đẹp và hiện đại
    image_style: Optional[str] = Field(
        default="Pixar style, 3D render, cute, vibrant colors",
        description="Image generation style"
    )
    
    # SỬA: Gợi ý giọng đọc Tiếng Anh (Jenny/Guy)
    voice: Optional[str] = Field(
        default="en-US-News-L",  
        description="TTS voice selection",
        examples=["en-US-News-L", "en-US-Studio-O", "en-US-Neural2-F"] 
    )
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v):
        """Ensure prompt is not empty or just whitespace."""
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


# =================================
# SCENE MODELS
# =================================

class Scene(BaseModel):
    """Scene structure from LLM generation."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    scene_number: int = Field(..., ge=1, description="Scene order number")
    # SỬA: Xác định rõ là Text tiếng Anh
    text: str = Field(..., min_length=10, description="Scene narrative text (English)")
    image_prompt: str = Field(..., description="Prompt for image generation")
    word_count: Optional[int] = Field(default=None, description="Number of words in text")
    
    @field_validator('word_count', mode='before')
    @classmethod
    def calculate_word_count(cls, v, info):
        """Auto-calculate word count if not provided."""
        if v is None and 'text' in info.data:
            return len(info.data['text'].split())
        return v


class SceneGenerated(BaseModel):
    """Scene with generated assets (images + audio)."""
    
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    id: str
    story_id: str
    scene_order: int
    paragraph_text: str
    image_prompt_used: str
    image_url: str
    audio_url: str
    audio_duration: Optional[float] = None

    # Transcript segments from STT
    transcript:  Optional[List[Dict]] = Field(
        default=None,
        description="Transcript segments with timing from Speech-to-Text"
    )

    image_style: Optional[str] = None
    narration_voice: Optional[str] = None
    word_count: Optional[int] = None


# =================================
# RESPONSE MODELS
# =================================

class StoryResponse(BaseModel):
    """Response model for generated story."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, from_attributes = True)
    id: str
    user_id: str
    title: str
    short_title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    character_name: Optional[str] = None
    story_length: str
    story_tone: str
    theme_selected: str
    status: StoryStatus
    cover_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Scenes (populated when fetching full story)
    scenes: List[SceneGenerated] = Field(default_factory=list)


class StoryListItem(BaseModel):
    """Simplified story item for list view."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    id: str
    title: str
    short_title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    character_name: Optional[str] = None
    theme_selected: str
    status: StoryStatus
    cover_image_url: Optional[str] = None
    created_at: datetime
    scene_count: Optional[int] = None


class StoryGenerationResponse(BaseModel):
    """Response after triggering story generation."""
    
    story_id: str
    status: StoryStatus
    message: str
    estimated_time: int = Field(..., description="Estimated completion time in seconds")


# ========================================
# PROGRESS TRACKING MODELS (NEW)
# Models cho progressive generation
# ========================================
class SceneStatus(str, Enum):
    """
    Enum cho trạng thái của scene. 
    
    GIẢI THÍCH:
    - PENDING: Scene vừa tạo, chưa bắt đầu generate
    - GENERATING: Đang generate image + audio
    - COMPLETED: Đã xong (có image_url + audio_url)
    - FAILED: Lỗi khi generate
    """
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressInfo(BaseModel):
    """
    Thông tin progress của story generation. 
    
    DÙNG ĐỂ:
    - Hiển thị progress bar: "3/6 scenes (50%)"
    - Estimate thời gian còn lại
    
    VÍ DỤ:
    {
        "completed": 3,
        "total": 6,
        "percentage": 50. 0
    }
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    completed: int = Field(
        description="Số scenes đã hoàn thành",
        ge=0  # Greater or equal 0
    )
    total: int = Field(
        description="Tổng số scenes",
        ge=1  # Ít nhất 1 scene
    )
    percentage: float = Field(
        description="Phần trăm hoàn thành (0-100)",
        ge=0.0,
        le=100.0
    )


class SceneWithStatus(SceneGenerated):
    """
    Scene model có thêm status field.
    
    KẾ THỪA TỪ SceneGenerated + THÊM:
    - status: Trạng thái scene
    - error_message: Lỗi nếu có
    - started_at: Thời gian bắt đầu
    - completed_at: Thời gian hoàn thành
    
    DÙNG CHO:
    - API 2 response (cần biết scene đang ở trạng thái nào)
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    status: SceneStatus = Field(
        default=SceneStatus.PENDING,
        description="Trạng thái của scene"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Thông báo lỗi nếu status=failed"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Thời gian bắt đầu generate"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Thời gian hoàn thành"
    )
    

class StoryProgressResponse(BaseModel):
    """
    Response cho API 2: GET /stories/{id}/progress
    
    TRẢ VỀ:
    - Thông tin story (id, title, status...)
    - Progress info (completed/total, %)
    - List các scenes ĐÃ HOÀN THÀNH
    - Estimated time remaining
    
    FRONTEND DÙNG ĐỂ:
    - Hiển thị progress bar
    - Show scenes khi chúng sẵn sàng
    - Biết khi nào dừng polling (status='completed')
    
    VÍ DỤ RESPONSE:
    {
        "story_id": "abc-123",
        "title": "Max và Rừng Phép Thuật",
        "status": "generating",
        "progress": {
            "completed": 3,
            "total": 6,
            "percentage": 50.0
        },
        "scenes": [
            {scene_1},
            {scene_2},
            {scene_3}
        ],
        "estimated_time_remaining": 18
    }
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    story_id: str = Field(description="ID của story")
    
    title: str = Field(description="Tiêu đề story")
    
    status: str = Field(
        description="Trạng thái story: 'generating' | 'completed' | 'failed'"
    )
    
    progress: ProgressInfo = Field(
        description="Thông tin progress"
    )
    
    scenes: List[SceneWithStatus] = Field(
        default=[],
        description="List các scenes đã hoàn thành (chỉ status='completed')"
    )
    
    estimated_time_remaining: Optional[int] = Field(
        default=None,
        description="Thời gian còn lại ước tính (seconds)"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Thông báo lỗi nếu story failed"
    )


class StoryGenerationStartResponse(BaseModel):
    """
    Response cho API 1: POST /generate (khi bắt đầu generation). 
    
    TRẢ VỀ:
    - Story info
    - Scene 1 (đã hoàn thành)
    - Progress (1/6)
    - Message hướng dẫn user poll API 2
    
    FRONTEND NHẬN ĐƯỢC:
    - Hiển thị scene 1 ngay
    - Bắt đầu polling API 2 để lấy scenes còn lại
    
    VÍ DỤ:
    {
        "story_id": "abc-123",
        "title": "Max và Rừng Phép Thuật",
        "status": "generating",
        "progress": {
            "completed": 1,
            "total": 6,
            "percentage": 16.7
        },
        "scenes": [{scene_1}],
        "message": "Scene 1 hoàn thành.  Đang tạo scenes còn lại..."
    }
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    story_id: str = Field(description="ID của story")
    
    title: str = Field(description="Tiêu đề story")
    
    short_title: Optional[str] = Field(
        default=None,
        description="Tiêu đề rút gọn cho thumbnail (max 30 chars)"
    )
    
    thumbnail_url: Optional[str] = Field(
        default=None,
        description="URL của thumbnail (600x900px, 2: 3 ratio)"
    )
    
    character_name: Optional[str] = Field(
        default=None,
        description="Tên nhân vật chính"
    )
    
    status: str = Field(
        default="generating",
        description="Luôn là 'generating' khi mới bắt đầu"
    )
    
    progress: ProgressInfo = Field(
        description="Progress hiện tại (thường là 1/6)"
    )
    
    scenes: List[SceneGenerated] = Field(
        description="List scenes (chỉ có scene 1)"
    )
    
    message: str = Field(
        default="Scene đầu tiên đã hoàn thành. Đang tạo các scenes còn lại...",
        description="Message cho user"
    )
    
    poll_url: Optional[str] = Field(
        default=None,
        description="URL để poll progress (API 2)"
    )
    

