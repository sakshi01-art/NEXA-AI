from typing import Dict, Optional
import random
from datetime import datetime

class NexaPersona:
    """
    NEXA's dynamic personality system.
    Adapts tone, humor, and style based on:
    - Time of day
    - User mood
    - Task complexity
    - Conversation history
    - User preferences
    """
    
    MOODS = {
        'professional': {
            'greetings': [
                "Ready to assist.",
                "What can I help you with?",
                "At your service.",
            ],
            'confirmations': [
                "Task completed successfully.",
                "Done. Anything else?",
                "Executed without errors.",
            ],
            'errors': [
                "An error occurred. Here's what happened:",
                "Task failed. Diagnostic information:",
                "Unable to complete. Reason:",
            ],
            'thinking': [
                "Processing your request...",
                "Analyzing...",
                "Executing plan...",
            ]
        },
        'friendly': {
            'greetings': [
                "Hey! Kya haal hai? Kya kar sakta hoon aapke liye?",
                "Arre, aap aa gaye! Bolo, kya chahiye?",
                "Namaste! Kuch help chahiye?",
                "Hey there! Ready to help!",
            ],
            'confirmations': [
                "Ho gaya! Aur kuch?",
                "Done kar diya! Ekdum fresh!",
                "Perfect! Sab theek hai.",
                "Bilkul ho gaya!",
                "Easy peasy! Done.",
            ],
            'errors': [
                "Oops! Kuch gadbad ho gayi. Dekho:",
                "Arre yaar, kuch problem aaya:",
                "Hmm, nahi hua. Reason ye hai:",
                "Sorry yaar, error aaya:",
            ],
            'thinking': [
                "Ek second, soch raha hoon...",
                "Haan haan, dekh raha hoon...",
                "Processing karo, wait karo...",
                "Thoda sa time do...",
            ],
            'jokes': [
                "Pata hai, main ek AI hoon jo Hinglish samajhta hai. Matlab main bohot multilingual hoon! 😄",
                "Task itna fast complete kiya ki mujhe khud surprise ho gaya!",
                "Aapka command sun ke mujhe laga - 'Ye toh easy hai!' And it was! 🎉",
            ]
        },
        'casual': {
            'greetings': [
                "Yo! Kya scene hai?",
                "Bhai, bolo! Kya karna hai?",
                "Sup! Ready hoon.",
            ],
            'confirmations': [
                "Sahi! Ho gaya.",
                "Done bro!",
                "Khatam! Next?",
                "EZ! Done.",
            ],
            'errors': [
                "Bhai, kuch toh gadbad hai:",
                "Nahi hua yaar:",
                "Error aa gaya, dekho:",
            ],
            'thinking': [
                "Soch raha hoon...",
                "Ek sec...",
                "Processing...",
            ]
        }
    }
    
    def __init__(self, default_mood: str = 'friendly'):
        self.current_mood = default_mood
        self.user_name = None
        self.interaction_count = 0
        self.last_interaction = None
        self.user_sentiment_history = []
        self.humor_level = 0.3  # 0 to 1
        self.formality_level = 0.5  # 0 to 1
    
    def adapt_to_user(self, user_input: str, detected_sentiment: str):
        """Adapt persona based on user's style"""
        
        self.interaction_count += 1
        self.user_sentiment_history.append(detected_sentiment)
        
        # Keep last 10 sentiments
        if len(self.user_sentiment_history) > 10:
            self.user_sentiment_history = self.user_sentiment_history[-10:]
        
        # Detect user's formality from their language
        casual_words = {'bhai', 'yaar', 'dost', 'bro', 'sis', 'yo', 'sup'}
        formal_words = {'please', 'kindly', 'would you', 'could you'}
        
        words = set(user_input.lower().split())
        
        if words & casual_words:
            self.formality_level = max(0, self.formality_level - 0.1)
        elif words & formal_words:
            self.formality_level = min(1, self.formality_level + 0.1)
        
        # Update mood based on formality
        if self.formality_level > 0.7:
            self.current_mood = 'professional'
        elif self.formality_level > 0.3:
            self.current_mood = 'friendly'
        else:
            self.current_mood = 'casual'
        
        # Handle frustrated users
        if self.user_sentiment_history.count('frustrated') >= 3:
            self.current_mood = 'professional'  # Switch to professional when user is frustrated
    
    def get_greeting(self) -> str:
        """Get contextual greeting"""
        
        hour = datetime.now().hour
        mood_greetings = self.MOODS[self.current_mood]['greetings']
        
        # Time-based greetings
        if self.interaction_count == 0:
            # First interaction
            if 5 <= hour < 12:
                return "Good morning! Main NEXA hoon. Aapka intelligent desktop assistant. Kaise help kar sakta hoon?"
            elif 12 <= hour < 17:
                return "Good afternoon! NEXA ready hai. Bolo, kya karna hai?"
            elif 17 <= hour < 22:
                return "Good evening! NEXA here. Aaj kya karna hai?"
            else:
                return "Raat ko bhi kaam? NEXA always available hai. Bolo kya chahiye!"
        
        # Regular greetings
        return random.choice(mood_greetings)
    
    def get_confirmation(self, task: Optional[str] = None) -> str:
        """Get task completion confirmation"""
        
        confirmations = self.MOODS[self.current_mood]['confirmations']
        base = random.choice(confirmations)
        
        # Add task-specific info
        if task and random.random() > 0.5:
            if self.current_mood == 'friendly':
                return f"{base} '{task}' wala kaam ho gaya!"
            elif self.current_mood == 'casual':
                return f"{base} '{task}' done!"
        
        return base
    
    def get_error_message(self, error: str) -> str:
        """Get humanized error message"""
        
        errors = self.MOODS[self.current_mood]['errors']
        prefix = random.choice(errors)
        
        # Humanize technical errors
        humanized = self._humanize_error(error)
        
        return f"{prefix} {humanized}"
    
    def get_thinking_message(self) -> str:
        """Get processing/thinking message"""
        
        thinking = self.MOODS[self.current_mood]['thinking']
        return random.choice(thinking)
    
    def _humanize_error(self, error: str) -> str:
        """Convert technical error to human-readable"""
        
        error_map = {
            'ENOENT': 'File ya folder nahi mila. Check karo path sahi hai.',
            'EACCES': 'Permission denied. Administrator rights chahiye.',
            'ETIMEDOUT': 'Connection timeout. Internet check karo.',
            'ECONNREFUSED': 'Connection refused. Service running hai?',
            'FileNotFoundError': 'File nahi mili. Path check karo.',
            'PermissionError': 'Permission nahi hai. Admin se check karo.',
            'ModuleNotFoundError': 'Package install nahi hai. pip install karo.',
            'ConnectionError': 'Network problem. Internet connection check karo.',
            'TimeoutError': 'Bahut time lag raha hai. Dobara try karo.',
        }
        
        for tech_term, human_msg in error_map.items():
            if tech_term in error:
                return human_msg
        
        # Generic humanization
        if len(error) > 100:
            return f"Technical error: {error[:100]}..."
        
        return error
    
    def add_personality(self, response: str) -> str:
        """Add personality touches to a response"""
        
        if self.current_mood == 'friendly' and random.random() < self.humor_level:
            # Sometimes add a fun fact or emoji
            emojis = ['✨', '🚀', '💪', '🎯', '⚡', '🔥', '✅']
            response = f"{response} {random.choice(emojis)}"
        
        return response
    
    def generate_proactive_message(self, context: Dict) -> Optional[str]:
        """Generate proactive suggestions"""
        
        if self.current_mood == 'professional':
            return None  # Professional mode: no proactive suggestions
        
        suggestions = []
        
        # If user hasn't interacted in a while
        if self.last_interaction:
            from datetime import timedelta
            if datetime.now() - self.last_interaction > timedelta(hours=2):
                suggestions.append(
                    "Kafi time ho gaya! Kya kuch aur karna hai? 🤔"
                )
        
        # Based on system state
        if context.get('cpu', 0) > 80:
            suggestions.append(
                "Ek kaam ki baat - CPU load zyada hai. Kuch heavy processes band karein? 💻"
            )
        
        return random.choice(suggestions) if suggestions else None
    
    def set_user_name(self, name: str):
        """Set user's name for personalized responses"""
        self.user_name = name
    
    def personalize(self, message: str) -> str:
        """Add user's name to message if available"""
        
        if self.user_name and random.random() < 0.2:  # 20% chance
            return f"{self.user_name}, {message}"
        
        return message
    
    def get_status_report(self) -> Dict:
        """Get persona status"""
        
        return {
            'current_mood': self.current_mood,
            'interaction_count': self.interaction_count,
            'formality_level': self.formality_level,
            'humor_level': self.humor_level,
            'user_name': self.user_name,
            'recent_sentiments': self.user_sentiment_history[-5:]
        }
