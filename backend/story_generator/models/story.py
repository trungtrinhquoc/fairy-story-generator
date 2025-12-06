"""
Pydantic models for Story and Scene data structures.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


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
        examples=["A brave little boy meets a friendly dragon in a magical forest"]
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
        default=None,
        description="TTS voice selection (uses en-US-JennyNeural by default)",
        examples=["en-US-JennyNeural", "en-US-GuyNeural"]
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
    
    id: str
    story_id: str
    scene_order: int
    paragraph_text: str
    image_prompt_used: str
    image_url: str
    audio_url: str
    audio_duration: Optional[float] = None
    image_style: Optional[str] = None
    narration_voice: Optional[str] = None
    word_count: Optional[int] = None


# =================================
# RESPONSE MODELS
# =================================

class StoryResponse(BaseModel):
    """Response model for generated story."""
    
    id: str
    user_id: str
    title: str
    story_length: str
    story_tone: str
    theme_selected: str
    status: StoryStatus
    cover_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Scenes (populated when fetching full story)
    scenes: List[SceneGenerated] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class StoryListItem(BaseModel):
    """Simplified story item for list view."""
    
    id: str
    title: str
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