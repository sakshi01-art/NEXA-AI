import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import hashlib

class NeuralShortcutSystem:
    """
    Learns your most common command patterns and
    creates intelligent one-tap shortcuts.
    
    UNIQUE: Shortcuts are NOT manually created.
    They emerge automatically from usage patterns.
    
    Examples:
    - User says "Chrome kholo YouTube search karo music" 3 times
    → NEXA auto-creates shortcut "Music Mode"
    
    - User opens VS Code + Terminal + GitHub Desktop every morning
    → NEXA creates "Dev Morning Routine" shortcut
    
    - User always checks email then Slack then Calendar
    → NEXA creates "Morning Check" shortcut
    """
    
    def __init__(self, ai_provider, min_occurrences: int = 3):
        self.ai = ai_provider
        self.min_occurrences = min_occurrences
        self.command_sequences: List[Dict] = []
        self.discovered_shortcuts: List[Dict] = []
        self.active_shortcuts: Dict[str, Dict] = {}
        self.shortcuts_file = Path("./data/neural_shortcuts.json")
        self._load_shortcuts()
    
    def _load_shortcuts(self):
        """Load saved shortcuts"""
        if self.shortcuts_file.exists():
            with open(self.shortcuts_file) as f:
                data = json.load(f)
                self.active_shortcuts = data.get("shortcuts", {})
                self.command_sequences = data.get("sequences", [])
    
    def _save_shortcuts(self):
        """Save shortcuts to disk"""
        self.shortcuts_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.shortcuts_file, 'w') as f:
            json.dump({
                "shortcuts": self.active_shortcuts,
                "sequences": self.command_sequences[-200:]  # Keep last 200
            }, f, indent=2, default=str)
    
    def record_command(
        self,
        command: str,
        tools_used: List[str],
        timestamp: Optional[datetime] = None
    ):
        """Record each command for pattern learning"""
        
        ts = timestamp or datetime.now()
        
        self.command_sequences.append({
            "command": command,
            "tools": tools_used,
            "hour": ts.hour,
            "weekday": ts.weekday(),
            "timestamp": ts.isoformat()
        })
        
        # Keep last 500 commands
        self.command_sequences = self.command_sequences[-500:]
        
        # Try to discover new shortcuts after every 10 commands
        if len(self.command_sequences) % 10 == 0:
            import asyncio
            asyncio.create_task(self.discover_shortcuts())
        
        self._save_shortcuts()
    
    async def discover_shortcuts(self) -> List[Dict]:
        """
        Automatically discover shortcut opportunities
        from command history.
        """
        
        if len(self.command_sequences) < self.min_occurrences:
            return []
        
        # Find sequences that repeat
        new_shortcuts = []
        
        # Time-based patterns (morning routine, etc.)
        time_patterns = self._find_time_patterns()
        
        # Sequence patterns (always do A then B then C)
        sequence_patterns = self._find_sequence_patterns()
        
        all_patterns = time_patterns + sequence_patterns
        
        # Generate shortcut names using AI
        for pattern in all_patterns:
            shortcut_id = self._generate_id(pattern)
            
            # Skip already discovered shortcuts
            if shortcut_id in self.active_shortcuts:
                continue
            
            # Generate creative shortcut name
            name = await self._generate_shortcut_name(pattern)
            
            shortcut = {
                "id": shortcut_id,
                "name": name,
                "pattern": pattern,
                "commands": pattern.get("commands", []),
                "trigger_type": pattern.get("type", "manual"),
                "trigger_condition": pattern.get("condition", ""),
                "usage_count": pattern.get("count", 0),
                "discovered_at": datetime.now().isoformat(),
                "enabled": False,  # User must approve
                "last_used": None
            }
            
            new_shortcuts.append(shortcut)
            self.discovered_shortcuts.append(shortcut)
        
        return new_shortcuts
    
    def _find_time_patterns(self) -> List[Dict]:
        """Find commands that happen at specific times"""
        
        # Group by hour
        hour_groups: Dict[int, List[Dict]] = {}
        
        for cmd in self.command_sequences:
            hour = cmd["hour"]
            if hour not in hour_groups:
                hour_groups[hour] = []
            hour_groups[hour].append(cmd)
        
        patterns = []
        
        for hour, commands in hour_groups.items():
            if len(commands) >= self.min_occurrences:
                # Find most common commands at this hour
                tool_counts: Dict[str, int] = {}
                for cmd in commands:
                    for tool in cmd.get("tools", []):
                        tool_counts[tool] = tool_counts.get(tool, 0) + 1
                
                # Tools used at least min_occurrences times
                common_tools = [
                    t for t, c in tool_counts.items()
                    if c >= self.min_occurrences
                ]
                
                if len(common_tools) >= 2:
                    time_label = self._hour_to_label(hour)
                    
                    patterns.append({
                        "type": "time_based",
                        "hour": hour,
                        "time_label": time_label,
                        "tools": common_tools,
                        "commands": [c["command"] for c in commands[:3]],
                        "count": len(commands),
                        "condition": f"hour == {hour}"
                    })
        
        return patterns
    
    def _find_sequence_patterns(self) -> List[Dict]:
        """Find repeated command sequences"""
        
        # Look for 2-5 command sequences that repeat
        patterns = {}
        
        commands = [c["command"] for c in self.command_sequences]
        
        for length in range(2, 6):
            for i in range(len(commands) - length + 1):
                sequence = tuple(commands[i:i + length])
                
                # Generate hash for sequence
                seq_hash = hashlib.md5(
                    ' | '.join(sequence).encode()
                ).hexdigest()[:8]
                
                if seq_hash not in patterns:
                    patterns[seq_hash] = {
                        "sequence": sequence,
                        "count": 0,
                        "last_seen": None
                    }
                
                patterns[seq_hash]["count"] += 1
                patterns[seq_hash]["last_seen"] = self.command_sequences[i + length - 1]["timestamp"]
        
        # Filter patterns with enough occurrences
        repeated = []
        for seq_id, data in patterns.items():
            if data["count"] >= self.min_occurrences:
                repeated.append({
                    "type": "sequence",
                    "commands": list(data["sequence"]),
                    "count": data["count"],
                    "last_seen": data["last_seen"],
                    "condition": "manual"
                })
        
        # Sort by frequency
        repeated.sort(key=lambda x: x["count"], reverse=True)
        
        return repeated[:5]  # Top 5 patterns
    
    def _hour_to_label(self, hour: int) -> str:
        """Convert hour to readable label"""
        
        if 5 <= hour < 9:
            return "Morning Startup"
        elif 9 <= hour < 12:
            return "Morning Work"
        elif 12 <= hour < 14:
            return "Lunch Break"
        elif 14 <= hour < 17:
            return "Afternoon Work"
        elif 17 <= hour < 20:
            return "Evening"
        elif 20 <= hour < 24:
            return "Night Work"
        else:
            return "Late Night"
    
    def _generate_id(self, pattern: Dict) -> str:
        """Generate unique ID for pattern"""
        
        content = json.dumps(pattern.get("commands", []), sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def _generate_shortcut_name(self, pattern: Dict) -> str:
        """Use AI to generate a creative, descriptive shortcut name"""
        
        commands = pattern.get("commands", [])
        time_label = pattern.get("time_label", "")
        pattern_type = pattern.get("type", "")
        
        prompt = f"""
        Generate a short, catchy shortcut name for this workflow pattern.
        
        Pattern type: {pattern_type}
        Time context: {time_label}
        Commands in pattern: {commands[:5]}
        
        Requirements:
        - 2-4 words maximum
        - Descriptive of what it does
        - Catchy and memorable
        - Can use Hinglish if appropriate
        
        Examples of good names:
        - "Dev Morning Boost"
        - "YouTube Music Mode"
        - "Project Launchpad"
        - "Quick Research Mode"
        - "Night Coding Setup"
        
        Return ONLY the name, nothing else.
        """
        
        try:
            response = await self.ai.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9
            )
            
            return response["content"].strip().strip('"')
        except:
            return f"{time_label or 'Custom'} Shortcut"
    
    def approve_shortcut(self, shortcut_id: str) -> Dict:
        """User approves a discovered shortcut"""
        
        shortcut = next(
            (s for s in self.discovered_shortcuts if s["id"] == shortcut_id),
            None
        )
        
        if not shortcut:
            return {"success": False, "error": "Shortcut not found"}
        
        shortcut["enabled"] = True
        self.active_shortcuts[shortcut_id] = shortcut
        self._save_shortcuts()
        
        return {
            "success": True,
            "shortcut": shortcut,
            "message": f"Shortcut '{shortcut['name']}' activated!"
        }
    
    def reject_shortcut(self, shortcut_id: str) -> Dict:
        """User rejects a discovered shortcut"""
        
        self.discovered_shortcuts = [
            s for s in self.discovered_shortcuts
            if s["id"] != shortcut_id
        ]
        
        return {"success": True, "message": "Shortcut rejected"}
    
    async def execute_shortcut(
        self,
        shortcut_id: str,
        tool_executor
    ) -> Dict:
        """Execute a neural shortcut"""
        
        shortcut = self.active_shortcuts.get(shortcut_id)
        
        if not shortcut:
            return {"success": False, "error": "Shortcut not found or disabled"}
        
        commands = shortcut.get("commands", [])
        results = []
        
        for command in commands:
            # Re-execute each command in the shortcut
            result = await tool_executor.execute_from_text(command)
            results.append({
                "command": command,
                "result": result
            })
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": f"Step failed: {command}",
                    "results_so_far": results
                }
        
        # Update usage
        shortcut["last_used"] = datetime.now().isoformat()
        shortcut["usage_count"] = shortcut.get("usage_count", 0) + 1
        self._save_shortcuts()
        
        return {
            "success": True,
            "shortcut_name": shortcut["name"],
            "steps_executed": len(results),
            "results": results
        }
    
    def get_shortcuts_summary(self) -> Dict:
        """Get summary of all shortcuts"""
        
        return {
            "active_shortcuts": list(self.active_shortcuts.values()),
            "pending_approval": [
                s for s in self.discovered_shortcuts
                if not s.get("enabled")
            ],
            "total_commands_analyzed": len(self.command_sequences),
            "shortcuts_count": len(self.active_shortcuts)
        }
    
    def delete_shortcut(self, shortcut_id: str) -> Dict:
        """Delete an active shortcut"""
        
        if shortcut_id in self.active_shortcuts:
            name = self.active_shortcuts[shortcut_id]["name"]
            del self.active_shortcuts[shortcut_id]
            self._save_shortcuts()
            return {"success": True, "message": f"'{name}' deleted"}
        
        return {"success": False, "error": "Shortcut not found"}
