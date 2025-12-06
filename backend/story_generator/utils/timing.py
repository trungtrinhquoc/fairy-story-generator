"""
Audio timing utilities.
Calculate reading duration and audio duration.
"""

import io
import logging
from pydub import AudioSegment

logger = logging.getLogger(__name__)


def estimate_reading_duration(text: str) -> float:
    """
    Estimate reading duration in seconds.
    
    Average reading speed for children's stories: 150 words/minute
    = ~2.5 words/second
    
    Args:
        text: Text to estimate duration for
    
    Returns:
        Estimated duration in seconds
    """
    word_count = len(text.split())
    duration = word_count / 2.5  # 2.5 words per second
    return round(duration, 1)


def get_audio_duration(audio_bytes: bytes) -> float:
    """
    Get actual duration of audio file.
    
    Args:
        audio_bytes: Audio file bytes (MP3)
    
    Returns:
        Duration in seconds
    """
    try:
        audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
        duration = len(audio) / 1000.0  # Convert milliseconds to seconds
        return round(duration, 2)
    except Exception as e:
        logger.error(f"❌ Error getting audio duration: {e}")
        return 0.0


def format_duration(seconds: float) -> str:
    """
    Format duration as MM:SS.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted string (e.g., "01:23")
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"