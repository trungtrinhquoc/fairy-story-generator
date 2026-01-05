import logging
import io
import asyncio
from typing import Optional, Tuple, List, Dict
from google.cloud import texttospeech
from google.cloud import speech
from google.oauth2 import service_account
from story_generator.utils.timing import get_audio_duration
from story_generator.config import settings 
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
INITIAL_WAIT_TIME = 2.0
class VoiceGenerator:  
    """Generate voice narration using Google TTS with Speech-to-Text transcript"""
    
    def __init__(self):
        credentials_path = settings.google_application_credentials
        if not credentials_path:
             # Nếu đường dẫn không có, SDK sẽ sử dụng cơ chế mặc định (ADC)
             self.tts_client = texttospeech.TextToSpeechClient() 
             self.stt_client = speech.SpeechClient()
             logger.warning("🔑 Using default credentials (ADC) for Cloud TTS.")
        else:
            # 2. TẠO ĐỐI TƯỢNG CREDENTIALS TỪ FILE PATH
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )

            # 3. KHỞI TẠO CLIENT VÀ TRUYỀN VÀO ĐỐI TƯỢNG CREDENTIALS
            self.tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
            self.stt_client = speech.SpeechClient(credentials=credentials)
    logger.info("✅ Voice Generator initialized (Google Cloud TTS WaveNet)")

    
    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> Tuple[Optional[bytes], float, List[Dict]]:
        """
        Generate audio from text using gTTS.  
        
        Uses thread pool to avoid blocking event loop.
        
        Args:
            text: Text to convert to speech
            voice:   Voice parameter 
        
        Returns:
            Tuple of (audio_bytes, duration_seconds)
        """
        
        # Validate text
        if not text or len(text.strip()) < 5:
            logger.warning(f"⚠️ Text too short or empty: {len(text)} chars")
            return None, 0.0, []
        
        final_voice_id = voice if voice and voice != 'auto' else settings.tts_voice
        try:
            for attempt in range(MAX_RETRIES):
                try:
                    #STEP 1: Generate TTS audio SỬ DỤNG asyncio.to_thread ĐỂ GỌI HÀM BLOCKING (SDK)
                    audio_data, duration = await asyncio.to_thread(
                        self._generate_sync,
                        text,
                        final_voice_id
                    )

                    # STEP 2: Get transcript segments from STT
                    transcript_segments = await asyncio.to_thread(
                        self._extract_transcript_from_stt,
                        audio_data
                    )
                    # logger.info(f"✅ Audio generated (Cloud TTS): {len(audio_data)} bytes, ~{duration:.2f}s, Voice: {final_voice_id}")
                    return audio_data, duration, transcript_segments
                
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
            return None, 0.0, []
    
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
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.85,
            pitch=0.0
        )
        
        # 4. Gọi API (BLOCKING CALL)
        response = self.tts_client.synthesize_speech(
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
    
    def _extract_transcript_from_stt(self, audio_bytes: bytes) -> List[Dict]:
        """
        Extract transcript segments from audio using Google STT.
        
        Args:
            audio_bytes: MP3 audio content
        
        Returns:
            List of transcript segments: 
            [
                {
                    "start": 0.0,
                    "end": 3.5,
                    "text": "Once upon a time, there was a brave princess."
                }
            ]
        """
        
        # Config STT with word timestamps
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=24000,  # Google TTS default
            language_code="en-US",
            enable_word_time_offsets=True,  # Enable word timestamps
            enable_automatic_punctuation=True,
            model="default"
        )
        
        audio = speech.RecognitionAudio(content=audio_bytes)
        
        # Call STT API
        response = self.stt_client.recognize(config=config, audio=audio)
        
        # Parse transcript segments
        transcript_segments = []
        
        if not response.results:
            logger. warning("⚠️ STT returned no results")
            return []
        
        # Process each result (each result is a segment)
        # for result in response. results:
        #     alternative = result.alternatives[0]
            
        #     # Get start/end time from words
        #     if alternative.words:
        #         start_time = alternative.words[0].start_time. total_seconds()
        #         end_time = alternative.words[-1]. end_time.total_seconds()
        #     else:
        #         start_time = 0.0
        #         end_time = 0.0
            
        #     segment = {
        #         "start": round(start_time, 2),
        #         "end": round(end_time, 2),
        #         "text": alternative.transcript. strip()
        #     }
            
        #     transcript_segments.append(segment)
        
        # #logger.info(f"📝 STT extracted {len(transcript_segments)} segments")
        # #for seg in transcript_segments:
        #     #logger.info(f"   {seg['start']}s-{seg['end']}s: {seg['text'][: 50]}...")
        
        # return transcript_segments
        # Get first alternative (highest confidence)
        #alternative = response.results[0]. alternatives[0]
        
        for result in response.results:
            alternative = result.alternatives[0]
            for word_info in alternative.words:
                transcript_segments.append({
                    "word":  word_info.word, 
                    "start": round(word_info.start_time.total_seconds(), 2),
                    "end": round(word_info.end_time.total_seconds(), 2)
                })
            
            #logger.info(f"📝 STT transcript: {alternative.transcript}")
            #logger.info(f"🕐 Extracted {len(transcript_segments)} word timestamps from STT")
            
        return transcript_segments

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