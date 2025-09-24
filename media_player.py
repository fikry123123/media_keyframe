import os
import time
import cv2
import numpy as np
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QMimeData, QUrl
from PyQt5.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

class MediaPlayer(QWidget):
    frameIndexChanged = pyqtSignal(int, int)
    frameReady = pyqtSignal()
    playStateChanged = pyqtSignal(bool)
    fpsChanged = pyqtSignal(float)
    playbackFinished = pyqtSignal()
    fileDropped = pyqtSignal(str, str)
    
    def __init__(self, enable_audio=True):
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
        self.video_timer.setTimerType(Qt.PreciseTimer)
        self.video_timer.timeout.connect(self.update_video_frame)
        self.fps = 30
        self.current_media_path = None
        self.has_finished = False
        self._volume = 50
        self.loop_in_point = None
        self.loop_out_point = None
        self.enable_audio = enable_audio
        self.audio_player = QMediaPlayer(self) if enable_audio else None
        if self.audio_player:
            self.audio_player.setVolume(self._volume)
        self.playback_start_time = None
        self.compare_split_ratio = None

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

    def _prepare_audio(self, file_path):
        if not self.audio_player:
            return
        self.audio_player.stop()
        if file_path:
            media = QMediaContent(QUrl.fromLocalFile(file_path))
            self.audio_player.setMedia(media)
            self.audio_player.setVolume(self._volume)
            self._sync_audio_to_current_frame(force=True)
        else:
            self.audio_player.setMedia(QMediaContent())

    def _current_time_ms(self):
        if self.fps <= 0 or self.current_frame_index < 0:
            return 0
        return int((self.current_frame_index / self.fps) * 1000)

    def _sync_audio_to_current_frame(self, force=False):
        if not self.audio_player or self.fps <= 0 or self.current_frame_index < 0:
            return
        if self.is_playing and not force:
            return
        target_ms = self._current_time_ms()
        if force or abs(self.audio_player.position() - target_ms) > max(60, int(1000 / max(self.fps, 1))):
            self.audio_player.setPosition(target_ms)

    def _reset_playback_clock(self):
        if self.is_playing and self.fps > 0:
            self.playback_start_time = time.monotonic() - (self.current_frame_index / self.fps)
        elif not self.is_playing:
            self.playback_start_time = None

    def set_volume(self, value):
        self._volume = max(0, min(100, int(value)))
        if self.audio_player:
            self.audio_player.setVolume(self._volume)

    def volume(self):
        return self._volume
    
    def set_compare_split(self, width_a=None, width_b=None):
        if width_a is None or width_b is None:
            self.compare_split_ratio = None
            return
        if width_a <= 0 or width_b <= 0:
            self.compare_split_ratio = None
            return
        total = float(width_a + width_b)
        self.compare_split_ratio = (width_a / total) if total > 0 else None
        
    def set_loop_range(self, in_point, out_point):
        """Sets the loop-in and loop-out points for playback."""
        self.loop_in_point = in_point
        self.loop_out_point = out_point
        
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
                    self.has_finished = False 
                    self.playback_start_time = None
                    self._prepare_audio(file_path)
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
                self.has_finished = False
                self.playback_start_time = None
                self._prepare_audio(None)
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
            
    def toggle_play(self):
        if not self.is_video or not self.video_capture: return

        if self.has_finished:
            self.seek_to_position(0)
            self.has_finished = False

        if self.is_playing:
            self.video_timer.stop()
            self.is_playing = False
            self.playback_start_time = None
            if self.audio_player and self.audio_player.state() == QMediaPlayer.PlayingState:
                self.audio_player.pause()
        else:
            if self.fps > 0:
                interval = int(1000 / self.fps)
            else:
                interval = 41
            self.video_timer.start(interval)
            self.is_playing = True
            if self.fps > 0:
                self.playback_start_time = time.monotonic() - (self.current_frame_index / self.fps if self.current_frame_index >= 0 else 0)
            else:
                self.playback_start_time = time.monotonic()
            if self.audio_player and self.audio_player.mediaStatus() != QMediaPlayer.NoMedia:
                self._sync_audio_to_current_frame(force=True)
                self.audio_player.play()
        self.playStateChanged.emit(self.is_playing)
        
    def stop(self):
        if self.video_timer.isActive(): self.video_timer.stop()
        self.is_playing = False
        self.playback_start_time = None
        if self.audio_player:
            self.audio_player.stop()
        if self.is_video and self.video_capture:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame = frame
                self.displayed_frame_source = frame
                self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                self.display_frame(frame)
                self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
                self._sync_audio_to_current_frame(force=True)
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
                self._sync_audio_to_current_frame()
                self._reset_playback_clock()
        
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
                self._sync_audio_to_current_frame()
                self._reset_playback_clock()
        
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
                self.has_finished = False 
                self._sync_audio_to_current_frame(force=True)
                self._reset_playback_clock()
                
    def update_video_frame(self):
        if not self.is_video or not self.video_capture or not self.is_playing:
            return

        if self.loop_out_point is not None and self.current_frame_index >= self.loop_out_point:
            loop_start_frame = self.loop_in_point if self.loop_in_point is not None else 0
            self.seek_to_position(loop_start_frame)
            return

        if self.total_frames <= 0:
            self.stop()
            return

        target_index = self.current_frame_index + 1
        if self.fps > 0:
            now = time.monotonic()
            if self.playback_start_time is None:
                self.playback_start_time = now - (self.current_frame_index / self.fps if self.current_frame_index >= 0 else 0)
            elapsed = now - self.playback_start_time
            expected_index = int(elapsed * self.fps)
            if expected_index <= self.current_frame_index:
                expected_index = self.current_frame_index + 1
            target_index = min(expected_index, self.total_frames - 1)

        if target_index >= self.total_frames:
            self.video_timer.stop()
            self.is_playing = False
            self.has_finished = True
            self.playback_start_time = None
            if self.audio_player:
                self.audio_player.stop()
            self.playStateChanged.emit(False)
            self.playbackFinished.emit()
            return

        if target_index > self.current_frame_index + 1:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, target_index)

        ret, frame = self.video_capture.read()
        if ret:
            self.current_frame = frame
            self.displayed_frame_source = frame
            self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            self.display_frame(frame)
            self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
            self._sync_audio_to_current_frame()
            self._reset_playback_clock()
        else:
            self.video_timer.stop()
            self.is_playing = False
            self.has_finished = True
            self.playback_start_time = None
            if self.audio_player:
                self.audio_player.stop()
            self.playStateChanged.emit(False)
            self.playbackFinished.emit()
            
    def closeEvent(self, event):
        if self.video_capture: self.video_capture.release()
        if self.audio_player:
            self.audio_player.stop()
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
        self.loop_in_point = None
        self.loop_out_point = None
        self.playback_start_time = None
        self._prepare_audio(None)
        self.compare_split_ratio = None

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
            split_ratio = self.compare_split_ratio if self.compare_split_ratio is not None else 0.5
            if split_ratio <= 0.0 or split_ratio >= 1.0:
                split_ratio = 0.5
            split_x = self.width() * split_ratio

            pixmap = self.video_label.pixmap()
            if pixmap:
                pm_width = pixmap.width()
                label_width = self.video_label.width()
                offset_x = (label_width - pm_width) / 2
                relative_x = pos.x() - offset_x
                if 0 <= relative_x <= pm_width:
                    split_x = offset_x + pm_width * split_ratio
            target_view = 'A'
            if pos.x() > split_x:
                target_view = 'B'

            self.fileDropped.emit(file_path, target_view)
            event.acceptProposedAction()