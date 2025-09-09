"""
Helper utilities for media player application.
"""

import os
import time
from pathlib import Path


def formatFileSize(size_bytes):
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
        
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
        
    return f"{size_bytes:.1f} {size_names[i]}"


def formatDuration(seconds):
    """
    Format duration in human readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "1:23:45")
    """
    if seconds < 0:
        return "00:00"
        
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def getFileInfo(file_path):
    """
    Get file information.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file information
    """
    if not os.path.exists(file_path):
        return None
        
    stat = os.stat(file_path)
    
    return {
        'name': os.path.basename(file_path),
        'path': file_path,
        'size': stat.st_size,
        'size_formatted': formatFileSize(stat.st_size),
        'modified': time.ctime(stat.st_mtime),
        'extension': Path(file_path).suffix.lower()
    }


def ensureDirectoryExists(directory_path):
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory_path: Path to directory
    """
    os.makedirs(directory_path, exist_ok=True)


def getAppDataDir():
    """
    Get application data directory.
    
    Returns:
        Path to app data directory
    """
    if os.name == 'nt':  # Windows
        app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(app_data, 'StudioMediaPlayer')
    else:  # Unix-like
        return os.path.expanduser('~/.studio_media_player')


def getConfigFile():
    """
    Get configuration file path.
    
    Returns:
        Path to config file
    """
    app_dir = getAppDataDir()
    ensureDirectoryExists(app_dir)
    return os.path.join(app_dir, 'config.json')


def getCacheDir():
    """
    Get cache directory path.
    
    Returns:
        Path to cache directory
    """
    app_dir = getAppDataDir()
    cache_dir = os.path.join(app_dir, 'cache')
    ensureDirectoryExists(cache_dir)
    return cache_dir


def clamp(value, min_value, max_value):
    """
    Clamp value between min and max.
    
    Args:
        value: Value to clamp
        min_value: Minimum value
        max_value: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_value, min(value, max_value))


def lerp(start, end, t):
    """
    Linear interpolation between two values.
    
    Args:
        start: Start value
        end: End value
        t: Interpolation factor (0.0 - 1.0)
        
    Returns:
        Interpolated value
    """
    return start + (end - start) * clamp(t, 0.0, 1.0)


def isValidMediaFile(file_path):
    """
    Check if file is a valid media file.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file is valid media file
    """
    if not os.path.exists(file_path):
        return False
        
    # Check file size (must be > 0)
    if os.path.getsize(file_path) == 0:
        return False
        
    # Check if file is readable
    try:
        with open(file_path, 'rb') as f:
            f.read(1)
        return True
    except (IOError, OSError):
        return False
