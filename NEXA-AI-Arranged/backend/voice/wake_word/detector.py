try:
    import pvporcupine
    import pyaudio
except ImportError:
    pvporcupine = None
    pyaudio = None
import struct
from typing import Callable, Optional
import threading

class WakeWordDetector:
    def __init__(
        self,
        access_key: str,
        keywords: list = ['computer'],
        on_detection: Optional[Callable] = None
    ):
        self.access_key = access_key
        self.keywords = keywords
        self.on_detection = on_detection
        self.porcupine = None
        self.audio_stream = None
        self.is_running = False
        self.thread = None
    
    def start(self):
        """Start listening for wake word"""
        if self.is_running or not pvporcupine or not pyaudio:
            return
        
        self.porcupine = pvporcupine.create(
            access_key=self.access_key,
            keywords=self.keywords
        )
        
        self.audio_stream = pyaudio.PyAudio().open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )
        
        self.is_running = True
        self.thread = threading.Thread(target=self._listen)
        self.thread.start()
    
    def stop(self):
        """Stop listening for wake word"""
        self.is_running = False
        
        if self.thread:
            self.thread.join()
        
        if self.audio_stream:
            self.audio_stream.close()
        
        if self.porcupine:
            self.porcupine.delete()
    
    def _listen(self):
        """Internal listening loop"""
        while self.is_running:
            pcm = self.audio_stream.read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            
            keyword_index = self.porcupine.process(pcm)
            
            if keyword_index >= 0:
                detected_keyword = self.keywords[keyword_index]
                if self.on_detection:
                    self.on_detection(detected_keyword)
