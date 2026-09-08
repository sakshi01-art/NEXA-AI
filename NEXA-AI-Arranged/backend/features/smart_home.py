import asyncio
import json
import aiohttp
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from pathlib import Path
import socket

class SmartHomeController:
    """
    Complete Smart Home Control from NEXA.
    
    Supports:
    - Philips Hue lights
    - Smart plugs (TP-Link, Tasmota)
    - Thermostats (Nest, Ecobee)
    - Smart locks
    - Security cameras
    - TV control (Samsung, LG WebOS)
    - AC control (via IR blaster)
    - Door bells
    - Sensors
    - Home Assistant integration
    - Google Home devices
    - Amazon Echo/Alexa
    - MQTT devices
    
    Commands:
    "Nexa, living room ki lights off kar"
    "Bedroom ka AC 22 degree pe set kar"
    "TV band karo"
    "Main door lock karo"
    "Ghar ki sabhi lights dim karo"
    "Movie mode activate karo"
    "Good night mode set karo"
    """
    
    def __init__(self, ai_provider, notification_callback: Callable):
        self.ai = ai_provider
        self.notify = notification_callback
        
        self.devices: Dict[str, Dict] = {}
        self.rooms: Dict[str, List[str]] = {}
        self.scenes: Dict[str, Dict] = {}
        self.automations: List[Dict] = []
        
        self.home_assistant_url = None
        self.home_assistant_token = None
        self.hue_bridge_ip = None
        self.hue_api_key = None
        
        self._load_config()
    
    def _load_config(self):
        """Load smart home configuration"""
        
        config_file = Path("./data/smart_home_config.json")
        
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
                self.home_assistant_url = config.get('home_assistant_url')
                self.home_assistant_token = config.get('home_assistant_token')
                self.hue_bridge_ip = config.get('hue_bridge_ip')
                self.hue_api_key = config.get('hue_api_key')
                self.rooms = config.get('rooms', {})
                self.scenes = config.get('scenes', {})
    
    async def discover_devices(self) -> Dict:
        """Discover all smart home devices on network"""
        
        discovered = []
        
        # Discover Home Assistant devices
        if self.home_assistant_url and self.home_assistant_token:
            ha_devices = await self._discover_ha_devices()
            discovered.extend(ha_devices)
        
        # Discover Philips Hue
        if not self.hue_bridge_ip:
            self.hue_bridge_ip = await self._find_hue_bridge()
        
        if self.hue_bridge_ip:
            hue_devices = await self._discover_hue_devices()
            discovered.extend(hue_devices)
        
        # Discover local network devices (smart plugs, etc.)
        local_devices = await self._discover_local_devices()
        discovered.extend(local_devices)
        
        # Register all devices
        for device in discovered:
            self.devices[device['id']] = device
        
        return {
            'success': True,
            'devices': discovered,
            'count': len(discovered),
            'rooms': list(set(d.get('room', 'Unknown') for d in discovered))
        }
    
    async def _discover_ha_devices(self) -> List[Dict]:
        """Discover devices via Home Assistant API"""
        
        try:
            headers = {
                'Authorization': f'Bearer {self.home_assistant_token}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.home_assistant_url}/api/states',
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        states = await response.json()
                        
                        devices = []
                        for state in states:
                            entity_id = state['entity_id']
                            domain = entity_id.split('.')[0]
                            
                            if domain in ['light', 'switch', 'climate',
                                         'media_player', 'lock', 'cover']:
                                
                                device = {
                                    'id': entity_id,
                                    'name': state['attributes'].get(
                                        'friendly_name',
                                        entity_id
                                    ),
                                    'type': domain,
                                    'state': state['state'],
                                    'attributes': state['attributes'],
                                    'source': 'home_assistant',
                                    'room': self._guess_room(
                                        state['attributes'].get('friendly_name', '')
                                    )
                                }
                                
                                devices.append(device)
                        
                        return devices
        
        except Exception as e:
            return []
    
    async def _find_hue_bridge(self) -> Optional[str]:
        """Auto-discover Philips Hue bridge IP"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://discovery.meethue.com/',
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    if response.status == 200:
                        bridges = await response.json()
                        if bridges:
                            return bridges[0].get('internalipaddress')
        except Exception:
            pass
        
        return None
    
    async def _discover_hue_devices(self) -> List[Dict]:
        """Discover Philips Hue lights"""
        
        if not self.hue_bridge_ip or not self.hue_api_key:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f'http://{self.hue_bridge_ip}/api/{self.hue_api_key}/lights'
                
                async with session.get(url) as response:
                    if response.status == 200:
                        lights = await response.json()
                        
                        devices = []
                        for light_id, light_info in lights.items():
                            state = light_info.get('state', {})
                            
                            devices.append({
                                'id': f'hue_light_{light_id}',
                                'name': light_info.get('name', f'Light {light_id}'),
                                'type': 'light',
                                'state': 'on' if state.get('on') else 'off',
                                'brightness': state.get('bri', 254),
                                'hue': state.get('hue', 0),
                                'saturation': state.get('sat', 0),
                                'color_temp': state.get('ct', 0),
                                'source': 'philips_hue',
                                'hue_id': light_id,
                                'room': self._guess_room(light_info.get('name', ''))
                            })
                        
                        return devices
        
        except Exception:
            return []
    
    async def _discover_local_devices(self) -> List[Dict]:
        """Discover local network smart devices"""
        
        devices = []
        
        # Scan for common smart device ports
        smart_ports = {
            80: 'http_device',
            8080: 'http_alt',
            9000: 'network_device',
            1883: 'mqtt'
        }
        
        # Get local network range
        local_ip = socket.gethostbyname(socket.gethostname())
        ip_parts = local_ip.split('.')
        network_prefix = '.'.join(ip_parts[:3])
        
        # Scan subnet (simplified - checks a few IPs)
        scan_ips = [f"{network_prefix}.{i}" for i in range(1, 20)]
        
        tasks = []
        for ip in scan_ips:
            tasks.append(self._probe_device(ip))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict) and result.get('found'):
                devices.append(result['device'])
        
        return devices
    
    async def _probe_device(self, ip: str) -> Dict:
        """Probe an IP for smart device"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'http://{ip}/',
                    timeout=aiohttp.ClientTimeout(total=1)
                ) as response:
                    content = await response.text()
                    
                    # Check for Tasmota
                    if 'Tasmota' in content:
                        return {
                            'found': True,
                            'device': {
                                'id': f'tasmota_{ip.replace(".", "_")}',
                                'name': f'Smart Plug ({ip})',
                                'type': 'switch',
                                'ip': ip,
                                'source': 'tasmota',
                                'state': 'unknown'
                            }
                        }
        except Exception:
            pass
        
        return {'found': False}
    
    def _guess_room(self, device_name: str) -> str:
        """Guess room from device name"""
        
        name_lower = device_name.lower()
        
        room_keywords = {
            'living': 'Living Room',
            'bedroom': 'Bedroom',
            'kitchen': 'Kitchen',
            'bathroom': 'Bathroom',
            'office': 'Office',
            'dining': 'Dining Room',
            'garage': 'Garage',
            'outdoor': 'Outdoor',
            'hall': 'Hallway',
            'study': 'Study Room',
        }
        
        for keyword, room in room_keywords.items():
            if keyword in name_lower:
                return room
        
        return 'Unknown'
    
    async def control_device(
        self,
        device_id: str,
        action: str,
        params: Optional[Dict] = None
    ) -> Dict:
        """Control a smart home device"""
        
        device = self.devices.get(device_id)
        if not device:
            return {'success': False, 'error': f'Device {device_id} not found'}
        
        params = params or {}
        source = device.get('source', 'unknown')
        
        if source == 'home_assistant':
            return await self._ha_control(device, action, params)
        elif source == 'philips_hue':
            return await self._hue_control(device, action, params)
        elif source == 'tasmota':
            return await self._tasmota_control(device, action, params)
        else:
            return {'success': False, 'error': f'Unknown device source: {source}'}
    
    async def _ha_control(
        self,
        device: Dict,
        action: str,
        params: Dict
    ) -> Dict:
        """Control device via Home Assistant"""
        
        if not self.home_assistant_url or not self.home_assistant_token:
            return {'success': False, 'error': 'Home Assistant not configured'}
        
        entity_id = device['id']
        domain = entity_id.split('.')[0]
        
        # Map actions to HA services
        service_map = {
            'turn_on': f'{domain}/turn_on',
            'turn_off': f'{domain}/turn_off',
            'toggle': f'{domain}/toggle',
            'set_brightness': 'light/turn_on',
            'set_temperature': 'climate/set_temperature',
            'set_color': 'light/turn_on',
            'lock': 'lock/lock',
            'unlock': 'lock/unlock',
            'open': 'cover/open_cover',
            'close': 'cover/close_cover',
        }
        
        service = service_map.get(action, f'{domain}/turn_on')
        
        service_data = {'entity_id': entity_id}
        
        if action == 'set_brightness' and 'brightness' in params:
            service_data['brightness'] = int(params['brightness'] * 2.54)
        
        if action == 'set_temperature' and 'temperature' in params:
            service_data['temperature'] = params['temperature']
        
        if action == 'set_color' and 'color' in params:
            service_data['rgb_color'] = params['color']
        
        try:
            headers = {
                'Authorization': f'Bearer {self.home_assistant_token}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.home_assistant_url}/api/services/{service}',
                    headers=headers,
                    json=service_data
                ) as response:
                    
                    if response.status in [200, 201]:
                        device['state'] = 'on' if 'on' in action else 'off'
                        
                        return {
                            'success': True,
                            'device': device['name'],
                            'action': action,
                            'params': params
                        }
                    
                    return {
                        'success': False,
                        'error': f'HA returned status {response.status}'
                    }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _hue_control(
        self,
        device: Dict,
        action: str,
        params: Dict
    ) -> Dict:
        """Control Philips Hue light"""
        
        if not self.hue_bridge_ip or not self.hue_api_key:
            return {'success': False, 'error': 'Hue bridge not configured'}
        
        hue_id = device.get('hue_id')
        url = f'http://{self.hue_bridge_ip}/api/{self.hue_api_key}/lights/{hue_id}/state'
        
        state_data = {}
        
        if action == 'turn_on':
            state_data['on'] = True
        elif action == 'turn_off':
            state_data['on'] = False
        elif action == 'toggle':
            state_data['on'] = device.get('state') != 'on'
        elif action == 'set_brightness':
            state_data['on'] = True
            state_data['bri'] = int(params.get('brightness', 100) * 2.54)
        elif action == 'set_color':
            state_data['on'] = True
            color = params.get('color_name', 'white')
            state_data.update(self._color_to_hue(color))
        elif action == 'set_color_temp':
            state_data['on'] = True
            state_data['ct'] = params.get('color_temp', 370)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=state_data) as response:
                    
                    if response.status == 200:
                        device['state'] = 'on' if state_data.get('on', True) else 'off'
                        
                        return {
                            'success': True,
                            'device': device['name'],
                            'action': action,
                            'state': device['state']
                        }
                    
                    return {'success': False, 'error': 'Hue control failed'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _tasmota_control(
        self,
        device: Dict,
        action: str,
        params: Dict
    ) -> Dict:
        """Control Tasmota device"""
        
        ip = device.get('ip')
        if not ip:
            return {'success': False, 'error': 'Device IP not found'}
        
        command_map = {
            'turn_on': 'Power1%20On',
            'turn_off': 'Power1%20Off',
            'toggle': 'Power1%20Toggle'
        }
        
        cmd = command_map.get(action, 'Power1%20Toggle')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'http://{ip}/cm?cmnd={cmd}',
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        state = result.get('POWER', 'UNKNOWN')
                        device['state'] = state.lower()
                        
                        return {
                            'success': True,
                            'device': device['name'],
                            'action': action,
                            'state': device['state']
                        }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _color_to_hue(self, color_name: str) -> Dict:
        """Convert color name to Hue values"""
        
        color_map = {
            'red': {'hue': 0, 'sat': 254},
            'orange': {'hue': 6553, 'sat': 254},
            'yellow': {'hue': 10923, 'sat': 254},
            'green': {'hue': 21845, 'sat': 254},
            'blue': {'hue': 43690, 'sat': 254},
            'purple': {'hue': 54613, 'sat': 254},
            'pink': {'hue': 56100, 'sat': 200},
            'white': {'hue': 0, 'sat': 0},
            'warm': {'ct': 447},
            'cool': {'ct': 153},
            'neutral': {'ct': 300},
        }
        
        return color_map.get(color_name.lower(), {'hue': 0, 'sat': 0})
    
    async def control_room(
        self,
        room_name: str,
        action: str,
        params: Optional[Dict] = None
    ) -> Dict:
        """Control all devices in a room"""
        
        results = []
        
        for device_id, device in self.devices.items():
            if device.get('room', '').lower() == room_name.lower():
                result = await self.control_device(device_id, action, params)
                results.append({
                    'device': device['name'],
                    'result': result
                })
        
        if not results:
            return {
                'success': False,
                'error': f'No devices found in {room_name}'
            }
        
        success_count = sum(1 for r in results if r['result'].get('success'))
        
        return {
            'success': success_count > 0,
            'room': room_name,
            'action': action,
            'devices_controlled': len(results),
            'success_count': success_count,
            'results': results
        }
    
    async def activate_scene(self, scene_name: str) -> Dict:
        """Activate a predefined scene"""
        
        # Built-in scenes
        builtin_scenes = {
            'movie': {
                'name': 'Movie Mode',
                'actions': [
                    {'room': 'living room', 'action': 'set_brightness',
                     'params': {'brightness': 20}},
                ]
            },
            'good_night': {
                'name': 'Good Night Mode',
                'actions': [
                    {'all_rooms': True, 'action': 'turn_off'},
                ]
            },
            'good_morning': {
                'name': 'Good Morning Mode',
                'actions': [
                    {'room': 'bedroom', 'action': 'set_brightness',
                     'params': {'brightness': 50}},
                ]
            },
            'party': {
                'name': 'Party Mode',
                'actions': [
                    {'all_rooms': True, 'action': 'set_color',
                     'params': {'color_name': 'purple'}},
                ]
            },
            'focus': {
                'name': 'Focus Mode',
                'actions': [
                    {'room': 'office', 'action': 'set_brightness',
                     'params': {'brightness': 100}},
                    {'room': 'office', 'action': 'set_color',
                     'params': {'color_name': 'cool'}},
                ]
            },
            'relax': {
                'name': 'Relax Mode',
                'actions': [
                    {'all_rooms': True, 'action': 'set_brightness',
                     'params': {'brightness': 40}},
                    {'all_rooms': True, 'action': 'set_color',
                     'params': {'color_name': 'warm'}},
                ]
            }
        }
        
        # Check built-in first, then custom
        scene = builtin_scenes.get(scene_name.lower()) or self.scenes.get(scene_name)
        
        if not scene:
            return {
                'success': False,
                'error': f'Scene "{scene_name}" not found',
                'available_scenes': list(builtin_scenes.keys()) + list(self.scenes.keys())
            }
        
        results = []
        
        for action_config in scene.get('actions', []):
            if action_config.get('all_rooms'):
                for device_id, device in self.devices.items():
                    result = await self.control_device(
                        device_id,
                        action_config['action'],
                        action_config.get('params', {})
                    )
                    results.append(result)
            
            elif action_config.get('room'):
                result = await self.control_room(
                    action_config['room'],
                    action_config['action'],
                    action_config.get('params', {})
                )
                results.append(result)
        
        return {
            'success': True,
            'scene': scene['name'],
            'actions_executed': len(results),
            'message': f'{scene["name"]} activate ho gaya!'
        }
    
    async def get_home_status(self) -> Dict:
        """Get complete smart home status"""
        
        device_by_room: Dict[str, List] = {}
        
        for device in self.devices.values():
            room = device.get('room', 'Unknown')
            if room not in device_by_room:
                device_by_room[room] = []
            device_by_room[room].append({
                'name': device['name'],
                'type': device['type'],
                'state': device.get('state', 'unknown')
            })
        
        on_count = sum(
            1 for d in self.devices.values()
            if d.get('state') == 'on'
        )
        
        return {
            'success': True,
            'total_devices': len(self.devices),
            'devices_on': on_count,
            'devices_off': len(self.devices) - on_count,
            'rooms': device_by_room,
            'available_scenes': [
                'movie', 'good_night', 'good_morning',
                'party', 'focus', 'relax'
            ]
        }
    
    async def natural_language_control(self, command: str) -> Dict:
        """Control smart home using natural language AI"""
        
        devices_summary = [
            {
                'id': d_id,
                'name': d['name'],
                'type': d['type'],
                'room': d.get('room'),
                'state': d.get('state')
            }
            for d_id, d in self.devices.items()
        ]
        
        prompt = f"""
        Smart home control command: "{command}"
        
        Available devices:
        {json.dumps(devices_summary, indent=2)}
        
        Determine what device(s) to control and how.
        
        JSON response:
        {{
            "intent": "description of what user wants",
            "controls": [
                {{
                    "device_id": "exact device id",
                    "action": "turn_on/turn_off/set_brightness/set_color/set_temperature",
                    "params": {{}}
                }}
            ],
            "scene": "scene name if applicable or null",
            "response_message": "natural Hinglish response to user"
        }}
        """
        
        try:
            response = await self.ai.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            plan = json.loads(response['content'])
            
            # Execute scene if specified
            if plan.get('scene'):
                scene_result = await self.activate_scene(plan['scene'])
                return {
                    'success': scene_result['success'],
                    'message': plan.get('response_message', 'Done!'),
                    'scene_activated': plan['scene']
                }
            
            # Execute individual controls
            results = []
            for control in plan.get('controls', []):
                result = await self.control_device(
                    control['device_id'],
                    control['action'],
                    control.get('params', {})
                )
                results.append(result)
            
            success = any(r.get('success') for r in results)
            
            return {
                'success': success,
                'message': plan.get('response_message', 'Command executed!'),
                'controls_executed': len(results),
                'results': results
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def create_automation(
        self,
        name: str,
        trigger: Dict,
        actions: List[Dict]
    ) -> Dict:
        """Create smart home automation"""
        
        automation = {
            'id': f"auto_{datetime.now().timestamp()}",
            'name': name,
            'trigger': trigger,
            'actions': actions,
            'enabled': True,
            'created_at': datetime.now().isoformat(),
            'last_triggered': None,
            'trigger_count': 0
        }
        
        self.automations.append(automation)
        self._save_automations()
        
        return {
            'success': True,
            'automation_id': automation['id'],
            'name': name,
            'message': f'Automation "{name}" create ho gaya!'
        }
    
    def _save_automations(self):
        """Save automations to disk"""
        
        auto_file = Path("./data/smart_home_automations.json")
        with open(auto_file, 'w') as f:
            json.dump(self.automations, f, indent=2, default=str)
