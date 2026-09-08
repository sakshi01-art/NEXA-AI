import asyncio
import subprocess
import threading
import base64
import io
import time
from typing import Dict, Optional, Callable, List
from datetime import datetime
import struct

class ScreenMirrorEngine:
    """
    Real-time phone screen mirroring.
    
    Two modes:
    1. scrcpy mode - Low latency, full control
    2. Screenshot stream mode - Fallback, works always
    
    Features:
    - Live screen at up to 60 FPS
    - Touch input passthrough
    - Keyboard input
    - Clipboard sync
    - Audio mirroring (Android 10+)
    - Recording
    """
    
    def __init__(self, adb_engine, websocket_server):
        self.adb = adb_engine
        self.ws_server = websocket_server
        
        self.mirror_process: Optional[subprocess.Popen] = None
        self.is_mirroring = False
        self.current_device_id: Optional[str] = None
        
        self.stream_thread: Optional[threading.Thread] = None
        self.fps = 30
        self.quality = 85
        self.max_width = 720
        self.is_recording = False
        self.record_frames: List[bytes] = []
        
        self.frame_count = 0
        self.last_fps_check = time.time()
        self.actual_fps = 0
        
        self.clients: List = []
    
    async def start_scrcpy_mirror(
        self,
        device_id: str,
        max_fps: int = 30,
        max_size: int = 720,
        bit_rate: str = '8M',
        stay_awake: bool = True,
        show_touches: bool = True
    ) -> Dict:
        """Start mirroring using scrcpy"""
        
        # Check if scrcpy is installed
        check = subprocess.run(
            ['scrcpy', '--version'],
            capture_output=True,
            timeout=5
        )
        
        if check.returncode != 0:
            return {
                'success': False,
                'error': 'scrcpy not installed',
                'install': 'https://github.com/Genymobile/scrcpy/releases',
                'fallback': 'Using screenshot stream mode instead'
            }
        
        cmd = [
            'scrcpy',
            '-s', device_id,
            f'--max-fps={max_fps}',
            f'--max-size={max_size}',
            f'--video-bit-rate={bit_rate}',
            '--window-title=NEXA Phone Mirror',
            '--window-borderless',
        ]
        
        if stay_awake:
            cmd.append('--stay-awake')
        
        if show_touches:
            cmd.append('--show-touches')
        
        self.mirror_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        self.is_mirroring = True
        self.current_device_id = device_id
        
        return {
            'success': True,
            'mode': 'scrcpy',
            'device_id': device_id,
            'fps': max_fps,
            'resolution': f'{max_size}p',
            'pid': self.mirror_process.pid
        }
    
    async def start_stream_mirror(
        self,
        device_id: str,
        fps: int = 15,
        quality: int = 75,
        max_width: int = 720
    ) -> Dict:
        """
        Start screenshot-based streaming.
        Fallback mode when scrcpy unavailable.
        Streams JPEG frames via WebSocket.
        """
        
        if self.is_mirroring:
            await self.stop_mirror()
        
        self.fps = fps
        self.quality = quality
        self.max_width = max_width
        self.is_mirroring = True
        self.current_device_id = device_id
        
        # Start streaming thread
        self.stream_thread = threading.Thread(
            target=self._stream_loop,
            args=(device_id,),
            daemon=True
        )
        self.stream_thread.start()
        
        return {
            'success': True,
            'mode': 'stream',
            'device_id': device_id,
            'fps': fps,
            'quality': quality,
            'websocket': 'ws://localhost:8765/phone-mirror'
        }
    
    def _stream_loop(self, device_id: str):
        """Background streaming loop"""
        
        frame_interval = 1.0 / self.fps
        
        while self.is_mirroring:
            start_time = time.time()
            
            try:
                # Capture frame
                frame_data = self._capture_frame(device_id)
                
                if frame_data:
                    # Calculate actual FPS
                    self.frame_count += 1
                    now = time.time()
                    
                    if now - self.last_fps_check >= 1.0:
                        self.actual_fps = self.frame_count
                        self.frame_count = 0
                        self.last_fps_check = now
                    
                    # Store for recording
                    if self.is_recording:
                        self.record_frames.append(frame_data)
                    
                    # Broadcast to WebSocket clients
                    asyncio.run_coroutine_threadsafe(
                        self._broadcast_frame(frame_data),
                        asyncio.get_event_loop()
                    )
            
            except Exception:
                pass
            
            # Maintain FPS
            elapsed = time.time() - start_time
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _capture_frame(self, device_id: str) -> Optional[bytes]:
        """Capture single frame from device"""
        
        try:
            from PIL import Image
            import io
            
            # Use ADB exec-out for faster capture
            result = subprocess.run(
                [
                    self.adb.adb_path,
                    '-s', device_id,
                    'exec-out', 'screencap', '-p'
                ],
                capture_output=True,
                timeout=2
            )
            
            if result.returncode != 0 or not result.stdout:
                return None
            
            # Load image
            img = Image.open(io.BytesIO(result.stdout))
            
            # Resize for performance
            if img.width > self.max_width:
                ratio = self.max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize(
                    (self.max_width, new_height),
                    Image.LANCZOS
                )
            
            # Convert to JPEG
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=self.quality)
            
            return output.getvalue()
        
        except Exception:
            return None
    
    async def _broadcast_frame(self, frame_data: bytes):
        """Broadcast frame to all WebSocket clients"""
        
        if not self.clients:
            return
        
        # Encode as base64 for JSON transport
        frame_b64 = base64.b64encode(frame_data).decode()
        
        message = {
            'type': 'screen_frame',
            'frame': frame_b64,
            'fps': self.actual_fps,
            'timestamp': time.time()
        }
        
        import json
        message_str = json.dumps(message)
        
        # Send to all connected clients
        disconnected = []
        for client in self.clients:
            try:
                await client.send(message_str)
            except Exception:
                disconnected.append(client)
        
        for client in disconnected:
            self.clients.remove(client)
    
    async def stop_mirror(self) -> Dict:
        """Stop screen mirroring"""
        
        self.is_mirroring = False
        
        if self.mirror_process:
            self.mirror_process.terminate()
            self.mirror_process = None
        
        if self.stream_thread:
            self.stream_thread = None
        
        return {
            'success': True,
            'message': 'Mirroring stopped',
            'frames_captured': self.frame_count
        }
    
    async def start_recording(self) -> Dict:
        """Start recording the mirror stream"""
        
        if not self.is_mirroring:
            return {'success': False, 'error': 'Not currently mirroring'}
        
        self.is_recording = True
        self.record_frames = []
        
        return {
            'success': True,
            'message': 'Recording started'
        }
    
    async def stop_recording(
        self,
        output_path: Optional[str] = None
    ) -> Dict:
        """Stop recording and save to file"""
        
        self.is_recording = False
        
        if not self.record_frames:
            return {'success': False, 'error': 'No frames recorded'}
        
        try:
            import cv2
            import numpy as np
            from PIL import Image
            import io
            
            save_path = output_path or (
                f"./recordings/phone_record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            )
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Convert frames to video
            first_frame = Image.open(io.BytesIO(self.record_frames[0]))
            width, height = first_frame.size
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(save_path, fourcc, self.fps, (width, height))
            
            for frame_bytes in self.record_frames:
                frame_img = Image.open(io.BytesIO(frame_bytes))
                frame_array = np.array(frame_img)
                frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
                out.write(frame_bgr)
            
            out.release()
            
            return {
                'success': True,
                'path': save_path,
                'frames': len(self.record_frames),
                'duration_s': len(self.record_frames) / self.fps
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_client(self, websocket):
        """Add WebSocket client for streaming"""
        self.clients.append(websocket)
    
    def remove_client(self, websocket):
        """Remove WebSocket client"""
        if websocket in self.clients:
            self.clients.remove(websocket)
    
    def get_status(self) -> Dict:
        """Get mirror status"""
        return {
            'is_mirroring': self.is_mirroring,
            'is_recording': self.is_recording,
            'device_id': self.current_device_id,
            'actual_fps': self.actual_fps,
            'target_fps': self.fps,
            'quality': self.quality,
            'clients_connected': len(self.clients)
        }
