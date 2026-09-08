from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get completion from AI
        
        Returns:
            {
                'content': str,
                'tool_calls': List[Dict],
                'finish_reason': str
            }
        """
        pass
    
    @abstractmethod
    async def stream_complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None
    ):
        """Stream completion tokens"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured"""
        pass
