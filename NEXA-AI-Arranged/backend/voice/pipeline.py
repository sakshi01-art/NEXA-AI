from typing import Optional, Callable
import asyncio
from .stt.interface import STTProvider
from .tts.interface import TTSProvider
from .wake_word.detector import WakeWordDetector

class VoicePipeline:
    def __init__(
        self,
        stt_provider: STTProvider,
        tts_provider: TTSProvider,
        wake_word_detector: Optional[WakeWordDetector] = None
    ):
        self.stt = stt_provider
        self.tts = tts_provider
        self.wake_word = wake_word_detector
        
        self.on_transcript: Optional[Callable] = None
        self.on_wake_word: Optional[Callable] = None
        self.is_listening = False
    
    async def start_listening(self, audio_data: bytes) -> dict:
        """Transcribe audio to text"""
        try:
            result = await self.stt.transcribe(audio_data)
            
            if self.on_transcript:
                await self.on_transcript(result)
            
            return result
        except Exception as e:
            return {
                'text': '',
                'error': str(e),
                'confidence': 0.0
            }
    
    async def speak(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> bytes:
        """Convert text to speech"""
        try:
            audio_data = await self.tts.synthesize(
                text=text,
                voice=voice,
                speed=speed
            )
            return audio_data
        except Exception as e:
            raise Exception(f"TTS failed: {str(e)}")
    
    def enable_wake_word(self, callback: Callable):
        """Enable wake word detection"""
        if self.wake_word:
            self.wake_word.on_detection = callback
            self.wake_word.start()
    
    def disable_wake_word(self):
        """Disable wake word detection"""
        if self.wake_word:
            self.wake_word.stop()
    
    def is_ready(self) -> bool:
        """Check if pipeline is ready"""
        return self.stt.is_available() and self.tts.is_available()
