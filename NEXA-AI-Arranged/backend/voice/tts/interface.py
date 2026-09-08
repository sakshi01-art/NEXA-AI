from abc import ABC, abstractmethod
from typing import Optional

class TTSProvider(ABC):
    """Abstract base class for Text-to-Speech providers"""
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0
    ) -> bytes:
        """
        Convert text to speech
        
        Returns:
            Audio data as bytes
        """
        pass
    
    @abstractmethod
    def list_voices(self) -> list:
        """List available voices"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available"""
        pass
