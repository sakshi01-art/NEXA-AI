import asyncio
import json
import threading
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime
from pathlib import Path
import numpy as np

class AROverlayEngine:
    """
    Augmented Reality overlay on Windows desktop.
    
    NEXA draws floating UI elements OVER your desktop:
    - Floating command bubbles near any app
    - Click-to-command on any UI element
    - Real-time information overlays
    - Smart annotations on screen content
    - Gesture recognition zones
    - Virtual control panels floating anywhere
    
    Like having a HUD over your entire Windows desktop.
    """
    
    def __init__(self, ai_provider, screen_analyzer, tool_executor):
        self.ai = ai_provider
        self.screen = screen_analyzer
        self.tools = tool_executor
        
        self.overlay_window = None
        self.overlays: Dict[str, Dict] = {}
        self.is_active = False
        self.transparency = 0.85
        self.gesture_zones: List[Dict] = []
        self.floating_panels: List[Dict] = []
        self.smart_annotations: List[Dict] = []
        
        self.overlay_config = {
            "show_app_commands": True,
            "show_smart_annotations": True,
            "show_gesture_zones": True,
            "show_floating_panels": True,
            "auto_annotate_text": True,
            "show_ai_suggestions": True
        }
    
    async def initialize_overlay(self) -> Dict:
        """Create transparent overlay window over desktop"""
        
        try:
            import tkinter as tk
            from tkinter import ttk
            import win32gui
            import win32con
            import win32api
            
            # Create overlay window
            self.root = tk.Tk()
            self.root.title("NEXA AR Overlay")
            
            # Make it fullscreen and transparent
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")
            self.root.configure(bg='black')
            self.root.attributes('-alpha', 0.01)  # Nearly invisible background
            self.root.attributes('-topmost', True)
            self.root.overrideredirect(True)  # No title bar
            
            # Make click-through for areas without overlays
            hwnd = win32gui.FindWindow(None, "NEXA AR Overlay")
            win32gui.SetWindowLong(
                hwnd,
                win32con.GWL_EXSTYLE,
                win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) |
                win32con.WS_EX_LAYERED |
                win32con.WS_EX_TRANSPARENT
            )
            
            # Canvas for drawing overlays
            self.canvas = tk.Canvas(
                self.root,
                width=screen_width,
                height=screen_height,
                bg='black',
                highlightthickness=0
            )
            self.canvas.pack(fill='both', expand=True)
            
            self.is_active = True
            
            # Start update loop
            asyncio.create_task(self._update_loop())
            
            return {
                'success': True,
                'screen_size': (screen_width, screen_height),
                'message': 'AR Overlay activated'
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _update_loop(self):
        """Continuous overlay update loop"""
        
        while self.is_active:
            try:
                # Clear canvas
                self.canvas.delete('all')
                
                # Draw all active overlays
                for overlay_id, overlay in self.overlays.items():
                    await self._draw_overlay(overlay)
                
                # Draw floating panels
                for panel in self.floating_panels:
                    await self._draw_floating_panel(panel)
                
                # Draw gesture zones
                if self.overlay_config['show_gesture_zones']:
                    for zone in self.gesture_zones:
                        self._draw_gesture_zone(zone)
                
                # Update smart annotations
                if self.overlay_config['show_smart_annotations']:
                    await self._update_smart_annotations()
                
                # Refresh canvas
                self.root.update()
                
                await asyncio.sleep(0.033)  # ~30 FPS
            
            except Exception:
                await asyncio.sleep(0.1)
    
    async def _draw_overlay(self, overlay: Dict):
        """Draw a single overlay element"""
        
        x, y = overlay.get('position', (100, 100))
        overlay_type = overlay.get('type', 'bubble')
        content = overlay.get('content', '')
        color = overlay.get('color', '#6366F1')
        
        if overlay_type == 'bubble':
            self._draw_command_bubble(x, y, content, color)
        
        elif overlay_type == 'info_card':
            self._draw_info_card(x, y, content, color)
        
        elif overlay_type == 'progress_ring':
            self._draw_progress_ring(
                x, y,
                overlay.get('progress', 0),
                color
            )
        
        elif overlay_type == 'status_dot':
            self._draw_status_dot(x, y, color)
    
    def _draw_command_bubble(self, x: int, y: int, text: str, color: str):
        """Draw floating command bubble"""
        
        padding = 10
        
        # Measure text
        text_width = len(text) * 7
        text_height = 20
        
        bubble_width = text_width + padding * 2
        bubble_height = text_height + padding * 2
        
        # Draw rounded rectangle
        self.canvas.create_rounded_rect = self._create_rounded_rect
        
        # Background
        self.canvas.create_rectangle(
            x, y,
            x + bubble_width, y + bubble_height,
            fill=color,
            outline='',
            tags='overlay'
        )
        
        # Glow effect
        for i in range(5, 0, -1):
            self.canvas.create_rectangle(
                x - i, y - i,
                x + bubble_width + i, y + bubble_height + i,
                outline=color,
                width=1,
                tags='overlay'
            )
        
        # Text
        self.canvas.create_text(
            x + bubble_width // 2,
            y + bubble_height // 2,
            text=text,
            fill='white',
            font=('Inter', 11, 'bold'),
            tags='overlay'
        )
    
    def _draw_info_card(self, x: int, y: int, content: Dict, color: str):
        """Draw floating information card"""
        
        width = 250
        height = 120
        
        # Card background
        self.canvas.create_rectangle(
            x, y, x + width, y + height,
            fill='#0A0E1A',
            outline=color,
            width=2,
            tags='overlay'
        )
        
        # Title
        self.canvas.create_text(
            x + 15, y + 20,
            text=content.get('title', ''),
            fill=color,
            font=('Inter', 11, 'bold'),
            anchor='w',
            tags='overlay'
        )
        
        # Content lines
        lines = content.get('lines', [])
        for i, line in enumerate(lines[:4]):
            self.canvas.create_text(
                x + 15,
                y + 45 + i * 18,
                text=line,
                fill='#D1D5DB',
                font=('Inter', 10),
                anchor='w',
                tags='overlay'
            )
    
    def _draw_progress_ring(
        self,
        x: int,
        y: int,
        progress: float,
        color: str
    ):
        """Draw animated progress ring"""
        
        radius = 30
        cx, cy = x + radius, y + radius
        
        # Background ring
        self.canvas.create_oval(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            outline='#374151',
            width=4,
            tags='overlay'
        )
        
        # Progress arc
        extent = progress * 360
        self.canvas.create_arc(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            start=90,
            extent=-extent,
            outline=color,
            width=4,
            style='arc',
            tags='overlay'
        )
        
        # Percentage text
        self.canvas.create_text(
            cx, cy,
            text=f'{int(progress * 100)}%',
            fill='white',
            font=('Inter', 10, 'bold'),
            tags='overlay'
        )
    
    def _draw_status_dot(self, x: int, y: int, color: str):
        """Draw animated status indicator dot"""
        
        size = 8
        
        # Outer glow
        self.canvas.create_oval(
            x - size * 2, y - size * 2,
            x + size * 2, y + size * 2,
            fill=color,
            outline='',
            tags='overlay'
        )
        
        # Inner dot
        self.canvas.create_oval(
            x - size, y - size,
            x + size, y + size,
            fill='white',
            outline='',
            tags='overlay'
        )
    
    def _draw_gesture_zone(self, zone: Dict):
        """Draw gesture recognition zone"""
        
        x, y, w, h = zone['x'], zone['y'], zone['width'], zone['height']
        
        # Dashed border
        self.canvas.create_rectangle(
            x, y, x + w, y + h,
            outline='#6366F1',
            width=1,
            dash=(5, 5),
            tags='overlay'
        )
        
        # Label
        self.canvas.create_text(
            x + w // 2, y + h // 2,
            text=zone.get('label', 'Gesture Zone'),
            fill='#6366F1',
            font=('Inter', 9),
            tags='overlay'
        )
    
    async def _draw_floating_panel(self, panel: Dict):
        """Draw a floating control panel"""
        
        x, y = panel['x'], panel['y']
        width = panel.get('width', 200)
        
        # Panel background
        self.canvas.create_rectangle(
            x, y,
            x + width, y + 40 + len(panel.get('buttons', [])) * 35,
            fill='#111827',
            outline='#374151',
            width=1,
            tags='overlay'
        )
        
        # Title bar
        self.canvas.create_rectangle(
            x, y,
            x + width, y + 30,
            fill='#1F2937',
            outline='',
            tags='overlay'
        )
        
        self.canvas.create_text(
            x + 10, y + 15,
            text=panel.get('title', 'NEXA Panel'),
            fill='#6366F1',
            font=('Inter', 10, 'bold'),
            anchor='w',
            tags='overlay'
        )
        
        # Buttons
        for i, button in enumerate(panel.get('buttons', [])):
            btn_y = y + 40 + i * 35
            
            self.canvas.create_rectangle(
                x + 10, btn_y,
                x + width - 10, btn_y + 28,
                fill='#374151',
                outline='#4B5563',
                tags='overlay'
            )
            
            self.canvas.create_text(
                x + width // 2, btn_y + 14,
                text=button.get('label', ''),
                fill='white',
                font=('Inter', 10),
                tags='overlay'
            )
    
    async def _update_smart_annotations(self):
        """Automatically annotate screen content"""
        
        # This would use OCR to find text and annotate it
        # For now, we use pre-defined annotations
        for annotation in self.smart_annotations:
            x, y = annotation['position']
            text = annotation['text']
            
            self.canvas.create_text(
                x, y,
                text=text,
                fill='#F59E0B',
                font=('Inter', 9),
                tags='overlay'
            )
    
    def add_overlay(
        self,
        overlay_id: str,
        position: Tuple[int, int],
        overlay_type: str,
        content: any,
        color: str = '#6366F1',
        duration: Optional[float] = None
    ):
        """Add a new overlay element"""
        
        self.overlays[overlay_id] = {
            'id': overlay_id,
            'position': position,
            'type': overlay_type,
            'content': content,
            'color': color,
            'created_at': datetime.now()
        }
        
        if duration:
            asyncio.create_task(self._auto_remove(overlay_id, duration))
    
    async def _auto_remove(self, overlay_id: str, delay: float):
        """Auto-remove overlay after delay"""
        await asyncio.sleep(delay)
        self.remove_overlay(overlay_id)
    
    def remove_overlay(self, overlay_id: str):
        """Remove an overlay element"""
        if overlay_id in self.overlays:
            del self.overlays[overlay_id]
    
    def add_floating_panel(
        self,
        title: str,
        position: Tuple[int, int],
        buttons: List[Dict]
    ):
        """Add floating control panel"""
        
        panel = {
            'id': f"panel_{datetime.now().timestamp()}",
            'title': title,
            'x': position[0],
            'y': position[1],
            'buttons': buttons
        }
        
        self.floating_panels.append(panel)
        return panel['id']
    
    def add_gesture_zone(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
        callback: Callable
    ):
        """Add gesture recognition zone"""
        
        zone = {
            'id': f"zone_{datetime.now().timestamp()}",
            'x': x, 'y': y,
            'width': width, 'height': height,
            'label': label,
            'callback': callback
        }
        
        self.gesture_zones.append(zone)
        return zone['id']
    
    async def show_app_quick_commands(self, app_name: str, position: Tuple[int, int]):
        """Show quick commands for an app as floating bubbles"""
        
        # Get AI-suggested commands for this app
        prompt = f"""
        What are the 4 most useful quick commands for {app_name}?
        Return as JSON array of short strings (max 20 chars each).
        Example: ["Open new tab", "Search...", "Bookmark", "History"]
        """
        
        try:
            response = await self.ai.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            commands = json.loads(response['content'])
            
            x, y = position
            for i, cmd in enumerate(commands[:4]):
                self.add_overlay(
                    overlay_id=f"quick_{app_name}_{i}",
                    position=(x + i * 130, y),
                    overlay_type='bubble',
                    content=cmd,
                    color='#6366F1',
                    duration=5.0
                )
        except:
            pass
    
    def deactivate(self):
        """Deactivate AR overlay"""
        self.is_active = False
        if self.overlay_window:
            self.root.destroy()
    
    def _create_rounded_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
        """Helper to draw rounded rectangle on canvas"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, **kwargs, smooth=True)
