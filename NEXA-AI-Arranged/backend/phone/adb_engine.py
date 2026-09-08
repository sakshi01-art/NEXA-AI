import asyncio
import subprocess
import os
import re
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class ADBEngine:
    """
    Low-level ADB interface for Android device control.
    All Android operations go through this engine.
    """
    
    def __init__(self):
        self.adb_path = self._find_adb()
        self.device_cache: Dict[str, Dict] = {}
    
    def _find_adb(self) -> str:
        """Auto-detect ADB executable path"""
        
        search_paths = [
            os.path.expandvars(
                r'%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe'
            ),
            os.path.expandvars(
                r'%PROGRAMFILES%\Android\android-studio\platform-tools\adb.exe'
            ),
            os.path.expandvars(r'%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe'),
            r'C:\adb\adb.exe',
            'adb.exe',
            'adb'
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return path
        
        # Check PATH
        try:
            result = subprocess.run(
                ['where', 'adb'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0].strip()
        except Exception:
            pass
        
        return 'adb'
    
    def _run(
        self,
        args: List[str],
        device_id: Optional[str] = None,
        timeout: int = 30,
        input_data: Optional[str] = None
    ) -> Dict:
        """Run ADB command synchronously"""
        
        cmd = [self.adb_path]
        
        if device_id:
            cmd.extend(['-s', device_id])
        
        cmd.extend(args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                input=input_data
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'returncode': result.returncode
            }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Command timed out after {timeout}s',
                'stdout': '',
                'stderr': ''
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'ADB not found. Install Android SDK Platform Tools.',
                'download': 'https://developer.android.com/studio/releases/platform-tools',
                'stdout': '',
                'stderr': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': ''
            }
    
    async def _run_async(
        self,
        args: List[str],
        device_id: Optional[str] = None,
        timeout: int = 30
    ) -> Dict:
        """Run ADB command asynchronously"""
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._run(args, device_id, timeout)
        )
    
    async def get_connected_devices(self) -> List[Dict]:
        """Get list of all connected Android devices"""
        
        result = await self._run_async(['devices', '-l'])
        
        if not result['success']:
            return []
        
        devices = []
        lines = result['stdout'].split('\n')[1:]
        
        for line in lines:
            line = line.strip()
            
            if not line or 'offline' in line:
                continue
            
            parts = line.split()
            
            if len(parts) >= 2 and parts[1] in ['device', 'unauthorized']:
                device_info = {
                    'id': parts[0],
                    'status': parts[1]
                }
                
                # Parse additional info
                for part in parts[2:]:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        device_info[key] = value
                
                if parts[1] == 'device':
                    devices.append(device_info)
        
        return devices
    
    async def shell(
        self,
        device_id: str,
        command: str,
        timeout: int = 30
    ) -> Optional[str]:
        """Execute shell command on device"""
        
        result = await self._run_async(
            ['shell', command],
            device_id=device_id,
            timeout=timeout
        )
        
        if result['success']:
            return result['stdout']
        return None
    
    async def get_prop(self, device_id: str, prop: str) -> Optional[str]:
        """Get Android system property"""
        
        output = await self.shell(device_id, f'getprop {prop}')
        return output.strip() if output else None
    
    async def get_battery_info(self, device_id: str) -> Dict:
        """Get detailed battery information"""
        
        output = await self.shell(device_id, 'dumpsys battery')
        
        if not output:
            return {}
        
        info = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if 'level:' in line:
                try:
                    info['level'] = int(line.split(':')[1].strip())
                except Exception:
                    pass
            
            elif 'status:' in line:
                try:
                    status = int(line.split(':')[1].strip())
                    info['is_charging'] = status in [2, 5]
                    info['status'] = {
                        1: 'unknown', 2: 'charging',
                        3: 'discharging', 4: 'not_charging',
                        5: 'full'
                    }.get(status, 'unknown')
                except Exception:
                    pass
            
            elif 'temperature:' in line:
                try:
                    temp = int(line.split(':')[1].strip())
                    info['temperature_c'] = temp / 10
                except Exception:
                    pass
            
            elif 'voltage:' in line:
                try:
                    info['voltage_mv'] = int(line.split(':')[1].strip())
                except Exception:
                    pass
            
            elif 'health:' in line:
                try:
                    health = int(line.split(':')[1].strip())
                    info['health'] = {
                        1: 'unknown', 2: 'good', 3: 'overheat',
                        4: 'dead', 5: 'over_voltage', 7: 'cold'
                    }.get(health, 'unknown')
                except Exception:
                    pass
            
            elif 'technology:' in line:
                info['technology'] = line.split(':')[1].strip()
        
        return info
    
    async def get_storage_info(self, device_id: str) -> Dict:
        """Get device storage information"""
        
        output = await self.shell(device_id, 'df /sdcard')
        
        if not output:
            return {}
        
        try:
            lines = output.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 4:
                    total_kb = int(parts[1])
                    used_kb = int(parts[2])
                    free_kb = int(parts[3])
                    
                    return {
                        'total_gb': round(total_kb / 1024 / 1024, 2),
                        'used_gb': round(used_kb / 1024 / 1024, 2),
                        'free_gb': round(free_kb / 1024 / 1024, 2),
                        'percent_used': round(used_kb / total_kb * 100, 1)
                    }
        except Exception:
            pass
        
        return {}
    
    async def take_screenshot(
        self,
        device_id: str,
        local_path: str
    ) -> Dict:
        """Capture device screenshot"""
        
        remote_path = '/sdcard/nexa_temp_screenshot.png'
        
        # Capture
        cap_result = await self._run_async(
            ['shell', 'screencap', '-p', remote_path],
            device_id=device_id
        )
        
        if not cap_result['success']:
            return cap_result
        
        # Pull to PC
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        pull_result = await self._run_async(
            ['pull', remote_path, local_path],
            device_id=device_id
        )
        
        # Cleanup remote
        await self._run_async(
            ['shell', 'rm', remote_path],
            device_id=device_id
        )
        
        if pull_result['success']:
            return {
                'success': True,
                'path': local_path,
                'size': os.path.getsize(local_path) if os.path.exists(local_path) else 0
            }
        
        return pull_result
    
    async def tap(
        self,
        device_id: str,
        x: int,
        y: int
    ) -> Dict:
        """Tap screen at coordinates"""
        
        result = await self._run_async(
            ['shell', 'input', 'tap', str(x), str(y)],
            device_id=device_id
        )
        
        return {
            'success': result['success'],
            'position': {'x': x, 'y': y}
        }
    
    async def long_press(
        self,
        device_id: str,
        x: int,
        y: int,
        duration: int = 1000
    ) -> Dict:
        """Long press at coordinates"""
        
        result = await self._run_async(
            ['shell', 'input', 'swipe',
             str(x), str(y), str(x), str(y), str(duration)],
            device_id=device_id
        )
        
        return {'success': result['success']}
    
    async def swipe(
        self,
        device_id: str,
        x1: int, y1: int,
        x2: int, y2: int,
        duration: int = 300
    ) -> Dict:
        """Swipe on screen"""
        
        result = await self._run_async(
            ['shell', 'input', 'swipe',
             str(x1), str(y1), str(x2), str(y2), str(duration)],
            device_id=device_id
        )
        
        return {'success': result['success']}
    
    async def type_text(self, device_id: str, text: str) -> Dict:
        """Type text on device"""
        
        # Escape special characters
        escaped = text.replace(' ', '%s').replace("'", "\\'")
        
        result = await self._run_async(
            ['shell', 'input', 'text', escaped],
            device_id=device_id
        )
        
        return {'success': result['success']}
    
    async def press_key(self, device_id: str, keycode: str) -> Dict:
        """Press hardware/virtual key"""
        
        result = await self._run_async(
            ['shell', 'input', 'keyevent', keycode],
            device_id=device_id
        )
        
        return {'success': result['success']}
    
    async def push_file(
        self,
        device_id: str,
        local_path: str,
        remote_path: str
    ) -> Dict:
        """Push file from PC to device"""
        
        if not os.path.exists(local_path):
            return {'success': False, 'error': 'Local file not found'}
        
        result = await self._run_async(
            ['push', local_path, remote_path],
            device_id=device_id,
            timeout=120
        )
        
        if result['success']:
            size = os.path.getsize(local_path)
            return {
                'success': True,
                'local_path': local_path,
                'remote_path': remote_path,
                'size_bytes': size,
                'size_mb': round(size / 1024 / 1024, 2)
            }
        
        return result
    
    async def pull_file(
        self,
        device_id: str,
        remote_path: str,
        local_path: str
    ) -> Dict:
        """Pull file from device to PC"""
        
        os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
        
        result = await self._run_async(
            ['pull', remote_path, local_path],
            device_id=device_id,
            timeout=120
        )
        
        if result['success'] and os.path.exists(local_path):
            size = os.path.getsize(local_path)
            return {
                'success': True,
                'remote_path': remote_path,
                'local_path': local_path,
                'size_bytes': size,
                'size_mb': round(size / 1024 / 1024, 2)
            }
        
        return result
    
    async def install_apk(
        self,
        device_id: str,
        apk_path: str
    ) -> Dict:
        """Install APK on device"""
        
        if not os.path.exists(apk_path):
            return {'success': False, 'error': 'APK file not found'}
        
        result = await self._run_async(
            ['install', '-r', '-t', apk_path],
            device_id=device_id,
            timeout=120
        )
        
        success = 'Success' in result.get('stdout', '')
        
        return {
            'success': success,
            'apk': apk_path,
            'output': result.get('stdout', ''),
            'error': result.get('stderr', '') if not success else None
        }
    
    async def uninstall_app(
        self,
        device_id: str,
        package_name: str
    ) -> Dict:
        """Uninstall app from device"""
        
        result = await self._run_async(
            ['uninstall', package_name],
            device_id=device_id
        )
        
        return {
            'success': 'Success' in result.get('stdout', ''),
            'package': package_name
        }
    
    async def start_screen_record(
        self,
        device_id: str,
        remote_path: str = '/sdcard/nexa_record.mp4',
        duration: int = 30,
        bit_rate: str = '8M'
    ) -> subprocess.Popen:
        """Start screen recording (returns process handle)"""
        
        cmd = [
            self.adb_path,
            '-s', device_id,
            'shell', 'screenrecord',
            f'--time-limit={duration}',
            f'--bit-rate={bit_rate}',
            remote_path
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return process
    
    async def enable_wifi_adb(
        self,
        device_id: str,
        port: int = 5555
    ) -> Dict:
        """Enable wireless ADB debugging"""
        
        result = await self._run_async(
            ['tcpip', str(port)],
            device_id=device_id
        )
        
        if result['success']:
            # Get device IP
            ip_output = await self.shell(device_id, 'ip route')
            
            if ip_output:
                ips = re.findall(r'src (\d+\.\d+\.\d+\.\d+)', ip_output)
                if ips:
                    return {
                        'success': True,
                        'ip': ips[0],
                        'port': port,
                        'connect_command': f'adb connect {ips[0]}:{port}'
                    }
        
        return {
            'success': False,
            'error': 'Could not enable wireless ADB',
            'note': 'Make sure USB debugging is enabled'
        }
    
    async def connect_wireless(
        self,
        ip: str,
        port: int = 5555
    ) -> Dict:
        """Connect to device wirelessly"""
        
        result = await self._run_async(
            ['connect', f'{ip}:{port}']
        )
        
        connected = 'connected' in result.get('stdout', '').lower()
        
        return {
            'success': connected,
            'device_id': f'{ip}:{port}',
            'message': result.get('stdout', '')
        }
    
    async def disconnect_wireless(self, ip: str, port: int = 5555) -> Dict:
        """Disconnect wireless device"""
        
        result = await self._run_async(
            ['disconnect', f'{ip}:{port}']
        )
        
        return {'success': result['success']}
    
    async def get_running_apps(self, device_id: str) -> List[str]:
        """Get list of running app packages"""
        
        output = await self.shell(
            device_id,
            'dumpsys activity activities | grep packageName'
        )
        
        if not output:
            return []
        
        packages = set()
        for line in output.split('\n'):
            match = re.search(r'packageName=([a-zA-Z0-9\.]+)', line)
            if match:
                pkg = match.group(1)
                if 'android' not in pkg and pkg not in packages:
                    packages.add(pkg)
        
        return list(packages)
    
    async def get_installed_apps(
        self,
        device_id: str,
        user_only: bool = True
    ) -> List[Dict]:
        """Get installed applications"""
        
        flag = '-3' if user_only else ''
        output = await self.shell(
            device_id,
            f'pm list packages {flag} -f'
        )
        
        if not output:
            return []
        
        apps = []
        for line in output.split('\n'):
            if 'package:' in line:
                parts = line.strip().split('=')
                if len(parts) >= 2:
                    apk_path = parts[0].replace('package:', '')
                    package = parts[1]
                    apps.append({
                        'package': package,
                        'apk_path': apk_path
                    })
        
        return apps
    
    async def launch_app(
        self,
        device_id: str,
        package_name: str,
        activity: Optional[str] = None
    ) -> Dict:
        """Launch application"""
        
        if activity:
            cmd = f'am start -n {package_name}/{activity}'
        else:
            cmd = (
                f'monkey -p {package_name} '
                f'-c android.intent.category.LAUNCHER 1'
            )
        
        output = await self.shell(device_id, cmd)
        
        success = output is not None and 'Error' not in (output or '')
        
        return {
            'success': success,
            'package': package_name,
            'output': output
        }
    
    async def force_stop_app(
        self,
        device_id: str,
        package_name: str
    ) -> Dict:
        """Force stop application"""
        
        output = await self.shell(
            device_id,
            f'am force-stop {package_name}'
        )
        
        return {
            'success': output is not None,
            'package': package_name
        }
    
    async def clear_app_data(
        self,
        device_id: str,
        package_name: str
    ) -> Dict:
        """Clear app data and cache"""
        
        output = await self.shell(
            device_id,
            f'pm clear {package_name}'
        )
        
        return {
            'success': 'Success' in (output or ''),
            'package': package_name
        }
    
    async def get_app_info(
        self,
        device_id: str,
        package_name: str
    ) -> Dict:
        """Get detailed app information"""
        
        output = await self.shell(
            device_id,
            f'dumpsys package {package_name}'
        )
        
        if not output:
            return {}
        
        info = {'package': package_name}
        
        # Version
        ver_match = re.search(r'versionName=([^\s]+)', output)
        if ver_match:
            info['version'] = ver_match.group(1)
        
        # Version code
        code_match = re.search(r'versionCode=(\d+)', output)
        if code_match:
            info['version_code'] = code_match.group(1)
        
        # Install date
        install_match = re.search(r'firstInstallTime=([^\s]+)', output)
        if install_match:
            info['installed_at'] = install_match.group(1)
        
        # Last updated
        update_match = re.search(r'lastUpdateTime=([^\s]+)', output)
        if update_match:
            info['updated_at'] = update_match.group(1)
        
        return info
    
    async def set_screen_brightness(
        self,
        device_id: str,
        level: int
    ) -> Dict:
        """Set screen brightness (0-255)"""
        
        level = max(0, min(255, level))
        
        # Disable auto brightness
        await self.shell(
            device_id,
            'settings put system screen_brightness_mode 0'
        )
        
        # Set brightness
        output = await self.shell(
            device_id,
            f'settings put system screen_brightness {level}'
        )
        
        return {
            'success': True,
            'brightness': level,
            'percentage': round(level / 255 * 100)
        }
    
    async def set_screen_timeout(
        self,
        device_id: str,
        timeout_ms: int
    ) -> Dict:
        """Set screen timeout in milliseconds"""
        
        output = await self.shell(
            device_id,
            f'settings put system screen_off_timeout {timeout_ms}'
        )
        
        return {
            'success': True,
            'timeout_ms': timeout_ms,
            'timeout_s': timeout_ms // 1000
        }
    
    async def enable_mobile_data(
        self,
        device_id: str,
        enable: bool = True
    ) -> Dict:
        """Enable or disable mobile data"""
        
        state = 'enable' if enable else 'disable'
        output = await self.shell(
            device_id,
            f'svc data {state}'
        )
        
        return {
            'success': True,
            'mobile_data': enable
        }
    
    async def enable_wifi(
        self,
        device_id: str,
        enable: bool = True
    ) -> Dict:
        """Enable or disable WiFi"""
        
        state = 'enable' if enable else 'disable'
        output = await self.shell(
            device_id,
            f'svc wifi {state}'
        )
        
        return {
            'success': True,
            'wifi': enable
        }
    
    async def enable_bluetooth(
        self,
        device_id: str,
        enable: bool = True
    ) -> Dict:
        """Enable or disable Bluetooth"""
        
        state = '1' if enable else '0'
        output = await self.shell(
            device_id,
            f'am broadcast -a android.bluetooth.adapter.action.REQUEST_{state}'
        )
        
        return {
            'success': True,
            'bluetooth': enable
        }
    
    async def reboot_device(
        self,
        device_id: str,
        mode: str = 'normal'
    ) -> Dict:
        """Reboot device (normal/recovery/bootloader)"""
        
        if mode == 'normal':
            cmd = ['reboot']
        elif mode == 'recovery':
            cmd = ['reboot', 'recovery']
        elif mode == 'bootloader':
            cmd = ['reboot', 'bootloader']
        else:
            return {'success': False, 'error': f'Unknown mode: {mode}'}
        
        result = await self._run_async(cmd, device_id=device_id)
        
        return {
            'success': True,
            'mode': mode,
            'message': f'Device rebooting in {mode} mode'
        }
