import asyncio
import base64
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from PIL import Image
import io

class MultiModalAgent:
    """
    Agent that can process:
    - Voice commands
    - Screen vision
    - Text input
    - Images
    - Documents
    """
    
    def __init__(self, ai_provider, tool_registry, memory_store):
        self.ai = ai_provider
        self.tools = tool_registry
        self.memory = memory_store
        self.active_sessions: Dict[str, Dict] = {}
        self.screen_analyzer = None
        self.current_task = None
        self.task_queue = asyncio.Queue()
        self.is_processing = False
    
    async def process_multimodal_input(
        self,
        text: Optional[str] = None,
        image_path: Optional[str] = None,
        audio_path: Optional[str] = None,
        screen_region: Optional[tuple] = None,
        session_id: str = "default"
    ) -> Dict:
        """
        Process any combination of inputs simultaneously
        """
        
        inputs = []
        context_parts = []
        
        # Process text
        if text:
            inputs.append({'type': 'text', 'content': text})
            context_parts.append(f"User said: {text}")
        
        # Process image
        if image_path:
            image_analysis = await self._analyze_image(image_path)
            inputs.append({'type': 'image', 'content': image_analysis})
            context_parts.append(f"Image contains: {image_analysis.get('description', '')}")
        
        # Process screen capture
        if screen_region:
            screen_analysis = await self._analyze_screen_region(screen_region)
            inputs.append({'type': 'screen', 'content': screen_analysis})
            context_parts.append(f"Screen shows: {screen_analysis.get('description', '')}")
        
        # Get session context
        session = self.active_sessions.get(session_id, {
            'history': [],
            'context': {},
            'preferences': {}
        })
        
        # Get memory context
        similar_past = await self.memory.recall_similar_conversations(
            query=text or "",
            limit=3
        )
        
        memory_context = "\n".join([
            f"Past context: {item['content']}"
            for item in similar_past
        ])
        
        # Build comprehensive context
        full_context = "\n".join(context_parts)
        
        if memory_context:
            full_context = f"{full_context}\n\nRelevant memory:\n{memory_context}"
        
        # Process with AI
        response = await self._process_with_ai(
            inputs=inputs,
            context=full_context,
            session=session
        )
        
        # Store in memory
        if text and response.get('response'):
            await self.memory.store_conversation(
                user_input=text,
                assistant_response=response['response']
            )
        
        # Update session
        session['history'].append({
            'user': full_context,
            'assistant': response.get('response', '')
        })
        self.active_sessions[session_id] = session
        
        return response
    
    async def _analyze_image(self, image_path: str) -> Dict:
        """Analyze image with Vision AI"""
        
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            image_b64 = base64.b64encode(image_data).decode()
            
            # Use GPT-4 Vision or similar
            prompt = """
            Analyze this image and provide:
            1. Main content description
            2. Any text visible
            3. UI elements if it's a screenshot
            4. Objects or people present
            5. Color scheme and style
            6. Any actionable information
            """
            
            # This would use vision-capable AI
            description = await self._get_vision_description(image_b64, prompt)
            
            return {
                'success': True,
                'description': description,
                'image_b64': image_b64
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _analyze_screen_region(self, region: tuple) -> Dict:
        """Analyze specific screen region"""
        
        try:
            from PIL import ImageGrab
            
            screenshot = ImageGrab.grab(bbox=region)
            
            # Convert to base64
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            img_b64 = base64.b64encode(buffer.getvalue()).decode()
            
            description = await self._get_vision_description(
                img_b64,
                "Describe what's on screen. Be specific about text, UI elements, and what the user might want to do."
            )
            
            return {
                'success': True,
                'description': description,
                'region': region
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _get_vision_description(self, image_b64: str, prompt: str) -> str:
        """Get AI description of image"""
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
        
        try:
            response = await self.ai.complete(messages=messages)
            return response.get('content', '')
        except Exception as e:
            return f"Vision analysis unavailable: {str(e)}"
    
    async def _process_with_ai(
        self,
        inputs: List[Dict],
        context: str,
        session: Dict
    ) -> Dict:
        """Process multi-modal inputs with AI agent"""
        
        # Build tool schemas
        tool_schemas = self.tools.get_tool_schemas()
        
        # Build session history
        history = session.get('history', [])[-5:]  # Last 5 turns
        
        messages = []
        
        # System message
        messages.append({
            "role": "system",
            "content": self._build_system_prompt(tool_schemas)
        })
        
        # History
        for turn in history:
            messages.append({"role": "user", "content": turn['user']})
            messages.append({"role": "assistant", "content": turn['assistant']})
        
        # Current context
        messages.append({
            "role": "user",
            "content": context
        })
        
        # Get AI response
        response = await self.ai.complete(
            messages=messages,
            tools=tool_schemas,
            temperature=0.7
        )
        
        result = {
            'response': response.get('content', ''),
            'tool_calls': [],
            'actions_taken': []
        }
        
        # Execute tool calls
        tool_calls = response.get('tool_calls', [])
        
        for tool_call in tool_calls:
            function = tool_call.get('function', {})
            tool_name = function.get('name', '')
            
            try:
                params = json.loads(function.get('arguments', '{}'))
            except:
                params = {}
            
            # Execute tool
            tool_result = await self.tools.execute_tool(tool_name, params)
            
            result['tool_calls'].append({
                'tool': tool_name,
                'params': params,
                'result': tool_result
            })
            
            result['actions_taken'].append(
                f"Executed {tool_name}: {'Success' if tool_result.get('success') else 'Failed'}"
            )
        
        return result
    
    def _build_system_prompt(self, tool_schemas: List[Dict]) -> str:
        return f"""You are NEXA, an advanced multi-modal AI desktop assistant.

You can see the screen, hear voice commands, and understand images.

You have access to {len(tool_schemas)} tools to control the computer.

Respond naturally in the same language the user uses (English, Hindi, or Hinglish).

Be concise, accurate, and helpful.
Execute tasks immediately when safe to do so.
Ask for confirmation only for destructive operations.

Current capabilities:
- Screen vision and understanding
- Voice recognition
- File management
- Application control
- Web browsing
- Code analysis
- System monitoring
"""
    
    async def continuous_screen_watch(
        self,
        callback,
        interval: float = 2.0,
        watch_region: Optional[tuple] = None
    ):
        """Continuously watch screen for changes"""
        
        import hashlib
        from PIL import ImageGrab
        
        last_hash = None
        
        while True:
            try:
                screenshot = ImageGrab.grab(bbox=watch_region)
                
                # Generate hash to detect changes
                img_bytes = screenshot.tobytes()
                current_hash = hashlib.md5(img_bytes).hexdigest()
                
                if current_hash != last_hash:
                    # Screen changed - analyze
                    buffer = io.BytesIO()
                    screenshot.save(buffer, format='PNG')
                    img_b64 = base64.b64encode(buffer.getvalue()).decode()
                    
                    description = await self._get_vision_description(
                        img_b64,
                        "What changed on screen? Be brief."
                    )
                    
                    await callback({
                        'type': 'screen_change',
                        'description': description,
                        'timestamp': asyncio.get_event_loop().time()
                    })
                    
                    last_hash = current_hash
                
                await asyncio.sleep(interval)
            
            except Exception as e:
                await asyncio.sleep(interval)
