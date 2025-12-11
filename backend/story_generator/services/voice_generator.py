"""
Voice generation service using gTTS (Google Text-to-Speech).
100% FREE, no API key required, very reliable.
"""

import logging
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple
from gtts import gTTS
from story_generator.utils.timing import get_audio_duration

logger = logging.getLogger(__name__)

# ✅ THÊM:  Thread pool cho blocking I/O
_thread_pool = ThreadPoolExecutor(max_workers=5)  # Cho phép 5 gTTS calls đồng thời


class VoiceGenerator:  
    """Generate voice narration using Google TTS."""
    
    def __init__(self):
        """Initialize voice generator."""
        logger.info("✅ Voice Generator initialized (gTTS with thread pool)")
    
    async def generate_audio(
        self,
        text: str,
        voice:   Optional[str] = None
    ) -> Tuple[Optional[bytes], float]:
        """
        Generate audio from text using gTTS.  
        
        Uses thread pool to avoid blocking event loop.
        
        Args:
            text: Text to convert to speech
            voice:   Voice parameter (ignored in gTTS, kept for compatibility)
        
        Returns:
            Tuple of (audio_bytes, duration_seconds)
        """
        
        # Validate text
        if not text or len(text.  strip()) < 5:
            logger.warning(f"⚠️ Text too short or empty: {len(text)} chars")
            return None, 0.0
        
        logger.info(f"🎤 Generating audio with gTTS - Text length: {len(text)}")
        
        try:
            # ✅ RUN IN THREAD POOL (non-blocking)
            loop = asyncio.get_event_loop()
            audio_data, duration = await loop.run_in_executor(
                _thread_pool,
                self._generate_sync,  # ← Blocking function
                text
            )
            
            logger. info(f"✅ Audio generated:   {len(audio_data)} bytes, ~{duration:.2f}s")
            
            return audio_data, duration
        
        except Exception as e:  
            logger.error(f"❌ Error generating audio with gTTS: {e}", exc_info=True)
            return None, 0.0
    
    def _generate_sync(self, text: str) -> Tuple[bytes, float]:
        """
        Synchronous audio generation (runs in thread pool).
        
        This method contains BLOCKING I/O and should only be called 
        via run_in_executor().
        
        Args:
            text: Text to convert
        
        Returns:
            Tuple of (audio_bytes, duration)
        """
        # Detect language
        lang = self._detect_language(text)
        
        # Create gTTS object (BLOCKING)
        tts = gTTS(
            text=text,
            lang=lang,
            slow=False
        )
        
        # Generate audio to BytesIO (BLOCKING I/O)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        
        # Get audio bytes
        audio_fp.seek(0)
        audio_data = audio_fp.read()
        
        if not audio_data or len(audio_data) == 0:
            raise Exception("gTTS returned empty audio data")
        
        # Calculate duration
        try:
            duration = get_audio_duration(audio_data)
        except Exception as e:
            # Fallback:   estimate
            logger.warning(f"⚠️ Could not calculate exact duration: {e}")
            word_count = len(text.split())
            duration = (word_count / 150) * 60
            duration = max(2.0, duration)
        
        return audio_data, duration
    
    def _detect_language(self, text: str) -> str:
        """
        Detect language from text.  
        
        Returns: 
            Language code (en, vi, etc.)
        """
        vietnamese_chars = 'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ'
        
        viet_count = sum(1 for char in text.  lower() if char in vietnamese_chars)
        
        if viet_count > len(text) * 0.05: 
            logger.info("   Detected language:   Vietnamese (vi)")
            return 'vi'
        else:  
            logger.info("   Detected language:  English (en)")
            return 'en'