import logging
import io
import asyncio
from typing import Optional, Tuple
from google.cloud import texttospeech
from google.oauth2 import service_account
from story_generator.utils.timing import get_audio_duration
from story_generator.config import settings 
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
INITIAL_WAIT_TIME = 2.0
class VoiceGenerator:  
    """Generate voice narration using Google TTS WaveNet."""
    
    def __init__(self):
        credentials_path = settings.google_application_credentials
        if not credentials_path:
             # Nếu đường dẫn không có, SDK sẽ sử dụng cơ chế mặc định (ADC)
             self.client = texttospeech.TextToSpeechClient() 
             logger.warning("🔑 Using default credentials (ADC) for Cloud TTS.")
        else:
            # 2. TẠO ĐỐI TƯỢNG CREDENTIALS TỪ FILE PATH
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )

            # 3. KHỞI TẠO CLIENT VÀ TRUYỀN VÀO ĐỐI TƯỢNG CREDENTIALS
            self.client = texttospeech.TextToSpeechClient(
                credentials=credentials # <--- TRUYỀN CREDENTIALS TƯỜNG MINH
            )
    logger.info("✅ Voice Generator initialized (Google Cloud TTS WaveNet)")
    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None
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
        
        final_voice_id = voice if voice and voice != 'auto' else settings.tts_voice
        try:
            for attempt in range(MAX_RETRIES):
                try:
                    # SỬ DỤNG asyncio.to_thread ĐỂ GỌI HÀM BLOCKING (SDK)
                    audio_data, duration = await asyncio.to_thread(
                        self._generate_sync,
                        text,
                        final_voice_id
                    )
                    logger.info(f"✅ Audio generated (Cloud TTS): {len(audio_data)} bytes, ~{duration:.2f}s, Voice: {final_voice_id}")
                    return audio_data, duration
                
                except Exception as e:
                    logger.warning(f"❌ Attempt {attempt + 1}/{MAX_RETRIES} failed for Cloud TTS. Error: {e}")
                    if attempt < MAX_RETRIES - 1:
                        # Hồi chiêu (Exponential Backoff)
                        wait_time = INITIAL_WAIT_TIME * (2 ** attempt)
                        logger.info(f"Retrying in {wait_time:.2f} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        raise e 
            
        except Exception as e:
            logger.error(f"❌ Fatal error generating audio with Cloud TTS after {MAX_RETRIES} retries: {e}", exc_info=True)
            return None, 0.0
    
    def _generate_sync(self, text: str, voice_id: str) -> Tuple[bytes, float]:
        """
        Synchronous audio generation using Google Cloud TTS SDK.
        Chạy trong luồng riêng.
        
        Args:
            text: Text to convert
        
        Returns:
            Tuple of (audio_bytes, duration)
        """
        # 1. Cấu hình Input
        synthesis_input = texttospeech.SynthesisInput(text = text)
        
        # 2. Cấu hình Voice (DÒNG NÀY CHỌN WAVENET/NEURAL2)
        language_code = '-'.join(voice_id.split('-')[:2]) 
        voice_selection = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_id # <-- Chuyển tên WaveNet/Neural2 voice
        )
        
        # 3. Cấu hình Output (MP3)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # 4. Gọi API (BLOCKING CALL)
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice_selection,
            audio_config=audio_config
        )
        
        audio_data = response.audio_content
        
        if not audio_data or len(audio_data) == 0:
            raise Exception("Cloud TTS returned empty audio data")
        
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