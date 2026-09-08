
# Example NEXA Plugin

PLUGIN_INFO = {
    "name": "Example Plugin",
    "version": "1.0.0"
}

def get_tools():
    """Return list of tools this plugin provides"""
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
    """Example tool implementation"""
    return {"success": True, "result": f"Example: {message}"}

def on_message(message: str):
    """Hook: called on every user message"""
    pass

def on_task_complete(task: dict):
    """Hook: called when a task completes"""
    pass
