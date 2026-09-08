import asyncio
import json
import subprocess
import threading
import time
import os
import socket
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

class DeviceType(Enum):
    ANDROID = "android"
    IOS = "ios"
    UNKNOWN = "unknown"

class ConnectionType(Enum):
    USB = "usb"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"

@dataclass
class PhoneDevice:
    id: str
    name: str
    model: str
    manufacturer: str
    device_type: DeviceType
    connection_type: ConnectionType
    android_version: Optional[str] = None
    ios_version: Optional[str] = None
    battery_level: int = 0
    is_charging: bool = False
    is_locked: bool = True
    ip_address: Optional[str] = None
    screen_width: int = 1080
    screen_height: int = 1920
    storage_total_gb: float = 0
    storage_free_gb: float = 0
    connected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    is_online: bool = True
    capabilities: List[str] = field(default_factory=list)

class DeviceManager:
    """
    Central manager for all connected phone devices.
    Handles discovery, connection, and device registry.
    """
    
    def __init__(
        self,
        adb_engine,
        ios_controller,
        notification_callback: Callable
    ):
        self.adb = adb_engine
        self.ios = ios_controller
        self.notify = notification_callback
        
        self.devices: Dict[str, PhoneDevice] = {}
        self.active_device_id: Optional[str] = None
        self.event_listeners: Dict[str, List[Callable]] = {}
        
        # Start background monitoring
        self._monitoring = False
        self._monitor_thread = None
    
    async def start_monitoring(self):
        """Start continuous device monitoring"""
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
    
    def _monitor_loop(self):
        """Background device monitoring loop"""
        while self._monitoring:
            try:
                # Scan for devices
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._scan_all_devices())
                loop.close()
            except Exception:
                pass
            time.sleep(3)
    
    async def _scan_all_devices(self):
        """Scan for all connected devices"""
        
        # Scan Android via ADB
        android_devices = await self.adb.get_connected_devices()
        
        for device_info in android_devices:
            device_id = device_info['id']
            
            if device_id not in self.devices:
                # New device connected
                device = await self._create_device_profile(device_info)
                self.devices[device_id] = device
                
                await self._emit_event('device_connected', device)
                
                await self.notify({
                    'type': 'success',
                    'title': '📱 Phone Connected!',
                    'message': f'{device.name} connected via {device.connection_type.value}',
                    'priority': 'medium'
                })
                
                # Set as active if first device
                if not self.active_device_id:
                    self.active_device_id = device_id
            else:
                # Update existing device
                await self._update_device_status(device_id)
        
        # Check for disconnected devices
        connected_ids = {d['id'] for d in android_devices}
        for device_id in list(self.devices.keys()):
            if device_id not in connected_ids:
                device = self.devices[device_id]
                device.is_online = False
                
                await self._emit_event('device_disconnected', device)
                
                await self.notify({
                    'type': 'warning',
                    'title': '📱 Phone Disconnected',
                    'message': f'{device.name} disconnected',
                    'priority': 'low'
                })
    
    async def _create_device_profile(self, device_info: Dict) -> PhoneDevice:
        """Create detailed device profile"""
        
        device_id = device_info['id']
        
        # Detect connection type
        conn_type = (
            ConnectionType.WIFI
            if ':' in device_id
            else ConnectionType.USB
        )
        
        # Get detailed info
        model = await self.adb.get_prop(device_id, 'ro.product.model')
        manufacturer = await self.adb.get_prop(device_id, 'ro.product.manufacturer')
        android_ver = await self.adb.get_prop(device_id, 'ro.build.version.release')
        
        # Screen size
        size_result = await self.adb.shell(device_id, 'wm size')
        width, height = 1080, 1920
        if size_result and 'x' in size_result:
            try:
                parts = size_result.split(':')[-1].strip().split('x')
                width = int(parts[0].strip())
                height = int(parts[1].strip())
            except Exception:
                pass
        
        # Battery
        battery_info = await self.adb.get_battery_info(device_id)
        
        # Storage
        storage_info = await self.adb.get_storage_info(device_id)
        
        # IP address
        ip_result = await self.adb.shell(device_id, 'ip route')
        ip_address = None
        if ip_result:
            import re
            ips = re.findall(r'src (\d+\.\d+\.\d+\.\d+)', ip_result)
            if ips:
                ip_address = ips[0]
        
        device_name = f"{manufacturer} {model}".strip()
        
        return PhoneDevice(
            id=device_id,
            name=device_name,
            model=model or 'Unknown',
            manufacturer=manufacturer or 'Unknown',
            device_type=DeviceType.ANDROID,
            connection_type=conn_type,
            android_version=android_ver,
            battery_level=battery_info.get('level', 0),
            is_charging=battery_info.get('is_charging', False),
            ip_address=ip_address,
            screen_width=width,
            screen_height=height,
            storage_total_gb=storage_info.get('total_gb', 0),
            storage_free_gb=storage_info.get('free_gb', 0),
            capabilities=self._detect_capabilities(android_ver)
        )
    
    async def _update_device_status(self, device_id: str):
        """Update real-time device status"""
        
        device = self.devices[device_id]
        device.last_seen = datetime.now().isoformat()
        device.is_online = True
        
        # Update battery
        battery = await self.adb.get_battery_info(device_id)
        device.battery_level = battery.get('level', device.battery_level)
        device.is_charging = battery.get('is_charging', device.is_charging)
    
    def _detect_capabilities(self, android_version: Optional[str]) -> List[str]:
        """Detect device capabilities based on Android version"""
        
        capabilities = [
            'screen_capture',
            'file_transfer',
            'app_control',
            'input_control',
            'notification_access'
        ]
        
        if android_version:
            try:
                major = int(android_version.split('.')[0])
                
                if major >= 10:
                    capabilities.extend([
                        'screen_record',
                        'wireless_debug',
                        'background_process_limit'
                    ])
                
                if major >= 11:
                    capabilities.extend([
                        'wireless_adb',
                        'paired_devices'
                    ])
                
                if major >= 12:
                    capabilities.extend([
                        'quick_tiles_api',
                        'privacy_indicators'
                    ])
            except Exception:
                pass
        
        return capabilities
    
    async def _emit_event(self, event_type: str, data: Any):
        """Emit device event to all listeners"""
        
        listeners = self.event_listeners.get(event_type, [])
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(data)
                else:
                    listener(data)
            except Exception:
                pass
    
    def on(self, event_type: str, callback: Callable):
        """Register event listener"""
        
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        
        self.event_listeners[event_type].append(callback)
    
    def get_active_device(self) -> Optional[PhoneDevice]:
        """Get currently active device"""
        return self.devices.get(self.active_device_id)
    
    def set_active_device(self, device_id: str) -> bool:
        """Set active device"""
        
        if device_id in self.devices:
            self.active_device_id = device_id
            return True
        return False
    
    def get_all_devices(self) -> List[PhoneDevice]:
        """Get all connected devices"""
        return list(self.devices.values())
    
    def stop_monitoring(self):
        """Stop device monitoring"""
        self._monitoring = False
