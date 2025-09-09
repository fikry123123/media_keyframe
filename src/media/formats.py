"""
Media Formats Handler.
Menangani deteksi dan validasi format media yang didukung.
"""

import os
from pathlib import Path


class MediaFormats:
    """Handler untuk format media yang didukung."""
    
    # Format yang didukung
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.exr'}
    SUPPORTED_VIDEO_FORMATS = {'.mov', '.mp4'}
    SUPPORTED_AUDIO_FORMATS = {'.mp3'}
    
    ALL_SUPPORTED_FORMATS = (
        SUPPORTED_IMAGE_FORMATS | 
        SUPPORTED_VIDEO_FORMATS | 
        SUPPORTED_AUDIO_FORMATS
    )
    
    @classmethod
    def isSupported(cls, file_path):
        """Check if file format is supported."""
        if not file_path or not os.path.exists(file_path):
            return False
            
        extension = Path(file_path).suffix.lower()
        return extension in cls.ALL_SUPPORTED_FORMATS
        
    @classmethod
    def getMediaType(cls, file_path):
        """Get media type (image, video, audio)."""
        if not cls.isSupported(file_path):
            return None
            
        extension = Path(file_path).suffix.lower()
        
        if extension in cls.SUPPORTED_IMAGE_FORMATS:
            return 'image'
        elif extension in cls.SUPPORTED_VIDEO_FORMATS:
            return 'video'
        elif extension in cls.SUPPORTED_AUDIO_FORMATS:
            return 'audio'
        else:
            return None
            
    @classmethod
    def isImage(cls, file_path):
        """Check if file is an image."""
        return cls.getMediaType(file_path) == 'image'
        
    @classmethod
    def isVideo(cls, file_path):
        """Check if file is a video."""
        return cls.getMediaType(file_path) == 'video'
        
    @classmethod
    def isAudio(cls, file_path):
        """Check if file is audio."""
        return cls.getMediaType(file_path) == 'audio'
        
    @classmethod
    def getSupportedExtensions(cls):
        """Get list of all supported extensions."""
        return sorted(list(cls.ALL_SUPPORTED_FORMATS))
        
    @classmethod
    def getFileFilter(cls):
        """Get file filter string for file dialogs."""
        image_exts = " ".join([f"*{ext}" for ext in cls.SUPPORTED_IMAGE_FORMATS])
        video_exts = " ".join([f"*{ext}" for ext in cls.SUPPORTED_VIDEO_FORMATS])
        audio_exts = " ".join([f"*{ext}" for ext in cls.SUPPORTED_AUDIO_FORMATS])
        all_exts = " ".join([f"*{ext}" for ext in cls.ALL_SUPPORTED_FORMATS])
        
        return (
            f"Media Files ({all_exts});;"
            f"Images ({image_exts});;"
            f"Videos ({video_exts});;"
            f"Audio ({audio_exts});;"
            "All Files (*)"
        )
