import requests
from .interface import TTSProvider
from typing import Optional
import os

class ElevenLabsTTS(TTSProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        self.base_url = "https://api.elevenlabs.io/v1"
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0
    ) -> bytes:
        voice_id = voice or "21m00Tcm4TlvDq8ikWAM"  # Default voice
        
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Supports Hindi
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5,
                "speed": speed
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"ElevenLabs TTS failed: {response.text}")
    
    def list_voices(self) -> list:
        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()['voices']
        return []
    
    def is_available(self) -> bool:
        return bool(self.api_key)
