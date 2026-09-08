import asyncio
import base64
import io
import json
from typing import Dict, Optional, Callable, Set
from PIL import ImageGrab
import websockets
import threading

class RemoteAssistanceServer:
    """
    Allows NEXA to share screen and accept remote
    AI assistance from the cloud
    """
    
    def __init__(self, port: int = 8766):
        self.port = port
        self.clients: Set = set()
        self.server = None
        self.is_running = False
        self.session_id = None
        self.on_command_received: Optional[Callable] = None
        self.streaming = False
        self.stream_quality = 0.5  # JPEG quality 0-1
        self.stream_fps = 10
    
    async def start_server(self) -> Dict:
        """Start WebSocket server for screen sharing"""
        
        try:
            import uuid
            self.session_id = str(uuid.uuid4())[:8].upper()
            
            self.server = await websockets.serve(
                self._handle_client,
                "0.0.0.0",
                self.port
            )
            
            self.is_running = True
            
            return {
                'success': True,
                'session_id': self.session_id,
                'port': self.port,
                'url': f"ws://localhost:{self.port}"
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _handle_client(self, websocket, path):
        """Handle incoming WebSocket connection"""
        
        self.clients.add(websocket)
        
        try:
            # Send session info
            await websocket.send(json.dumps({
                'type': 'session_info',
                'session_id': self.session_id
            }))
            
            # Start screen streaming
            streaming_task = asyncio.create_task(
                self._stream_screen(websocket)
            )
            
            async for message in websocket:
                data = json.loads(message)
                
                if data.get('type') == 'command':
                    if self.on_command_received:
                        await self.on_command_received(data.get('command'))
                
                elif data.get('type') == 'mouse_control':
                    await self._handle_mouse_control(data)
                
                elif data.get('type') == 'keyboard_control':
                    await self._handle_keyboard_control(data)
                
                elif data.get('type') == 'stop_streaming':
                    streaming_task.cancel()
        
        finally:
            self.clients.discard(websocket)
            streaming_task.cancel()
    
    async def _stream_screen(self, websocket):
        """Stream screen frames to client"""
        
        frame_interval = 1.0 / self.stream_fps
        
        while True:
            try:
                # Capture screen
                screen = ImageGrab.grab()
                
                # Resize for efficiency
                width, height = screen.size
                scale = min(1280 / width, 720 / height)
                new_size = (int(width * scale), int(height * scale))
                screen = screen.resize(new_size)
                
                # Convert to JPEG bytes
                buffer = io.BytesIO()
                screen.save(buffer, format='JPEG', quality=int(self.stream_quality * 100))
                frame_bytes = buffer.getvalue()
                
                # Encode and send
                frame_b64 = base64.b64encode(frame_bytes).decode()
                
                await websocket.send(json.dumps({
                    'type': 'screen_frame',
                    'frame': frame_b64,
                    'width': new_size[0],
                    'height': new_size[1],
                    'timestamp': asyncio.get_event_loop().time()
                }))
                
                await asyncio.sleep(frame_interval)
            
            except asyncio.CancelledError:
                break
            except Exception:
                break
    
    async def _handle_mouse_control(self, data: Dict):
        """Handle remote mouse control"""
        
        import pyautogui
        
        action = data.get('action')
        x = data.get('x', 0)
        y = data.get('y', 0)
        
        if action == 'move':
            pyautogui.moveTo(x, y)
        elif action == 'click':
            pyautogui.click(x, y)
        elif action == 'right_click':
            pyautogui.rightClick(x, y)
        elif action == 'double_click':
            pyautogui.doubleClick(x, y)
        elif action == 'scroll':
            pyautogui.scroll(data.get('amount', 0), x, y)
    
    async def _handle_keyboard_control(self, data: Dict):
        """Handle remote keyboard control"""
        
        import pyautogui
        
        action = data.get('action')
        
        if action == 'type':
            pyautogui.typewrite(data.get('text', ''))
        elif action == 'hotkey':
            keys = data.get('keys', [])
            pyautogui.hotkey(*keys)
        elif action == 'press':
            pyautogui.press(data.get('key', ''))
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        
        self.is_running = False
        
        for client in self.clients:
            await client.close()
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
    
    async def broadcast_event(self, event: Dict):
        """Broadcast event to all connected clients"""
        
        if self.clients:
            message = json.dumps(event)
            
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )
