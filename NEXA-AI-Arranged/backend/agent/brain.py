from typing import List, Dict, Any, Optional
try:
    from ..ai.providers.interface import AIProvider
    from ..tools.registry import ToolRegistry
except (ImportError, ValueError):
    from ai.providers.interface import AIProvider
    from tools.registry import ToolRegistry
import json

class AgentBrain:
    def __init__(
        self,
        ai_provider: AIProvider,
        tool_registry: ToolRegistry,
        system_prompt: Optional[str] = None
    ):
        self.ai = ai_provider
        self.tools = tool_registry
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.conversation_history: List[Dict[str, str]] = []
    
    def _default_system_prompt(self) -> str:
        return """You are NEXA, an advanced AI desktop assistant for Windows 11.

You understand and respond in:
- English
- Hindi  
- Hinglish (mixed Hindi-English)

Your capabilities:
- Control Windows applications
- Manage files and folders
- Execute system commands
- Search the web
- Automate workflows
- Monitor system status

Communication style:
- Natural and conversational
- Use Hinglish when the user uses Hinglish
- Be concise but helpful
- Confirm before destructive actions
- Explain what you're doing

When you receive a command:
1. Understand the user's intent
2. Plan the necessary steps
3. Use available tools to execute
4. Verify results
5. Provide clear feedback

Available tools:
{tools}

Always use the appropriate tool for the task. Never fake tool execution.
If you cannot do something, clearly say so.
"""
    
    async def understand_intent(
        self,
        user_input: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze user input and determine intent
        
        Returns:
            {
                'intent': str,
                'entities': Dict,
                'language': str,
                'confidence': float,
                'requires_confirmation': bool
            }
        """
        
        # Build messages
        messages = [
            {"role": "system", "content": self._intent_analysis_prompt()},
            {"role": "user", "content": user_input}
        ]
        
        if context:
            messages.insert(1, {
                "role": "system",
                "content": f"Previous context: {json.dumps(context)}"
            })
        
        try:
            response = await self.ai.complete(
                messages=messages,
                temperature=0.3,  # Lower temperature for intent classification
                max_tokens=500
            )
            
            # Parse response
            intent_data = json.loads(response['content'])
            
            return intent_data
        except Exception as e:
            return {
                'intent': 'unknown',
                'entities': {},
                'language': 'unknown',
                'confidence': 0.0,
                'requires_confirmation': False,
                'error': str(e)
            }
    
    async def plan_execution(
        self,
        intent: Dict[str, Any],
        user_input: str
    ) -> List[Dict[str, Any]]:
        """
        Create execution plan for the given intent
        
        Returns:
            List of steps with tool calls
        """
        
        # Get available tools
        available_tools = self.tools.get_tool_schemas()
        
        # Build planning prompt
        messages = [
            {"role": "system", "content": self.system_prompt.format(
                tools=json.dumps(available_tools, indent=2)
            )},
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = await self.ai.complete(
                messages=messages,
                tools=available_tools,
                temperature=0.5
            )
            
            # Extract tool calls
            tool_calls = response.get('tool_calls', [])
            
            if not tool_calls:
                # No tools needed, just text response
                return [{
                    'type': 'response',
                    'content': response['content']
                }]
            
            # Convert tool calls to execution steps
            steps = []
            for tool_call in tool_calls:
                function = tool_call['function']
                steps.append({
                    'type': 'tool',
                    'tool': function['name'],
                    'input': json.loads(function['arguments']),
                    'description': f"Execute {function['name']}"
                })
            
            return steps
        except Exception as e:
            raise Exception(f"Planning failed: {str(e)}")
    
    async def generate_response(
        self,
        user_input: str,
        execution_result: Any,
        language: str = 'hinglish'
    ) -> str:
        """
        Generate natural language response based on execution result
        """
        
        messages = [
            {
                "role": "system",
                "content": f"""Generate a natural {language} response for the user.
                
Be conversational and friendly.
If the task succeeded, confirm it naturally.
If it failed, explain why in simple terms.
Match the user's language style."""
            },
            {
                "role": "user",
                "content": f"User asked: {user_input}"
            },
            {
                "role": "system",
                "content": f"Execution result: {json.dumps(execution_result)}"
            }
        ]
        
        try:
            response = await self.ai.complete(
                messages=messages,
                temperature=0.8,  # More creative for natural responses
                max_tokens=200
            )
            
            return response['content']
        except Exception as e:
            # Fallback response
            if language == 'hinglish' or language == 'hi':
                return f"Kuch error ho gaya: {str(e)}"
            return f"Something went wrong: {str(e)}"
    
    def _intent_analysis_prompt(self) -> str:
        return """Analyze the user's command and extract:

1. Primary intent (what they want to do)
2. Entities (applications, files, folders, etc.)
3. Language (english, hindi, hinglish)
4. Confidence (0.0 to 1.0)
5. Whether this requires confirmation (for destructive actions)

Examples:

Input: "Chrome kholo"
Output: {
  "intent": "open_application",
  "entities": {"application": "chrome"},
  "language": "hinglish",
  "confidence": 0.95,
  "requires_confirmation": false
}

Input: "Delete all PDFs in Downloads"
Output: {
  "intent": "delete_files",
  "entities": {"file_type": "pdf", "location": "downloads"},
  "language": "english",
  "confidence": 0.9,
  "requires_confirmation": true
}

Input: "Mera project folder open kar aur VS Code mein khol"
Output: {
  "intent": "open_project_in_editor",
  "entities": {"folder": "project", "editor": "vscode"},
  "language": "hinglish",
  "confidence": 0.85,
  "requires_confirmation": false
}

Respond only with valid JSON."""
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        
        # Keep last 20 messages
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
