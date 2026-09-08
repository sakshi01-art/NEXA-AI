from typing import Optional
import torch
from TTS.api import TTS
import os

class CustomVoiceTTS:
    """Custom voice synthesis with voice cloning capability"""
    
    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = None
        self.custom_voice_path = None
        
    def initialize(self):
        """Initialize TTS model"""
        self.tts = TTS(self.model_name).to(self.device)
    
    def clone_voice(self, audio_sample_path: str, output_path: str = "./data/voice/custom.wav"):
        """Clone voice from audio sample"""
        
        if not os.path.exists(audio_sample_path):
            return {
                'success': False,
                'error': 'Audio sample not found'
            }
        
        # Save custom voice reference
        self.custom_voice_path = audio_sample_path
        
        return {
            'success': True,
            'message': 'Voice cloned successfully',
            'voice_path': audio_sample_path
        }
    
    async def synthesize(
        self,
        text: str,
        output_path: str = "./temp/output.wav",
        language: str = "en",
        use_custom_voice: bool = True
    ) -> dict:
        """Synthesize speech with optional custom voice"""
        
        try:
            if not self.tts:
                self.initialize()
            
            if use_custom_voice and self.custom_voice_path:
                # Use cloned voice
                self.tts.tts_to_file(
                    text=text,
                    file_path=output_path,
                    speaker_wav=self.custom_voice_path,
                    language=language
                )
            else:
                # Use default voice
                self.tts.tts_to_file(
                    text=text,
                    file_path=output_path,
                    language=language
                )
            
            # Read file as bytes
            with open(output_path, 'rb') as f:
                audio_data = f.read()
            
            return {
                'success': True,
                'audio_data': audio_data,
                'path': output_path
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def adjust_voice_characteristics(
        self,
        speed: float = 1.0,
        pitch: float = 1.0,
        energy: float = 1.0
    ):
        """Adjust voice characteristics"""
        
        # This would modify TTS parameters
        self.voice_config = {
            'speed': speed,
            'pitch': pitch,
            'energy': energy
        }
    
    def list_available_languages(self) -> list:
        """List supported languages"""
        
        # XTTS v2 supports these languages
        return [
            'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr',
            'ru', 'nl', 'cs', 'ar', 'zh-cn', 'ja', 'hu', 'ko', 'hi'
        ]
