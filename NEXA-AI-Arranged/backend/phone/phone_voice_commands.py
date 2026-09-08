from typing import Dict, List
import re

PHONE_VOICE_COMMANDS = {
    # Connection
    r'phone (connect|jodo|connect karo)': 'scan_devices',
    r'wireless (connect|connection)': 'enable_wifi_adb',

    # Screen
    r'phone (ka |ki )?(screen |display )?(mirror|dikhao|show)': 'start_mirror',
    r'(mirror|mirroring) (band karo|stop)': 'stop_mirror',
    r'phone (ka )?screenshot (le|lo|lao)': 'take_screenshot',
    r'phone (ki )?screen record': 'start_recording',

    # Navigation
    r'phone (pe |mein )?(home|ghar) (button|jao)': 'press_home',
    r'phone (pe )?back (jao|karo)': 'press_back',
    r'recent (apps|kaam)': 'press_recents',
    r'phone (lock|band) karo': 'lock_screen',
    r'phone (unlock|kholo)': 'unlock_screen',

    # Battery
    r'phone (ki )?battery (kitni|check|status|bata)': 'get_battery',

    # Apps
    r'phone (pe )?(.+) (app |)(kholo|open karo|chala)': 'open_app',
    r'phone (pe )?(.+) (band|close) karo': 'close_app',
    r'phone (ke |pe )?apps (list|dikhao|bata)': 'list_apps',

    # Files
    r'phone (se |ki )?(.+) (file |photo |image )?(le aao|download|transfer)': 'pull_file',
    r'phone (pe |mein )(.+) (bhejo|send|transfer)': 'push_file',
    r'phone (ki )?latest (photo|image|pic) (le aao|dikhao)': 'get_latest_photo',

    # Communication
    r'(.+) (ko |pe )?message (bhejo|send|kar)': 'send_sms',
    r'(.+) (ko )?call (karo|lagao|karne)': 'make_call',
    r'call (band|end|khatam) karo': 'end_call',
    r'phone (ke )?messages (dikhao|bata|check)': 'get_messages',

    # Notifications
    r'phone (ki )?notifications (dikhao|bata|check)': 'get_notifications',
    r'(saari|all) notifications (hatao|clear|dismiss)': 'dismiss_all_notifications',

    # Media
    r'phone (pe |mein )?(music |gaana )?(play|chala)': 'media_play',
    r'phone (pe )?pause (karo|kar)': 'media_pause',
    r'agla (gaana|song|track)': 'media_next',
    r'pichla (gaana|song|track)': 'media_previous',
    r'phone (ki )?volume (badhao|up|zyada)': 'volume_up',
    r'phone (ki )?volume (ghataao|down|kam)': 'volume_down',

    # Settings
    r'phone (ka )?wifi (on|enable|chalu) karo': 'enable_wifi',
    r'phone (ka )?wifi (off|disable|band) karo': 'disable_wifi',
    r'phone (ka )?mobile data (on|enable)': 'enable_data',
    r'phone (ki )?brightness (badhao|zyada)': 'increase_brightness',
    r'phone (ki )?brightness (ghataao|kam)': 'decrease_brightness',

    # Storage
    r'phone (ki )?storage (check|bata|kitni)': 'get_storage',
    r'phone (ki )?contacts (dikhao|bata|list)': 'get_contacts',
    r'phone (ki )?location (bata|check|kahan)': 'get_location',

    # System
    r'phone (restart|reboot) karo': 'reboot_device',
    r'phone (ki )?info (bata|dikhao)': 'get_device_info',
}


def match_phone_command(user_input: str) -> Dict:
    """Match user input to phone command"""

    text = user_input.lower().strip()

    for pattern, command in PHONE_VOICE_COMMANDS.items():
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            # Extract entities from match groups
            groups = match.groups()
            entities = [g for g in groups if g and len(g.strip()) > 1]

            return {
                'matched': True,
                'command': command,
                'entities': entities,
                'original': user_input,
                'pattern': pattern
            }

    return {'matched': False}
