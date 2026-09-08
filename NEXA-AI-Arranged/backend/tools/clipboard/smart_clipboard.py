try:
    import pyperclip
except ImportError:
    pyperclip = None
try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None
from typing import List, Dict, Optional
from datetime import datetime
import re
import json
import io
import base64

class SmartClipboardManager:
    """Intelligent clipboard with history, search, and AI understanding"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history: List[Dict] = []
        self.favorites: List[Dict] = []
        self.last_clipboard = ""
        
    def start_monitoring(self):
        """Start monitoring clipboard changes"""
        import threading
        
        def monitor():
            while True:
                try:
                    current = pyperclip.paste()
                    
                    if current != self.last_clipboard and current.strip():
                        self.add_to_history(current)
                        self.last_clipboard = current
                    
                    import time
                    time.sleep(0.5)  # Check every 500ms
                except Exception:
                    pass
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def add_to_history(self, content: str):
        """Add item to clipboard history"""
        
        # Detect content type
        content_type = self._detect_content_type(content)
        
        item = {
            'id': datetime.now().timestamp(),
            'content': content,
            'type': content_type,
            'timestamp': datetime.now().isoformat(),
            'metadata': self._extract_metadata(content, content_type)
        }
        
        self.history.insert(0, item)
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
    
    def _detect_content_type(self, content: str) -> str:
        """Detect type of clipboard content"""
        
        # URL
        if re.match(r'https?://', content):
            return 'url'
        
        # Email
        if re.match(r'[\w\.-]+@[\w\.-]+\.\w+', content):
            return 'email'
        
        # Phone
        if re.match(r'[\+\d][\d\-\(\) ]{8,}', content):
            return 'phone'
        
        # Code (has common programming patterns)
        if any(keyword in content for keyword in ['function', 'def ', 'class ', 'import ', '<?php', 'const ']):
            return 'code'
        
        # JSON
        try:
            json.loads(content)
            return 'json'
        except:
            pass
        
        # Color hex
        if re.match(r'#[0-9A-Fa-f]{6}', content):
            return 'color'
        
        # File path
        if re.match(r'[A-Za-z]:\\|/', content):
            return 'path'
        
        # Number
        if content.replace('.', '').replace('-', '').isdigit():
            return 'number'
        
        return 'text'
    
    def _extract_metadata(self, content: str, content_type: str) -> Dict:
        """Extract useful metadata from content"""
        
        metadata = {
            'length': len(content),
            'words': len(content.split()) if content_type == 'text' else 0
        }
        
        if content_type == 'url':
            # Extract domain
            match = re.search(r'https?://([^/]+)', content)
            if match:
                metadata['domain'] = match.group(1)
        
        elif content_type == 'code':
            # Detect language
            if 'def ' in content or 'import ' in content:
                metadata['language'] = 'python'
            elif 'function' in content or 'const ' in content:
                metadata['language'] = 'javascript'
            elif '<?php' in content:
                metadata['language'] = 'php'
        
        elif content_type == 'color':
            metadata['hex'] = content
        
        return metadata
    
    def get_history(
        self,
        content_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get clipboard history"""
        
        if content_type:
            filtered = [
                item for item in self.history
                if item['type'] == content_type
            ]
            return filtered[:limit]
        
        return self.history[:limit]
    
    def search_history(self, query: str) -> List[Dict]:
        """Search clipboard history"""
        
        query_lower = query.lower()
        
        results = [
            item for item in self.history
            if query_lower in item['content'].lower()
        ]
        
        return results
    
    def add_to_favorites(self, item_id: float):
        """Add clipboard item to favorites"""
        
        item = next((i for i in self.history if i['id'] == item_id), None)
        
        if item and item not in self.favorites:
            self.favorites.append(item)
            return True
        
        return False
    
    def get_favorites(self) -> List[Dict]:
        """Get favorite clipboard items"""
        return self.favorites
    
    def copy_from_history(self, item_id: float):
        """Copy item from history back to clipboard"""
        
        item = next((i for i in self.history if i['id'] == item_id), None)
        
        if item:
            pyperclip.copy(item['content'])
            return True
        
        return False
    
    def clear_history(self):
        """Clear clipboard history"""
        self.history = []
    
    async def smart_paste(self, context: str, ai_provider) -> str:
        """AI-powered smart paste based on context"""
        
        # Get recent clipboard items
        recent = self.get_history(limit=10)
        
        # Ask AI to choose the most relevant item
        prompt = f"""
        User is in this context: {context}
        
        Recent clipboard items:
        {json.dumps([{'id': i['id'], 'content': i['content'][:100], 'type': i['type']} for i in recent], indent=2)}
        
        Which clipboard item is most relevant? Return the item id as a number.
        """
        
        # This would use the AI provider to make a decision
        # For now, return the most recent
        return recent[0]['content'] if recent else ""
    
    def capture_screenshot_to_clipboard(self) -> Dict:
        """Capture screenshot and add to clipboard"""
        
        try:
            screenshot = ImageGrab.grab()
            
            # Convert to base64 for storage
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            item = {
                'id': datetime.now().timestamp(),
                'content': img_str,
                'type': 'image',
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'width': screenshot.width,
                    'height': screenshot.height,
                    'format': 'PNG'
                }
            }
            
            self.history.insert(0, item)
            
            return {'success': True, 'item': item}
        except Exception as e:
            return {'success': False, 'error': str(e)}
