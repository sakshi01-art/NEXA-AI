try:
    from PIL import ImageGrab, Image
except ImportError:
    ImageGrab = None
    Image = None
try:
    import pytesseract
except ImportError:
    pytesseract = None
try:
    import cv2
except ImportError:
    cv2 = None
try:
    import numpy as np
except ImportError:
    np = None
import base64
import io

class ScreenAnalyzer:
    """Analyze screen content, perform OCR, detect UI elements"""
    
    def __init__(self):
        # Set tesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def capture_screen(self, region: Optional[Tuple] = None) -> Image:
        """Capture screen or region"""
        if region:
            return ImageGrab.grab(bbox=region)
        return ImageGrab.grab()
    
    def extract_text(
        self,
        image: Optional[Image] = None,
        region: Optional[Tuple] = None,
        language: str = 'eng+hin'  # English + Hindi
    ) -> Dict:
        """Extract text from screen using OCR"""
        
        try:
            if not image:
                image = self.capture_screen(region)
            
            # Perform OCR
            text = pytesseract.image_to_string(image, lang=language)
            
            # Get detailed data with positions
            data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
            
            # Extract words with positions
            words = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 60:  # Confidence threshold
                    words.append({
                        'text': data['text'][i],
                        'confidence': data['conf'][i],
                        'position': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })
            
            return {
                'success': True,
                'text': text.strip(),
                'words': words,
                'word_count': len([w for w in words if w['text'].strip()])
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_text_on_screen(self, search_text: str) -> Dict:
        """Find specific text on screen and return its position"""
        
        result = self.extract_text()
        
        if not result['success']:
            return result
        
        search_lower = search_text.lower()
        
        matches = [
            word for word in result['words']
            if search_lower in word['text'].lower()
        ]
        
        if matches:
            return {
                'success': True,
                'found': True,
                'matches': matches,
                'count': len(matches)
            }
        
        return {
            'success': True,
            'found': False,
            'message': f'Text "{search_text}" not found on screen'
        }
    
    def detect_ui_elements(self, image: Optional[Image] = None) -> Dict:
        """Detect buttons, text fields, and other UI elements"""
        
        try:
            if not image:
                image = self.capture_screen()
            
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours (potential UI elements)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            elements = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size (likely UI elements)
                if 20 < w < 500 and 20 < h < 100:
                    # Classify by shape
                    aspect_ratio = w / h
                    
                    if 2 < aspect_ratio < 10:
                        element_type = 'button'
                    elif 0.8 < aspect_ratio < 1.2:
                        element_type = 'icon'
                    else:
                        element_type = 'field'
                    
                    elements.append({
                        'type': element_type,
                        'position': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                        'center': {'x': int(x + w/2), 'y': int(y + h/2)}
                    })
            
            return {
                'success': True,
                'elements': elements,
                'count': len(elements)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def describe_screen(self, ai_provider) -> str:
        """Use AI to describe what's on screen"""
        
        # Capture screen
        screen = self.capture_screen()
        
        # Convert to base64
        buffer = io.BytesIO()
        screen.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # This would use GPT-4 Vision or similar
        # For demonstration:
        prompt = """
        Analyze this screenshot and describe:
        1. What application is open
        2. What the user seems to be doing
        3. Any important information visible
        4. Suggestions for next actions
        
        Be concise and helpful.
        """
        
        # Send to AI with image
        # response = await ai_provider.complete_with_image(prompt, img_base64)
        
        return "Screen analysis would go here with vision AI"
    
    def find_and_click_text(self, text: str) -> Dict:
        """Find text on screen and click it"""
        
        result = self.find_text_on_screen(text)
        
        if result.get('found'):
            match = result['matches'][0]
            position = match['position']
            
            # Calculate click position (center of text)
            click_x = position['x'] + position['width'] // 2
            click_y = position['y'] + position['height'] // 2
            
            # Click using pyautogui
            import pyautogui
            pyautogui.click(click_x, click_y)
            
            return {
                'success': True,
                'clicked': True,
                'position': {'x': click_x, 'y': click_y}
            }
        
        return {
            'success': False,
            'error': f'Could not find text: {text}'
        }
    
    def read_notification(self, region: Tuple = (1600, 900, 1900, 1000)) -> Dict:
        """Read notification area"""
        
        # This would be customized based on Windows notification position
        return self.extract_text(region=region)
