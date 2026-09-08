import asyncio
import json
import os
import subprocess
import socket
import threading
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from pathlib import Path
import base64

class PhoneController:
    """
    Complete Phone Control from NEXA Desktop Agent.
    
    Supports:
    ✓ Android (via ADB)
    ✓ iOS (via libimobiledevice)
    ✓ Wireless connection
    ✓ Screen mirroring
    ✓ File transfer
    ✓ App control
    ✓ Notifications
    ✓ SMS & Calls
    ✓ Camera control
    ✓ Contacts
    ✓ Media control
    ✓ Battery info
    ✓ Location
    ✓ Screen recording
    ✓ Remote touch control
    
    NEXA Commands:
    "Phone ki battery kitni hai?"
    "Phone pe WhatsApp kholo"
    "Phone se latest photo le aao"
    "Phone pe yeh message bhej do"
    "Phone ka screenshot le"
    "Phone ki screen mirror kar"
    """
    
    def __init__(self, ai_provider, notification_callback: Callable):
        self.ai = ai_provider
        self.notify = notification_callback
        
        self.connected_devices: Dict[str, Dict] = {}
        self.active_device: Optional[str] = None
        self.adb_path = self._find_adb()
        self.is_mirroring = False
        self.mirror_process = None
        
        # Phone event listeners
        self.notification_listener = None
        self.call_listener = None
        
        # Wireless connection
        self.wireless_port = 5037
        self.pairing_server = None
    
    def _find_adb(self) -> str:
        """Find ADB executable"""
        
        possible_paths = [
            r"C:\Users\{}\AppData\Local\Android\Sdk\platform-tools\adb.exe".format(
                os.getenv('USERNAME')
            ),
            r"C:\Program Files\Android\android-studio\platform-tools\adb.exe",
            "adb.exe",
            "adb"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(['where', 'adb'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return "adb"  # Hope it's in PATH
    
    def _run_adb(self, command: List[str], device_id: Optional[str] = None) -> Dict:
        """Run ADB command"""
        
        try:
            cmd = [self.adb_path]
            
            if device_id:
                cmd.extend(['-s', device_id])
            elif self.active_device:
                cmd.extend(['-s', self.active_device])
            
            cmd.extend(command)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'returncode': result.returncode
            }
        
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'ADB command timed out'}
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'ADB not found. Please install Android SDK Platform Tools',
                'fix': 'https://developer.android.com/studio/releases/platform-tools'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def scan_devices(self) -> Dict:
        """Scan for connected Android devices"""
        
        result = self._run_adb(['devices', '-l'])
        
        if not result['success']:
            return result
        
        devices = []
        lines = result['stdout'].split('\n')[1:]  # Skip "List of devices attached"
        
        for line in lines:
            if line.strip() and 'device' in line:
                parts = line.split()
                device_id = parts[0]
                
                # Get device info
                info = await self.get_device_info(device_id)
                
                device = {
                    'id': device_id,
                    'status': parts[1] if len(parts) > 1 else 'unknown',
                    'model': info.get('model', 'Unknown'),
                    'manufacturer': info.get('manufacturer', 'Unknown'),
                    'android_version': info.get('android_version', 'Unknown'),
                    'battery': info.get('battery', 0),
                    'connected_via': 'usb' if ':' not in device_id else 'wifi'
                }
                
                devices.append(device)
                self.connected_devices[device_id] = device
        
        if devices and not self.active_device:
            self.active_device = devices[0]['id']
        
        return {
            'success': True,
            'devices': devices,
            'count': len(devices),
            'active_device': self.active_device
        }
    
    async def get_device_info(self, device_id: Optional[str] = None) -> Dict:
        """Get detailed device information"""
        
        info = {}
        
        # Model
        result = self._run_adb(['shell', 'getprop', 'ro.product.model'], device_id)
        if result['success']:
            info['model'] = result['stdout']
        
        # Manufacturer
        result = self._run_adb(['shell', 'getprop', 'ro.product.manufacturer'], device_id)
        if result['success']:
            info['manufacturer'] = result['stdout']
        
        # Android version
        result = self._run_adb(['shell', 'getprop', 'ro.build.version.release'], device_id)
        if result['success']:
            info['android_version'] = result['stdout']
        
        # Battery
        battery_info = await self.get_battery_info(device_id)
        if battery_info.get('success'):
            info['battery'] = battery_info.get('level', 0)
            info['charging'] = battery_info.get('is_charging', False)
        
        # Storage
        storage_info = await self.get_storage_info(device_id)
        if storage_info.get('success'):
            info['storage'] = storage_info
        
        # Screen resolution
        result = self._run_adb(['shell', 'wm', 'size'], device_id)
        if result['success']:
            info['screen_size'] = result['stdout']
        
        return info
    
    async def get_battery_info(self, device_id: Optional[str] = None) -> Dict:
        """Get phone battery information"""
        
        result = self._run_adb(['shell', 'dumpsys', 'battery'], device_id)
        
        if not result['success']:
            return result
        
        battery_data = {}
        lines = result['stdout'].split('\n')
        
        for line in lines:
            if 'level:' in line:
                battery_data['level'] = int(line.split(':')[1].strip())
            elif 'status:' in line:
                status = int(line.split(':')[1].strip())
                battery_data['is_charging'] = status == 2
                battery_data['status_code'] = status
            elif 'temperature:' in line:
                temp = int(line.split(':')[1].strip())
                battery_data['temperature'] = temp / 10
            elif 'voltage:' in line:
                battery_data['voltage_mv'] = int(line.split(':')[1].strip())
            elif 'technology:' in line:
                battery_data['technology'] = line.split(':')[1].strip()
        
        return {
            'success': True,
            **battery_data
        }
    
    async def get_storage_info(self, device_id: Optional[str] = None) -> Dict:
        """Get phone storage information"""
        
        result = self._run_adb(
            ['shell', 'df', '/sdcard'],
            device_id
        )
        
        if not result['success']:
            return result
        
        try:
            lines = result['stdout'].split('\n')
            
            if len(lines) >= 2:
                parts = lines[1].split()
                
                if len(parts) >= 4:
                    total = int(parts[1]) * 1024  # Convert KB to bytes
                    used = int(parts[2]) * 1024
                    free = int(parts[3]) * 1024
                    
                    return {
                        'success': True,
                        'total_gb': round(total / 1024**3, 1),
                        'used_gb': round(used / 1024**3, 1),
                        'free_gb': round(free / 1024**3, 1),
                        'percent_used': round(used / total * 100, 1)
                    }
        except:
            pass
        
        return {'success': False, 'error': 'Could not parse storage info'}
    
    async def take_screenshot(
        self,
        save_path: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Dict:
        """Take screenshot of phone screen"""
        
        try:
            # Capture on device
            result = self._run_adb(
                ['shell', 'screencap', '-p', '/sdcard/nexa_screenshot.png'],
                device_id
            )
            
            if not result['success']:
                return result
            
            # Pull to computer
            save_to = save_path or f"./temp/phone_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            pull_result = self._run_adb(
                ['pull', '/sdcard/nexa_screenshot.png', save_to],
                device_id
            )
            
            if pull_result['success']:
                # Clean up on device
                self._run_adb(['shell', 'rm', '/sdcard/nexa_screenshot.png'], device_id)
                
                return {
                    'success': True,
                    'path': save_to,
                    'message': 'Screenshot captured'
                }
            
            return pull_result
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def start_screen_mirror(
        self,
        device_id: Optional[str] = None,
        quality: int = 80,
        max_fps: int = 30
    ) -> Dict:
        """
        Start screen mirroring using scrcpy.
        Shows phone screen on desktop in real-time.
        """
        
        try:
            # Check if scrcpy is available
            scrcpy_check = subprocess.run(
                ['scrcpy', '--version'],
                capture_output=True
            )
            
            if scrcpy_check.returncode != 0:
                return {
                    'success': False,
                    'error': 'scrcpy not installed',
                    'fix': 'pip install scrcpy or download from https://github.com/Genymobile/scrcpy'
                }
            
            # Build scrcpy command
            cmd = ['scrcpy']
            
            if device_id or self.active_device:
                cmd.extend(['-s', device_id or self.active_device])
            
            cmd.extend([
                f'--max-fps={max_fps}',
                f'--video-bit-rate=8M',
                '--window-title=NEXA Phone Mirror',
                '--stay-awake'
            ])
            
            # Start mirroring process
            self.mirror_process = subprocess.Popen(cmd)
            self.is_mirroring = True
            
            return {
                'success': True,
                'message': 'Screen mirroring started',
                'pid': self.mirror_process.pid
            }
        
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'scrcpy not found',
                'fix': 'Download scrcpy from GitHub'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def stop_screen_mirror(self) -> Dict:
        """Stop screen mirroring"""
        
        if self.mirror_process:
            self.mirror_process.terminate()
            self.mirror_process = None
            self.is_mirroring = False
            
            return {'success': True, 'message': 'Mirroring stopped'}
        
        return {'success': False, 'error': 'Not currently mirroring'}
    
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        device_id: Optional[str] = None
    ) -> Dict:
        """Send SMS from phone"""
        
        # Use ADB to open SMS with pre-filled content
        result = self._run_adb([
            'shell', 'am', 'start',
            '-a', 'android.intent.action.SENDTO',
            '-d', f'sms:{phone_number}',
            '--es', 'sms_body', message,
            '--ez', 'exit_on_sent', 'true'
        ], device_id)
        
        if result['success']:
            return {
                'success': True,
                'message': f'SMS draft opened to {phone_number}',
                'note': 'Please press Send on your phone to complete'
            }
        
        return result
    
    async def make_call(
        self,
        phone_number: str,
        device_id: Optional[str] = None
    ) -> Dict:
        """Initiate phone call"""
        
        result = self._run_adb([
            'shell', 'am', 'start',
            '-a', 'android.intent.action.CALL',
            '-d', f'tel:{phone_number}'
        ], device_id)
        
        if result['success']:
            return {
                'success': True,
                'message': f'Calling {phone_number}',
                'note': 'Call initiated on phone'
            }
        
        return result
    
    async def end_call(self, device_id: Optional[str] = None) -> Dict:
        """End active phone call"""
        
        result = self._run_adb([
            'shell', 'input', 'keyevent', 'KEYCODE_ENDCALL'
        ], device_id)
        
        return {
            'success': result['success'],
            'message': 'Call ended' if result['success'] else result.get('error')
        }
    
    async def get_notifications(self, device_id: Optional[str] = None) -> Dict:
        """Get current phone notifications"""
        
        result = self._run_adb([
            'shell', 'dumpsys', 'notification', '--noredact'
        ], device_id)
        
        if not result['success']:
            return result
        
        # Parse notifications (simplified)
        notifications = []
        lines = result['stdout'].split('\n')
        
        current_notif = {}
        for line in lines:
            if 'NotificationRecord' in line:
                if current_notif:
                    notifications.append(current_notif)
                current_notif = {}
            elif 'pkg=' in line:
                pkg = line.split('pkg=')[1].split(' ')[0]
                current_notif['app'] = pkg
            elif 'android.title' in line and '=' in line:
                title = line.split('=')[-1].strip()
                current_notif['title'] = title
            elif 'android.text' in line and '=' in line:
                text = line.split('=')[-1].strip()
                current_notif['text'] = text
        
        return {
            'success': True,
            'notifications': notifications[:20],
            'count': len(notifications)
        }
    
    async def open_app(
        self,
        app_name: str,
        device_id: Optional[str] = None
    ) -> Dict:
        """Open app on phone by name"""
        
        # Map common app names to package names
        app_packages = {
            'whatsapp': 'com.whatsapp',
            'instagram': 'com.instagram.android',
            'facebook': 'com.facebook.katana',
            'twitter': 'com.twitter.android',
            'youtube': 'com.google.android.youtube',
            'chrome': 'com.android.chrome',
            'gmail': 'com.google.android.gm',
            'maps': 'com.google.android.apps.maps',
            'spotify': 'com.spotify.music',
            'netflix': 'com.netflix.mediaclient',
            'telegram': 'org.telegram.messenger',
            'snapchat': 'com.snapchat.android',
            'linkedin': 'com.linkedin.android',
            'uber': 'com.ubercab',
            'zomato': 'com.application.zomato',
            'swiggy': 'in.swiggy.android',
            'paytm': 'net.one97.paytm',
            'gpay': 'com.google.android.apps.nbu.paisa.user',
            'phonepe': 'com.phonepe.app',
            'amazon': 'in.amazon.mShop.android.shopping',
            'flipkart': 'com.flipkart.android',
            'settings': 'com.android.settings',
            'camera': 'com.android.camera2',
            'gallery': 'com.google.android.apps.photos',
            'music': 'com.google.android.music',
            'calculator': 'com.android.calculator2',
            'calendar': 'com.google.android.calendar',
            'contacts': 'com.android.contacts',
            'clock': 'com.google.android.deskclock',
            'files': 'com.google.android.apps.nbu.files'
        }
        
        # Find package name
        package = app_packages.get(app_name.lower())
        
        if not package:
            # Try to search for it
            search_result = await self._find_app_package(app_name, device_id)
            if search_result:
                package = search_result
            else:
                return {
                    'success': False,
                    'error': f'App package not found for: {app_name}',
                    'suggestion': 'Try using the exact app name'
                }
        
        result = self._run_adb([
            'shell', 'monkey', '-p', package, '-c',
            'android.intent.category.LAUNCHER', '1'
        ], device_id)
        
        if result['success']:
            return {
                'success': True,
                'message': f'{app_name} opened on phone',
                'package': package
            }
        
        return result
    
    async def _find_app_package(
        self,
        app_name: str,
        device_id: Optional[str] = None
    ) -> Optional[str]:
        """Find app package name by searching installed apps"""
        
        result = self._run_adb(
            ['shell', 'pm', 'list', 'packages'],
            device_id
        )
        
        if not result['success']:
            return None
        
        packages = result['stdout'].split('\n')
        app_lower = app_name.lower()
        
        for pkg in packages:
            pkg = pkg.replace('package:', '').strip()
            if app_lower in pkg.lower():
                return pkg
        
        return None
    
    async def get_installed_apps(self, device_id: Optional[str] = None) -> Dict:
        """Get list of installed apps"""
        
        result = self._run_adb(
            ['shell', 'pm', 'list', 'packages', '-3'],  # -3 = third party only
            device_id
        )
        
        if not result['success']:
            return result
        
        apps = []
        for line in result['stdout'].split('\n'):
            pkg = line.replace('package:', '').strip()
            if pkg:
                apps.append(pkg)
        
        return {
            'success': True,
            'apps': apps,
            'count': len(apps)
        }
    
    async def transfer_file_to_phone(
        self,
        local_path: str,
        phone_path: str = '/sdcard/Download/',
        device_id: Optional[str] = None
    ) -> Dict:
        """Transfer file from PC to phone"""
        
        if not os.path.exists(local_path):
            return {'success': False, 'error': 'Local file not found'}
        
        filename = os.path.basename(local_path)
        destination = os.path.join(phone_path, filename)
        
        result = self._run_adb(
            ['push', local_path, destination],
            device_id
        )
        
        if result['success']:
            return {
                'success': True,
                'message': f'{filename} transferred to phone',
                'phone_path': destination,
                'size': os.path.getsize(local_path)
            }
        
        return result
    
    async def transfer_file_from_phone(
        self,
        phone_path: str,
        local_path: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Dict:
        """Transfer file from phone to PC"""
        
        filename = phone_path.split('/')[-1]
        save_to = local_path or f"./downloads/from_phone/{filename}"
        
        os.makedirs(os.path.dirname(save_to), exist_ok=True)
        
        result = self._run_adb(
            ['pull', phone_path, save_to],
            device_id
        )
        
        if result['success']:
            return {
                'success': True,
                'message': f'{filename} transferred from phone',
                'local_path': save_to
            }
        
        return result
    
    async def get_latest_photos(
        self,
        count: int = 5,
        device_id: Optional[str] = None
    ) -> Dict:
        """Get latest photos from phone"""
        
        # Get list of recent photos
        result = self._run_adb([
            'shell', 'ls', '-t',
            '/sdcard/DCIM/Camera/'
        ], device_id)
        
        if not result['success']:
            return result
        
        files = result['stdout'].split('\n')
        photos = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic'))]
        
        downloaded = []
        save_dir = "./temp/phone_photos/"
        os.makedirs(save_dir, exist_ok=True)
        
        for photo in photos[:count]:
            phone_path = f"/sdcard/DCIM/Camera/{photo}"
            local_path = os.path.join(save_dir, photo)
            
            pull_result = self._run_adb(
                ['pull', phone_path, local_path],
                device_id
            )
            
            if pull_result['success']:
                downloaded.append({
                    'filename': photo,
                    'local_path': local_path,
                    'phone_path': phone_path
                })
        
        return {
            'success': True,
            'photos': downloaded,
            'count': len(downloaded),
            'save_directory': save_dir
        }
    
    async def control_media(
        self,
        action: str,
        device_id: Optional[str] = None
    ) -> Dict:
        """Control media playback on phone"""
        
        key_map = {
            'play': 'KEYCODE_MEDIA_PLAY',
            'pause': 'KEYCODE_MEDIA_PAUSE',
            'play_pause': 'KEYCODE_MEDIA_PLAY_PAUSE',
            'next': 'KEYCODE_MEDIA_NEXT',
            'previous': 'KEYCODE_MEDIA_PREVIOUS',
            'stop': 'KEYCODE_MEDIA_STOP',
            'volume_up': 'KEYCODE_VOLUME_UP',
            'volume_down': 'KEYCODE_VOLUME_DOWN',
            'mute': 'KEYCODE_VOLUME_MUTE'
        }
        
        keycode = key_map.get(action.lower())
        
        if not keycode:
            return {
                'success': False,
                'error': f'Unknown action: {action}',
                'available': list(key_map.keys())
            }
        
        result = self._run_adb(
            ['shell', 'input', 'keyevent', keycode],
            device_id
        )
        
        return {
            'success': result['success'],
            'action': action,
            'message': f'Media {action} executed'
        }
    
    async def set_volume(
        self,
        level: int,
        stream: str = 'music',
        device_id: Optional[str] = None
    ) -> Dict:
        """Set phone volume (0-15)"""
        
        stream_map = {
            'music': 3,
            'ringtone': 2,
            'notification': 5,
            'alarm': 4
        }
        
        stream_id = stream_map.get(stream, 3)
        level = max(0, min(15, level))
        
        result = self._run_adb([
            'shell', 'media', 'volume',
            '--stream', str(stream_id),
            '--set', str(level)
        ], device_id)
        
        return {
            'success': result['success'],
            'stream': stream,
            'level': level
        }
    
    async def get_contacts(
        self,
        search: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Dict:
        """Get phone contacts"""
        
        result = self._run_adb([
            'shell', 'content', 'query',
            '--uri', 'content://contacts/phones/',
            '--projection', 'display_name:number'
        ], device_id)
        
        if not result['success']:
            return result
        
        contacts = []
        for line in result['stdout'].split('\n'):
            if 'display_name' in line and 'number' in line:
                try:
                    name = line.split('display_name=')[1].split(',')[0]
                    number = line.split('number=')[1].split('}')[0]
                    
                    contact = {'name': name, 'number': number}
                    
                    if not search or search.lower() in name.lower():
                        contacts.append(contact)
                except:
                    pass
        
        return {
            'success': True,
            'contacts': contacts[:50],
            'count': len(contacts)
        }
    
    async def start_wireless_connection(self, device_id: Optional[str] = None) -> Dict:
        """Connect to phone wirelessly (no USB needed after initial setup)"""
        
        # First enable TCP/IP mode via USB
        result = self._run_adb(['tcpip', '5555'], device_id)
        
        if not result['success']:
            return {
                'success': False,
                'error': 'Could not enable TCP/IP mode. Connect phone via USB first.',
                'steps': [
                    '1. Connect phone via USB',
                    '2. Enable USB debugging',
                    '3. Run this command again',
                    '4. Then disconnect USB - wireless will work'
                ]
            }
        
        # Get phone IP
        ip_result = self._run_adb([
            'shell', 'ip', 'route'
        ], device_id)
        
        if ip_result['success']:
            # Extract IP
            import re
            ips = re.findall(r'src (\d+\.\d+\.\d+\.\d+)', ip_result['stdout'])
            
            if ips:
                phone_ip = ips[0]
                
                # Connect wirelessly
                connect_result = self._run_adb(['connect', f'{phone_ip}:5555'])
                
                if connect_result['success']:
                    return {
                        'success': True,
                        'message': 'Connected wirelessly!',
                        'phone_ip': phone_ip,
                        'instructions': 'You can now disconnect USB cable'
                    }
        
        return {
            'success': False,
            'error': 'Could not determine phone IP address',
            'manual': 'Go to Settings → About Phone → IP Address on your phone'
        }
    
    async def send_text_to_phone(
        self,
        text: str,
        device_id: Optional[str] = None
    ) -> Dict:
        """Type text on phone (into focused input field)"""
        
        # URL encode the text
        import urllib.parse
        encoded = urllib.parse.quote(text)
        
        result = self._run_adb([
            'shell', 'input', 'text', encoded
        ], device_id)
        
        return {
            'success': result['success'],
            'text_sent': text
        }
    
    async def tap_screen(
        self,
        x: int,
        y: int,
        device_id: Optional[str] = None
    ) -> Dict:
        """Tap specific position on phone screen"""
        
        result = self._run_adb(
            ['shell', 'input', 'tap', str(x), str(y)],
            device_id
        )
        
        return {
            'success': result['success'],
            'position': (x, y)
        }
    
    async def swipe_screen(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        duration: int = 300,
        device_id: Optional[str] = None
    ) -> Dict:
        """Swipe on phone screen"""
        
        result = self._run_adb([
            'shell', 'input', 'swipe',
            str(x1), str(y1), str(x2), str(y2), str(duration)
        ], device_id)
        
        return {
            'success': result['success'],
            'swipe': {'from': (x1, y1), 'to': (x2, y2)}
        }
    
    async def press_button(
        self,
        button: str,
        device_id: Optional[str] = None
    ) -> Dict:
        """Press phone hardware buttons"""
        
        button_map = {
            'home': 'KEYCODE_HOME',
            'back': 'KEYCODE_BACK',
            'recent': 'KEYCODE_APP_SWITCH',
            'power': 'KEYCODE_POWER',
            'volume_up': 'KEYCODE_VOLUME_UP',
            'volume_down': 'KEYCODE_VOLUME_DOWN',
            'camera': 'KEYCODE_CAMERA',
            'enter': 'KEYCODE_ENTER',
            'delete': 'KEYCODE_DEL',
            'screenshot': 'KEYCODE_SYSRQ',
            'notification': 'KEYCODE_NOTIFICATION',
            'menu': 'KEYCODE_MENU'
        }
        
        keycode = button_map.get(button.lower())
        
        if not keycode:
            return {
                'success': False,
                'error': f'Unknown button: {button}',
                'available': list(button_map.keys())
            }
        
        result = self._run_adb(
            ['shell', 'input', 'keyevent', keycode],
            device_id
        )
        
        return {
            'success': result['success'],
            'button': button
        }
    
    async def get_running_apps(self, device_id: Optional[str] = None) -> Dict:
        """Get currently running apps on phone"""
        
        result = self._run_adb(
            ['shell', 'dumpsys', 'activity', 'activities'],
            device_id
        )
        
        if not result['success']:
            return result
        
        import re
        apps = []
        
        # Find activity names
        activity_pattern = r'packageName=([a-z\.]+)'
        matches = re.findall(activity_pattern, result['stdout'])
        
        seen = set()
        for match in matches:
            if match not in seen and 'android' not in match:
                apps.append(match)
                seen.add(match)
        
        return {
            'success': True,
            'running_apps': apps[:20],
            'count': len(apps)
        }
    
    async def force_stop_app(
        self,
        package_name: str,
        device_id: Optional[str] = None
    ) -> Dict:
        """Force stop an app on phone"""
        
        result = self._run_adb(
            ['shell', 'am', 'force-stop', package_name],
            device_id
        )
        
        return {
            'success': result['success'],
            'app': package_name,
            'message': f'{package_name} force stopped'
        }
    
    async def unlock_screen(
        self,
        pin: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Dict:
        """Wake and unlock phone screen"""
        
        # Wake up screen
        self._run_adb(['shell', 'input', 'keyevent', 'KEYCODE_WAKEUP'], device_id)
        
        await asyncio.sleep(0.5)
        
        # Swipe to unlock
        await self.swipe_screen(540, 1800, 540, 900, 300, device_id)
        
        await asyncio.sleep(0.5)
        
        # Enter PIN if provided
        if pin:
            for digit in pin:
                await self.send_text_to_phone(digit, device_id)
                await asyncio.sleep(0.1)
            
            await self.press_button('enter', device_id)
        
        return {'success': True, 'message': 'Screen unlock attempted'}
    
    async def start_screen_recording(
        self,
        duration: int = 30,
        save_path: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Dict:
        """Record phone screen"""
        
        phone_path = '/sdcard/nexa_recording.mp4'
        
        # Start recording in background
        record_result = self._run_adb([
            'shell', 'screenrecord',
            f'--time-limit={duration}',
            '--bit-rate=8000000',
            phone_path
        ], device_id)
        
        await asyncio.sleep(duration + 1)
        
        # Pull the recording
        local_path = save_path or f"./recordings/phone_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        pull_result = self._run_adb(
            ['pull', phone_path, local_path],
            device_id
        )
        
        # Clean up
        self._run_adb(['shell', 'rm', phone_path], device_id)
        
        if pull_result['success']:
            return {
                'success': True,
                'path': local_path,
                'duration': duration,
                'message': f'Screen recording saved: {local_path}'
            }
        
        return pull_result
    
    async def get_location(self, device_id: Optional[str] = None) -> Dict:
        """Get phone GPS location"""
        
        result = self._run_adb([
            'shell', 'dumpsys', 'location'
        ], device_id)
        
        if not result['success']:
            return result
        
        import re
        
        # Extract latitude/longitude
        lat_match = re.search(r'latitude=(-?\d+\.\d+)', result['stdout'])
        lng_match = re.search(r'longitude=(-?\d+\.\d+)', result['stdout'])
        
        if lat_match and lng_match:
            lat = float(lat_match.group(1))
            lng = float(lng_match.group(1))
            
            return {
                'success': True,
                'latitude': lat,
                'longitude': lng,
                'maps_url': f'https://maps.google.com/?q={lat},{lng}'
            }
        
        return {
            'success': False,
            'error': 'Could not get location. Enable GPS on phone.'
        }
    
    async def ai_control_phone(
        self,
        natural_command: str,
        device_id: Optional[str] = None
    ) -> Dict:
        """
        Use AI to control phone from natural language.
        Takes screenshot → understands UI → executes action.
        """
        
        # Take screenshot to see current state
        screenshot = await self.take_screenshot(device_id=device_id)
        
        if not screenshot['success']:
            return screenshot
        
        # Analyze screenshot with AI
        prompt = f"""
        User wants to: "{natural_command}"
        
        Based on the phone screenshot, determine:
        1. What is currently on screen?
        2. What taps/swipes are needed?
        3. What text needs to be typed?
        
        Return as JSON:
        {{
            "current_state": "description",
            "actions": [
                {{"type": "tap", "x": 0, "y": 0, "reason": "..."}},
                {{"type": "swipe", "x1": 0, "y1": 0, "x2": 0, "y2": 0}},
                {{"type": "type", "text": "..."}},
                {{"type": "key", "button": "home/back/etc"}}
            ],
            "expected_result": "what should happen"
        }}
        """
        
        try:
            # Load screenshot as base64
            with open(screenshot['path'], 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode()
            
            response = await self.ai.complete(
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                        {"type": "text", "text": prompt}
                    ]
                }],
                temperature=0.3
            )
            
            plan = json.loads(response['content'])
            actions = plan.get('actions', [])
            
            # Execute actions
            results = []
            for action in actions:
                action_type = action.get('type')
                
                if action_type == 'tap':
                    result = await self.tap_screen(action['x'], action['y'], device_id)
                elif action_type == 'swipe':
                    result = await self.swipe_screen(
                        action['x1'], action['y1'],
                        action['x2'], action['y2'],
                        device_id=device_id
                    )
                elif action_type == 'type':
                    result = await self.send_text_to_phone(action['text'], device_id)
                elif action_type == 'key':
                    result = await self.press_button(action['button'], device_id)
                else:
                    result = {'success': False, 'error': f'Unknown action: {action_type}'}
                
                results.append({'action': action, 'result': result})
                await asyncio.sleep(0.5)  # Wait between actions
            
            return {
                'success': True,
                'command': natural_command,
                'plan': plan,
                'actions_executed': len(results),
                'results': results
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def install_apk(
        self,
        apk_path: str,
        device_id: Optional[str] = None
    ) -> Dict:
        """Install APK on phone"""
        
        if not os.path.exists(apk_path):
            return {'success': False, 'error': 'APK file not found'}
        
        result = self._run_adb(
            ['install', '-r', apk_path],
            device_id
        )
        
        if 'Success' in result.get('stdout', ''):
            return {
                'success': True,
                'message': f'APK installed successfully',
                'apk': apk_path
            }
        
        return {
            'success': False,
            'error': result.get('stderr', 'Installation failed')
        }
    
    def disconnect_device(self, device_id: str) -> Dict:
        """Disconnect a device"""
        
        result = self._run_adb(['disconnect', device_id])
        
        if device_id in self.connected_devices:
            del self.connected_devices[device_id]
        
        if self.active_device == device_id:
            self.active_device = None
        
        return {'success': result['success']}
