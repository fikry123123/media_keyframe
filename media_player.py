from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
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
            # Try to load as image first
            frame = cv2.imread(file_path)
            if frame is not None:
                self.current_frame = frame
                self.total_frames = 1
                self.current_frame_index = 0
                self.display_frame(frame)
                self.frameIndexChanged.emit(0, 1)
                self.frameReady.emit()
                return True
            
            # Try to load as video
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    self.current_frame = frame
                    self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    self.current_frame_index = 0
                    self.display_frame(frame)
                    self.frameIndexChanged.emit(0, self.total_frames)
                    self.frameReady.emit()
                cap.release()
                return True
                
        except Exception as e:
            print(f"Error loading media: {e}")
            self.video_label.setText(f"Error loading file: {file_path}")
            return False
            
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
        # This will be handled by the main window for image sequences
        pass
        
    def stop(self):
        """Stop playback"""
        # This will be handled by the main window for image sequences
        pass
        
    def previous_frame(self):
        """Go to previous frame"""
        # This will be handled by the main window for image sequences
        pass
        
    def next_frame(self):
        """Go to next frame"""
        # This will be handled by the main window for image sequences
        pass
        
    def seek_to_position(self, position):
        """Seek to a specific position"""
        # This will be handled by the main window for image sequences
        pass