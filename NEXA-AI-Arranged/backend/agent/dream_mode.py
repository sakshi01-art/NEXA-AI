import asyncio
import json
import os
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path

class DreamModeEngine:
    """
    NEXA Dream Mode - Works while you sleep.
    
    Schedule tasks to run overnight:
    - Download large files
    - Process videos/images
    - Backup important data
    - Analyze and organize files
    - Train custom AI models
    - Generate reports
    - Send scheduled emails
    - System maintenance
    - Update software
    - Process data pipelines
    
    "Nexa, raat ko mere downloads complete kar dena"
    "Kal subah tak mera project build kar ke ready rakh"
    "Raat 2 baje system ka full backup le lena"
    """
    
    def __init__(
        self,
        tool_executor,
        ai_provider,
        notification_callback: Callable
    ):
        self.tools = tool_executor
        self.ai = ai_provider
        self.notify = notification_callback
        
        self.dream_queue: List[Dict] = []
        self.completed_tasks: List[Dict] = []
        self.failed_tasks: List[Dict] = []
        self.is_dreaming = False
        self.dream_start_time: Optional[datetime] = None
        self.dream_end_time: Optional[datetime] = None
        
        self.config = {
            'auto_start_hour': 23,      # 11 PM
            'auto_end_hour': 6,         # 6 AM
            'max_cpu_usage': 50,        # Max CPU during dream
            'pause_on_user_activity': True,
            'send_morning_report': True,
            'power_saving_mode': False
        }
        
        self._load_queue()
    
    def _load_queue(self):
        """Load dream queue from disk"""
        queue_file = Path("./data/dream_queue.json")
        if queue_file.exists():
            with open(queue_file) as f:
                data = json.load(f)
                self.dream_queue = data.get('queue', [])
    
    def _save_queue(self):
        """Save dream queue to disk"""
        queue_file = Path("./data/dream_queue.json")
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        with open(queue_file, 'w') as f:
            json.dump({'queue': self.dream_queue}, f, indent=2, default=str)
    
    async def add_dream_task(
        self,
        task_description: str,
        scheduled_time: Optional[datetime] = None,
        priority: str = 'normal',
        estimated_duration: Optional[int] = None
    ) -> Dict:
        """Add a task to dream queue"""
        
        # Use AI to plan the task
        plan = await self._plan_dream_task(task_description)
        
        task = {
            'id': f"dream_{datetime.now().timestamp()}",
            'description': task_description,
            'plan': plan,
            'scheduled_time': scheduled_time.isoformat() if scheduled_time else None,
            'priority': priority,
            'estimated_duration': estimated_duration,
            'status': 'queued',
            'added_at': datetime.now().isoformat(),
            'result': None
        }
        
        self.dream_queue.append(task)
        
        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'normal': 2, 'low': 3}
        self.dream_queue.sort(key=lambda x: priority_order.get(x['priority'], 2))
        
        self._save_queue()
        
        return {
            'success': True,
            'task_id': task['id'],
            'description': task_description,
            'scheduled': scheduled_time.isoformat() if scheduled_time else 'Tonight',
            'plan_steps': len(plan.get('steps', [])),
            'message': f"Task added to dream queue! Will execute {scheduled_time or 'tonight'}."
        }
    
    async def _plan_dream_task(self, description: str) -> Dict:
        """Use AI to create execution plan for dream task"""
        
        prompt = f"""
        Create a detailed execution plan for this overnight task:
        "{description}"
        
        The task will run unattended while user sleeps.
        Make it safe, resumable, and with error recovery.
        
        JSON:
        {{
            "steps": [
                {{
                    "id": 1,
                    "description": "step description",
                    "tool": "tool_name",
                    "params": {{}},
                    "timeout": 300,
                    "retry_count": 3,
                    "on_failure": "skip/abort/retry",
                    "reversible": true
                }}
            ],
            "estimated_duration_minutes": 0,
            "resource_intensity": "low/medium/high",
            "can_pause": true,
            "cleanup_on_failure": []
        }}
        """
        
        try:
            response = await self.ai.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return json.loads(response['content'])
        except:
            return {
                'steps': [{'description': description, 'tool': 'ai_execute', 'params': {'command': description}}],
                'estimated_duration_minutes': 30,
                'resource_intensity': 'medium',
                'can_pause': True
            }
    
    async def start_dreaming(self) -> Dict:
        """Start executing dream queue"""
        
        if self.is_dreaming:
            return {'success': False, 'error': 'Already in dream mode'}
        
        if not self.dream_queue:
            return {'success': False, 'error': 'No tasks in dream queue'}
        
        self.is_dreaming = True
        self.dream_start_time = datetime.now()
        
        asyncio.create_task(self._dream_loop())
        
        await self.notify({
            'type': 'info',
            'title': '😴 Dream Mode Started',
            'message': f'{len(self.dream_queue)} tasks will run overnight. Good night!',
            'priority': 'low'
        })
        
        return {
            'success': True,
            'tasks_queued': len(self.dream_queue),
            'started_at': self.dream_start_time.isoformat()
        }
    
    async def _dream_loop(self):
        """Main dream execution loop"""
        
        while self.is_dreaming and self.dream_queue:
            task = self.dream_queue[0]
            
            try:
                # Check if scheduled time has arrived
                if task.get('scheduled_time'):
                    scheduled = datetime.fromisoformat(task['scheduled_time'])
                    if datetime.now() < scheduled:
                        await asyncio.sleep(60)
                        continue
                
                # Check CPU usage
                import psutil
                if psutil.cpu_percent() > self.config['max_cpu_usage']:
                    await asyncio.sleep(30)
                    continue
                
                # Execute task
                task['status'] = 'running'
                task['started_at'] = datetime.now().isoformat()
                
                result = await self._execute_dream_task(task)
                
                task['status'] = 'completed' if result['success'] else 'failed'
                task['result'] = result
                task['completed_at'] = datetime.now().isoformat()
                
                if result['success']:
                    self.completed_tasks.append(task)
                else:
                    self.failed_tasks.append(task)
                
                self.dream_queue.pop(0)
                self._save_queue()
                
                await asyncio.sleep(5)
            
            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
                self.failed_tasks.append(task)
                self.dream_queue.pop(0)
        
        self.is_dreaming = False
        self.dream_end_time = datetime.now()
        
        # Send morning report
        if self.config['send_morning_report']:
            await self._send_morning_report()
    
    async def _execute_dream_task(self, task: Dict) -> Dict:
        """Execute a single dream task"""
        
        plan = task.get('plan', {})
        steps = plan.get('steps', [])
        
        if not steps:
            # Execute directly
            return await self.tools.execute_from_text(task['description'])
        
        results = []
        
        for step in steps:
            try:
                result = await self.tools.execute_tool(
                    name=step.get('tool', 'ai_execute'),
                    parameters=step.get('params', {})
                )
                
                results.append({'step': step['id'], 'result': result})
                
                if not result.get('success'):
                    on_failure = step.get('on_failure', 'abort')
                    
                    if on_failure == 'abort':
                        return {
                            'success': False,
                            'error': f"Step {step['id']} failed",
                            'completed_steps': len(results) - 1
                        }
                
                await asyncio.sleep(1)
            
            except Exception as e:
                if step.get('on_failure') == 'skip':
                    continue
                return {'success': False, 'error': str(e)}
        
        return {
            'success': True,
            'steps_completed': len(results),
            'results': results
        }
    
    async def _send_morning_report(self):
        """Send morning report of dream mode results"""
        
        total = len(self.completed_tasks) + len(self.failed_tasks)
        success_rate = len(self.completed_tasks) / max(total, 1) * 100
        
        duration = None
        if self.dream_start_time and self.dream_end_time:
            duration = (self.dream_end_time - self.dream_start_time).seconds // 60
        
        report = f"""
        🌅 Good morning! Dream Mode Report:
        
        ✅ Completed: {len(self.completed_tasks)} tasks
        ❌ Failed: {len(self.failed_tasks)} tasks
        📊 Success rate: {success_rate:.0f}%
        ⏱️ Duration: {duration or '?'} minutes
        """
        
        await self.notify({
            'type': 'success' if success_rate > 80 else 'warning',
            'title': '🌅 Good Morning! Dream Report Ready',
            'message': report.strip(),
            'priority': 'medium'
        })
    
    async def stop_dreaming(self) -> Dict:
        """Stop dream mode"""
        self.is_dreaming = False
        return {
            'success': True,
            'completed': len(self.completed_tasks),
            'remaining': len(self.dream_queue)
        }
    
    def get_dream_status(self) -> Dict:
        """Get current dream mode status"""
        return {
            'is_dreaming': self.is_dreaming,
            'queue_length': len(self.dream_queue),
            'completed': len(self.completed_tasks),
            'failed': len(self.failed_tasks),
            'started_at': self.dream_start_time.isoformat() if self.dream_start_time else None,
            'queued_tasks': [
                {
                    'id': t['id'],
                    'description': t['description'],
                    'priority': t['priority'],
                    'status': t['status']
                }
                for t in self.dream_queue
            ]
        }
    
    def clear_queue(self) -> Dict:
        """Clear the dream queue"""
        count = len(self.dream_queue)
        self.dream_queue = []
        self._save_queue()
        return {'success': True, 'cleared': count}
