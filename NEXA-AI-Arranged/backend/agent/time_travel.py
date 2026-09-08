import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import copy

class TimeTravelDebugger:
    """
    Record every single action NEXA takes.
    Then replay any session from any point in time.
    
    Use cases:
    - "Nexa, 2 ghante pehle wala session replay kar"
    - "Kal wala workflow recreate kar"
    - "Is task ka step 3 se dobara chala"
    - Debug what went wrong
    - Reproduce successful workflows
    """
    
    def __init__(self, storage_path: str = "./data/sessions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.current_session: List[Dict] = []
        self.session_id = self._generate_session_id()
        self.is_recording = True
        self.is_replaying = False
        self.playback_speed = 1.0
        self.current_replay_index = 0
        
        # Start new session file
        self.session_file = self.storage_path / f"{self.session_id}.json"
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{ts}"
    
    def record_event(
        self,
        event_type: str,
        data: Dict,
        tool: Optional[str] = None,
        result: Optional[Dict] = None
    ):
        """Record a single event"""
        
        if not self.is_recording or self.is_replaying:
            return
        
        event = {
            "id": len(self.current_session),
            "type": event_type,
            "tool": tool,
            "data": data,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id
        }
        
        self.current_session.append(event)
        
        # Auto-save every 10 events
        if len(self.current_session) % 10 == 0:
            self._save_session()
    
    def _save_session(self):
        """Save current session to disk"""
        
        session_data = {
            "session_id": self.session_id,
            "started_at": self.current_session[0]["timestamp"] if self.current_session else None,
            "last_updated": datetime.now().isoformat(),
            "event_count": len(self.current_session),
            "events": self.current_session
        }
        
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
    
    def get_all_sessions(self) -> List[Dict]:
        """Get list of all recorded sessions"""
        
        sessions = []
        
        for session_file in sorted(self.storage_path.glob("session_*.json"), reverse=True):
            try:
                with open(session_file) as f:
                    data = json.load(f)
                
                sessions.append({
                    "session_id": data["session_id"],
                    "started_at": data.get("started_at"),
                    "event_count": data.get("event_count", 0),
                    "file": str(session_file)
                })
            except:
                pass
        
        return sessions[:50]  # Return last 50 sessions
    
    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load a specific session"""
        
        session_file = self.storage_path / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        with open(session_file) as f:
            return json.load(f)
    
    async def replay_session(
        self,
        session_id: str,
        tool_executor,
        start_from_event: int = 0,
        speed: float = 1.0,
        dry_run: bool = True,
        on_event: Optional[callable] = None
    ) -> Dict:
        """
        Replay a recorded session.
        
        Args:
            session_id: Session to replay
            tool_executor: Tool execution system
            start_from_event: Start from specific event index
            speed: Playback speed multiplier
            dry_run: If True, simulate without actual execution
            on_event: Callback for each event during replay
        """
        
        session = self.load_session(session_id)
        
        if not session:
            return {"success": False, "error": f"Session {session_id} not found"}
        
        events = session["events"][start_from_event:]
        
        if not events:
            return {"success": False, "error": "No events to replay"}
        
        self.is_replaying = True
        replay_results = []
        
        try:
            prev_timestamp = None
            
            for i, event in enumerate(events):
                if not self.is_replaying:
                    break
                
                # Calculate delay to maintain timing
                if prev_timestamp and speed > 0:
                    current_ts = datetime.fromisoformat(event["timestamp"])
                    prev_ts = datetime.fromisoformat(prev_timestamp)
                    
                    delay = (current_ts - prev_ts).total_seconds() / speed
                    delay = min(delay, 5.0)  # Cap at 5 seconds
                    
                    if delay > 0:
                        await asyncio.sleep(delay)
                
                # Notify listener
                if on_event:
                    await on_event({
                        "index": i,
                        "total": len(events),
                        "event": event,
                        "progress": (i / len(events)) * 100
                    })
                
                # Execute or simulate
                if not dry_run and event.get("tool"):
                    result = await tool_executor.execute_tool(
                        name=event["tool"],
                        parameters=event["data"]
                    )
                    
                    replay_results.append({
                        "event": event,
                        "original_result": event.get("result"),
                        "replay_result": result,
                        "matches": result.get("success") == event.get("result", {}).get("success")
                    })
                else:
                    # Dry run - just record what would happen
                    replay_results.append({
                        "event": event,
                        "simulated": True,
                        "would_execute": event.get("tool"),
                        "with_params": event.get("data")
                    })
                
                prev_timestamp = event["timestamp"]
        
        finally:
            self.is_replaying = False
        
        return {
            "success": True,
            "session_id": session_id,
            "events_replayed": len(replay_results),
            "dry_run": dry_run,
            "results": replay_results,
            "completed": not self.is_replaying or len(replay_results) == len(events)
        }
    
    def stop_replay(self):
        """Stop current replay"""
        self.is_replaying = False
    
    async def find_similar_sessions(
        self,
        description: str,
        ai_provider
    ) -> List[Dict]:
        """
        Find sessions that match a description.
        
        Example: "wo session dhundo jab maine React project banaya tha"
        """
        
        sessions = self.get_all_sessions()
        
        if not sessions:
            return []
        
        # Sample events from each session
        session_summaries = []
        
        for session in sessions[:20]:
            full_session = self.load_session(session["session_id"])
            
            if not full_session:
                continue
            
            # Get first 10 events as summary
            sample_events = full_session["events"][:10]
            commands = [e.get("data", {}).get("command", "") for e in sample_events if e.get("data")]
            
            session_summaries.append({
                "session_id": session["session_id"],
                "started_at": session["started_at"],
                "commands_sample": commands[:5]
            })
        
        prompt = f"""
        Find sessions matching this description: "{description}"
        
        Available sessions:
        {json.dumps(session_summaries, indent=2, default=str)}
        
        Return the IDs of matching sessions (most relevant first):
        JSON: {{"matching_sessions": ["id1", "id2"]}}
        """
        
        try:
            response = await ai_provider.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response["content"])
            matching_ids = result.get("matching_sessions", [])
            
            return [
                session for session in sessions
                if session["session_id"] in matching_ids
            ]
        
        except:
            return sessions[:3]  # Return latest if AI fails
    
    def create_session_snapshot(self, name: str) -> Dict:
        """Create a named snapshot of current session"""
        
        snapshot = {
            "name": name,
            "session_id": self.session_id,
            "snapshot_at_event": len(self.current_session),
            "created_at": datetime.now().isoformat(),
            "events_up_to": self.current_session.copy()
        }
        
        snapshot_file = self.storage_path / f"snapshot_{name.replace(' ', '_')}.json"
        
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2, default=str)
        
        return {
            "success": True,
            "name": name,
            "events_saved": len(self.current_session)
        }
    
    def get_session_analytics(self, session_id: str) -> Dict:
        """Get analytics for a specific session"""
        
        session = self.load_session(session_id)
        
        if not session:
            return {"success": False, "error": "Session not found"}
        
        events = session["events"]
        
        # Tool usage stats
        tool_usage: Dict[str, int] = {}
        success_count = 0
        failure_count = 0
        
        for event in events:
            tool = event.get("tool")
            if tool:
                tool_usage[tool] = tool_usage.get(tool, 0) + 1
            
            result = event.get("result", {})
            if result.get("success"):
                success_count += 1
            elif result:
                failure_count += 1
        
        # Calculate duration
        if len(events) >= 2:
            start = datetime.fromisoformat(events[0]["timestamp"])
            end = datetime.fromisoformat(events[-1]["timestamp"])
            duration_minutes = (end - start).seconds / 60
        else:
            duration_minutes = 0
        
        return {
            "success": True,
            "session_id": session_id,
            "total_events": len(events),
            "duration_minutes": round(duration_minutes, 1),
            "tool_usage": tool_usage,
            "success_rate": success_count / max(success_count + failure_count, 1),
            "most_used_tool": max(tool_usage.items(), key=lambda x: x[1])[0] if tool_usage else None,
            "started_at": session.get("started_at")
        }
