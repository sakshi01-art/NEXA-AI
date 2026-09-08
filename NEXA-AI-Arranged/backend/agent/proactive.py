from typing import List, Dict, Optional, Callable
import asyncio
from datetime import datetime, timedelta
import psutil
try:
    from ..tools.system.monitor import SystemMonitorTools
except (ImportError, ValueError):
    from tools.system.monitor import SystemMonitorTools

class ProactiveAssistant:
    """AI that proactively helps user without being asked"""
    
    def __init__(self, memory_store, notification_callback: Callable):
        self.memory = memory_store
        self.notify = notification_callback
        self.monitors_active = False
        self.insights: List[Dict] = []
    
    async def start_monitoring(self):
        """Start background monitoring for proactive assistance"""
        self.monitors_active = True
        
        # Start multiple monitoring coroutines
        await asyncio.gather(
            self._monitor_system_health(),
            self._monitor_work_patterns(),
            self._monitor_battery(),
            self._suggest_breaks(),
            self._detect_repeated_tasks()
        )
    
    async def _monitor_system_health(self):
        """Monitor system resources and suggest optimizations"""
        while self.monitors_active:
            stats = SystemMonitorTools.get_system_stats()
            
            if stats['success']:
                cpu = stats['cpu']['percent']
                memory = stats['memory']['percent']
                disk = stats['disk']['percent']
                
                # High CPU usage
                if cpu > 90:
                    await self.notify({
                        'type': 'warning',
                        'title': 'High CPU Usage',
                        'message': f'CPU {cpu}% use ho raha hai. Kya main resource-heavy processes check karun?',
                        'action': 'show_processes',
                        'priority': 'high'
                    })
                
                # High memory usage
                if memory > 85:
                    await self.notify({
                        'type': 'warning',
                        'title': 'Memory Almost Full',
                        'message': f'RAM {memory}% full hai. Kya main unused applications close kar dun?',
                        'action': 'optimize_memory',
                        'priority': 'medium'
                    })
                
                # Low disk space
                if disk > 90:
                    await self.notify({
                        'type': 'error',
                        'title': 'Low Disk Space',
                        'message': f'Disk {disk}% full hai. Kya main temporary files clean karun?',
                        'action': 'clean_disk',
                        'priority': 'high'
                    })
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    async def _monitor_battery(self):
        """Monitor battery and suggest power-saving actions"""
        while self.monitors_active:
            stats = SystemMonitorTools.get_system_stats()
            
            if stats['success'] and stats['battery']:
                battery = stats['battery']
                percent = battery['percent']
                plugged = battery['plugged_in']
                
                # Low battery warning
                if not plugged and percent <= 20 and percent > 15:
                    await self.notify({
                        'type': 'warning',
                        'title': 'Battery Low',
                        'message': f'Battery {percent}% hai. Charger laga lo ya main power-saving mode enable kar dun?',
                        'action': 'enable_power_saving',
                        'priority': 'medium'
                    })
                
                # Critical battery
                if not plugged and percent <= 15:
                    await self.notify({
                        'type': 'error',
                        'title': 'Battery Critical',
                        'message': f'Battery sirf {percent}% hai! Kya main work save karke system sleep mode mein dal dun?',
                        'action': 'emergency_save',
                        'priority': 'critical'
                    })
                
                # Battery full
                if plugged and percent >= 95:
                    await self.notify({
                        'type': 'info',
                        'title': 'Battery Charged',
                        'message': 'Battery full ho gayi hai. Charger nikal lo for better battery health.',
                        'priority': 'low'
                    })
            
            await asyncio.sleep(180)  # Check every 3 minutes
    
    async def _monitor_work_patterns(self):
        """Learn work patterns and suggest optimizations"""
        while self.monitors_active:
            # Check if user is working on same type of task repeatedly
            recent_tasks = await self.memory.recall_similar_conversations(
                query="open application",
                limit=10
            )
            
            # Detect repeated application launches
            app_counts = {}
            for task in recent_tasks:
                # Extract app name from conversation
                if 'chrome' in task['content'].lower():
                    app_counts['chrome'] = app_counts.get('chrome', 0) + 1
                elif 'vscode' in task['content'].lower():
                    app_counts['vscode'] = app_counts.get('vscode', 0) + 1
            
            # Suggest automation if pattern detected
            for app, count in app_counts.items():
                if count >= 5:
                    workflow = await self.memory.suggest_workflow(f"open {app}")
                    
                    if not workflow:
                        await self.notify({
                            'type': 'suggestion',
                            'title': 'Automation Suggestion',
                            'message': f'Tum {app} bahut baar open kar rahe ho. Kya main iske liye automation create kar dun?',
                            'action': 'create_automation',
                            'data': {'app': app},
                            'priority': 'low'
                        })
            
            await asyncio.sleep(1800)  # Check every 30 minutes
    
    async def _suggest_breaks(self):
        """Suggest breaks based on work duration"""
        work_start = datetime.now()
        
        while self.monitors_active:
            work_duration = (datetime.now() - work_start).total_seconds() / 60
            
            # Suggest break after 50 minutes (Pomodoro-style)
            if work_duration >= 50 and work_duration < 52:
                await self.notify({
                    'type': 'suggestion',
                    'title': 'Break Time',
                    'message': 'Tum 50 minutes se kaam kar rahe ho. 5-10 minute ka break le lo? 👀',
                    'action': 'start_break_timer',
                    'priority': 'low'
                })
                
                # Reset timer if user takes break
                await asyncio.sleep(600)  # Wait 10 minutes
                work_start = datetime.now()
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _detect_repeated_tasks(self):
        """Detect and suggest automation for repeated manual tasks"""
        task_sequence = []
        
        while self.monitors_active:
            # This would connect to actual user activity monitoring
            # For now, we'll check conversation history
            
            recent = await self.memory.recall_similar_conversations(
                query="",
                limit=20
            )
            
            # Detect sequences like: open app -> open folder -> open file
            sequences = self._find_task_sequences(recent)
            
            for sequence in sequences:
                if sequence['count'] >= 3:
                    await self.notify({
                        'type': 'suggestion',
                        'title': 'Automation Opportunity',
                        'message': f'Maine notice kiya ki tum ye steps repeat kar rahe ho: {" → ".join(sequence["steps"])}. Automation bana dun?',
                        'action': 'create_workflow',
                        'data': sequence,
                        'priority': 'medium'
                    })
            
            await asyncio.sleep(3600)  # Check every hour
    
    def _find_task_sequences(self, conversations: List[Dict]) -> List[Dict]:
        """Find repeated task sequences"""
        # Simplified sequence detection
        sequences = {}
        
        for i in range(len(conversations) - 2):
            sequence = tuple([
                conversations[i]['content'],
                conversations[i+1]['content'],
                conversations[i+2]['content']
            ])
            
            sequences[sequence] = sequences.get(sequence, 0) + 1
        
        repeated = []
        for seq, count in sequences.items():
            if count >= 2:
                repeated.append({
                    'steps': list(seq),
                    'count': count
                })
        
        return repeated
    
    async def stop_monitoring(self):
        """Stop proactive monitoring"""
        self.monitors_active = False
    
    async def get_daily_insights(self) -> Dict:
        """Generate daily productivity insights"""
        
        # Get today's activity
        stats = SystemMonitorTools.get_system_stats()
        conversations = await self.memory.recall_similar_conversations("", limit=50)
        
        insights = {
            'date': datetime.now().date().isoformat(),
            'total_interactions': len(conversations),
            'most_used_apps': self._get_most_used_apps(conversations),
            'productivity_score': self._calculate_productivity_score(conversations),
            'system_health': {
                'cpu_avg': stats.get('cpu', {}).get('percent', 0),
                'memory_avg': stats.get('memory', {}).get('percent', 0)
            },
            'suggestions': []
        }
        
        # Add personalized suggestions
        if insights['productivity_score'] < 50:
            insights['suggestions'].append(
                "Aaj productivity kam lagi. Kya distractions zyada the? Time-blocking try karo."
            )
        
        if insights['total_interactions'] > 100:
            insights['suggestions'].append(
                "Bahut saare tasks the aaj! Kal ke liye priorities list bana dun?"
            )
        
        return insights
    
    def _get_most_used_apps(self, conversations: List[Dict]) -> List[Dict]:
        """Extract most used applications from conversations"""
        apps = {}
        
        for conv in conversations:
            content = conv['content'].lower()
            
            # Simple app detection
            for app in ['chrome', 'vscode', 'notepad', 'explorer', 'cmd']:
                if app in content:
                    apps[app] = apps.get(app, 0) + 1
        
        sorted_apps = sorted(apps.items(), key=lambda x: x[1], reverse=True)
        
        return [{'app': app, 'count': count} for app, count in sorted_apps[:5]]
    
    def _calculate_productivity_score(self, conversations: List[Dict]) -> float:
        """Calculate productivity score based on activity"""
        # Simplified scoring
        if not conversations:
            return 0.0
        
        productive_keywords = ['open', 'create', 'write', 'code', 'build', 'deploy']
        distracting_keywords = ['youtube', 'facebook', 'instagram', 'twitter']
        
        productive_count = 0
        distracting_count = 0
        
        for conv in conversations:
            content = conv['content'].lower()
            
            if any(keyword in content for keyword in productive_keywords):
                productive_count += 1
            
            if any(keyword in content for keyword in distracting_keywords):
                distracting_count += 1
        
        if productive_count + distracting_count == 0:
            return 50.0
        
        score = (productive_count / (productive_count + distracting_count)) * 100
        return round(score, 1)
