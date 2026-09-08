import os
import shutil
from pathlib import Path
from typing import List, Optional
import glob

class FileSystemTools:
    """Tools for file system operations"""
    
    @staticmethod
    def list_files(
        directory: str,
        pattern: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> dict:
        """
        List files in a directory
        
        Args:
            directory: Directory path
            pattern: Glob pattern (e.g., "*.pdf")
            file_type: File extension filter (e.g., "pdf")
        
        Returns:
            {'success': bool, 'files': List[dict]}
        """
        try:
            # Expand user path
            directory = os.path.expanduser(directory)
            directory = os.path.expandvars(directory)
            
            if not os.path.exists(directory):
                return {
                    'success': False,
                    'error': f'Directory not found: {directory}'
                }
            
            # Build search pattern
            if pattern:
                search_pattern = os.path.join(directory, pattern)
            elif file_type:
                search_pattern = os.path.join(directory, f'*.{file_type}')
            else:
                search_pattern = os.path.join(directory, '*')
            
            # Find files
            files = []
            for file_path in glob.glob(search_pattern):
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        'name': os.path.basename(file_path),
                        'path': file_path,
                        'size_bytes': stat.st_size,
                        'size_mb': round(stat.st_size / 1024 / 1024, 2),
                        'modified': stat.st_mtime,
                        'extension': os.path.splitext(file_path)[1]
                    })
            
            # Sort by modified time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            return {
                'success': True,
                'files': files,
                'count': len(files),
                'directory': directory
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_folder(path: str) -> dict:
        """Create a new folder"""
        try:
            path = os.path.expanduser(path)
            path = os.path.expandvars(path)
            
            os.makedirs(path, exist_ok=True)
            
            return {
                'success': True,
                'path': path,
                'message': f'Folder created: {path}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def delete_file(path: str, confirm: bool = False) -> dict:
        """
        Delete a file
        
        Args:
            path: File path
            confirm: Must be True for destructive operations
        """
        if not confirm:
            return {
                'success': False,
                'error': 'Confirmation required for file deletion',
                'requires_confirmation': True
            }
        
        try:
            path = os.path.expanduser(path)
            
            if not os.path.exists(path):
                return {'success': False, 'error': 'File not found'}
            
            if os.path.isfile(path):
                os.remove(path)
                return {
                    'success': True,
                    'message': f'File deleted: {path}'
                }
            else:
                return {'success': False, 'error': 'Path is not a file'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def copy_file(source: str, destination: str) -> dict:
        """Copy a file"""
        try:
            source = os.path.expanduser(source)
            destination = os.path.expanduser(destination)
            
            if not os.path.exists(source):
                return {'success': False, 'error': 'Source file not found'}
            
            shutil.copy2(source, destination)
            
            return {
                'success': True,
                'source': source,
                'destination': destination,
                'message': 'File copied successfully'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def move_file(source: str, destination: str) -> dict:
        """Move a file"""
        try:
            source = os.path.expanduser(source)
            destination = os.path.expanduser(destination)
            
            if not os.path.exists(source):
                return {'success': False, 'error': 'Source file not found'}
            
            shutil.move(source, destination)
            
            return {
                'success': True,
                'source': source,
                'destination': destination,
                'message': 'File moved successfully'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def rename_file(path: str, new_name: str) -> dict:
        """Rename a file"""
        try:
            path = os.path.expanduser(path)
            
            if not os.path.exists(path):
                return {'success': False, 'error': 'File not found'}
            
            directory = os.path.dirname(path)
            new_path = os.path.join(directory, new_name)
            
            os.rename(path, new_path)
            
            return {
                'success': True,
                'old_path': path,
                'new_path': new_path,
                'message': f'Renamed to: {new_name}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def read_text_file(path: str, max_lines: int = 100) -> dict:
        """Read a text file"""
        try:
            path = os.path.expanduser(path)
            
            if not os.path.exists(path):
                return {'success': False, 'error': 'File not found'}
            
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:max_lines]
            
            return {
                'success': True,
                'content': ''.join(lines),
                'lines_read': len(lines),
                'truncated': len(lines) >= max_lines
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def write_text_file(path: str, content: str) -> dict:
        """Write to a text file"""
        try:
            path = os.path.expanduser(path)
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'path': path,
                'bytes_written': len(content.encode('utf-8')),
                'message': 'File written successfully'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_file_info(path: str) -> dict:
        """Get detailed file information"""
        try:
            path = os.path.expanduser(path)
            
            if not os.path.exists(path):
                return {'success': False, 'error': 'File not found'}
            
            stat = os.stat(path)
            
            return {
                'success': True,
                'path': path,
                'name': os.path.basename(path),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / 1024 / 1024, 2),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'accessed': stat.st_atime,
                'is_file': os.path.isfile(path),
                'is_directory': os.path.isdir(path),
                'extension': os.path.splitext(path)[1]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
