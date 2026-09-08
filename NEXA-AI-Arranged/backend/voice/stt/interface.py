from abc import ABC, abstractmethod
from typing import Optional

class STTProvider(ABC):
    """Abstract base class for Speech-to-Text providers"""
    
    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio to text
        
        Returns:
            {
                'text': str,
                'language': str,
                'confidence': float
            }
        """
        pass
    
    @abstractmethod
    async def transcribe_stream(self, audio_stream):
        """Stream audio and get real-time transcription"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available"""
        pass
