import os
import json
from typing import List, Dict, Any, Optional
from .interface import AIProvider

class OpenAIProvider(AIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview"
    ):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        self.client = None
        if self.api_key and self.api_key != "your_openai_api_key_here":
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
            except Exception:
                self.client = None
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        if not self.client:
            # Fallback local interpretation
            from ..factory import LocalRuleAIProvider
            return await LocalRuleAIProvider().complete(messages, tools, temperature, max_tokens)
            
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            response = await self.client.chat.completions.create(**params)
            choice = response.choices[0]
            message = choice.message
            
            tool_calls = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })
                    
            return {
                'content': message.content or '',
                'tool_calls': tool_calls,
                'finish_reason': choice.finish_reason
            }
        except Exception as e:
            # If OpenAI call fails (invalid key/rate limit/quota), use local fallback
            from ..factory import LocalRuleAIProvider
            return await LocalRuleAIProvider().complete(messages, tools, temperature, max_tokens)
    
    async def stream_complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None
    ):
        if not self.client:
            from ..factory import LocalRuleAIProvider
            async for chunk in LocalRuleAIProvider().stream_complete(messages, tools):
                yield chunk
            return
            
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "stream": True,
            }
            if tools:
                params["tools"] = tools
                
            response = await self.client.chat.completions.create(**params)
            async for chunk in response:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    yield {
                        'content': delta.content or '',
                        'tool_calls': delta.tool_calls or [],
                        'finish_reason': chunk.choices[0].finish_reason
                    }
        except Exception:
            from ..factory import LocalRuleAIProvider
            async for chunk in LocalRuleAIProvider().stream_complete(messages, tools):
                yield chunk
    
    def is_available(self) -> bool:
        return bool(self.client and self.api_key and self.api_key != "your_openai_api_key_here")
