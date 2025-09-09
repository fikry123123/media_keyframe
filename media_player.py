from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QPen, QFont
import cv2
import numpy as np

class MediaPlayer(QWidget):
    frameIndexChanged = pyqtSignal(int, int)  # current_frame, total_frames
    frameReady = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_frame = None
        self.total_frames = 0
        self.current_frame_index = 0
        self.video_capture = None
        self.is_video = False
        self.is_playing = False
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video_frame)
        self.fps = 30  # Default FPS
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Video display area
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px solid #444444;
                border-radius: 8px;
                color: #cccccc;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        self.video_label.setText("Load media file to start...")
        layout.addWidget(self.video_label)
        
    def load_media(self, file_path):
        """Load a media file (video or image)"""
        try:
            print(f"Attempting to load: {file_path}")
            
            # Clean up previous video capture
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None
                
            # Try to load as video first
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                # Check if it's a valid video by reading first frame
                ret, frame = cap.read()
                if ret:
                    print(f"Video loaded successfully: {file_path}")
                    self.video_capture = cap
                    self.is_video = True
                    self.current_frame = frame
                    self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    self.fps = cap.get(cv2.CAP_PROP_FPS) or 30
                    self.current_frame_index = 0
                    
                    print(f"Video info: {self.total_frames} frames, {self.fps} FPS")
                    
                    # Reset to beginning
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if ret:
                        self.current_frame = frame
                        self.display_frame(frame)
                        self.frameIndexChanged.emit(0, self.total_frames)
                        self.frameReady.emit()
                        return True
                else:
                    print(f"Could not read frame from video: {file_path}")
                    cap.release()
            else:
                print(f"Could not open as video: {file_path}")
            
            # If video loading failed, try as image
            frame = cv2.imread(file_path)
            if frame is not None:
                print(f"Image loaded successfully: {file_path}")
                self.is_video = False
                self.current_frame = frame
                self.total_frames = 1
                self.current_frame_index = 0
                self.display_frame(frame)
                self.frameIndexChanged.emit(0, 1)
                self.frameReady.emit()
                return True
                
        except Exception as e:
            print(f"Error loading media: {e}")
            self.video_label.setText(f"Error loading file: {file_path}")
            return False
            
        print(f"Unsupported file format: {file_path}")
        self.video_label.setText("Unsupported file format")
        return False
        
    def display_frame(self, frame):
        """Display a frame in the video label"""
        if frame is None:
            return
            
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get label dimensions
        label_size = self.video_label.size()
        if label_size.width() <= 0 or label_size.height() <= 0:
            label_size = self.video_label.sizeHint()
            
        # Calculate scaling to fit the label while maintaining aspect ratio
        frame_height, frame_width = rgb_frame.shape[:2]
        label_width, label_height = label_size.width() - 20, label_size.height() - 20  # Padding
        
        if label_width <= 0 or label_height <= 0:
            return
            
        # Calculate scale factor
        scale_x = label_width / frame_width
        scale_y = label_height / frame_height
        scale = min(scale_x, scale_y)
        
        # Calculate new dimensions
        new_width = int(frame_width * scale)
        new_height = int(frame_height * scale)
        
        # Resize frame
        resized_frame = cv2.resize(rgb_frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Convert to QPixmap and display
        from PyQt5.QtGui import QImage, QPixmap
        h, w, ch = resized_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(resized_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        self.video_label.setPixmap(pixmap)
        
    def resizeEvent(self, event):
        """Handle widget resize events"""
        super().resizeEvent(event)
        if self.current_frame is not None:
            self.display_frame(self.current_frame)
            
    def toggle_play(self):
        """Toggle play/pause state"""
        if not self.is_video or not self.video_capture:
            return
            
        if self.is_playing:
            self.video_timer.stop()
            self.is_playing = False
        else:
            # Start video playback
            interval = int(1000 / self.fps)  # Convert FPS to milliseconds
            self.video_timer.start(interval)
            self.is_playing = True
        
    def stop(self):
        """Stop playback"""
        if self.video_timer.isActive():
            self.video_timer.stop()
        self.is_playing = False
        
        if self.is_video and self.video_capture:
            # Go back to first frame
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame = frame
                self.current_frame_index = 0
                self.display_frame(frame)
                self.frameIndexChanged.emit(0, self.total_frames)
        
    def previous_frame(self):
        """Go to previous frame"""
        if not self.is_video or not self.video_capture:
            return
            
        if self.current_frame_index > 0:
            new_index = self.current_frame_index - 1
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, new_index)
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame = frame
                self.current_frame_index = new_index
                self.display_frame(frame)
                self.frameIndexChanged.emit(new_index, self.total_frames)
        
    def next_frame(self):
        """Go to next frame"""
        if not self.is_video or not self.video_capture:
            return
            
        if self.current_frame_index < self.total_frames - 1:
            new_index = self.current_frame_index + 1
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, new_index)
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame = frame
                self.current_frame_index = new_index
                self.display_frame(frame)
                self.frameIndexChanged.emit(new_index, self.total_frames)
        
    def seek_to_position(self, position):
        """Seek to a specific position"""
        if not self.is_video or not self.video_capture:
            return
            
        frame_index = int(position)
        if 0 <= frame_index < self.total_frames:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame = frame
                self.current_frame_index = frame_index
                self.display_frame(frame)
                self.frameIndexChanged.emit(frame_index, self.total_frames)
                
    def update_video_frame(self):
        """Update video frame during playback"""
        if not self.is_video or not self.video_capture:
            return
            
        ret, frame = self.video_capture.read()
        if ret:
            self.current_frame = frame
            self.current_frame_index += 1
            self.display_frame(frame)
            self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
        else:
            # End of video
            self.video_timer.stop()
            self.is_playing = False
            
    def closeEvent(self, event):
        """Clean up when widget is closed"""
        if self.video_capture:
            self.video_capture.release()
        super().closeEvent(event)
        
    def get_video_info(self):
        """Get video information"""
        if self.is_video and self.video_capture:
            return {
                'is_video': True,
                'total_frames': self.total_frames,
                'fps': self.fps,
                'current_frame': self.current_frame_index,
                'is_playing': self.is_playing
            }
        return {'is_video': False}