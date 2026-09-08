import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

class DigitalTwinEngine:
    """
    Creates a Digital Twin of the user.
    
    The AI learns:
    - How you type and speak
    - Your work patterns and habits
    - Your decision-making style
    - Your preferences for every app
    - Your productivity peaks and valleys
    - Your communication style
    - Your most common workflows
    
    Then it can:
    - Predict what you'll do next
    - Pre-execute tasks before you ask
    - Respond AS YOU in certain contexts
    - Auto-draft emails/messages in your style
    - Suggest exactly what you need
    """
    
    def __init__(self, ai_provider, memory_store, user_id: str = "default"):
        self.ai = ai_provider
        self.memory = memory_store
        self.user_id = user_id
        self.twin_profile = self._load_profile()
        self.behavior_tracker = BehaviorTracker()
        self.pattern_analyzer = PatternAnalyzer()
        self.predictor = ActionPredictor()
        self.style_cloner = StyleCloner(ai_provider)
        self.is_learning = True
        self.confidence_threshold = 0.85
    
    def _load_profile(self) -> Dict:
        """Load or create digital twin profile"""
        
        profile_path = Path(f"./data/twins/{self.user_id}.json")
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        
        if profile_path.exists():
            with open(profile_path) as f:
                return json.load(f)
        
        return {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "personality": {
                "communication_style": "neutral",
                "formality_level": 0.5,
                "response_length": "medium",
                "humor_preference": 0.3,
                "directness": 0.6,
                "emoji_usage": 0.2
            },
            "work_patterns": {
                "peak_hours": [],
                "break_patterns": [],
                "task_duration_avg": {},
                "focus_sessions": [],
                "distraction_apps": []
            },
            "app_behaviors": {},
            "decision_patterns": {
                "speed": "medium",
                "risk_tolerance": 0.4,
                "confirmation_needed": [],
                "auto_approve": []
            },
            "vocabulary": {
                "common_words": {},
                "phrases": {},
                "hinglish_preference": 0.5
            },
            "workflows": [],
            "predictions_accuracy": 0.0,
            "total_observations": 0
        }
    
    def _save_profile(self):
        """Save digital twin profile"""
        
        profile_path = Path(f"./data/twins/{self.user_id}.json")
        with open(profile_path, 'w') as f:
            json.dump(self.twin_profile, f, indent=2, default=str)
    
    async def observe_behavior(
        self,
        action: str,
        context: Dict,
        result: Dict,
        timestamp: Optional[datetime] = None
    ):
        """
        Observe and learn from user behavior.
        Every action teaches the twin.
        """
        
        if not self.is_learning:
            return
        
        ts = timestamp or datetime.now()
        
        # Record observation
        observation = {
            "action": action,
            "context": context,
            "result": result,
            "hour": ts.hour,
            "weekday": ts.weekday(),
            "timestamp": ts.isoformat()
        }
        
        # Update work patterns
        await self._update_work_patterns(observation)
        
        # Update app behaviors
        await self._update_app_behaviors(observation)
        
        # Update vocabulary
        if "text" in context:
            await self._update_vocabulary(context["text"])
        
        # Detect new workflow
        await self._detect_workflow_pattern(observation)
        
        # Update profile
        self.twin_profile["total_observations"] += 1
        self._save_profile()
    
    async def _update_work_patterns(self, observation: Dict):
        """Learn when and how user works"""
        
        hour = observation["hour"]
        patterns = self.twin_profile["work_patterns"]
        
        # Track active hours
        if hour not in patterns["peak_hours"]:
            hour_count = sum(
                1 for h in patterns.get("hour_history", [])
                if h == hour
            )
            if hour_count >= 5:  # Active in this hour at least 5 times
                patterns["peak_hours"].append(hour)
                patterns["peak_hours"] = list(set(patterns["peak_hours"]))
        
        # Track task durations per app
        if "app" in observation["context"]:
            app = observation["context"]["app"]
            duration = observation["context"].get("duration", 0)
            
            if app not in patterns["task_duration_avg"]:
                patterns["task_duration_avg"][app] = []
            
            patterns["task_duration_avg"][app].append(duration)
            
            # Keep last 20 durations
            patterns["task_duration_avg"][app] = patterns["task_duration_avg"][app][-20:]
        
        self.twin_profile["work_patterns"] = patterns
    
    async def _update_app_behaviors(self, observation: Dict):
        """Learn how user uses each app"""
        
        app = observation["context"].get("app")
        if not app:
            return
        
        behaviors = self.twin_profile["app_behaviors"]
        
        if app not in behaviors:
            behaviors[app] = {
                "usage_count": 0,
                "typical_actions": {},
                "typical_duration": 0,
                "common_workflows": []
            }
        
        behaviors[app]["usage_count"] += 1
        
        action = observation["action"]
        behaviors[app]["typical_actions"][action] = (
            behaviors[app]["typical_actions"].get(action, 0) + 1
        )
        
        self.twin_profile["app_behaviors"] = behaviors
    
    async def _update_vocabulary(self, text: str):
        """Learn user's vocabulary and communication style"""
        
        words = text.lower().split()
        vocab = self.twin_profile["vocabulary"]
        
        # Count word frequencies
        for word in words:
            if len(word) > 2:  # Skip very short words
                vocab["common_words"][word] = vocab["common_words"].get(word, 0) + 1
        
        # Keep only top 500 words
        if len(vocab["common_words"]) > 500:
            sorted_words = sorted(
                vocab["common_words"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            vocab["common_words"] = dict(sorted_words[:500])
        
        # Detect Hinglish preference
        hindi_words = {
            "karo", "kar", "kholo", "bata", "hai", "hain",
            "mera", "meri", "mere", "aur", "nahi"
        }
        
        hindi_count = sum(1 for w in words if w in hindi_words)
        if words:
            hinglish_ratio = hindi_count / len(words)
            
            # Smooth update
            current = vocab["hinglish_preference"]
            vocab["hinglish_preference"] = current * 0.9 + hinglish_ratio * 0.1
        
        self.twin_profile["vocabulary"] = vocab
    
    async def _detect_workflow_pattern(self, observation: Dict):
        """Detect repeated workflow patterns"""
        
        # This would track sequences of actions
        # and identify repeating patterns
        pass
    
    async def predict_next_action(
        self,
        current_context: Dict
    ) -> Dict:
        """
        Predict what the user will do next.
        
        Returns:
            {
                'predicted_action': str,
                'confidence': float,
                'should_preempt': bool,
                'message': str
            }
        """
        
        hour = datetime.now().hour
        patterns = self.twin_profile["work_patterns"]
        app_behaviors = self.twin_profile["app_behaviors"]
        
        # Build prediction context
        prediction_context = {
            "current_hour": hour,
            "current_app": current_context.get("app"),
            "recent_actions": current_context.get("recent_actions", []),
            "peak_hours": patterns.get("peak_hours", []),
            "typical_sequences": self._get_typical_sequences(current_context),
            "profile": self.twin_profile
        }
        
        prompt = f"""
        Based on this user's digital twin profile, predict their next action.
        
        User Profile Summary:
        - Peak work hours: {prediction_context['peak_hours']}
        - Current hour: {prediction_context['current_hour']}
        - Current app: {prediction_context['current_app']}
        - Recent actions: {prediction_context['recent_actions'][-5:]}
        - Common workflows: {self.twin_profile['workflows'][:3]}
        
        Predict:
        1. What will the user do next?
        2. Confidence level (0.0-1.0)
        3. Should NEXA preemptively do it?
        
        JSON format:
        {{
            "predicted_action": "description",
            "action_type": "tool_name",
            "action_params": {{}},
            "confidence": 0.0,
            "reasoning": "why",
            "should_preempt": false
        }}
        """
        
        try:
            response = await self.ai.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            prediction = json.loads(response["content"])
            
            # Only preempt if confidence is high enough
            if prediction.get("confidence", 0) < self.confidence_threshold:
                prediction["should_preempt"] = False
            
            return {"success": True, "prediction": prediction}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_typical_sequences(self, context: Dict) -> List[List[str]]:
        """Get typical action sequences for current context"""
        
        current_app = context.get("app")
        if not current_app:
            return []
        
        app_data = self.twin_profile["app_behaviors"].get(current_app, {})
        return app_data.get("common_workflows", [])
    
    async def clone_writing_style(
        self,
        draft_text: str,
        purpose: str = "message"
    ) -> str:
        """
        Rewrite text in user's personal style.
        
        Uses learned vocabulary and communication patterns.
        """
        
        vocab = self.twin_profile["vocabulary"]
        personality = self.twin_profile["personality"]
        
        top_words = sorted(
            vocab["common_words"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:30]
        
        hinglish_pref = vocab.get("hinglish_preference", 0.3)
        
        prompt = f"""
        Rewrite this {purpose} in the user's personal communication style.
        
        User's style characteristics:
        - Formality level: {personality['formality_level']} (0=very casual, 1=very formal)
        - Response length preference: {personality['response_length']}
        - Humor level: {personality['humor_preference']}
        - Directness: {personality['directness']}
        - Hinglish usage: {hinglish_pref} (0=pure English, 1=pure Hindi)
        - Common words they use: {[w[0] for w in top_words[:15]]}
        
        Original draft:
        {draft_text}
        
        Rewrite it to sound exactly like this person would write it.
        Keep the meaning identical but match their style perfectly.
        Return only the rewritten text.
        """
        
        try:
            response = await self.ai.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            
            return response["content"]
        
        except Exception as e:
            return draft_text  # Return original if AI fails
    
    async def simulate_user_response(
        self,
        situation: str,
        options: Optional[List[str]] = None
    ) -> Dict:
        """
        Simulate how the user would respond to a situation.
        Used for automated decision making when user is away.
        """
        
        profile_summary = {
            "decision_style": self.twin_profile["decision_patterns"]["speed"],
            "risk_tolerance": self.twin_profile["decision_patterns"]["risk_tolerance"],
            "auto_approve": self.twin_profile["decision_patterns"]["auto_approve"],
            "personality": self.twin_profile["personality"]
        }
        
        prompt = f"""
        Based on this user's behavioral profile, simulate how they would respond.
        
        Profile: {json.dumps(profile_summary, indent=2)}
        
        Situation: {situation}
        Options: {options or ['proceed', 'skip', 'ask_later']}
        
        What would this user most likely choose and why?
        
        JSON:
        {{
            "choice": "most_likely_option",
            "confidence": 0.0,
            "reasoning": "why they would choose this",
            "would_want_notification": true/false
        }}
        """
        
        try:
            response = await self.ai.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            
            result = json.loads(response["content"])
            
            return {"success": True, "simulation": result}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_productivity_insights(self) -> Dict:
        """
        Deep productivity analysis based on twin data.
        """
        
        patterns = self.twin_profile["work_patterns"]
        peak_hours = patterns.get("peak_hours", [])
        app_behaviors = self.twin_profile["app_behaviors"]
        
        # Calculate app usage stats
        app_stats = []
        for app, data in app_behaviors.items():
            app_stats.append({
                "app": app,
                "usage_count": data["usage_count"],
                "most_common_action": max(
                    data["typical_actions"].items(),
                    key=lambda x: x[1]
                )[0] if data["typical_actions"] else "unknown"
            })
        
        app_stats.sort(key=lambda x: x["usage_count"], reverse=True)
        
        prompt = f"""
        Generate deep productivity insights for this user based on their digital twin data.
        
        Work Patterns:
        - Peak productivity hours: {peak_hours}
        - Top apps used: {app_stats[:5]}
        - Total observations: {self.twin_profile['total_observations']}
        
        Provide:
        1. Productivity score (0-100)
        2. Best time to do deep work
        3. Most productive workflow
        4. Time wasters detected
        5. 3 specific improvement suggestions
        6. Predicted best day of week
        
        Respond in friendly Hinglish.
        
        JSON format:
        {{
            "productivity_score": 0,
            "deep_work_time": "time range",
            "best_workflow": "description",
            "time_wasters": [],
            "improvements": [],
            "best_day": "day name",
            "fun_insight": "something interesting about their patterns"
        }}
        """
        
        try:
            response = await self.ai.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            insights = json.loads(response["content"])
            
            return {
                "success": True,
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_twin_status(self) -> Dict:
        """Get digital twin learning status"""
        
        return {
            "user_id": self.user_id,
            "total_observations": self.twin_profile["total_observations"],
            "learning_active": self.is_learning,
            "confidence_threshold": self.confidence_threshold,
            "peak_hours": self.twin_profile["work_patterns"]["peak_hours"],
            "known_apps": list(self.twin_profile["app_behaviors"].keys()),
            "vocabulary_size": len(self.twin_profile["vocabulary"]["common_words"]),
            "hinglish_preference": self.twin_profile["vocabulary"]["hinglish_preference"],
            "twin_maturity": min(
                100,
                self.twin_profile["total_observations"] / 10
            )
        }


class BehaviorTracker:
    """Track real-time user behavior"""
    
    def __init__(self):
        self.session_actions = []
        self.session_start = datetime.now()
    
    def record_action(self, action: str, context: Dict):
        self.session_actions.append({
            "action": action,
            "context": context,
            "time": datetime.now().isoformat()
        })
    
    def get_recent_actions(self, count: int = 10) -> List[Dict]:
        return self.session_actions[-count:]
    
    def get_session_summary(self) -> Dict:
        duration = (datetime.now() - self.session_start).seconds
        
        return {
            "duration_minutes": duration // 60,
            "total_actions": len(self.session_actions),
            "actions_per_minute": len(self.session_actions) / max(duration / 60, 1),
            "most_common": self._get_most_common()
        }
    
    def _get_most_common(self) -> Optional[str]:
        if not self.session_actions:
            return None
        
        action_counts = {}
        for action in self.session_actions:
            a = action["action"]
            action_counts[a] = action_counts.get(a, 0) + 1
        
        return max(action_counts.items(), key=lambda x: x[1])[0]


class PatternAnalyzer:
    """Analyze behavioral patterns"""
    
    def find_sequences(
        self,
        actions: List[str],
        min_length: int = 2,
        min_occurrences: int = 3
    ) -> List[Dict]:
        """Find repeated action sequences"""
        
        sequences = {}
        
        for length in range(min_length, 6):
            for i in range(len(actions) - length + 1):
                seq = tuple(actions[i:i + length])
                sequences[seq] = sequences.get(seq, 0) + 1
        
        repeated = [
            {"sequence": list(seq), "count": count}
            for seq, count in sequences.items()
            if count >= min_occurrences
        ]
        
        repeated.sort(key=lambda x: x["count"], reverse=True)
        return repeated[:10]
    
    def find_time_patterns(
        self,
        timestamped_actions: List[Dict]
    ) -> Dict:
        """Find when certain actions typically happen"""
        
        hour_actions = {}
        
        for item in timestamped_actions:
            hour = datetime.fromisoformat(item["timestamp"]).hour
            action = item["action"]
            
            if hour not in hour_actions:
                hour_actions[hour] = []
            hour_actions[hour].append(action)
        
        return {
            hour: {
                "count": len(actions),
                "most_common": max(
                    set(actions), key=actions.count
                ) if actions else None
            }
            for hour, actions in hour_actions.items()
        }


class ActionPredictor:
    """Predict next user actions"""
    
    def predict_from_sequence(
        self,
        recent_actions: List[str],
        known_sequences: List[Dict]
    ) -> Optional[str]:
        """Predict next action from known sequences"""
        
        if not recent_actions or not known_sequences:
            return None
        
        # Check if recent actions match beginning of known sequence
        for seq_data in known_sequences:
            sequence = seq_data["sequence"]
            
            if len(sequence) < 2:
                continue
            
            # Check if last N actions match first N-1 of sequence
            for n in range(1, len(sequence)):
                if recent_actions[-n:] == sequence[:n]:
                    # Next action would be sequence[n]
                    return sequence[n] if n < len(sequence) else None
        
        return None


class StyleCloner:
    """Clone user's writing/communication style"""
    
    def __init__(self, ai_provider):
        self.ai = ai_provider
        self.style_cache = {}
    
    async def analyze_style(self, text_samples: List[str]) -> Dict:
        """Analyze writing style from samples"""
        
        combined = "\n---\n".join(text_samples[:10])
        
        prompt = f"""
        Analyze the writing style of these text samples:
        
        {combined}
        
        Extract style characteristics:
        
        JSON:
        {{
            "average_sentence_length": 0,
            "vocabulary_complexity": "simple/medium/complex",
            "tone": "formal/casual/friendly/professional",
            "uses_emoji": true/false,
            "uses_hinglish": true/false,
            "punctuation_style": "heavy/light/minimal",
            "characteristic_phrases": [],
            "paragraph_length": "short/medium/long",
            "unique_patterns": []
        }}
        """
        
        try:
            response = await self.ai.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return json.loads(response["content"])
        except:
            return {}
