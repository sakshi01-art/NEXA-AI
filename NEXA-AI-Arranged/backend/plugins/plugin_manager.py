import importlib
import importlib.util
import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio

class PluginManager:
    """
    Dynamic plugin system for extending NEXA capabilities.
    Plugins can add:
    - New tools
    - New integrations
    - New UI panels
    - New voice commands
    - New automations
    """
    
    def __init__(self, plugins_dir: str = "./plugins", tool_registry=None):
        self.plugins_dir = Path(plugins_dir)
        self.tool_registry = tool_registry
        self.loaded_plugins: Dict[str, Dict] = {}
        self.plugin_hooks: Dict[str, List] = {}
        
        # Create plugins directory if it doesn't exist
        self.plugins_dir.mkdir(exist_ok=True)
        
        # Create example plugin manifest
        self._create_example_plugin()
    
    def _create_example_plugin(self):
        """Create example plugin structure"""
        
        example_dir = self.plugins_dir / "example_plugin"
        example_dir.mkdir(exist_ok=True)
        
        manifest = {
            "name": "Example Plugin",
            "id": "example_plugin",
            "version": "1.0.0",
            "description": "An example NEXA plugin",
            "author": "NEXA Developer",
            "entry_point": "main.py",
            "tools": ["example_tool"],
            "hooks": ["on_message", "on_task_complete"],
            "permissions": ["filesystem", "network"],
            "enabled": False
        }
        
        manifest_path = example_dir / "manifest.json"
        if not manifest_path.exists():
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
        
        main_py = example_dir / "main.py"
        if not main_py.exists():
            with open(main_py, 'w') as f:
                f.write("""
# Example NEXA Plugin

PLUGIN_INFO = {
    "name": "Example Plugin",
    "version": "1.0.0"
}

def get_tools():
    \"\"\"Return list of tools this plugin provides\"\"\"
    return [
        {
            "name": "example_tool",
            "description": "An example tool",
            "permission": "safe",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "A message"}
                },
                "required": ["message"]
            },
            "handler": example_tool_handler
        }
    ]

async def example_tool_handler(message: str):
    \"\"\"Example tool implementation\"\"\"
    return {"success": True, "result": f"Example: {message}"}

def on_message(message: str):
    \"\"\"Hook: called on every user message\"\"\"
    pass

def on_task_complete(task: dict):
    \"\"\"Hook: called when a task completes\"\"\"
    pass
""")
    
    def discover_plugins(self) -> List[Dict]:
        """Discover all available plugins"""
        
        plugins = []
        
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue
            
            manifest_path = plugin_dir / "manifest.json"
            
            if manifest_path.exists():
                try:
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                    
                    manifest['directory'] = str(plugin_dir)
                    manifest['installed'] = True
                    
                    plugins.append(manifest)
                
                except json.JSONDecodeError:
                    pass
        
        return plugins
    
    async def load_plugin(self, plugin_id: str) -> Dict:
        """Load and activate a plugin"""
        
        plugins = self.discover_plugins()
        plugin_info = next((p for p in plugins if p['id'] == plugin_id), None)
        
        if not plugin_info:
            return {'success': False, 'error': f'Plugin {plugin_id} not found'}
        
        if not plugin_info.get('enabled', False):
            return {'success': False, 'error': f'Plugin {plugin_id} is disabled'}
        
        try:
            # Load the module
            entry_point = Path(plugin_info['directory']) / plugin_info['entry_point']
            
            spec = importlib.util.spec_from_file_location(
                plugin_id,
                entry_point
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Register plugin tools
            if hasattr(module, 'get_tools') and self.tool_registry:
                tools = module.get_tools()
                
                for tool in tools:
                    self.tool_registry.register(
                        name=f"{plugin_id}_{tool['name']}",
                        description=tool['description'],
                        category=f"plugin_{plugin_id}",
                        permission=tool['permission'],
                        schema=tool['schema'],
                        handler=tool['handler']
                    )
            
            # Register hooks
            hooks = plugin_info.get('hooks', [])
            
            for hook in hooks:
                if hasattr(module, hook):
                    if hook not in self.plugin_hooks:
                        self.plugin_hooks[hook] = []
                    self.plugin_hooks[hook].append(getattr(module, hook))
            
            # Store loaded plugin
            self.loaded_plugins[plugin_id] = {
                'info': plugin_info,
                'module': module
            }
            
            return {
                'success': True,
                'plugin': plugin_info['name'],
                'tools_registered': len(plugin_info.get('tools', [])),
                'hooks_registered': len(hooks)
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def unload_plugin(self, plugin_id: str) -> Dict:
        """Unload a plugin"""
        
        if plugin_id not in self.loaded_plugins:
            return {'success': False, 'error': 'Plugin not loaded'}
        
        plugin = self.loaded_plugins[plugin_id]
        plugin_info = plugin['info']
        
        # Remove registered tools
        if self.tool_registry:
            for tool_name in plugin_info.get('tools', []):
                full_name = f"{plugin_id}_{tool_name}"
                if full_name in self.tool_registry.tools:
                    del self.tool_registry.tools[full_name]
        
        # Remove hooks
        for hook_name, handlers in self.plugin_hooks.items():
            self.plugin_hooks[hook_name] = [
                h for h in handlers
                if not str(h).startswith(f"<function {plugin_id}")
            ]
        
        del self.loaded_plugins[plugin_id]
        
        return {'success': True, 'message': f'Plugin {plugin_id} unloaded'}
    
    async def trigger_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Trigger a plugin hook"""
        
        results = []
        
        handlers = self.plugin_hooks.get(hook_name, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(*args, **kwargs)
                else:
                    result = handler(*args, **kwargs)
                
                results.append(result)
            except Exception as e:
                results.append({'error': str(e)})
        
        return results
    
    async def install_plugin_from_url(self, url: str) -> Dict:
        """Install plugin from URL (future feature)"""
        
        # This would download and install a plugin
        # Requires signature verification for security
        
        return {
            'success': False,
            'error': 'Remote plugin installation coming soon',
            'info': 'Place plugin folder manually in /plugins directory'
        }
    
    def get_loaded_plugins(self) -> List[Dict]:
        """Get list of loaded plugins"""
        
        return [
            {
                'id': pid,
                'name': plugin['info']['name'],
                'version': plugin['info']['version'],
                'tools': plugin['info'].get('tools', [])
            }
            for pid, plugin in self.loaded_plugins.items()
        ]
    
    def enable_plugin(self, plugin_id: str) -> Dict:
        """Enable a plugin"""
        
        plugins = self.discover_plugins()
        plugin = next((p for p in plugins if p['id'] == plugin_id), None)
        
        if not plugin:
            return {'success': False, 'error': 'Plugin not found'}
        
        manifest_path = Path(plugin['directory']) / 'manifest.json'
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        manifest['enabled'] = True
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return {'success': True, 'message': f'Plugin {plugin_id} enabled'}
    
    def disable_plugin(self, plugin_id: str) -> Dict:
        """Disable a plugin"""
        
        plugins = self.discover_plugins()
        plugin = next((p for p in plugins if p['id'] == plugin_id), None)
        
        if not plugin:
            return {'success': False, 'error': 'Plugin not found'}
        
        manifest_path = Path(plugin['directory']) / 'manifest.json'
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        manifest['enabled'] = False
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return {'success': True, 'message': f'Plugin {plugin_id} disabled'}
