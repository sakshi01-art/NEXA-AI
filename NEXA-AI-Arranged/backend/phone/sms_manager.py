import asyncio
import json
import re
from typing import Dict, List, Optional
from datetime import datetime

class SMSManager:
    """
    Complete SMS management from desktop.
    Read, send, delete, search messages.
    """
    
    def __init__(self, adb_engine):
        self.adb = adb_engine
    
    async def get_conversations(
        self,
        device_id: str,
        limit: int = 20
    ) -> Dict:
        """Get SMS conversations list"""
        
        output = await self.adb.shell(
            device_id,
            'content query --uri content://sms/conversations '
            '--projection thread_id:msg_count:date:body:address'
        )
        
        if not output:
            return {'success': False, 'error': 'Could not read SMS'}
        
        conversations = []
        
        for line in output.split('\n'):
            if 'Row:' in line:
                conv = self._parse_content_row(line)
                if conv:
                    conversations.append(conv)
        
        # Sort by date
        conversations.sort(key=lambda x: x.get('date', 0), reverse=True)
        
        return {
            'success': True,
            'conversations': conversations[:limit],
            'total': len(conversations)
        }
    
    async def get_messages(
        self,
        device_id: str,
        thread_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        limit: int = 50
    ) -> Dict:
        """Get messages from a conversation"""
        
        if thread_id:
            uri = f'content://sms/conversations/{thread_id}'
        else:
            uri = 'content://sms/inbox'
        
        output = await self.adb.shell(
            device_id,
            f'content query --uri {uri} '
            f'--projection _id:address:body:date:type:read '
            f'--sort "date DESC" '
        )
        
        if not output:
            return {'success': False, 'error': 'Could not read messages'}
        
        messages = []
        
        for line in output.split('\n'):
            if 'Row:' in line:
                msg = self._parse_content_row(line)
                if msg:
                    # Format
                    messages.append({
                        'id': msg.get('_id', ''),
                        'address': msg.get('address', ''),
                        'body': msg.get('body', ''),
                        'date': msg.get('date', 0),
                        'formatted_date': self._format_date(msg.get('date', 0)),
                        'type': 'sent' if msg.get('type') == '2' else 'received',
                        'read': msg.get('read') == '1'
                    })
        
        # Filter by phone number if specified
        if phone_number:
            messages = [
                m for m in messages
                if phone_number in m.get('address', '')
            ]
        
        return {
            'success': True,
            'messages': messages[:limit],
            'total': len(messages)
        }
    
    async def send_sms(
        self,
        device_id: str,
        phone_number: str,
        message: str
    ) -> Dict:
        """Send SMS message"""
        
        # Use SL4A or intent to send
        intent_cmd = (
            f'am start -a android.intent.action.SENDTO '
            f'-d "sms:{phone_number}" '
            f'--es sms_body "{message}" '
            f'--ez exit_on_sent true'
        )
        
        output = await self.adb.shell(device_id, intent_cmd)
        
        await asyncio.sleep(1)
        
        # Auto-press send button
        result = await self.adb.press_key(device_id, 'KEYCODE_ENTER')
        
        return {
            'success': True,
            'to': phone_number,
            'message': message,
            'sent_at': datetime.now().isoformat(),
            'note': 'SMS sent via messaging app'
        }
    
    async def delete_message(
        self,
        device_id: str,
        message_id: str
    ) -> Dict:
        """Delete SMS message"""
        
        output = await self.adb.shell(
            device_id,
            f'content delete --uri content://sms/{message_id}'
        )
        
        return {
            'success': True,
            'deleted_id': message_id
        }
    
    async def search_messages(
        self,
        device_id: str,
        query: str,
        limit: int = 20
    ) -> Dict:
        """Search through SMS messages"""
        
        output = await self.adb.shell(
            device_id,
            f'content query --uri content://sms '
            f'--projection _id:address:body:date '
            f'--where "body LIKE \'%{query}%\'"'
        )
        
        if not output:
            return {'success': True, 'messages': [], 'total': 0}
        
        messages = []
        for line in output.split('\n'):
            if 'Row:' in line:
                msg = self._parse_content_row(line)
                if msg:
                    messages.append({
                        'id': msg.get('_id', ''),
                        'address': msg.get('address', ''),
                        'body': msg.get('body', ''),
                        'date': self._format_date(msg.get('date', 0))
                    })
        
        return {
            'success': True,
            'query': query,
            'messages': messages[:limit],
            'total': len(messages)
        }
    
    async def get_unread_count(self, device_id: str) -> Dict:
        """Get count of unread SMS messages"""
        
        output = await self.adb.shell(
            device_id,
            'content query --uri content://sms/inbox '
            '--projection _id '
            '--where "read=0"'
        )
        
        count = 0
        if output:
            count = len([l for l in output.split('\n') if 'Row:' in l])
        
        return {
            'success': True,
            'unread_count': count
        }
    
    def _parse_content_row(self, line: str) -> Optional[Dict]:
        """Parse ADB content query row"""
        
        try:
            result = {}
            
            # Remove "Row: N " prefix
            if 'Row:' in line:
                line = line.split('Row:')[1]
                line = re.sub(r'^\d+\s+', '', line.strip())
            
            # Parse key=value pairs
            pairs = re.findall(r'(\w+)=([^,}]+)', line)
            
            for key, value in pairs:
                result[key.strip()] = value.strip()
            
            return result if result else None
        
        except Exception:
            return None
    
    def _format_date(self, timestamp) -> str:
        """Format SMS timestamp"""
        
        try:
            ts = int(str(timestamp)[:10])
            dt = datetime.fromtimestamp(ts)
            
            now = datetime.now()
            delta = now - dt
            
            if delta.days == 0:
                return dt.strftime('%I:%M %p')
            elif delta.days == 1:
                return 'Yesterday'
            elif delta.days < 7:
                return dt.strftime('%A')
            else:
                return dt.strftime('%d %b %Y')
        except Exception:
            return 'Unknown'
