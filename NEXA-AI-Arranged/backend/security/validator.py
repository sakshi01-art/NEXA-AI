import re
from typing import Tuple, List

class SecurityValidator:
    """Validates commands, paths, and actions for dangerous patterns"""
    
    BLOCKED_PATTERNS = [
        r"format\s+[c-z]:",
        r"del\s+/[sfq]\s+c:\\windows",
        r"rmdir\s+/s\s+/q\s+c:\\",
        r":(){ :|:& };:"
    ]
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        cmd_lower = command.lower()
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, cmd_lower):
                return False, f"Command matches blocked dangerous pattern: {pattern}"
        return True, ""
        
    def validate_path(self, path: str) -> Tuple[bool, str]:
        path_lower = path.lower()
        if "c:\\windows\\system32" in path_lower and "del" in path_lower:
            return False, "Access to system32 is restricted"
        return True, ""
