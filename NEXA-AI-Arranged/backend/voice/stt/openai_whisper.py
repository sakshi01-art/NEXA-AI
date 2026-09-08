import openai
from .interface import STTProvider
from typing import Optional
import os

class OpenAIWhisperSTT(STTProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        openai.api_key = self.api_key
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> dict:
        try:
            # Save audio temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(audio_data)
                audio_file_path = f.name
            
            # Transcribe
            with open(audio_file_path, 'rb') as audio_file:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )
            
            # Clean up
            os.remove(audio_file_path)
            
            return {
                'text': transcript['text'],
                'language': language or 'auto',
                'confidence': 1.0  # Whisper doesn't provide confidence
            }
        except Exception as e:
            raise Exception(f"Whisper transcription failed: {str(e)}")
    
    async def transcribe_stream(self, audio_stream):
        # Implementation for streaming (if supported)
        raise NotImplementedError("Streaming not yet implemented for Whisper")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
