import asyncio
import json
import threading
import time
import wave
try:
    import pyaudio
except ImportError:
    pyaudio = None
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

class MeetingAssistant:
    """
    Complete AI Meeting Assistant.
    
    Features:
    - Auto-detect when meeting starts
    - Real-time transcription of meeting
    - Speaker identification
    - Auto-generate meeting notes
    - Action items extraction
    - Meeting summary in Hinglish
    - Follow-up email draft
    - Key decisions tracking
    - Meeting analytics
    - Zoom/Teams/Meet integration
    - Schedule next meeting
    - Share notes automatically
    
    Commands:
    "Nexa, meeting start kar"
    "Meeting notes bana"
    "Aaj ki meeting ka summary bata"
    "Action items kya hain?"
    "Follow-up email draft kar"
    """
    
    def __init__(self, ai_provider, stt_provider, notification_callback: Callable):
        self.ai = ai_provider
        self.stt = stt_provider
        self.notify = notification_callback
        
        self.is_recording = False
        self.meeting_active = False
        self.current_meeting: Optional[Dict] = None
        self.all_meetings: List[Dict] = []
        
        self.audio_buffer: List[bytes] = []
        self.transcript_segments: List[Dict] = []
        self.speakers: Dict[str, str] = {}
        
        self.record_thread: Optional[threading.Thread] = None
        self.transcribe_thread: Optional[threading.Thread] = None
        
        self.meetings_dir = Path("./data/meetings")
        self.meetings_dir.mkdir(parents=True, exist_ok=True)
        
        self.audio_config = {
            'sample_rate': 16000,
            'channels': 1,
            'chunk_size': 1024,
            'format': pyaudio.paInt16 if pyaudio else 2
        }
    
    async def start_meeting(
        self,
        meeting_name: str = "Meeting",
        participants: Optional[List[str]] = None,
        agenda: Optional[str] = None
    ) -> Dict:
        """Start recording and transcribing a meeting"""
        
        meeting_id = f"meet_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_meeting = {
            'id': meeting_id,
            'name': meeting_name,
            'participants': participants or [],
            'agenda': agenda,
            'started_at': datetime.now().isoformat(),
            'ended_at': None,
            'duration_minutes': 0,
            'transcript': [],
            'summary': None,
            'action_items': [],
            'decisions': [],
            'key_points': [],
            'follow_up_email': None,
            'sentiment': 'neutral',
            'participation_stats': {}
        }
        
        self.transcript_segments = []
        self.is_recording = True
        self.meeting_active = True
        
        # Start audio recording
        self.record_thread = threading.Thread(
            target=self._record_audio,
            daemon=True
        )
        self.record_thread.start()
        
        # Start transcription
        self.transcribe_thread = threading.Thread(
            target=self._transcribe_loop,
            daemon=True
        )
        self.transcribe_thread.start()
        
        await self.notify({
            'type': 'success',
            'title': '🎤 Meeting Started',
            'message': f'Recording "{meeting_name}" - Live transcription active',
            'priority': 'medium'
        })
        
        return {
            'success': True,
            'meeting_id': meeting_id,
            'name': meeting_name,
            'started_at': self.current_meeting['started_at'],
            'message': 'Meeting recording started! Main sab record kar raha hoon.'
        }
    
    def _record_audio(self):
        """Background audio recording thread"""
        
        audio = pyaudio.PyAudio()
        
        try:
            stream = audio.open(
                format=self.audio_config['format'],
                channels=self.audio_config['channels'],
                rate=self.audio_config['sample_rate'],
                input=True,
                frames_per_buffer=self.audio_config['chunk_size']
            )
            
            while self.is_recording:
                try:
                    chunk = stream.read(
                        self.audio_config['chunk_size'],
                        exception_on_overflow=False
                    )
                    self.audio_buffer.append(chunk)
                except Exception:
                    pass
            
            stream.stop_stream()
            stream.close()
        
        finally:
            audio.terminate()
    
    def _transcribe_loop(self):
        """Background transcription loop - processes audio every 5 seconds"""
        
        segment_buffer = []
        last_transcribe = time.time()
        
        while self.is_recording or segment_buffer:
            time.sleep(0.1)
            
            # Collect audio chunks
            while self.audio_buffer:
                segment_buffer.append(self.audio_buffer.pop(0))
            
            # Transcribe every 5 seconds
            if time.time() - last_transcribe >= 5.0 and segment_buffer:
                audio_data = b''.join(segment_buffer)
                segment_buffer = []
                last_transcribe = time.time()
                
                # Transcribe in thread
                loop = asyncio.new_event_loop()
                result = loop.run_until_complete(
                    self._transcribe_segment(audio_data)
                )
                loop.close()
                
                if result and result.get('text'):
                    self.transcript_segments.append(result)
                    
                    if self.current_meeting:
                        self.current_meeting['transcript'].append(result)
    
    async def _transcribe_segment(self, audio_data: bytes) -> Optional[Dict]:
        """Transcribe a single audio segment"""
        
        try:
            result = await self.stt.transcribe(audio_data)
            
            if result and result.get('text', '').strip():
                return {
                    'text': result['text'],
                    'timestamp': datetime.now().isoformat(),
                    'speaker': 'Unknown',
                    'confidence': result.get('confidence', 1.0)
                }
        except Exception:
            pass
        
        return None
    
    async def stop_meeting(self) -> Dict:
        """Stop recording and generate meeting notes"""
        
        if not self.meeting_active or not self.current_meeting:
            return {'success': False, 'error': 'No active meeting'}
        
        self.is_recording = False
        self.meeting_active = False
        
        # Wait for threads to finish
        if self.record_thread:
            self.record_thread.join(timeout=5)
        if self.transcribe_thread:
            self.transcribe_thread.join(timeout=10)
        
        # Calculate duration
        started = datetime.fromisoformat(self.current_meeting['started_at'])
        ended = datetime.now()
        duration = (ended - started).seconds // 60
        
        self.current_meeting['ended_at'] = ended.isoformat()
        self.current_meeting['duration_minutes'] = duration
        
        # Generate AI analysis
        analysis = await self._analyze_meeting()
        self.current_meeting.update(analysis)
        
        # Save meeting
        self._save_meeting(self.current_meeting)
        self.all_meetings.append(self.current_meeting)
        
        await self.notify({
            'type': 'success',
            'title': '📋 Meeting Ended',
            'message': f'Meeting notes ready! {duration} minute ki meeting ka summary bana diya.',
            'priority': 'medium'
        })
        
        return {
            'success': True,
            'meeting_id': self.current_meeting['id'],
            'duration_minutes': duration,
            'transcript_segments': len(self.transcript_segments),
            'summary': self.current_meeting.get('summary'),
            'action_items': self.current_meeting.get('action_items', []),
            'message': f'{duration} minute ki meeting complete. Notes ready hain!'
        }
    
    async def _analyze_meeting(self) -> Dict:
        """Use AI to analyze meeting transcript"""
        
        if not self.transcript_segments:
            return {
                'summary': 'Meeting mein koi transcript nahi mila.',
                'action_items': [],
                'decisions': [],
                'key_points': [],
                'sentiment': 'neutral'
            }
        
        full_transcript = '\n'.join([
            f"[{seg.get('timestamp', '')}] {seg.get('speaker', 'Unknown')}: {seg.get('text', '')}"
            for seg in self.transcript_segments
        ])
        
        prompt = f"""
        Analyze this meeting transcript and provide a comprehensive summary.
        
        Meeting: {self.current_meeting.get('name')}
        Duration: {self.current_meeting.get('duration_minutes')} minutes
        Agenda: {self.current_meeting.get('agenda', 'Not specified')}
        
        Transcript:
        {full_transcript[:6000]}
        
        Provide analysis in JSON format:
        {{
            "summary": "Meeting ka brief summary in Hinglish (150 words max)",
            "key_points": ["point 1", "point 2", "point 3"],
            "action_items": [
                {{
                    "task": "task description",
                    "assignee": "person name or Unknown",
                    "deadline": "deadline or null",
                    "priority": "high/medium/low"
                }}
            ],
            "decisions": ["decision 1", "decision 2"],
            "questions_raised": ["question 1"],
            "sentiment": "positive/negative/neutral/mixed",
            "productivity_score": 0-100,
            "follow_up_needed": true/false,
            "next_meeting_suggested": "suggested timeframe or null"
        }}
        """
        
        try:
            response = await self.ai.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            return json.loads(response['content'])
        
        except Exception as e:
            return {
                'summary': 'Meeting analysis mein error aaya.',
                'action_items': [],
                'decisions': [],
                'key_points': [],
                'sentiment': 'neutral',
                'error': str(e)
            }
    
    async def generate_follow_up_email(
        self,
        meeting_id: Optional[str] = None,
        recipient_name: Optional[str] = None
    ) -> Dict:
        """Generate professional follow-up email for meeting"""
        
        meeting = self._get_meeting(meeting_id)
        if not meeting:
            return {'success': False, 'error': 'Meeting not found'}
        
        prompt = f"""
        Write a professional follow-up email for this meeting.
        
        Meeting: {meeting['name']}
        Date: {meeting['started_at'][:10]}
        Duration: {meeting['duration_minutes']} minutes
        Summary: {meeting.get('summary', 'No summary')}
        Action Items: {json.dumps(meeting.get('action_items', []))}
        Decisions: {json.dumps(meeting.get('decisions', []))}
        
        Recipient: {recipient_name or 'Team'}
        
        Requirements:
        - Professional but friendly tone
        - Clear subject line
        - Recap key decisions
        - List action items with owners
        - Next steps
        - Offer for questions
        
        Format as JSON:
        {{
            "subject": "email subject",
            "body": "complete email body",
            "cc_suggestions": ["suggested cc list"]
        }}
        """
        
        try:
            response = await self.ai.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            email = json.loads(response['content'])
            
            if self.current_meeting and meeting['id'] == self.current_meeting.get('id'):
                self.current_meeting['follow_up_email'] = email
            
            return {
                'success': True,
                'email': email,
                'meeting': meeting['name']
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def get_action_items(
        self,
        meeting_id: Optional[str] = None
    ) -> Dict:
        """Get action items from meeting"""
        
        meeting = self._get_meeting(meeting_id)
        if not meeting:
            return {'success': False, 'error': 'Meeting not found'}
        
        return {
            'success': True,
            'meeting': meeting['name'],
            'action_items': meeting.get('action_items', []),
            'count': len(meeting.get('action_items', []))
        }
    
    async def get_meeting_summary(
        self,
        meeting_id: Optional[str] = None
    ) -> Dict:
        """Get meeting summary"""
        
        meeting = self._get_meeting(meeting_id)
        if not meeting:
            return {'success': False, 'error': 'Meeting not found'}
        
        return {
            'success': True,
            'meeting': meeting['name'],
            'duration': meeting.get('duration_minutes'),
            'summary': meeting.get('summary'),
            'key_points': meeting.get('key_points', []),
            'decisions': meeting.get('decisions', []),
            'action_items_count': len(meeting.get('action_items', []))
        }
    
    def _get_meeting(self, meeting_id: Optional[str] = None) -> Optional[Dict]:
        """Get meeting by ID or return current"""
        
        if not meeting_id:
            return self.current_meeting
        
        for meeting in self.all_meetings:
            if meeting['id'] == meeting_id:
                return meeting
        
        return None
    
    def _save_meeting(self, meeting: Dict):
        """Save meeting to disk"""
        
        file_path = self.meetings_dir / f"{meeting['id']}.json"
        
        with open(file_path, 'w') as f:
            json.dump(meeting, f, indent=2, default=str)
    
    def get_all_meetings(self) -> List[Dict]:
        """Get list of all meetings"""
        
        meetings = []
        
        for file in sorted(
            self.meetings_dir.glob("meet_*.json"),
            reverse=True
        ):
            try:
                with open(file) as f:
                    meeting = json.load(f)
                    meetings.append({
                        'id': meeting['id'],
                        'name': meeting['name'],
                        'date': meeting['started_at'][:10],
                        'duration': meeting.get('duration_minutes', 0),
                        'action_items_count': len(meeting.get('action_items', [])),
                        'summary': meeting.get('summary', '')[:100]
                    })
            except Exception:
                pass
        
        return meetings[:20]
    
    async def get_live_transcript(self) -> Dict:
        """Get current live transcript"""
        
        if not self.meeting_active:
            return {'success': False, 'error': 'No active meeting'}
        
        return {
            'success': True,
            'is_recording': self.is_recording,
            'segments': self.transcript_segments[-10:],
            'total_segments': len(self.transcript_segments)
        }
