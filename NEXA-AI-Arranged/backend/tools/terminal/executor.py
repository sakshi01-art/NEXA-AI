import asyncio
import os
from typing import Dict, Any, Optional

class TerminalExecutor:
    """Executes shell commands asynchronously on Windows"""
    
    def __init__(self, default_dir: Optional[str] = None):
        self.default_dir = default_dir or os.getcwd()
        
    async def execute(self, command: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        cwd = working_dir or self.default_dir
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = await process.communicate()
            return {
                "success": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": command
            }
