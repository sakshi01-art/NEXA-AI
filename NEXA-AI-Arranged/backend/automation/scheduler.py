import asyncio
from typing import Dict, Any, Callable, List

class TaskScheduler:
    """Manages scheduled background automation tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, Any] = {}
        self.is_running = False
        
    def add_task(self, name: str, callback: Callable, interval_seconds: int):
        self.tasks[name] = {
            "callback": callback,
            "interval": interval_seconds,
            "enabled": True
        }
        
    def remove_task(self, name: str):
        self.tasks.pop(name, None)
        
    def list_tasks(self) -> List[Dict[str, Any]]:
        return [{"name": k, "interval": v["interval"], "enabled": v["enabled"]} for k, v in self.tasks.items()]
