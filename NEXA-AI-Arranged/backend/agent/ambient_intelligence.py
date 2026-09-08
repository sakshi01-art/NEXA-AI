import asyncio
import json
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import psutil

class AmbientIntelligence:
    """
    NEXA watches everything silently in the background.
    No commands needed.
    
    It monitors:
    - Active window title → understands what you're working on
    - File system changes → knows when files are created/modified
    - Network activity → detects downloads, uploads
    - App crashes → automatically helps
    - Meeting detection → goes quiet during calls
    - System anomalies → alerts you
    - Long-running processes → tracks and informs
    
    All without being asked.
    """
    
    def __init__(
        self,
        ai_provider,
        notification_callback: Callable,
        tool_executor
    ):
        self.ai = ai_provider
        self.notify = notification_callback
        self.tools = tool_executor
        
        self.monitors: Dict[str, bool] = {
            "window_monitor": True,
            "filesystem_monitor": True,
            "network_monitor": True,
            "crash_monitor": True,
            "meeting_monitor": True,
            "performance_monitor": True,
            "long_process_monitor": True
        }
        
        self.current_context = {
            "active_window": None,
            "current_project": None,
            "in_meeting": False,
            "active_downloads": [],
            "recent_crashes": [],
            "long_processes": []
        }
        
        self.ambient_tasks: List[asyncio.Task] = []
        self.is_running = False
        self.silence_mode = False  # True during meetings
    
    async def start(self):
        """Start all ambient monitors"""
        
        self.is_running = True
        
        monitors = []
        
        if self.monitors["window_monitor"]:
            monitors.append(self._monitor_active_window())
        
        if self.monitors["filesystem_monitor"]:
            monitors.append(self._monitor_filesystem())
        
        if self.monitors["network_monitor"]:
            monitors.append(self._monitor_network())
        
        if self.monitors["crash_monitor"]:
            monitors.append(self._monitor_crashes())
        
        if self.monitors["performance_monitor"]:
            monitors.append(self._monitor_performance())
        
        if self.monitors["long_process_monitor"]:
            monitors.append(self._monitor_long_processes())
        
        # Run all monitors concurrently
        self.ambient_tasks = [
            asyncio.create_task(monitor)
            for monitor in monitors
        ]
    
    async def stop(self):
        """Stop all ambient monitors"""
        
        self.is_running = False
        
        for task in self.ambient_tasks:
            task.cancel()
        
        self.ambient_tasks = []
    
    async def _monitor_active_window(self):
        """Monitor active window title to understand user context"""
        
        import ctypes
        import win32gui
        import win32process
        
        last_window = None
        window_start = datetime.now()
        
        while self.is_running:
            try:
                # Get active window
                hwnd = win32gui.GetForegroundWindow()
                title = win32gui.GetWindowText(hwnd)
                
                if title and title != last_window:
                    # Window changed
                    duration_in_prev = (datetime.now() - window_start).seconds
                    window_start = datetime.now()
                    
                    # Analyze new context
                    context = await self._analyze_window_context(title)
                    
                    self.current_context["active_window"] = {
                        "title": title,
                        "context": context,
                        "started_at": datetime.now().isoformat()
                    }
                    
                    # Detect meeting apps
                    meeting_apps = ["zoom", "teams", "meet", "webex", "discord"]
                    is_meeting = any(app in title.lower() for app in meeting_apps)
                    
                    if is_meeting and not self.current_context["in_meeting"]:
                        self.current_context["in_meeting"] = True
                        self.silence_mode = True
                        
                        # Go into meeting mode silently
                    
                    elif not is_meeting and self.current_context["in_meeting"]:
                        self.current_context["in_meeting"] = False
                        self.silence_mode = False
                        
                        # Coming out of meeting
                        if not self.silence_mode:
                            await self.notify({
                                "type": "info",
                                "title": "Meeting ended",
                                "message": "Welcome back! Meeting ke dauran kuch miss hua? Summary chahiye?",
                                "priority": "low"
                            })
                    
                    # Project detection
                    project = self._detect_project_context(title)
                    if project:
                        self.current_context["current_project"] = project
                    
                    last_window = title
                
                await asyncio.sleep(2)
            
            except Exception:
                await asyncio.sleep(5)
    
    async def _analyze_window_context(self, window_title: str) -> Dict:
        """Use AI to understand what user is doing from window title"""
        
        # Simple rule-based first (fast)
        context = {
            "activity": "unknown",
            "app": "unknown",
            "file": None,
            "project": None
        }
        
        title_lower = window_title.lower()
        
        # App detection
        if "chrome" in title_lower or "firefox" in title_lower:
            context["app"] = "browser"
            context["activity"] = "browsing"
        
        elif "visual studio code" in title_lower or "vscode" in title_lower:
            context["app"] = "vscode"
            context["activity"] = "coding"
            
            # Extract filename
            import re
            file_match = re.search(r'(.+?) - Visual Studio Code', window_title)
            if file_match:
                context["file"] = file_match.group(1)
        
        elif "notepad" in title_lower:
            context["app"] = "notepad"
            context["activity"] = "editing"
        
        elif "zoom" in title_lower or "teams" in title_lower:
            context["app"] = "meeting"
            context["activity"] = "in_meeting"
        
        elif "terminal" in title_lower or "cmd" in title_lower:
            context["app"] = "terminal"
            context["activity"] = "running_commands"
        
        return context
    
    def _detect_project_context(self, window_title: str) -> Optional[str]:
        """Detect which project user is working on"""
        
        # Look for project indicators
        import re
        
        # VS Code project
        vscode_match = re.search(r'(.+?) - Visual Studio Code', window_title)
        if vscode_match:
            return vscode_match.group(1)
        
        # File path in title
        path_match = re.search(r'([A-Z]:\\[^-]+)', window_title)
        if path_match:
            from pathlib import Path
            return Path(path_match.group(1)).name
        
        return None
    
    async def _monitor_filesystem(self):
        """Monitor file system for important changes"""
        
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class NexaFSHandler(FileSystemEventHandler):
                def __init__(self, notify_callback, ai_provider):
                    self.notify = notify_callback
                    self.ai = ai_provider
                    self.recent_events = []
                
                def on_created(self, event):
                    if not event.is_directory:
                        file_path = event.src_path
                        file_size = 0
                        
                        try:
                            import os
                            file_size = os.path.getsize(file_path)
                        except:
                            pass
                        
                        # Large file created (likely download)
                        if file_size > 10 * 1024 * 1024:  # > 10MB
                            asyncio.create_task(self.notify({
                                "type": "info",
                                "title": "Large file detected",
                                "message": f"New file: {Path(file_path).name} ({file_size // 1024 // 1024}MB)",
                                "priority": "low"
                            }))
                
                def on_deleted(self, event):
                    # Notify about deleted important files
                    import re
                    important_patterns = [r'\.py$', r'\.js$', r'\.ts$', r'\.json$']
                    
                    for pattern in important_patterns:
                        if re.search(pattern, event.src_path):
                            # Could be accidental - notify
                            asyncio.create_task(self.notify({
                                "type": "warning",
                                "title": "File Deleted",
                                "message": f"{Path(event.src_path).name} delete ho gaya",
                                "actions": [{"label": "Undo", "action": "restore_file"}],
                                "priority": "medium"
                            }))
                            break
            
            # Watch common directories
            watch_dirs = [
                Path.home() / "Desktop",
                Path.home() / "Downloads",
                Path.home() / "Documents"
            ]
            
            observer = Observer()
            handler = NexaFSHandler(self.notify, self.ai)
            
            for watch_dir in watch_dirs:
                if watch_dir.exists():
                    observer.schedule(handler, str(watch_dir), recursive=False)
            
            observer.start()
            
            while self.is_running:
                await asyncio.sleep(10)
            
            observer.stop()
            observer.join()
        
        except ImportError:
            # watchdog not installed - use polling
            await asyncio.sleep(float('inf'))
    
    async def _monitor_network(self):
        """Monitor network for unusual activity"""
        
        prev_stats = psutil.net_io_counters()
        alerts_sent = set()
        
        while self.is_running:
            await asyncio.sleep(5)
            
            try:
                current_stats = psutil.net_io_counters()
                
                # Calculate speed (bytes per second)
                sent_speed = (
                    current_stats.bytes_sent - prev_stats.bytes_sent
                ) / 5  # 5 second interval
                
                recv_speed = (
                    current_stats.bytes_recv - prev_stats.bytes_recv
                ) / 5
                
                # High upload alert (possible data exfil or large upload)
                if sent_speed > 50 * 1024 * 1024 and "high_upload" not in alerts_sent:  # > 50 MB/s
                    await self.notify({
                        "type": "warning",
                        "title": "High Upload Speed",
                        "message": f"Upload speed bahut zyada hai: {sent_speed // 1024 // 1024:.1f} MB/s",
                        "priority": "medium"
                    })
                    alerts_sent.add("high_upload")
                
                elif sent_speed < 10 * 1024 * 1024:
                    alerts_sent.discard("high_upload")
                
                # No internet
                if recv_speed == 0 and sent_speed == 0:
                    if "no_internet" not in alerts_sent:
                        await self.notify({
                            "type": "error",
                            "title": "No Internet",
                            "message": "Internet connection lost ho gayi!",
                            "priority": "high"
                        })
                        alerts_sent.add("no_internet")
                else:
                    if "no_internet" in alerts_sent:
                        await self.notify({
                            "type": "success",
                            "title": "Internet Restored",
                            "message": "Internet wapas aa gaya!",
                            "priority": "medium"
                        })
                        alerts_sent.discard("no_internet")
                
                prev_stats = current_stats
            
            except Exception:
                pass
    
    async def _monitor_crashes(self):
        """Detect application crashes"""
        
        prev_processes = {p.pid: p.name() for p in psutil.process_iter(['pid', 'name'])}
        
        while self.is_running:
            await asyncio.sleep(5)
            
            try:
                current_processes = {p.pid: p.name() for p in psutil.process_iter(['pid', 'name'])}
                
                # Find disappeared processes (potential crashes)
                disappeared = {
                    pid: name
                    for pid, name in prev_processes.items()
                    if pid not in current_processes
                    and name not in ['System', 'svchost.exe', 'conhost.exe']
                    and not name.startswith('python')  # Exclude Python workers
                }
                
                for pid, name in disappeared.items():
                    # Check if it was a user-facing app
                    user_apps = ['chrome', 'code', 'notepad', 'word', 'excel', 'firefox']
                    
                    if any(app in name.lower() for app in user_apps):
                        await self.notify({
                            "type": "warning",
                            "title": f"{name} closed unexpectedly",
                            "message": f"Kya {name} crash ho gaya? Main restart karun?",
                            "actions": [
                                {"label": f"Restart {name}", "action": f"restart_{name}"},
                                {"label": "No thanks", "action": "dismiss"}
                            ],
                            "priority": "medium"
                        })
                
                prev_processes = current_processes
            
            except Exception:
                pass
    
    async def _monitor_performance(self):
        """Monitor system performance continuously"""
        
        sustained_high_cpu_start = None
        
        while self.is_running:
            await asyncio.sleep(30)
            
            try:
                cpu = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Sustained high CPU (> 80% for 5+ minutes)
                if cpu > 80:
                    if sustained_high_cpu_start is None:
                        sustained_high_cpu_start = datetime.now()
                    elif (datetime.now() - sustained_high_cpu_start).seconds > 300:
                        await self.notify({
                            "type": "warning",
                            "title": "CPU Overloaded",
                            "message": f"CPU {cpu}% load hai 5 minutes se. Process check karein?",
                            "actions": [
                                {"label": "Show processes", "action": "show_processes"},
                                {"label": "Ignore", "action": "dismiss"}
                            ],
                            "priority": "high"
                        })
                        sustained_high_cpu_start = None  # Reset
                else:
                    sustained_high_cpu_start = None
            
            except Exception:
                pass
    
    async def _monitor_long_processes(self):
        """Track long-running processes"""
        
        tracked_processes: Dict[int, Dict] = {}
        LONG_THRESHOLD = 300  # 5 minutes
        
        while self.is_running:
            await asyncio.sleep(60)
            
            try:
                for proc in psutil.process_iter(['pid', 'name', 'create_time', 'cpu_percent']):
                    try:
                        pid = proc.info['pid']
                        name = proc.info['name']
                        create_time = datetime.fromtimestamp(proc.info['create_time'])
                        duration = (datetime.now() - create_time).seconds
                        
                        # Track high-CPU long processes
                        if proc.info['cpu_percent'] > 30 and duration > LONG_THRESHOLD:
                            if pid not in tracked_processes:
                                tracked_processes[pid] = {
                                    "name": name,
                                    "duration": duration,
                                    "notified": False
                                }
                            
                            if not tracked_processes[pid]["notified"]:
                                await self.notify({
                                    "type": "info",
                                    "title": "Long-running Process",
                                    "message": f"{name} {duration // 60} minutes se chal raha hai aur CPU use kar raha hai.",
                                    "priority": "low"
                                })
                                tracked_processes[pid]["notified"] = True
                    
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Clean up finished processes
                tracked_processes = {
                    pid: data
                    for pid, data in tracked_processes.items()
                    if any(p.pid == pid for p in psutil.process_iter(['pid']))
                }
            
            except Exception:
                pass
    
    def get_current_context(self) -> Dict:
        """Get current ambient context"""
        return {
            **self.current_context,
            "monitors_active": self.monitors,
            "silence_mode": self.silence_mode
        }
    
    def enable_monitor(self, monitor_name: str):
        """Enable a specific monitor"""
        if monitor_name in self.monitors:
            self.monitors[monitor_name] = True
    
    def disable_monitor(self, monitor_name: str):
        """Disable a specific monitor"""
        if monitor_name in self.monitors:
            self.monitors[monitor_name] = False
