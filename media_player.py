from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QPen, QFont, QImage
import cv2
import numpy as np

class MediaPlayer(QWidget):
    frameIndexChanged = pyqtSignal(int, int)  # current_frame, total_frames
    frameReady = pyqtSignal()
    playStateChanged = pyqtSignal(bool)
    fpsChanged = pyqtSignal(float)
    
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
        self.current_media_path = None # Melacak path file saat ini

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                /* Hapus border dan margin untuk menghilangkan celah */
                border: none; 
                margin: 0px;
                color: #cccccc;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        self.video_label.setText("Load media file to start...")
        layout.addWidget(self.video_label)
        
    def load_media(self, file_path):
        self.clear_media() # Hapus media sebelumnya sebelum memuat yang baru
        self.current_media_path = None # Reset path di awal
        try:
            print(f"Attempting to load: {file_path}")
            
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None
                
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
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
                    
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if ret:
                        self.current_frame = frame
                        self.display_frame(frame)
                        self.frameIndexChanged.emit(0, self.total_frames)
                        self.fpsChanged.emit(self.fps) # Kirimkan nilai FPS
                        self.frameReady.emit()
                        self.current_media_path = file_path # Simpan path
                        return True
                else:
                    print(f"Could not read frame from video: {file_path}")
                    cap.release()
            else:
                print(f"Could not open as video: {file_path}")
            
            frame = cv2.imread(file_path)
            if frame is not None:
                print(f"Image loaded successfully: {file_path}")
                self.is_video = False
                self.current_frame = frame
                self.total_frames = 1
                self.current_frame_index = 0
                self.display_frame(frame)
                self.frameIndexChanged.emit(0, 1)
                self.fpsChanged.emit(0.0) # FPS 0 untuk gambar statis
                self.frameReady.emit()
                self.current_media_path = file_path # Simpan path
                return True
                
        except Exception as e:
            print(f"Error loading media: {e}")
            self.video_label.setText(f"Error loading file: {file_path}")
            self.fpsChanged.emit(0.0)
            return False
            
        print(f"Unsupported file format: {file_path}")
        self.video_label.setText("Unsupported file format")
        self.fpsChanged.emit(0.0)
        return False
        
    def display_frame(self, frame):
        if frame is None:
            return
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Ambil ukuran QLabel untuk penskalaan
        label_size = self.video_label.size()
        
        # Jika ukuran label belum diinisialisasi atau terlalu kecil, gunakan ukuran hint sebagai fallback
        if label_size.width() <= 0 or label_size.height() <= 0:
            label_size = self.video_label.sizeHint()
            
        frame_height, frame_width = rgb_frame.shape[:2]
        
        # Perhitungan lebar/tinggi tanpa padding atau border
        label_width, label_height = label_size.width(), label_size.height()
        
        if label_width <= 0 or label_height <= 0:
            return
            
        scale_x = label_width / frame_width
        scale_y = label_height / frame_height
        scale = min(scale_x, scale_y)
        
        new_width = int(frame_width * scale)
        new_height = int(frame_height * scale)
        
        resized_frame = cv2.resize(rgb_frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        from PyQt5.QtGui import QImage, QPixmap
        h, w, ch = resized_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(resized_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        # Scaling the pixmap to fill the label completely
        self.video_label.setPixmap(pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_frame is not None:
            self.display_frame(self.current_frame)
            
    def toggle_play(self):
        if not self.is_video or not self.video_capture:
            return
            
        if self.is_playing:
            self.video_timer.stop()
            self.is_playing = False
        else:
            interval = int(1000 / self.fps)
            self.video_timer.start(interval)
            self.is_playing = True
        
        self.playStateChanged.emit(self.is_playing)
            
    def play(self):
        if not self.is_playing and self.is_video:
            print("Pemutaran dimulai")
            interval = int(1000 / self.fps)
            self.video_timer.start(interval)
            self.is_playing = True
            self.playStateChanged.emit(True)
        
    def stop(self):
        if self.video_timer.isActive():
            self.video_timer.stop()
        self.is_playing = False
        
        if self.is_video and self.video_capture:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame = frame
                self.current_frame_index = 0
                self.display_frame(frame)
                self.frameIndexChanged.emit(0, self.total_frames)
        
        self.playStateChanged.emit(False)
        
    def previous_frame(self):
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
        if not self.is_video or not self.video_capture:
            return
            
        ret, frame = self.video_capture.read()
        if ret:
            self.current_frame = frame
            self.current_frame_index += 1
            self.display_frame(frame)
            self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
        else:
            self.video_timer.stop()
            self.is_playing = False
            self.playStateChanged.emit(False)
            
    def closeEvent(self, event):
        if self.video_capture:
            self.video_capture.release()
        super().closeEvent(event)

    def has_media(self):
        """Mengembalikan True jika ada media yang dimuat."""
        return self.current_media_path is not None

    def get_current_file_path(self):
        """Mengembalikan path file media yang sedang dimuat."""
        return self.current_media_path

    def clear_media(self):
        """Menghentikan dan membersihkan media yang sedang dimuat."""
        self.stop()
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        
        self.current_media_path = None
        self.current_frame = None
        self.total_frames = 0
        self.current_frame_index = 0
        self.is_video = False
        self.video_label.setText("Load media file to start...")
        self.frameIndexChanged.emit(0, 0)
        self.fpsChanged.emit(0.0)

    def get_video_info(self):
        if self.is_video and self.video_capture:
            return {
                'is_video': True,
                'total_frames': self.total_frames,
                'fps': self.fps,
                'current_frame': self.current_frame_index,
                'is_playing': self.is_playing
            }
        return {'is_video': False}