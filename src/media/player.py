"""
Media Player Core.
Core engine untuk pemrosesan dan playback media menggunakan PyAV.
"""

import os
import av
import cv2
import numpy as np
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QImage
from PIL import Image

from src.media.formats import MediaFormats
from src.media.frame_manager import FrameManager


class MediaPlayer(QObject):
    """Core media player menggunakan PyAV."""
    
    # Signals
    frameReady = pyqtSignal(QImage)
    positionChanged = pyqtSignal(float)  # Position as percentage
    durationChanged = pyqtSignal(float)  # Duration in seconds
    playbackStateChanged = pyqtSignal(bool)  # True if playing
    frameIndexChanged = pyqtSignal(int, int, float)  # current_frame, total_frames, fps
    errorOccurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.container = None
        self.video_stream = None
        self.audio_stream = None
        self.frame_manager = FrameManager()
        
        # Playback state
        self.current_file = None
        self.is_playing = False
        self.is_loaded = False
        self.current_frame_index = 0
        self.total_frames = 0
        self.fps = 0
        self.duration = 0.0
        self.current_frame = None
        
        # Playback timer
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.nextFrame)
        
    def loadFile(self, file_path):
        """Load media file."""
        try:
            self.stop()
            self.cleanup()
            
            if not MediaFormats.isSupported(file_path):
                raise ValueError(f"Unsupported file format: {file_path}")
                
            self.current_file = file_path
            media_type = MediaFormats.getMediaType(file_path)
            
            if media_type == 'image':
                self.loadImage(file_path)
            elif media_type == 'video':
                self.loadVideo(file_path)
            elif media_type == 'audio':
                self.loadAudio(file_path)
                
            self.is_loaded = True
            
        except Exception as e:
            self.errorOccurred.emit(f"Failed to load file: {str(e)}")
            
    def loadImage(self, file_path):
        """Load static image."""
        try:
            # Handle different image formats
            if file_path.lower().endswith('.exr'):
                # Use OpenCV for EXR files
                img = cv2.imread(file_path, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
                if img is None:
                    raise ValueError("Failed to load EXR file")
                # Convert to 8-bit for display
                img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                # Use PIL for standard formats
                pil_image = Image.open(file_path)
                img = np.array(pil_image.convert('RGB'))
                
            # Convert to QImage
            h, w, ch = img.shape
            bytes_per_line = ch * w
            qt_image = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            self.current_frame = qt_image
            self.total_frames = 1
            self.current_frame_index = 0
            self.fps = 0
            self.duration = 0.0
            
            # Emit signals
            self.frameReady.emit(qt_image)
            self.frameIndexChanged.emit(self.current_frame_index, self.total_frames, self.fps)
            self.durationChanged.emit(0.0)
            self.positionChanged.emit(0.0)
            
        except Exception as e:
            raise ValueError(f"Failed to load image: {str(e)}")
            
    def loadVideo(self, file_path):
        """Load video file using PyAV."""
        try:
            self.container = av.open(file_path)
            self.video_stream = self.container.streams.video[0]
            
            # Get video properties
            self.fps = float(self.video_stream.average_rate)
            self.total_frames = self.video_stream.frames
            self.duration = float(self.video_stream.duration * self.video_stream.time_base)
            
            if self.total_frames == 0:
                # Estimate frame count if not available
                self.total_frames = int(self.duration * self.fps)
                
            # Load first frame
            self.current_frame_index = 0
            self.seekToFrame(0)
            
            # Emit signals
            self.durationChanged.emit(self.duration)
            self.positionChanged.emit(0.0)
            
        except Exception as e:
            raise ValueError(f"Failed to load video: {str(e)}")
            
    def loadAudio(self, file_path):
        """Load audio file using PyAV."""
        try:
            self.container = av.open(file_path)
            self.audio_stream = self.container.streams.audio[0]
            
            # Get audio properties
            self.duration = float(self.audio_stream.duration * self.audio_stream.time_base)
            self.fps = 0  # No frames for audio
            self.total_frames = 0
            self.current_frame_index = 0
            
            # Create a simple audio visualization placeholder
            self.createAudioVisualization()
            
            # Emit signals
            self.durationChanged.emit(self.duration)
            self.positionChanged.emit(0.0)
            
        except Exception as e:
            raise ValueError(f"Failed to load audio: {str(e)}")
            
    def createAudioVisualization(self):
        """Create simple audio visualization."""
        # Create a simple waveform placeholder
        width, height = 800, 400
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img.fill(50)  # Dark gray background
        
        # Add some text
        cv2.putText(img, "Audio File", (width//2 - 80, height//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(img, os.path.basename(self.current_file), 
                   (width//2 - 100, height//2 + 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        
        # Convert to QImage
        bytes_per_line = 3 * width
        qt_image = QImage(img.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        self.current_frame = qt_image
        self.frameReady.emit(qt_image)
        self.frameIndexChanged.emit(self.current_frame_index, self.total_frames, self.fps)
        
    def play(self):
        """Start playback."""
        if not self.is_loaded or MediaFormats.isImage(self.current_file):
            return
            
        if not self.is_playing:
            self.is_playing = True
            
            if MediaFormats.isVideo(self.current_file) and self.fps > 0:
                # Start timer for video playback
                interval = int(1000 / self.fps)  # Convert to milliseconds
                self.playback_timer.start(interval)
                
            self.playbackStateChanged.emit(True)
            
    def pause(self):
        """Pause playback."""
        if self.is_playing:
            self.is_playing = False
            self.playback_timer.stop()
            self.playbackStateChanged.emit(False)
            
    def stop(self):
        """Stop playback."""
        self.pause()
        if self.is_loaded:
            self.seekToFrame(0)
            
    def nextFrame(self):
        """Go to next frame."""
        if not self.is_loaded or MediaFormats.isImage(self.current_file):
            return
            
        if self.current_frame_index < self.total_frames - 1:
            self.seekToFrame(self.current_frame_index + 1)
        else:
            # End of media
            self.pause()
            
    def previousFrame(self):
        """Go to previous frame."""
        if not self.is_loaded or MediaFormats.isImage(self.current_file):
            return
            
        if self.current_frame_index > 0:
            self.seekToFrame(self.current_frame_index - 1)
            
    def seekToFrame(self, frame_index):
        """Seek to specific frame."""
        if not self.is_loaded or not MediaFormats.isVideo(self.current_file):
            return
            
        try:
            frame_index = max(0, min(frame_index, self.total_frames - 1))
            
            # Calculate timestamp
            timestamp = frame_index / self.fps
            pts = int(timestamp / self.video_stream.time_base)
            
            # Seek to frame
            self.container.seek(pts, stream=self.video_stream)
            
            # Decode frame
            for frame in self.container.decode(video=0):
                # Convert frame to QImage
                img = frame.to_ndarray(format='rgb24')
                h, w, ch = img.shape
                bytes_per_line = ch * w
                qt_image = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
                
                self.current_frame = qt_image
                self.current_frame_index = frame_index
                
                # Emit signals
                self.frameReady.emit(qt_image)
                self.frameIndexChanged.emit(self.current_frame_index, self.total_frames, self.fps)
                position = frame_index / max(1, self.total_frames - 1)
                self.positionChanged.emit(position)
                break
                
        except Exception as e:
            self.errorOccurred.emit(f"Seek error: {str(e)}")
            
    def seekToPosition(self, position):
        """Seek to position (0.0 - 1.0)."""
        if not self.is_loaded:
            return
            
        if MediaFormats.isVideo(self.current_file):
            frame_index = int(position * max(1, self.total_frames - 1))
            self.seekToFrame(frame_index)
        elif MediaFormats.isAudio(self.current_file):
            # For audio, just update position
            self.positionChanged.emit(position)
            
    def isPlaying(self):
        """Check if media is playing."""
        return self.is_playing
        
    def getCurrentFrame(self):
        """Get current frame as QImage."""
        return self.current_frame
        
    def getFrameInfo(self):
        """Get current frame information."""
        return {
            'current_frame': self.current_frame_index,
            'total_frames': self.total_frames,
            'fps': self.fps,
            'duration': self.duration,
            'position': self.current_frame_index / max(1, self.total_frames - 1) if self.total_frames > 1 else 0.0
        }
        
    def cleanup(self):
        """Clean up resources."""
        self.pause()
        
        if self.container:
            self.container.close()
            self.container = None
            
        self.video_stream = None
        self.audio_stream = None
        self.current_file = None
        self.is_loaded = False
        self.current_frame = None
        self.current_frame_index = 0
        self.total_frames = 0
        self.fps = 0
        self.duration = 0.0
