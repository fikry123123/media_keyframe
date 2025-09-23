import os
import cv2
import numpy as np
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QMimeData
from PyQt5.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent

class MediaPlayer(QWidget):
    frameIndexChanged = pyqtSignal(int, int)
    frameReady = pyqtSignal()
    playStateChanged = pyqtSignal(bool)
    fpsChanged = pyqtSignal(float)
    playbackFinished = pyqtSignal()
    fileDropped = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setup_ui()
        self.current_frame = None
        self.displayed_frame_source = None
        self.total_frames = 0
        self.current_frame_index = -1
        self.video_capture = None
        self.is_video = False
        self.is_playing = False
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video_frame)
        self.fps = 30
        self.current_media_path = None
        # --- TAMBAHAN BARU: Penanda status video selesai ---
        self.has_finished = False

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.video_label = QLabel()
        self.video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setScaledContents(False)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
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
        self.clear_media()
        if not file_path or not os.path.exists(file_path):
            self.video_label.setText("Load media for this view...")
            self.frameIndexChanged.emit(-1, 0)
            self.fpsChanged.emit(0.0)
            return False
            
        self.current_media_path = None
        try:
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    self.video_capture = cap
                    self.is_video = True
                    self.current_frame = frame
                    self.displayed_frame_source = frame
                    self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
                    self.fps = cap.get(cv2.CAP_PROP_FPS) or 30
                    self.current_frame_index = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                    self.display_frame(frame)
                    self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
                    self.fpsChanged.emit(self.fps)
                    self.frameReady.emit()
                    self.current_media_path = file_path
                    self.has_finished = False # Reset penanda saat load media baru
                    return True
                else:
                    cap.release()
            else:
                cap.release()
            
            frame = cv2.imread(file_path)
            if frame is not None:
                self.is_video = False
                self.current_frame = frame
                self.displayed_frame_source = frame
                self.total_frames = 1
                self.current_frame_index = 0
                self.display_frame(frame)
                self.frameIndexChanged.emit(0, 1)
                self.fpsChanged.emit(0.0)
                self.frameReady.emit()
                self.current_media_path = file_path
                self.has_finished = False # Reset penanda saat load media baru
                return True
        except Exception as e:
            print(f"Error loading media: {e}")
            self.video_label.setText(f"Error loading file: {file_path}")
            self.fpsChanged.emit(0.0)
            return False
        self.video_label.setText("Unsupported file format")
        self.fpsChanged.emit(0.0)
        return False
        
    def display_frame(self, frame):
        if frame is None:
            return
        
        self.displayed_frame_source = frame
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        widget_size = self.size()
        if widget_size.width() <= 0 or widget_size.height() <= 0: widget_size = self.video_label.size()
        if widget_size.width() <= 0 or widget_size.height() <= 0: widget_size = self.video_label.sizeHint()
        if widget_size.width() <= 0 or widget_size.height() <= 0: return
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(widget_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.displayed_frame_source is not None:
            self.display_frame(self.displayed_frame_source)
            
    # --- PERUBAHAN LOGIKA DI FUNGSI INI ---
    def toggle_play(self):
        if not self.is_video or not self.video_capture: return
        
        # Jika video sudah selesai, kembali ke awal sebelum memutar
        if self.has_finished:
            self.seek_to_position(0)
            self.has_finished = False
        
        if self.is_playing:
            self.video_timer.stop()
            self.is_playing = False
        else:
            if self.fps > 0:
                interval = int(1000 / self.fps)
            else:
                interval = 41 
            self.video_timer.start(interval)
            self.is_playing = True
        self.playStateChanged.emit(self.is_playing)
        
    def stop(self):
        if self.video_timer.isActive(): self.video_timer.stop()
        self.is_playing = False
        if self.is_video and self.video_capture:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame = frame
                self.displayed_frame_source = frame
                self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                self.display_frame(frame)
                self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
        self.playStateChanged.emit(False)
        self.has_finished = False
        
    def previous_frame(self):
        if not self.is_video or not self.video_capture: return
        new_index = self.current_frame_index - 1
        if new_index >= 0:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, new_index)
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame = frame
                self.displayed_frame_source = frame
                self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                self.display_frame(frame)
                self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
                self.has_finished = False
        
    def next_frame(self):
        if not self.is_video or not self.video_capture: return
        if self.current_frame_index < self.total_frames - 1:
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame = frame
                self.displayed_frame_source = frame
                self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                self.display_frame(frame)
                self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
                self.has_finished = False
        
    def seek_to_position(self, position):
        if not self.is_video or not self.video_capture: return
        frame_index = int(position)
        if 0 <= frame_index < self.total_frames:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame = frame
                self.displayed_frame_source = frame
                self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                self.display_frame(frame)
                self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
                self.has_finished = False # Jika user seek, video belum selesai
                
    def update_video_frame(self):
        if not self.is_video or not self.video_capture or not self.is_playing: return
        ret, frame = self.video_capture.read()
        if ret:
            self.current_frame = frame
            self.displayed_frame_source = frame
            self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            self.display_frame(frame)
            self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
        else:
            self.video_timer.stop()
            self.is_playing = False
            self.has_finished = True # Tandai video sudah selesai
            self.playStateChanged.emit(False)
            self.playbackFinished.emit()
            
    def closeEvent(self, event):
        if self.video_capture: self.video_capture.release()
        super().closeEvent(event)

    def has_media(self): return self.current_media_path is not None
    def get_current_file_path(self): return self.current_media_path

    def clear_media(self):
        self.stop()
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        self.current_media_path = None
        self.current_frame = None
        self.displayed_frame_source = None
        self.total_frames = 0
        self.current_frame_index = -1
        self.is_video = False
        self.video_label.setText("Load media file to start...")
        self.video_label.setPixmap(QPixmap())
        self.frameIndexChanged.emit(-1, 0)
        self.fpsChanged.emit(0.0)
        self.has_finished = False

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-playlist-paths"):
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        file_path = None
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                file_path = url.toLocalFile()
        elif event.mimeData().hasFormat("application/x-playlist-paths"):
            paths_data = event.mimeData().data("application/x-playlist-paths")
            paths = str(paths_data, 'utf-8').split(',')
            if paths:
                file_path = paths[0]
        
        if file_path:
            pos = event.pos()
            target_view = 'A'
            if pos.x() > self.width() / 2:
                target_view = 'B'
            
            self.fileDropped.emit(file_path, target_view)
            event.acceptProposedAction()