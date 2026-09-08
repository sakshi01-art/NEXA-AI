from typing import Dict, List, Optional, Callable
try:
    from ..schemas import ToolDefinition, PermissionLevel
except (ImportError, ValueError):
    from schemas import ToolDefinition, PermissionLevel
import inspect

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Dict] = {}
        self.categories: Dict[str, List[str]] = {}
    
    def register(
        self,
        name: str,
        description: str,
        category: str,
        permission: PermissionLevel,
        schema: dict,
        handler: Callable
    ):
        """Register a new tool"""
        
        self.tools[name] = {
            'name': name,
            'description': description,
            'category': category,
            'permission': permission,
            'schema': schema,
            'handler': handler,
            'enabled': True
        }
        
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(name)
    
    def get_tool(self, name: str) -> Optional[Dict]:
        """Get tool by name"""
        return self.tools.get(name)
    
    def get_tools_by_category(self, category: str) -> List[Dict]:
        """Get all tools in a category"""
        tool_names = self.categories.get(category, [])
        return [self.tools[name] for name in tool_names if name in self.tools]
    
    def get_all_tools(self) -> List[Dict]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def get_tool_schemas(self) -> List[Dict]:
        """Get OpenAI function calling format schemas"""
        schemas = []
        
        for tool in self.tools.values():
            if not tool['enabled']:
                continue
            
            schemas.append({
                'type': 'function',
                'function': {
                    'name': tool['name'],
                    'description': tool['description'],
                    'parameters': tool['schema']
                }
            })
        
        return schemas
    
    def enable_tool(self, name: str):
        """Enable a tool"""
        if name in self.tools:
            self.tools[name]['enabled'] = True
    
    def disable_tool(self, name: str):
        """Disable a tool"""
        if name in self.tools:
            self.tools[name]['enabled'] = False
    
    async def execute_tool(
        self,
        name: str,
        parameters: dict
    ) -> dict:
        """Execute a tool"""
        tool = self.get_tool(name)
        
        if not tool:
            return {
                'success': False,
                'error': f'Tool {name} not found'
            }
        
        if not tool['enabled']:
            return {
                'success': False,
                'error': f'Tool {name} is disabled'
            }
        
        try:
            handler = tool['handler']
            
            # Check if handler is async
            if inspect.iscoroutinefunction(handler):
                result = await handler(**parameters)
            else:
                result = handler(**parameters)
            
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
