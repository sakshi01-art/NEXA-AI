import subprocess
import psutil
try:
    import pygetwindow as gw
except ImportError:
    gw = None
from typing import Optional, List
import os

class WindowsApplicationTools:
    """Tools for managing Windows applications"""
    
    # Common application paths
    APP_PATHS = {
        'chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        'firefox': r'C:\Program Files\Mozilla Firefox\firefox.exe',
        'vscode': r'C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe',
        'notepad': 'notepad.exe',
        'explorer': 'explorer.exe',
        'cmd': 'cmd.exe',
        'powershell': 'powershell.exe',
    }
    
    @staticmethod
    def open_application(
        application: str,
        arguments: Optional[List[str]] = None
    ) -> dict:
        """
        Open an application
        
        Args:
            application: Application name or path
            arguments: Optional command-line arguments
        
        Returns:
            {'success': bool, 'process_id': int, 'message': str}
        """
        try:
            # Normalize application name
            app_name = application.lower().replace(' ', '')
            
            # Get executable path
            if app_name in WindowsApplicationTools.APP_PATHS:
                executable = WindowsApplicationTools.APP_PATHS[app_name]
                # Replace username placeholder
                executable = executable.replace(
                    '{username}',
                    os.getenv('USERNAME')
                )
            else:
                executable = application
            
            # Build command
            cmd = [executable]
            if arguments:
                cmd.extend(arguments)
            
            # Launch process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return {
                'success': True,
                'process_id': process.pid,
                'message': f'{application} opened successfully'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': f'{application} not found. Please check if it is installed.',
                'suggestion': 'Try using the full path to the executable'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to open {application}: {str(e)}'
            }
    
    @staticmethod
    def close_application(application: str) -> dict:
        """
        Close an application by name
        
        Args:
            application: Application name
        
        Returns:
            {'success': bool, 'closed_count': int}
        """
        try:
            app_name = application.lower()
            closed_count = 0
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if app_name in proc.info['name'].lower():
                        proc.terminate()
                        closed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if closed_count > 0:
                return {
                    'success': True,
                    'closed_count': closed_count,
                    'message': f'Closed {closed_count} instance(s) of {application}'
                }
            else:
                return {
                    'success': False,
                    'error': f'{application} is not running'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to close {application}: {str(e)}'
            }
    
    @staticmethod
    def list_running_applications() -> dict:
        """
        List all running applications
        
        Returns:
            {'success': bool, 'applications': List[dict]}
        """
        try:
            applications = []
            seen = set()
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    name = proc.info['name']
                    if name not in seen and not name.startswith('System'):
                        applications.append({
                            'name': name,
                            'pid': proc.info['pid'],
                            'memory_mb': proc.info['memory_info'].rss / 1024 / 1024
                        })
                        seen.add(name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by memory usage
            applications.sort(key=lambda x: x['memory_mb'], reverse=True)
            
            return {
                'success': True,
                'applications': applications,
                'count': len(applications)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def focus_window(title: str) -> dict:
        """
        Bring a window to focus by title
        
        Args:
            title: Window title (partial match)
        
        Returns:
            {'success': bool}
        """
        try:
            if not gw:
                return {'success': False, 'error': 'pygetwindow not installed'}
            windows = gw.getWindowsWithTitle(title)
            
            if windows:
                window = windows[0]
                window.activate()
                return {
                    'success': True,
                    'message': f'Focused window: {window.title}'
                }
            else:
                return {
                    'success': False,
                    'error': f'No window found with title containing: {title}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def minimize_window(title: str) -> dict:
        """Minimize a window by title"""
        try:
            windows = gw.getWindowsWithTitle(title)
            
            if windows:
                windows[0].minimize()
                return {'success': True}
            return {'success': False, 'error': 'Window not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def maximize_window(title: str) -> dict:
        """Maximize a window by title"""
        try:
            windows = gw.getWindowsWithTitle(title)
            
            if windows:
                windows[0].maximize()
                return {'success': True}
            return {'success': False, 'error': 'Window not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
