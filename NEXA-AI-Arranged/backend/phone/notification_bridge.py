import asyncio
import json
import re
import threading
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime

class NotificationBridge:
    """
    Real-time phone notification mirroring.
    Shows phone notifications on desktop instantly.
    Can reply to messages directly from PC.
    """
    
    def __init__(self, adb_engine, notification_callback: Callable):
        self.adb = adb_engine
        self.notify = notification_callback
        
        self.active_notifications: Dict[str, Dict] = {}
        self.notification_history: List[Dict] = []
        self.is_watching = False
        self.watch_thread: Optional[threading.Thread] = None
        self.last_notification_time = time.time()
        
        # App icon mapping
        self.app_icons = {
            'com.whatsapp': '💬',
            'org.telegram.messenger': '✈️',
            'com.instagram.android': '📸',
            'com.facebook.katana': '👍',
            'com.twitter.android': '🐦',
            'com.google.android.gm': '📧',
            'com.google.android.apps.messaging': '💬',
            'com.android.phone': '📞',
            'com.spotify.music': '🎵',
            'com.youtube.android': '▶️',
            'com.snapchat.android': '👻',
            'com.linkedin.android': '💼',
            'in.swiggy.android': '🍔',
            'com.application.zomato': '🍕',
            'com.phonepe.app': '💳',
            'net.one97.paytm': '💰',
        }
    
    async def start_watching(self, device_id: str):
        """Start watching phone notifications"""
        
        self.is_watching = True
        self.watch_thread = threading.Thread(
            target=self._watch_loop,
            args=(device_id,),
            daemon=True
        )
        self.watch_thread.start()
        
        return {'success': True, 'watching': True}
    
    def _watch_loop(self, device_id: str):
        """Background notification watching loop"""
        
        while self.is_watching:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    self._check_notifications(device_id)
                )
                loop.close()
            except Exception:
                pass
            time.sleep(2)
    
    async def _check_notifications(self, device_id: str):
        """Check for new notifications"""
        
        output = await self.adb.shell(
            device_id,
            'dumpsys notification --noredact 2>/dev/null'
        )
        
        if not output:
            return
        
        # Parse notifications
        parsed = self._parse_notification_dump(output)
        
        # Check for new notifications
        for notif_id, notif in parsed.items():
            if notif_id not in self.active_notifications:
                # New notification!
                self.active_notifications[notif_id] = notif
                self.notification_history.insert(0, notif)
                
                # Keep history limited
                self.notification_history = self.notification_history[:100]
                
                # Show on desktop
                await self._show_notification(notif)
        
        # Remove dismissed notifications
        for notif_id in list(self.active_notifications.keys()):
            if notif_id not in parsed:
                del self.active_notifications[notif_id]
    
    def _parse_notification_dump(self, dump: str) -> Dict[str, Dict]:
        """Parse notification dump output"""
        
        notifications = {}
        current_notif = {}
        current_key = None
        
        for line in dump.split('\n'):
            line = line.strip()
            
            # New notification block
            if 'NotificationRecord(' in line:
                if current_notif and current_key:
                    notifications[current_key] = current_notif
                
                # Generate key from the line
                current_key = re.sub(r'[^a-zA-Z0-9]', '', line[:50])
                current_notif = {
                    'id': current_key,
                    'timestamp': datetime.now().isoformat(),
                    'raw_line': line
                }
            
            # Package name
            elif 'pkg=' in line and current_notif is not None:
                match = re.search(r'pkg=([a-zA-Z0-9\.]+)', line)
                if match:
                    pkg = match.group(1)
                    current_notif['package'] = pkg
                    current_notif['app_name'] = self._get_app_name(pkg)
                    current_notif['icon'] = self.app_icons.get(pkg, '📱')
            
            # Notification title
            elif 'android.title' in line and '=' in line:
                title = line.split('=', 1)[-1].strip()
                if title and title != 'null':
                    current_notif['title'] = title
            
            # Notification text
            elif 'android.text' in line and '=' in line:
                text = line.split('=', 1)[-1].strip()
                if text and text != 'null':
                    current_notif['text'] = text
            
            # Big text
            elif 'android.bigText' in line and '=' in line:
                big_text = line.split('=', 1)[-1].strip()
                if big_text and big_text != 'null':
                    current_notif['big_text'] = big_text
            
            # Sender (for messages)
            elif 'android.messagingUser' in line and '=' in line:
                sender = line.split('=', 1)[-1].strip()
                if sender:
                    current_notif['sender'] = sender
            
            # Can reply check
            elif 'remoteInputs' in line:
                current_notif['can_reply'] = True
        
        if current_notif and current_key:
            notifications[current_key] = current_notif
        
        # Filter valid notifications
        return {
            k: v for k, v in notifications.items()
            if v.get('title') or v.get('text')
        }
    
    def _get_app_name(self, package: str) -> str:
        """Get friendly app name from package"""
        
        app_names = {
            'com.whatsapp': 'WhatsApp',
            'org.telegram.messenger': 'Telegram',
            'com.instagram.android': 'Instagram',
            'com.facebook.katana': 'Facebook',
            'com.twitter.android': 'Twitter',
            'com.google.android.gm': 'Gmail',
            'com.android.phone': 'Phone',
            'com.spotify.music': 'Spotify',
            'com.snapchat.android': 'Snapchat',
            'com.linkedin.android': 'LinkedIn',
        }
        
        if package in app_names:
            return app_names[package]
        
        # Extract name from package
        parts = package.split('.')
        return parts[-1].capitalize()
    
    async def _show_notification(self, notif: Dict):
        """Display phone notification on desktop"""
        
        icon = notif.get('icon', '📱')
        app_name = notif.get('app_name', 'Phone')
        title = notif.get('title', '')
        text = notif.get('text', '')
        can_reply = notif.get('can_reply', False)
        
        await self.notify({
            'type': 'phone_notification',
            'source': 'phone',
            'title': f"{icon} {app_name}: {title}",
            'message': text or notif.get('big_text', ''),
            'package': notif.get('package', ''),
            'notification_id': notif.get('id', ''),
            'can_reply': can_reply,
            'actions': [
                {'label': '↩️ Reply', 'action': 'reply_notification'}
            ] if can_reply else [],
            'priority': 'medium',
            'timestamp': notif.get('timestamp')
        })
    
    async def reply_to_notification(
        self,
        device_id: str,
        package: str,
        reply_text: str
    ) -> Dict:
        """Reply to a notification directly from desktop"""
        
        # This uses ADB to send a reply via intent
        result = await self.adb.shell(
            device_id,
            f'am broadcast -a com.nexa.REPLY '
            f'--es package {package} '
            f'--es reply "{reply_text}"'
        )
        
        return {
            'success': True,
            'reply': reply_text,
            'package': package,
            'note': 'Reply sent via notification system'
        }
    
    async def dismiss_notification(
        self,
        device_id: str,
        notification_id: str
    ) -> Dict:
        """Dismiss phone notification"""
        
        result = await self.adb.shell(
            device_id,
            f'service call notification 1'
        )
        
        if notification_id in self.active_notifications:
            del self.active_notifications[notification_id]
        
        return {'success': True}
    
    async def dismiss_all_notifications(
        self,
        device_id: str
    ) -> Dict:
        """Dismiss all phone notifications"""
        
        result = await self.adb.shell(
            device_id,
            'service call statusbar 1'
        )
        
        self.active_notifications.clear()
        
        return {
            'success': True,
            'message': 'All notifications cleared'
        }
    
    def get_active_notifications(self) -> List[Dict]:
        """Get all active notifications"""
        return list(self.active_notifications.values())
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get notification history"""
        return self.notification_history[:limit]
    
    async def stop_watching(self):
        """Stop watching notifications"""
        self.is_watching = False
