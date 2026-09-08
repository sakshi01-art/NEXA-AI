import psutil
import platform
from typing import Optional

class SystemMonitorTools:
    """Tools for monitoring system resources"""
    
    @staticmethod
    def get_system_stats() -> dict:
        """Get comprehensive system statistics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory
            memory = psutil.virtual_memory()
            
            # Disk
            disk = psutil.disk_usage('/')
            
            # Network
            network = psutil.net_io_counters()
            
            # Battery
            battery = psutil.sensors_battery()
            
            return {
                'success': True,
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'frequency_mhz': cpu_freq.current if cpu_freq else None
                },
                'memory': {
                    'total_gb': round(memory.total / 1024**3, 2),
                    'used_gb': round(memory.used / 1024**3, 2),
                    'free_gb': round(memory.free / 1024**3, 2),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / 1024**3, 2),
                    'used_gb': round(disk.used / 1024**3, 2),
                    'free_gb': round(disk.free / 1024**3, 2),
                    'percent': disk.percent
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_received': network.bytes_recv,
                    'mb_sent': round(network.bytes_sent / 1024**2, 2),
                    'mb_received': round(network.bytes_recv / 1024**2, 2)
                },
                'battery': {
                    'percent': battery.percent if battery else None,
                    'plugged_in': battery.power_plugged if battery else None,
                    'time_left_minutes': battery.secsleft / 60 if battery and battery.secsleft > 0 else None
                } if battery else None,
                'platform': {
                    'system': platform.system(),
                    'release': platform.release(),
                    'version': platform.version(),
                    'machine': platform.machine(),
                    'processor': platform.processor()
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_cpu_info() -> dict:
        """Get detailed CPU information"""
        try:
            cpu_percent_per_core = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq(percpu=True)
            
            return {
                'success': True,
                'usage_per_core': cpu_percent_per_core,
                'average_usage': sum(cpu_percent_per_core) / len(cpu_percent_per_core),
                'frequency_per_core': [
                    {
                        'current_mhz': freq.current,
                        'min_mhz': freq.min,
                        'max_mhz': freq.max
                    } for freq in cpu_freq
                ] if cpu_freq else None,
                'core_count': psutil.cpu_count(logical=False),
                'logical_count': psutil.cpu_count(logical=True)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_process_list(limit: int = 10) -> dict:
        """Get list of top processes by resource usage"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            return {
                'success': True,
                'processes': processes[:limit],
                'total_processes': len(processes)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
