import asyncio
import threading
import time
try:
    import pyautogui
except ImportError:
    pyautogui = None
try:
    import pyperclip
except ImportError:
    pyperclip = None
from typing import Dict, Optional, Callable, List
import re

class VoiceKeyboard:
    """
    Type anywhere using voice in any language.
    
    Features:
    - Type in any active application using voice
    - Supports English, Hindi, Hinglish
    - Voice commands for editing
    - Punctuation by voice
    - Correction commands
    - Formatting commands
    - Works in any text field
    
    Commands:
    "Type: Hello World"
    "Likho: Mera naam Rahul hai"
    "Delete last word"
    "Pichla word delete karo"
    "Undo karo"
    "Select all"
    "Copy karo"
    "Paste karo"
    "New line"
    "Capital A"
    "Press Enter"
    """
    
    def __init__(self, stt_provider, ai_provider, notification_callback: Callable):
        self.stt = stt_provider
        self.ai = ai_provider
        self.notify = notification_callback
        
        self.is_active = False
        self.mode = 'command'
        self.typed_history: List[str] = []
        self.current_word_buffer = ''
        
        # Punctuation voice commands
        self.punctuation_map = {
            'full stop': '.',
            'period': '.',
            'dot': '.',
            'comma': ',',
            'question mark': '?',
            'exclamation': '!',
            'exclamation mark': '!',
            'colon': ':',
            'semicolon': ';',
            'open bracket': '(',
            'close bracket': ')',
            'open brace': '{',
            'close brace': '}',
            'slash': '/',
            'backslash': '\\',
            'at sign': '@',
            'hash': '#',
            'dollar': '$',
            'percent': '%',
            'ampersand': '&',
            'asterisk': '*',
            'hyphen': '-',
            'dash': '-',
            'underscore': '_',
            'equals': '=',
            'plus': '+',
            'tilde': '~',
            'double quote': '"',
            'single quote': "'",
            
            # Hindi punctuation
            'poorn viram': '।',
            'viraam': ',',
            'prashn chinh': '?',
        }
        
        # Editing commands
        self.edit_commands = {
            'delete': self._delete_char,
            'backspace': self._delete_char,
            'delete word': self._delete_word,
            'pichla word hatao': self._delete_word,
            'pichla word delete': self._delete_word,
            'undo': self._undo,
            'undo karo': self._undo,
            'redo': self._redo,
            'select all': self._select_all,
            'sab select karo': self._select_all,
            'copy': self._copy,
            'copy karo': self._copy,
            'paste': self._paste,
            'paste karo': self._paste,
            'cut': self._cut,
            'cut karo': self._cut,
            'new line': self._new_line,
            'nayi line': self._new_line,
            'enter': self._press_enter,
            'enter dabao': self._press_enter,
            'tab': self._press_tab,
            'space': self._press_space,
            'clear line': self._clear_line,
        }
    
    async def activate(self) -> Dict:
        """Activate voice keyboard mode"""
        
        self.is_active = True
        self.mode = 'typing'
        
        await self.notify({
            'type': 'info',
            'title': '⌨️ Voice Keyboard Active',
            'message': 'Ab voice se type karo! "Stop typing" bol ke band karo.',
            'priority': 'medium'
        })
        
        return {
            'success': True,
            'message': 'Voice keyboard active! Ab bolke type karo.'
        }
    
    async def deactivate(self) -> Dict:
        """Deactivate voice keyboard"""
        
        self.is_active = False
        self.mode = 'command'
        
        return {
            'success': True,
            'message': 'Voice keyboard band ho gaya.'
        }
    
    async def process_voice_input(self, text: str) -> Dict:
        """Process voice input for typing"""
        
        if not self.is_active:
            return {'success': False, 'error': 'Voice keyboard not active'}
        
        text_lower = text.lower().strip()
        
        # Check for deactivation
        stop_commands = ['stop typing', 'band karo', 'keyboard band', 'stop keyboard']
        if any(cmd in text_lower for cmd in stop_commands):
            return await self.deactivate()
        
        # Check for editing commands
        for cmd_pattern, handler in self.edit_commands.items():
            if cmd_pattern in text_lower:
                handler()
                return {
                    'success': True,
                    'action': cmd_pattern,
                    'typed': False
                }
        
        # Check for punctuation
        for punct_name, punct_char in self.punctuation_map.items():
            if punct_name in text_lower:
                pyautogui.write(punct_char)
                return {
                    'success': True,
                    'typed': punct_char
                }
        
        # Check for "type:" or "likho:" prefix
        type_prefixes = ['type:', 'type ', 'likho:', 'likho ', 'write:', 'write ']
        
        for prefix in type_prefixes:
            if text_lower.startswith(prefix):
                to_type = text[len(prefix):].strip()
                await self._type_text(to_type)
                return {
                    'success': True,
                    'typed': to_type
                }
        
        # Check for special formatting
        if 'capital' in text_lower:
            # "Capital A" → type uppercase A
            match = re.search(r'capital\s+([a-z])', text_lower)
            if match:
                pyautogui.write(match.group(1).upper())
                return {'success': True, 'typed': match.group(1).upper()}
        
        # Mode-based processing
        if self.mode == 'typing':
            # In typing mode, type everything
            await self._type_text(text)
            return {
                'success': True,
                'typed': text,
                'mode': 'typing'
            }
        
        return {'success': True, 'no_action': True}
    
    async def _type_text(self, text: str):
        """Type text into active application"""
        
        # Store in history
        self.typed_history.append(text)
        
        # Use clipboard for better Unicode support (Hindi, etc.)
        original_clipboard = pyperclip.paste()
        
        try:
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            await asyncio.sleep(0.1)
        finally:
            # Small delay then restore clipboard
            await asyncio.sleep(0.5)
            pyperclip.copy(original_clipboard)
    
    def _delete_char(self):
        """Delete last character"""
        pyautogui.press('backspace')
    
    def _delete_word(self):
        """Delete last word"""
        pyautogui.hotkey('ctrl', 'backspace')
    
    def _undo(self):
        """Undo last action"""
        pyautogui.hotkey('ctrl', 'z')
    
    def _redo(self):
        """Redo action"""
        pyautogui.hotkey('ctrl', 'y')
    
    def _select_all(self):
        """Select all text"""
        pyautogui.hotkey('ctrl', 'a')
    
    def _copy(self):
        """Copy selected text"""
        pyautogui.hotkey('ctrl', 'c')
    
    def _paste(self):
        """Paste from clipboard"""
        pyautogui.hotkey('ctrl', 'v')
    
    def _cut(self):
        """Cut selected text"""
        pyautogui.hotkey('ctrl', 'x')
    
    def _new_line(self):
        """Insert new line"""
        pyautogui.press('enter')
    
    def _press_enter(self):
        """Press Enter"""
        pyautogui.press('enter')
    
    def _press_tab(self):
        """Press Tab"""
        pyautogui.press('tab')
    
    def _press_space(self):
        """Press Space"""
        pyautogui.press('space')
    
    def _clear_line(self):
        """Clear current line"""
        pyautogui.hotkey('home')
        pyautogui.hotkey('shift', 'end')
        pyautogui.press('delete')
    
    async def dictate_document(
        self,
        duration: int = 60,
        output_file: Optional[str] = None
    ) -> Dict:
        """
        Dictate a complete document by voice.
        Records for specified duration and creates text file.
        """
        
        await self.activate()
        
        await self.notify({
            'type': 'info',
            'title': '🎤 Dictation Started',
            'message': f'{duration} seconds mein document dictate karo.',
            'priority': 'medium'
        })
        
        # Collect typed content
        dictated_content = []
        start_time = time.time()
        
        # This would integrate with continuous STT
        # For now, simulate
        await asyncio.sleep(duration)
        
        await self.deactivate()
        
        full_text = '\n'.join(dictated_content)
        
        if output_file and full_text:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_text)
        
        return {
            'success': True,
            'content': full_text,
            'word_count': len(full_text.split()),
            'output_file': output_file
        }
