import os
import json
from typing import List, Dict, Any, Optional
from .providers.interface import AIProvider
from .providers.openai_provider import OpenAIProvider

class LocalRuleAIProvider(AIProvider):
    """Fallback / Offline AI provider that interprets commands and answers questions"""
    
    def __init__(self):
        self.model = "local-nexa-engine"
    
    def is_available(self) -> bool:
        return True
        
    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        last_msg = messages[-1]["content"] if messages else ""
        system_msg = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        
        # Check if this is an intent analysis request
        if "Analyze the user's command and extract" in system_msg or "intent" in system_msg.lower():
            intent = "chat"
            entities = {}
            confidence = 0.9
            lower_input = last_msg.lower()
            
            if any(w in lower_input for w in ["chrome", "browser", "youtube", "google"]):
                intent = "open_application"
                entities = {"application": "chrome"}
            elif any(w in lower_input for w in ["notepad", "note"]):
                intent = "open_application"
                entities = {"application": "notepad"}
            elif any(w in lower_input for w in ["code", "vscode", "vs code"]):
                intent = "open_application"
                entities = {"application": "code"}
            elif any(w in lower_input for w in ["status", "system", "ram", "cpu", "battery"]):
                intent = "get_system_stats"
            elif any(w in lower_input for w in ["screenshot", "screen"]):
                intent = "take_screenshot"
            elif any(w in lower_input for w in ["file", "files", "folder", "list"]):
                intent = "list_files"
                entities = {"directory": "."}
                
            result = {
                "intent": intent,
                "entities": entities,
                "language": "hinglish" if any(w in lower_input for w in ["kholo", "bata", "karo", "kya", "hai"]) else "english",
                "confidence": confidence,
                "requires_confirmation": False
            }
            return {
                "content": json.dumps(result),
                "tool_calls": [],
                "finish_reason": "stop"
            }
            
        # Check if planning execution
        if tools and ("Available tools" in system_msg or "Execution plan" in system_msg):
            lower_input = last_msg.lower()
            tool_calls = []
            
            if "chrome" in lower_input:
                tool_calls.append({
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "open_application",
                        "arguments": json.dumps({"application": "chrome"})
                    }
                })
            elif "notepad" in lower_input:
                tool_calls.append({
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "open_application",
                        "arguments": json.dumps({"application": "notepad"})
                    }
                })
            elif "vscode" in lower_input or "code" in lower_input:
                tool_calls.append({
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "open_application",
                        "arguments": json.dumps({"application": "code"})
                    }
                })
            elif any(w in lower_input for w in ["status", "system", "ram", "cpu", "battery"]):
                tool_calls.append({
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "get_system_stats",
                        "arguments": json.dumps({})
                    }
                })
            elif "screenshot" in lower_input:
                tool_calls.append({
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "take_screenshot",
                        "arguments": json.dumps({})
                    }
                })
                
            if tool_calls:
                return {
                    "content": "Executing requested tools.",
                    "tool_calls": tool_calls,
                    "finish_reason": "tool_calls"
                }
            
            return {
                "content": f"Samajh gaya! Aapne kaha: '{last_msg}'. NEXA AI ready hai.",
                "tool_calls": [],
                "finish_reason": "stop"
            }
            
        # Normal conversational response
        return {
            "content": f"Namaste! Main NEXA AI hoon. Aapki command: '{last_msg}' prapt ho gayi hai.",
            "tool_calls": [],
            "finish_reason": "stop"
        }
        
    async def stream_complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None
    ):
        res = await self.complete(messages, tools)
        yield res["content"]

class AIProviderFactory:
    @staticmethod
    def create(provider: str = "openai", api_key: str = "", model: str = "gpt-4-turbo-preview") -> AIProvider:
        key = api_key or os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if provider.lower() == "openai" and key:
            try:
                return OpenAIProvider(api_key=key, model=model)
            except Exception:
                pass
        # Fallback to local rule engine so system never crashes
        return LocalRuleAIProvider()
