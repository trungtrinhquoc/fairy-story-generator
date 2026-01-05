"""
Configuration management using Pydantic Settings.
Loads environment variables from .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # =================================
    # SUPABASE
    # =================================
    supabase_url: str
    supabase_key: str
    
    # =================================
    # AI SERVICE API KEYS
    # =================================
    gemini_api_key: str
    openrouter_api_key: str
    openrouter_model: str = "google/gemini-3-flash-preview"
    
    # Google Cloud / Vertex AI (NEW - CẦN CHO IMAGE GENERATION)
    google_cloud_project: Optional[str] = None
    google_cloud_location: str = "us-central1"
    google_application_credentials: Optional[str] = None
    
    # =================================
    # APPLICATION SETTINGS
    # =================================
    environment: Literal["development", "production"] = "development"
    log_level: str = "DEBUG"
    default_user_id: str = "00000000-0000-0000-0000-000000000001"
    
    # =================================
    # STORY GENERATION
    # =================================
    default_story_length: Literal["short", "medium", "long"] = "short"
    default_num_scenes: int = 6
    max_scenes: int = 12
    
    # =================================
    # IMAGE GENERATION
    # =================================
    image_provider: Literal["vertex_ai", "placeholder"] = "vertex_ai"
    image_style: str = "Pixar 3D style, bright lighting, colorful, high quality"  # UPDATED
    enable_image_fallback: bool = True
    
    # NEW - Retry settings (FIX CHO LỖI SSL)
    max_image_retries: int = 3
    max_upload_retries: int = 3
    
    # =================================
    # VOICE SETTINGS
    # =================================
    tts_voice: str = "en-US-News-L"
    
    # =================================
    # COMPUTED PROPERTIES
    # =================================
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def scenes_by_length(self) -> dict[str, int]:
        """Return number of scenes based on story length."""
        return {
            "short": 6,
            "medium": 10,
            "long": 14
        }
    
    # NEW - Helper to find credentials file
    @property
    def credentials_path(self) -> str:
        """Get full path to Google Cloud credentials."""
        if not self.google_application_credentials:
            return ""
        
        # Check current directory first
        if os.path.exists(self.google_application_credentials):
            return self.google_application_credentials
        
        # Check parent directory
        parent_path = os.path.join(". .", self.google_application_credentials)
        if os.path. exists(parent_path):
            return parent_path
        
        return self.google_application_credentials


# Global settings instance
settings = Settings()