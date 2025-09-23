"""
Frame Manager.
Mengelola cache dan navigasi frame untuk playback yang smooth.
"""

from collections import OrderedDict
from PyQt5.QtGui import QImage


class FrameManager:
    """Manager untuk caching dan navigasi frame."""
    
    def __init__(self, max_cache_size=100):
        """
        Initialize frame manager.
        
        Args:
            max_cache_size: Maximum number of frames to cache
        """
        self.max_cache_size = max_cache_size
        self.frame_cache = OrderedDict()
        self.current_sequence = []
        
    def addFrame(self, frame_index, frame):
        """
        Add frame to cache.
        
        Args:
            frame_index: Index of the frame
            frame: QImage frame data
        """
        if frame_index in self.frame_cache:
            # Move to end (most recently used)
            self.frame_cache.move_to_end(frame_index)
        else:
            # Add new frame
            self.frame_cache[frame_index] = frame
            
            # Remove oldest frame if cache is full
            if len(self.frame_cache) > self.max_cache_size:
                self.frame_cache.popitem(last=False)
                
    def getFrame(self, frame_index):
        """
        Get frame from cache.
        
        Args:
            frame_index: Index of the frame
            
        Returns:
            QImage frame or None if not cached
        """
        if frame_index in self.frame_cache:
            # Move to end (most recently used)
            self.frame_cache.move_to_end(frame_index)
            return self.frame_cache[frame_index]
        return None
        
    def hasFrame(self, frame_index):
        """
        Check if frame is cached.
        
        Args:
            frame_index: Index of the frame
            
        Returns:
            True if frame is cached
        """
        return frame_index in self.frame_cache
        
    def preloadFrames(self, start_index, count, loader_function):
        """
        Preload frames in background.
        
        Args:
            start_index: Starting frame index
            count: Number of frames to preload
            loader_function: Function to load frame by index
        """
        # This could be implemented with threading for background loading
        for i in range(start_index, start_index + count):
            if not self.hasFrame(i):
                try:
                    frame = loader_function(i)
                    if frame:
                        self.addFrame(i, frame)
                except Exception:
                    # Skip failed frames
                    continue
                    
    def clearCache(self):
        """Clear all cached frames."""
        self.frame_cache.clear()
        
    def getCacheInfo(self):
        """
        Get cache information.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'cached_frames': len(self.frame_cache),
            'max_cache_size': self.max_cache_size,
            'cache_utilization': len(self.frame_cache) / self.max_cache_size,
            'cached_indices': list(self.frame_cache.keys())
        }
        
    def setMaxCacheSize(self, size):
        """
        Set maximum cache size.
        
        Args:
            size: New maximum cache size
        """
        self.max_cache_size = size
        
        # Remove excess frames if new size is smaller
        while len(self.frame_cache) > self.max_cache_size:
            self.frame_cache.popitem(last=False)
            
    def getAdjacentFrames(self, current_index, radius=5):
        """
        Get list of frame indices around current frame for preloading.
        
        Args:
            current_index: Current frame index
            radius: Number of frames before and after to include
            
        Returns:
            List of frame indices to preload
        """
        start = max(0, current_index - radius)
        end = current_index + radius + 1
        return list(range(start, end))
