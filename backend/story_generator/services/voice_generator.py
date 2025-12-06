"""
Voice generation service using Edge TTS (Microsoft).
100% FREE, no API key required.
"""

import logging
import edge_tts
import io
from typing import Optional
from story_generator.config import settings
from story_generator.utils.timing import get_audio_duration

logger = logging.getLogger(__name__)


class VoiceGenerator:
    """Generate voice narration using Edge TTS."""
    
    def __init__(self):
        """Initialize voice generator."""
        self.voice = settings.tts_voice
        self.rate = settings.tts_rate
        self.volume = settings.tts_volume
        logger.info(f"✅ Voice Generator initialized (voice: {self.voice})")
    
    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> tuple[Optional[bytes], float]:
        """
        Generate audio from text using Edge TTS.
        
        Args:
            text: Text to convert to speech
            voice: Optional voice override
        
        Returns:
            Tuple of (audio_bytes, duration_seconds)
        """
        
        selected_voice = voice or self.voice
        
        # THÊM VALIDATION
        if not selected_voice or not isinstance(selected_voice, str):
            logger.error(f"❌ Invalid voice: {selected_voice} (type: {type(selected_voice)})")
            return None, 0.0
        
        # THÊM LOG DEBUG
        logger.info(f"🎤 Generating audio - Voice: '{selected_voice}', Text length: {len(text)}")
        try:
            # Create TTS communicator
            communicate = edge_tts.Communicate(
                text=text,
                voice=selected_voice,
                rate=self.rate,
                volume=self.volume
            )
            
            # Generate audio
            audio_bytes = io.BytesIO()
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes.write(chunk["data"])
            
            # Get bytes
            audio_data = audio_bytes.getvalue()
            
            # Calculate duration
            duration = get_audio_duration(audio_data)
            
            logger.info(f"✅ Audio generated ({duration}s)")
            
            return audio_data, duration
        
        except Exception as e:
            logger.error(f"❌ Error generating audio: {e}")
            return None, 0.0