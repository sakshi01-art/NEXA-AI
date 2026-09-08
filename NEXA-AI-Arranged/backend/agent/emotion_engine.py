import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import json

class EmotionEngine:
    """
    NEXA detects your emotional state and adapts.
    
    Detects from:
    - Voice tone (speed, pitch, volume)
    - Typing speed and error rate
    - Command patterns
    - Time of day
    - Recent failures/successes
    - Response to suggestions
    
    Adapts:
    - Response tone
    - Proactive help level
    - Task complexity suggestions
    - Break suggestions
    - Encouragement messages
    """
    
    EMOTIONAL_STATES = {
        "focused": {
            "indicators": ["fast_typing", "long_sessions", "few_corrections", "sequential_tasks"],
            "nexa_behavior": "minimal_interruptions",
            "response_style": "brief_and_direct"
        },
        "stressed": {
            "indicators": ["rapid_commands", "many_cancellations", "error_repetition", "late_hours"],
            "nexa_behavior": "calming_and_helpful",
            "response_style": "gentle_and_reassuring"
        },
        "bored": {
            "indicators": ["slow_typing", "app_switching", "youtube_social_media", "short_sessions"],
            "nexa_behavior": "engaging_suggestions",
            "response_style": "fun_and_motivating"
        },
        "productive": {
            "indicators": ["consistent_pace", "completing_tasks", "using_tools_efficiently"],
            "nexa_behavior": "supportive_minimal",
            "response_style": "encouraging_concise"
        },
        "frustrated": {
            "indicators": ["repeated_same_command", "many_errors", "close_reopen_apps", "aggressive_typing"],
            "nexa_behavior": "proactively_help",
            "response_style": "calm_problem_solving"
        },
        "tired": {
            "indicators": ["slow_response", "many_typos", "late_night", "simple_commands"],
            "nexa_behavior": "suggest_break",
            "response_style": "caring_supportive"
        }
    }
    
    EMOTIONAL_RESPONSES = {
        "stressed": {
            "acknowledgment": [
                "Lagta hai kuch stress ho raha hai. Deep breath lo, sab ho jayega. 😊",
                "Thoda relax karo. Main hoon na help ke liye.",
                "Ek ek step karte hain. Kya problem hai batao?",
                "It's okay, we'll figure this out together. Bolo kya ho raha hai?"
            ],
            "help_offer": "Main thoda extra help karun? Step by step sab solve karte hain.",
            "break_suggestion": "15 minute ka break loge? Studies kehti hai productivity badhti hai."
        },
        "frustrated": {
            "acknowledgment": [
                "Samajh sakta hoon frustration. Ye issue fix karte hain abhi.",
                "Yaar, ye kaam annoying lag raha hai. Dekho main fast solve karta hoon.",
                "Chill karo - main handle kar leta hoon ye."
            ],
            "help_offer": "Bolo main directly kar deta hoon. Kya chahiye exactly?",
            "troubleshoot": "Let me diagnose this properly. Ek second..."
        },
        "tired": {
            "acknowledgment": [
                "Lagta hai thak gaye ho. Kaam important hai par health bhi. 😴",
                "Raat ho gayi. Important work save karke rest karo.",
                "Aaj bahut kaam kiya! Good job. Ab rest karna chahiye."
            ],
            "help_offer": "Kal ke liye tasks organize kar dun? Fresh mind mein better hoga.",
            "save_work": "Sab kuch save kar deta hoon. Kal fresh start karna."
        },
        "bored": {
            "acknowledgment": [
                "Kuch interesting karte hain! Koi naya project explore karein?",
                "Productivity tip: New skill seekho! Kuch suggest karun?",
                "Boredom is creativity's friend! Kuch cool banate hain?"
            ],
            "suggestions": [
                "Ek quick automation workflow bana lo - time bachega future mein",
                "GitHub pe koi interesting project explore karo",
                "Nexa se naya kuch try karo - screen recording? Code analysis?"
            ]
        },
        "focused": {
            "behavior": "minimal",
            "only_critical_alerts": True,
            "acknowledgment": "🎯"  # Just emoji, no text
        },
        "productive": {
            "acknowledgment": [
                "Great work! Productivity high hai aaj!",
                "You're on a roll! 🔥",
                "Excellent pace! Keep it up!"
            ]
        }
    }
    
    def __init__(self, ai_provider, notification_callback):
        self.ai = ai_provider
        self.notify = notification_callback
        self.current_state = "neutral"
        self.state_history: List[Dict] = []
        self.metrics = EmotionMetrics()
        self.last_intervention = None
        self.intervention_cooldown = 1800  # 30 minutes between interventions
    
    async def analyze_voice_emotion(
        self,
        audio_features: Dict
    ) -> Dict:
        """
        Detect emotion from voice characteristics.
        
        Voice features:
        - Speaking rate (words per minute)
        - Pitch variation
        - Volume
        - Pause frequency
        - Tone
        """
        
        speaking_rate = audio_features.get("speaking_rate", 150)
        pitch = audio_features.get("pitch", 200)
        volume = audio_features.get("volume", 0.5)
        pauses = audio_features.get("pause_count", 3)
        
        detected_emotions = []
        
        # Fast speech + high pitch = stressed/excited
        if speaking_rate > 200 and pitch > 250:
            detected_emotions.append(("stressed", 0.7))
        
        # Slow speech + low volume = tired
        if speaking_rate < 100 and volume < 0.3:
            detected_emotions.append(("tired", 0.8))
        
        # Normal rate + many pauses = thinking/focused
        if 120 <= speaking_rate <= 170 and pauses > 5:
            detected_emotions.append(("focused", 0.6))
        
        # Determine primary emotion
        if detected_emotions:
            primary = max(detected_emotions, key=lambda x: x[1])
            return {
                "emotion": primary[0],
                "confidence": primary[1],
                "all_detected": detected_emotions
            }
        
        return {"emotion": "neutral", "confidence": 0.5}
    
    def analyze_typing_emotion(
        self,
        typing_metrics: Dict
    ) -> Dict:
        """
        Detect emotion from typing patterns.
        
        Typing metrics:
        - Words per minute
        - Error rate (backspace frequency)
        - Pause duration
        - Key press force (if available)
        """
        
        wpm = typing_metrics.get("wpm", 60)
        error_rate = typing_metrics.get("error_rate", 0.05)
        pause_avg = typing_metrics.get("pause_avg_ms", 200)
        
        if wpm > 80 and error_rate > 0.15:
            return {"emotion": "stressed", "confidence": 0.75}
        
        if wpm < 30 and pause_avg > 500:
            return {"emotion": "tired", "confidence": 0.7}
        
        if wpm > 90 and error_rate < 0.05:
            return {"emotion": "focused", "confidence": 0.8}
        
        if error_rate > 0.20:
            return {"emotion": "frustrated", "confidence": 0.65}
        
        return {"emotion": "neutral", "confidence": 0.5}
    
    def analyze_behavior_emotion(
        self,
        behavior_data: Dict
    ) -> Dict:
        """Detect emotion from behavioral patterns"""
        
        cancellation_rate = behavior_data.get("cancellation_rate", 0)
        retry_count = behavior_data.get("retry_count", 0)
        app_switch_rate = behavior_data.get("app_switch_rate", 0)
        task_completion_rate = behavior_data.get("task_completion_rate", 1.0)
        
        if retry_count >= 3 or cancellation_rate > 0.5:
            return {"emotion": "frustrated", "confidence": 0.8}
        
        if app_switch_rate > 10 and task_completion_rate < 0.3:
            return {"emotion": "bored", "confidence": 0.7}
        
        if task_completion_rate > 0.8 and retry_count == 0:
            return {"emotion": "productive", "confidence": 0.75}
        
        return {"emotion": "neutral", "confidence": 0.5}
    
    async def update_emotional_state(
        self,
        voice_emotion: Optional[Dict] = None,
        typing_emotion: Optional[Dict] = None,
        behavior_emotion: Optional[Dict] = None
    ):
        """
        Combine multiple signals to determine emotional state.
        Then respond appropriately.
        """
        
        # Weighted combination of signals
        signals = []
        
        if voice_emotion and voice_emotion.get("confidence", 0) > 0.6:
            signals.append((voice_emotion["emotion"], voice_emotion["confidence"] * 0.5))
        
        if typing_emotion and typing_emotion.get("confidence", 0) > 0.6:
            signals.append((typing_emotion["emotion"], typing_emotion["confidence"] * 0.3))
        
        if behavior_emotion and behavior_emotion.get("confidence", 0) > 0.6:
            signals.append((behavior_emotion["emotion"], behavior_emotion["confidence"] * 0.2))
        
        if not signals:
            return
        
        # Find dominant emotion
        emotion_scores = {}
        for emotion, weight in signals:
            emotion_scores[emotion] = emotion_scores.get(emotion, 0) + weight
        
        new_state = max(emotion_scores.items(), key=lambda x: x[1])[0]
        
        # State change detected
        if new_state != self.current_state:
            old_state = self.current_state
            self.current_state = new_state
            
            self.state_history.append({
                "from": old_state,
                "to": new_state,
                "timestamp": datetime.now().isoformat(),
                "signals": signals
            })
            
            # Respond to emotional state change
            await self._respond_to_emotion(new_state)
    
    async def _respond_to_emotion(self, emotion: str):
        """Respond appropriately to detected emotion"""
        
        # Check cooldown
        if self.last_intervention:
            elapsed = (datetime.now() - self.last_intervention).seconds
            if elapsed < self.intervention_cooldown:
                return
        
        import random
        responses = self.EMOTIONAL_RESPONSES.get(emotion, {})
        
        if emotion == "stressed":
            acknowledgment = random.choice(responses.get("acknowledgment", []))
            
            await self.notify({
                "type": "emotion_aware",
                "emotion": "stressed",
                "title": "😟 Stress Detected",
                "message": acknowledgment,
                "actions": [
                    {"label": "Take a break", "action": "start_break"},
                    {"label": "Get help", "action": "open_assistant"}
                ],
                "priority": "medium"
            })
            
            self.last_intervention = datetime.now()
        
        elif emotion == "tired":
            acknowledgment = random.choice(responses.get("acknowledgment", []))
            
            await self.notify({
                "type": "emotion_aware",
                "emotion": "tired",
                "title": "😴 You seem tired",
                "message": acknowledgment,
                "actions": [
                    {"label": "Save & Close", "action": "save_all_close"},
                    {"label": "Continue", "action": "dismiss"}
                ],
                "priority": "low"
            })
            
            self.last_intervention = datetime.now()
        
        elif emotion == "frustrated":
            acknowledgment = random.choice(responses.get("acknowledgment", []))
            
            await self.notify({
                "type": "emotion_aware",
                "emotion": "frustrated",
                "title": "😤 Let me help!",
                "message": acknowledgment,
                "actions": [
                    {"label": "Show me the issue", "action": "diagnose"},
                    {"label": "I'm fine", "action": "dismiss"}
                ],
                "priority": "high"
            })
            
            self.last_intervention = datetime.now()
        
        elif emotion == "bored":
            suggestions = responses.get("suggestions", [])
            if suggestions:
                import random
                suggestion = random.choice(suggestions)
                
                await self.notify({
                    "type": "emotion_aware",
                    "emotion": "bored",
                    "title": "💡 Nexa Suggestion",
                    "message": suggestion,
                    "actions": [
                        {"label": "Try it!", "action": "execute_suggestion"},
                        {"label": "Maybe later", "action": "dismiss"}
                    ],
                    "priority": "low"
                })
    
    def get_emotion_report(self) -> Dict:
        """Get emotion history report"""
        
        if not self.state_history:
            return {
                "current_state": self.current_state,
                "total_states": 0,
                "most_common": "neutral"
            }
        
        state_counts = {}
        for state in self.state_history:
            s = state["to"]
            state_counts[s] = state_counts.get(s, 0) + 1
        
        most_common = max(state_counts.items(), key=lambda x: x[1])[0]
        
        return {
            "current_state": self.current_state,
            "total_state_changes": len(self.state_history),
            "most_common_state": most_common,
            "state_distribution": state_counts,
            "emotional_journey": self.state_history[-10:]
        }


