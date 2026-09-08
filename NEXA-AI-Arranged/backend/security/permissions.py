try:
    from ..schemas import PermissionLevel
except (ImportError, ValueError):
    from schemas import PermissionLevel

class PermissionManager:
    """Manages user and system permission levels for tools"""
    
    def __init__(self, default_level: PermissionLevel = PermissionLevel.SAFE):
        self.default_level = default_level
        self.granted_permissions = set()
        
    def check_permission(self, tool_name: str, required_level: PermissionLevel) -> bool:
        if required_level == PermissionLevel.SAFE:
            return True
        return tool_name in self.granted_permissions or required_level == PermissionLevel.SENSITIVE
        
    def grant_permission(self, tool_name: str):
        self.granted_permissions.add(tool_name)
        
    def revoke_permission(self, tool_name: str):
        self.granted_permissions.discard(tool_name)
