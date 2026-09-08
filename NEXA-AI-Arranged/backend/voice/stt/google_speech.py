from google.cloud import speech
from .interface import STTProvider
from typing import Optional

class GoogleSpeechSTT(STTProvider):
    def __init__(self, credentials_path: Optional[str] = None):
        self.client = speech.SpeechClient.from_service_account_file(
            credentials_path
        ) if credentials_path else speech.SpeechClient()
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> dict:
        audio = speech.RecognitionAudio(content=audio_data)
        
        # Support Hinglish
        language_codes = ['hi-IN', 'en-IN', 'en-US'] if not language else [language]
        
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language_codes[0],
            alternative_language_codes=language_codes[1:],
            enable_automatic_punctuation=True,
        )
        
        response = self.client.recognize(config=config, audio=audio)
        
        if response.results:
            result = response.results[0]
            alternative = result.alternatives[0]
            
            return {
                'text': alternative.transcript,
                'language': result.language_code,
                'confidence': alternative.confidence
            }
        
        return {'text': '', 'language': 'unknown', 'confidence': 0.0}
    
    async def transcribe_stream(self, audio_stream):
        # Streaming implementation
        config = speech.StreamingRecognitionConfig(
            config=speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code='hi-IN',
                alternative_language_codes=['en-IN', 'en-US'],
            ),
            interim_results=True,
        )
        
        requests = (
            speech.StreamingRecognizeRequest(audio_content=chunk)
            for chunk in audio_stream
        )
        
        responses = self.client.streaming_recognize(config, requests)
        
        for response in responses:
            for result in response.results:
                if result.is_final:
                    yield {
                        'text': result.alternatives[0].transcript,
                        'is_final': True,
                        'confidence': result.alternatives[0].confidence
                    }
                else:
                    yield {
                        'text': result.alternatives[0].transcript,
                        'is_final': False,
                        'confidence': 0.0
                    }
    
    def is_available(self) -> bool:
        return bool(self.client)
