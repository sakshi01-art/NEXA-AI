from typing import Dict, List, Optional, Tuple
import re
from difflib import SequenceMatcher

class HinglishEngine:
    """
    Advanced Hinglish understanding engine.
    Processes mixed Hindi-English commands with
    semantic understanding and intent extraction.
    """
    
    def __init__(self):
        # Hinglish command vocabulary
        self.command_map = {
            # Open/Launch
            'kholo': 'open',
            'khol': 'open',
            'khol do': 'open',
            'chala': 'launch',
            'chalao': 'launch',
            'start karo': 'launch',
            'start kar': 'launch',
            'open karo': 'open',
            'open kar': 'open',
            'launch karo': 'launch',
            
            # Close/Stop
            'band karo': 'close',
            'band kar': 'close',
            'close karo': 'close',
            'close kar': 'close',
            'rok': 'stop',
            'ruko': 'stop',
            'ruk ja': 'stop',
            'stop karo': 'stop',
            
            # Search/Find
            'dhundo': 'search',
            'dhund': 'search',
            'dhundho': 'search',
            'search karo': 'search',
            'search kar': 'search',
            'khojo': 'find',
            'khoj': 'find',
            
            # Create
            'banao': 'create',
            'bana': 'create',
            'bana do': 'create',
            'create karo': 'create',
            
            # Delete
            'hatao': 'delete',
            'hata': 'delete',
            'delete karo': 'delete',
            'delete kar': 'delete',
            
            # Copy
            'copy karo': 'copy',
            'copy kar': 'copy',
            'nakal karo': 'copy',
            
            # Move
            'move karo': 'move',
            'move kar': 'move',
            'le jao': 'move',
            
            # Show/Display
            'dikhao': 'show',
            'dikha': 'show',
            'bata': 'tell',
            'batao': 'tell',
            'dekho': 'check',
            
            # Run/Execute
            'chalao': 'run',
            'run karo': 'run',
            'execute karo': 'run',
            
            # Download
            'download karo': 'download',
            'download kar': 'download',
            
            # Install
            'install karo': 'install',
            'install kar': 'install',
            
            # Update
            'update karo': 'update',
            
            # Check status
            'status bata': 'get_status',
            'status check': 'get_status',
            'check karo': 'check',
        }
        
        # Common application name mappings
        self.app_aliases = {
            'chrome': ['chrome', 'google', 'browser', 'google chrome'],
            'vscode': ['vs code', 'vscode', 'code', 'visual studio code', 'visual studio'],
            'notepad': ['notepad', 'text editor', 'text file'],
            'explorer': ['explorer', 'file manager', 'files', 'folder'],
            'terminal': ['terminal', 'cmd', 'command prompt', 'powershell', 'bash'],
            'spotify': ['spotify', 'music', 'songs'],
            'discord': ['discord'],
            'slack': ['slack'],
            'zoom': ['zoom', 'meeting'],
            'teams': ['teams', 'microsoft teams'],
            'excel': ['excel', 'spreadsheet'],
            'word': ['word', 'document', 'doc'],
            'powerpoint': ['powerpoint', 'presentation', 'ppt'],
            'github': ['github', 'git hub'],
            'docker': ['docker'],
            'postman': ['postman'],
            'figma': ['figma'],
            'photoshop': ['photoshop', 'ps'],
            'vlc': ['vlc', 'media player', 'video player'],
        }
        
        # Location/folder mappings
        self.location_map = {
            'desktop': ['desktop', 'desktop pe', 'desk pe'],
            'downloads': ['downloads', 'download folder', 'downloaded'],
            'documents': ['documents', 'docs', 'mere documents'],
            'pictures': ['pictures', 'photos', 'images', 'photos folder'],
            'videos': ['videos', 'video folder'],
            'music': ['music', 'songs folder'],
            'temp': ['temp', 'temporary', 'temp folder'],
        }
        
        # Time references
        self.time_map = {
            'aaj': 'today',
            'kal': 'yesterday',
            'parso': 'day before yesterday',
            'agli kal': 'tomorrow',
            'is hafte': 'this week',
            'pichle hafte': 'last week',
            'is mahine': 'this month',
        }
        
        # Reference words (for context resolution)
        self.reference_words = {
            'woh': 'that',
            'wo': 'that',
            'yeh': 'this',
            'ye': 'this',
            'usme': 'in_it',
            'uska': 'its',
            'iske': 'of_this',
            'wala': 'the_one',
            'wali': 'the_one_feminine',
        }
        
        # Confirmation words
        self.affirmative = {'han', 'haan', 'yes', 'ji', 'bilkul', 'zaroor', 'ok', 'okay'}
        self.negative = {'nahi', 'na', 'no', 'mat', 'ruk', 'cancel', 'nope'}
        
        # Sentiment/urgency indicators
        self.urgency_words = {
            'jaldi': 'urgent',
            'abhi': 'immediate',
            'turant': 'immediate',
            'emergency': 'critical',
            'please': 'polite',
            'please karo': 'polite',
            'agar ho sake': 'optional',
        }
    
    def preprocess(self, text: str) -> Dict:
        """
        Full preprocessing pipeline for Hinglish text
        """
        
        original = text
        
        # Normalize
        text = text.lower().strip()
        text = self._normalize_spelling(text)
        
        # Detect language
        language = self._detect_language(text)
        
        # Extract components
        action = self._extract_action(text)
        entities = self._extract_entities(text)
        location = self._extract_location(text)
        time_ref = self._extract_time_reference(text)
        references = self._extract_references(text)
        urgency = self._extract_urgency(text)
        sentiment = self._analyze_sentiment(text)
        
        return {
            'original': original,
            'normalized': text,
            'language': language,
            'action': action,
            'entities': entities,
            'location': location,
            'time_reference': time_ref,
            'references': references,
            'urgency': urgency,
            'sentiment': sentiment,
            'is_question': self._is_question(text),
            'is_confirmation': self._is_confirmation(text),
            'is_cancellation': self._is_cancellation(text),
            'confidence': self._calculate_confidence(action, entities)
        }
    
    def _normalize_spelling(self, text: str) -> str:
        """Fix common Hinglish spelling variations"""
        
        # Common alternate spellings
        normalizations = {
            'kar do': 'karo',
            'kar de': 'karo',
            'kardo': 'karo',
            'mere liye': 'for me',
            'mera': 'my',
            'meri': 'my',
            'bhai': '',  # Remove filler words
            'yaar': '',
            'dost': '',
            'na': '',  # Often used as filler
        }
        
        # Transliteration alternatives
        transliterations = {
            'kro': 'karo',
            'kr': 'kar',
            'ho gya': 'ho gaya',
            'ho gyi': 'ho gayi',
            'nahi': 'nahi',
            'nahin': 'nahi',
        }
        
        for old, new in {**normalizations, **transliterations}.items():
            text = text.replace(old, new)
        
        return text.strip()
    
    def _detect_language(self, text: str) -> str:
        """Detect if text is English, Hindi, or Hinglish"""
        
        # Count Hindi/Hinglish words
        hindi_indicators = set([
            'karo', 'kar', 'kholo', 'khol', 'band', 'dikhao', 'bata',
            'mera', 'meri', 'mere', 'woh', 'yeh', 'aur', 'se', 'mein',
            'ko', 'ka', 'ki', 'ke', 'hai', 'hain', 'tha', 'thi',
            'gaya', 'gayi', 'hoga', 'hogi', 'nahi', 'haan', 'theek',
            'jao', 'aao', 'batao', 'dhundo', 'chalao', 'ruko'
        ])
        
        words = text.split()
        hindi_word_count = sum(1 for word in words if word in hindi_indicators)
        total_words = len(words)
        
        if total_words == 0:
            return 'unknown'
        
        hindi_ratio = hindi_word_count / total_words
        
        if hindi_ratio > 0.7:
            return 'hindi'
        elif hindi_ratio > 0.2:
            return 'hinglish'
        else:
            return 'english'
    
    def _extract_action(self, text: str) -> Optional[Dict]:
        """Extract the main action from text"""
        
        best_match = None
        best_score = 0
        
        for pattern, action in self.command_map.items():
            # Direct match
            if pattern in text:
                return {
                    'command': action,
                    'trigger': pattern,
                    'confidence': 1.0
                }
            
            # Fuzzy match
            score = SequenceMatcher(None, pattern, text).ratio()
            
            if score > best_score and score > 0.7:
                best_score = score
                best_match = {
                    'command': action,
                    'trigger': pattern,
                    'confidence': score
                }
        
        return best_match
    
    def _extract_entities(self, text: str) -> Dict:
        """Extract named entities (apps, files, etc.)"""
        
        entities = {
            'applications': [],
            'files': [],
            'folders': [],
            'urls': [],
            'commands': [],
            'other': []
        }
        
        # Applications
        for app, aliases in self.app_aliases.items():
            for alias in aliases:
                if alias in text:
                    if app not in entities['applications']:
                        entities['applications'].append(app)
        
        # URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        entities['urls'] = urls
        
        # File patterns
        file_pattern = r'[\w\-]+\.\w{2,4}'
        files = re.findall(file_pattern, text)
        entities['files'] = files
        
        # Quote-enclosed entities
        quoted_pattern = r'[\'"]([^\'"]+)[\'"]'
        quoted = re.findall(quoted_pattern, text)
        entities['other'].extend(quoted)
        
        return entities
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract file system location"""
        
        for location, indicators in self.location_map.items():
            for indicator in indicators:
                if indicator in text:
                    return location
        
        # Extract explicit paths
        path_pattern = r'[A-Za-z]:\\[\w\\]+'
        paths = re.findall(path_pattern, text)
        
        if paths:
            return paths[0]
        
        return None
    
    def _extract_time_reference(self, text: str) -> Optional[str]:
        """Extract time references from text"""
        
        for hindi_time, english_time in self.time_map.items():
            if hindi_time in text:
                return english_time
        
        # Time patterns
        time_pattern = r'(\d{1,2})\s*(baje|bajkar|am|pm|:00)'
        times = re.findall(time_pattern, text)
        
        if times:
            return f"{times[0][0]} {times[0][1]}"
        
        return None
    
    def _extract_references(self, text: str) -> Dict:
        """Extract contextual references (this, that, it, etc.)"""
        
        found_references = {}
        
        for ref, meaning in self.reference_words.items():
            if ref in text.split():
                found_references[ref] = meaning
        
        return found_references
    
    def _extract_urgency(self, text: str) -> str:
        """Extract urgency level"""
        
        for word, urgency in self.urgency_words.items():
            if word in text:
                return urgency
        
        return 'normal'
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        
        positive = ['acha', 'accha', 'badiya', 'sahi', 'perfect', 'great', 'good', 'thanks', 'shukriya']
        negative = ['bura', 'galat', 'problem', 'issue', 'error', 'nahi chal raha']
        frustrated = ['baar baar', 'kyun nahi', 'dobara', 'phir se', 'again']
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in frustrated):
            return 'frustrated'
        elif any(word in text_lower for word in positive):
            return 'positive'
        elif any(word in text_lower for word in negative):
            return 'negative'
        
        return 'neutral'
    
    def _is_question(self, text: str) -> bool:
        """Check if the text is a question"""
        
        question_indicators = [
            '?', 'kya hai', 'kya hua', 'kab', 'kahan', 'kaun', 'kaise',
            'kyun', 'kitna', 'kitne', 'what', 'when', 'where', 'who',
            'how', 'why', 'which', 'bata do', 'batao'
        ]
        
        return any(indicator in text for indicator in question_indicators)
    
    def _is_confirmation(self, text: str) -> bool:
        """Check if response is a confirmation"""
        
        words = set(text.split())
        return bool(words & self.affirmative)
    
    def _is_cancellation(self, text: str) -> bool:
        """Check if response is a cancellation"""
        
        words = set(text.split())
        return bool(words & self.negative)
    
    def _calculate_confidence(
        self,
        action: Optional[Dict],
        entities: Dict
    ) -> float:
        """Calculate overall understanding confidence"""
        
        score = 0.5  # Base score
        
        if action:
            score += action.get('confidence', 0) * 0.3
        
        total_entities = sum(len(v) for v in entities.values())
        
        if total_entities > 0:
            score += min(0.2, total_entities * 0.05)
        
        return min(1.0, score)
    
    def resolve_context(
        self,
        current_text: str,
        previous_context: Dict
    ) -> Dict:
        """
        Resolve contextual references using previous context.
        
        Example:
        Previous: "Chrome kholo"
        Current: "Usme YouTube kholo"
        Result: "Chrome mein YouTube kholo"
        """
        
        processed = self.preprocess(current_text)
        references = processed.get('references', {})
        
        if not references:
            return processed
        
        # Resolve 'it', 'this', 'that' etc.
        resolved_entities = processed.get('entities', {})
        
        if 'usme' in references or 'iske' in references:
            # "in it" - use previous app
            prev_apps = previous_context.get('entities', {}).get('applications', [])
            if prev_apps:
                resolved_entities['applications'] = prev_apps + resolved_entities.get('applications', [])
        
        if 'woh' in references or 'wo' in references:
            # "that" - use previous subject
            prev_entities = previous_context.get('entities', {})
            for key, values in prev_entities.items():
                if values and not resolved_entities.get(key):
                    resolved_entities[key] = values
        
        processed['entities'] = resolved_entities
        processed['context_resolved'] = True
        
        return processed
    
    def generate_response(
        self,
        intent: str,
        result: Dict,
        language: str = 'hinglish'
    ) -> str:
        """Generate natural Hinglish response"""
        
        success = result.get('success', False)
        
        response_templates = {
            'hinglish': {
                'open_success': [
                    "Haan, {app} open ho gaya!",
                    "Done! {app} chalu ho gaya.",
                    "Bilkul, {app} open kar diya.",
                    "{app} ready hai!",
                ],
                'open_failure': [
                    "{app} nahi khula. Shayad install nahi hai.",
                    "Sorry, {app} open karne mein problem aaya.",
                    "{app} nahi mil raha. PATH check karo.",
                ],
                'search_success': [
                    "{count} results mile hain.",
                    "Search complete! {count} cheezein mili.",
                    "Le lo, {count} results hain.",
                ],
                'generic_success': [
                    "Ho gaya!",
                    "Done kar diya!",
                    "Kaam ho gaya.",
                    "Sab theek hai!",
                ],
                'generic_failure': [
                    "Kuch problem aaya, dobara try karo.",
                    "Nahi ho paya. Error aaya.",
                    "Thoda problem hai, dekh raha hoon.",
                ],
                'confirmation_needed': [
                    "Kya main ye karna chahiye? Confirm karo.",
                    "Ek baar confirm karo - {action} karna hai?",
                    "Sure? Ye {action} hoga.",
                ],
                'thinking': [
                    "Ek second, soch raha hoon...",
                    "Dekh raha hoon...",
                    "Process ho raha hai...",
                ],
            },
            'english': {
                'open_success': ["Done! {app} is open.", "{app} launched successfully."],
                'open_failure': ["Could not open {app}. Check if it's installed."],
                'generic_success': ["Done!", "Completed successfully."],
                'generic_failure': ["Something went wrong. Please try again."],
            }
        }
        
        templates = response_templates.get(language, response_templates['hinglish'])
        
        import random
        
        if success:
            key = f"{intent}_success" if f"{intent}_success" in templates else 'generic_success'
        else:
            key = f"{intent}_failure" if f"{intent}_failure" in templates else 'generic_failure'
        
        options = templates.get(key, templates.get('generic_success', ['Done!']))
        template = random.choice(options)
        
        # Fill template variables
        template = template.format(
            app=result.get('app', result.get('application', '')),
            count=result.get('count', 0),
            action=intent,
            **result
        )
        
        return template