class EmotionMetrics:
    """Track metrics for emotion detection"""
    
    def __init__(self):
        self.typing_speeds = []
        self.error_rates = []
        self.cancellation_events = []
        self.app_switches = []
        self.task_completions = []
    
    def record_typing(self, wpm: float, error_rate: float):
        self.typing_speeds.append(wpm)
        self.error_rates.append(error_rate)
        
        # Keep last 20
        self.typing_speeds = self.typing_speeds[-20:]
        self.error_rates = self.error_rates[-20:]
    
    def record_cancellation(self):
        self.cancellation_events.append(datetime.now())
        
        # Keep last hour only
        cutoff = datetime.now() - timedelta(hours=1)
        self.cancellation_events = [e for e in self.cancellation_events if e > cutoff]
    
    def get_current_metrics(self) -> Dict:
        recent_speed = (
            sum(self.typing_speeds[-5:]) / len(self.typing_speeds[-5:])
            if self.typing_speeds else 60
        )
        
        recent_errors = (
            sum(self.error_rates[-5:]) / len(self.error_rates[-5:])
            if self.error_rates else 0.05
        )
        
        cancellations_last_hour = len(self.cancellation_events)
        
        return {
            "wpm": recent_speed,
            "error_rate": recent_errors,
            "cancellation_rate": cancellations_last_hour / max(cancellations_last_hour + 10, 1)
        }
