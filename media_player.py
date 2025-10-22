import os
import time
import cv2
import numpy as np
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QMimeData, QUrl, QPoint, QPointF
from PyQt5.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QPainter, QPen, QColor, QWheelEvent, QMouseEvent
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

class DrawingLabel(QLabel):
    """
    Label kustom yang menangani input mouse untuk menggambar PADA frame video,
    DAN menangani input zoom/pan PADA viewport.
    """
    def __init__(self, parent_media_player):
        super().__init__()
        self.media_player = parent_media_player
        self.drawing = False
        self.last_point_frame = None
        
        # --- PERBAIKAN: Lacak player mana yang sedang digambar ---
        self.last_target_player = None
        # --- AKHIR PERBAIKAN ---
        
        # --- State untuk Panning ---
        self.panning = False
        self.last_pan_pos = QPoint()
        # --- Akhir State Panning ---
        
        self.setMouseTracking(True) # Diperlukan untuk kursor

    def _map_widget_to_frame_coords(self, widget_pos: QPoint):
        """
        Memetakan koordinat QPoint dari widget label ke koordinat (x, y) 
        pada frame video asli.
        
        PERBAIKAN: Sekarang mengembalikan tuple (target_player, frame_pos_qpoint)
        target_player adalah instance MediaPlayer (A atau B)
        frame_pos_qpoint adalah QPoint di koordinat frame asli target
        """
        mp = self.media_player
        partner = mp.compare_partner
        
        # Tentukan dimensi frame target
        if mp.frame_dims_A is None:
            return None, None # Tidak ada media di A
        
        h_a, w_a, ch_a = mp.frame_dims_A

        # Pastikan kita memiliki info pixmap (tampilan)
        if not mp.pixmap_size or mp.pixmap_size.width() == 0 or mp.pixmap_size.height() == 0:
            return None, None

        # 1. Ubah koordinat widget (label) ke koordinat relatif pixmap (letterboxed)
        pixmap_relative_pos = widget_pos - mp.pixmap_offset
        
        # 2. Ubah ke koordinat panned
        panned_pos = pixmap_relative_pos - mp.zoom_pan
        
        # 3. Ubah ke koordinat scaled (batalkan zoom)
        scaled_pixmap_x = panned_pos.x() / mp.zoom_scale
        scaled_pixmap_y = panned_pos.y() / mp.zoom_scale

        # 4. Periksa apakah klik berada di dalam area pixmap yang di-render
        if not (0 <= scaled_pixmap_x < mp.pixmap_size.width() and 
                0 <= scaled_pixmap_y < mp.pixmap_size.height()):
            return None, None
            
        # 5. Ubah koordinat pixmap yang diskalakan ke koordinat frame asli
        if mp.compare_split_ratio is not None and partner:
            # --- Mode Compare ---
            # Hitung lebar Player A di dalam pixmap komposit
            split_width_a_scaled = mp.pixmap_size.width() * mp.compare_split_ratio
            split_width_b_scaled = mp.pixmap_size.width() - split_width_a_scaled

            if scaled_pixmap_x >= split_width_a_scaled:
                # --- Klik di VIEW B ---
                if partner.frame_dims_A is None: # Cek jika partner punya frame
                     return None, None
                h_b, w_b, _ = partner.frame_dims_A
                
                # Map dari koordinat B-scaled ke B-original
                # (scaled_pixmap_x - split_width_a_scaled) = X relatif di area B
                fx = (scaled_pixmap_x - split_width_a_scaled) * (w_b / split_width_b_scaled)
                fy = scaled_pixmap_y * (h_b / mp.pixmap_size.height()) # Tinggi A dan B sama
                
                return partner, QPoint(int(fx), int(fy))
                
            else:
                # --- Klik di VIEW A ---
                # Map dari koordinat A-scaled ke A-original
                fx = scaled_pixmap_x * (w_a / split_width_a_scaled)
                fy = scaled_pixmap_y * (h_a / mp.pixmap_size.height())
                
                return mp, QPoint(int(fx), int(fy))
        
        else:
            # --- Mode Single View ---
            # Map dari koordinat pixmap-scaled ke frame-original
            fx = scaled_pixmap_x * (w_a / mp.pixmap_size.width())
            fy = scaled_pixmap_y * (h_a / mp.pixmap_size.height())
            
            return mp, QPoint(int(fx), int(fy))


    def wheelEvent(self, event: QWheelEvent):
        """Menangani Ctrl+Scroll untuk Zoom."""
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            widget_pos = event.pos() 
            self.media_player.zoom(delta, widget_pos)
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton and self.media_player.zoom_scale > 1.0:
            self.panning = True
            self.last_pan_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        # --- PERBAIKAN: Logika drawing (Left Mouse) ---
        if event.button() == Qt.LeftButton and self.media_player.drawing_enabled and self.media_player.has_media():
            
            target_player, frame_pos = self._map_widget_to_frame_coords(event.pos())
            
            if target_player and frame_pos:
                self.drawing = True
                self.last_point_frame = frame_pos
                self.last_target_player = target_player # Simpan player yang dituju
                
                target_player.get_current_annotation_image() # Pastikan layer anotasi ada
                target_player.draw_on_annotation(frame_pos, frame_pos) # Gambar di player target
        else:
            super().mousePressEvent(event) # teruskan klik lain
        # --- AKHIR PERBAIKAN ---

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.panning:
            delta = event.pos() - self.last_pan_pos
            self.media_player.pan(delta)
            self.last_pan_pos = event.pos()
            event.accept()
            return

        # --- PERBAIKAN: Logika drawing (Left Mouse) ---
        if self.drawing and self.media_player.drawing_enabled:
            target_player, frame_pos = self._map_widget_to_frame_coords(event.pos())
            
            # Hanya menggambar jika masih di player yang sama
            if target_player and frame_pos and target_player == self.last_target_player:
                # Gambar garis dari titik terakhir ke titik sekarang
                target_player.draw_on_annotation(self.last_point_frame, frame_pos)
                self.last_point_frame = frame_pos
        else:
            super().mouseMoveEvent(event)
        # --- AKHIR PERBAIKAN ---

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton and self.panning:
            self.panning = False
            self.media_player.update_cursor() 
            event.accept()
            return

        # --- PERBAIKAN: Logika drawing (Left Mouse) ---
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            
            # Finalisasi di player yang terakhir digambar
            if self.last_target_player:
                self.last_target_player.finalize_drawing() 
                
            self.last_target_player = None
            self.last_point_frame = None
        else:
            super().mouseReleaseEvent(event)
        # --- AKHIR PERBAIKAN ---

class MediaPlayer(QWidget):
    frameIndexChanged = pyqtSignal(int, int)
    frameReady = pyqtSignal()
    playStateChanged = pyqtSignal(bool)
    fpsChanged = pyqtSignal(float)
    playbackFinished = pyqtSignal()
    fileDropped = pyqtSignal(str, str)
    annotationAdded = pyqtSignal(int) 
    viewNeedsRedraw = pyqtSignal()
    
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
        
        # --- PERBAIKAN: Tambah referensi ke partner ---
        self.compare_partner = None
        # --- AKHIR PERBAIKAN ---
        
        self.annotations = {} 
        self.drawing_enabled = False
        self.draw_pen_color = QColor(255, 0, 0, 255) 
        self.draw_pen_width = 5
        
        self.zoom_scale = 1.0
        self.zoom_pan = QPoint(0, 0)
        
        self.pixmap_offset = QPoint(0, 0)
        self.pixmap_size = None
        self.frame_dims = None # (h, w, ch)
        self.frame_dims_A = None # Dimensi asli Player A (untuk compare mode drawing)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.video_label = DrawingLabel(self) 
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

    # --- PERBAIKAN: Fungsi baru untuk set partner ---
    def set_compare_partner(self, partner):
        """Menyimpan referensi ke media player B."""
        self.compare_partner = partner
    # --- AKHIR PERBAIKAN ---

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
        
        path_exists = False
        if file_path:
            if '%' in file_path:
                dir_path = os.path.dirname(file_path)
                path_exists = os.path.isdir(dir_path)
            else:
                path_exists = os.path.exists(file_path)

        if not file_path or not path_exists:
            self.video_label.setText("File or sequence directory not found...")
            self.frameIndexChanged.emit(-1, 0)
            self.fpsChanged.emit(0.0)
            return False
            
        self.current_media_path = None
        try:
            cap = cv2.VideoCapture(file_path, cv2.CAP_FFMPEG)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    self.video_capture = cap
                    self.is_video = True
                    self.current_frame = frame
                    self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
                    self.fps = cap.get(cv2.CAP_PROP_FPS) or 24 
                    if self.fps == 0: self.fps = 24
                    self.current_frame_index = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                    
                    # Simpan dimensi Player A (untuk compare drawing)
                    h, w, ch = frame.shape
                    self.frame_dims_A = (h, w, ch)
                    
                    self.display_frame(frame) 
                    self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
                    self.fpsChanged.emit(self.fps)
                    self.frameReady.emit()
                    self.current_media_path = file_path
                    self.has_finished = False 
                    self.playback_start_time = None
                    self._prepare_audio(file_path if '%' not in file_path else None) 
                    return True
                else:
                    cap.release()
            else:
                cap.release()
            
            frame = cv2.imread(file_path)
            if frame is not None:
                self.is_video = False
                self.current_frame = frame
                self.total_frames = 1
                self.current_frame_index = 0
                
                # Simpan dimensi Player A (untuk compare drawing)
                h, w, ch = frame.shape
                self.frame_dims_A = (h, w, ch)
                
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
            self.pixmap_size = None
            self.pixmap_offset = QPoint(0, 0)
            self.frame_dims = None
            self.video_label.setPixmap(QPixmap())
            return
        
        self.displayed_frame_source = frame.copy() 
        
        rgb_frame = cv2.cvtColor(self.displayed_frame_source, cv2.COLOR_BGR2RGB)
        
        h, w, ch = rgb_frame.shape
        self.frame_dims = (h, w, ch)
        
        widget_size = self.size()
        if widget_size.width() <= 0 or widget_size.height() <= 0: widget_size = self.video_label.size()
        if widget_size.width() <= 0 or widget_size.height() <= 0: widget_size = self.video_label.sizeHint()
        if widget_size.width() <= 0 or widget_size.height() <= 0: return

        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        scaled_pixmap = pixmap.scaled(widget_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # (Anotasi di mode compare sudah dibake oleh main_window)
        annotation_image = self.annotations.get(self.current_frame_index)
        if annotation_image and self.compare_split_ratio is None: # Hanya gambar di mode single
            annotation_pixmap = QPixmap.fromImage(annotation_image)
            scaled_annotation = annotation_pixmap.scaled(scaled_pixmap.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter = QPainter(scaled_pixmap)
            painter.drawPixmap(0, 0, scaled_annotation)
            painter.end()

        self.pixmap_size = scaled_pixmap.size()
        lbl_size = self.video_label.size()
        self.pixmap_offset = QPoint((lbl_size.width() - self.pixmap_size.width()) // 2, (lbl_size.height() - self.pixmap_size.height()) // 2)

        final_canvas = QPixmap(widget_size)
        final_canvas.fill(QColor("#1a1a1a")) 
        
        painter = QPainter(final_canvas)
        
        if self.zoom_scale == 1.0:
            painter.drawPixmap(self.pixmap_offset, scaled_pixmap)
        else:
            zoomed_pixmap = scaled_pixmap.scaled(
                self.pixmap_size * self.zoom_scale, 
                Qt.IgnoreAspectRatio, 
                Qt.SmoothTransformation
            )
            draw_pos = self.pixmap_offset + self.zoom_pan
            painter.drawPixmap(draw_pos, zoomed_pixmap)
            
        painter.end()
        
        self.video_label.setPixmap(final_canvas)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.displayed_frame_source is not None:
            self.display_frame(self.displayed_frame_source)
            
    def toggle_play(self):
        if not self.is_video or not self.video_capture: return

        if self.has_finished:
            is_in_loop_range = (self.loop_out_point is not None and 
                                self.current_frame_index >= self.loop_out_point)
            
            if not is_in_loop_range:
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
                interval = 41 # Default ~24fps
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
                self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                self.display_frame(frame)
                self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
                self.has_finished = False 
                self.has_finished = (frame_index == self.total_frames - 1) # Set finished jika seek ke frame terakhir
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
            self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            self.display_frame(frame)
            self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
            self._sync_audio_to_current_frame()
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
        
        # --- PERBAIKAN: Reset partner ---
        self.compare_partner = None
        # --- AKHIR PERBAIKAN ---
        
        self.annotations.clear()
        self.pixmap_offset = QPoint(0, 0)
        self.pixmap_size = None
        self.frame_dims = None
        self.frame_dims_A = None 
        self.drawing_enabled = False
        self.video_label.setCursor(Qt.ArrowCursor)
        
        self.zoom_scale = 1.0
        self.zoom_pan = QPoint(0, 0)

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
    
    def get_current_annotation_image(self):
        """
        Mengambil layer anotasi QImage untuk frame saat ini.
        Membuatnya jika belum ada.
        INI SELALU MENGGUNAKAN frame_dims_A KARENA INI ADALAH FUNGSI DARI
        INSTANCE MediaPlayer (A atau B)
        """
        if self.current_frame_index < 0 or not self.frame_dims_A:
            return None
        
        image = self.annotations.get(self.current_frame_index)
        
        if image is None:
            h, w, ch = self.frame_dims_A
            image = QImage(w, h, QImage.Format_ARGB32)
            image.fill(Qt.transparent)
            self.annotations[self.current_frame_index] = image
            
        return image

    def draw_on_annotation(self, from_point_frame, to_point_frame):
        """
        Menggambar garis pada layer anotasi (dalam koordinat frame).
        """
        image = self.get_current_annotation_image()
        if image:
            painter = QPainter(image)
            pen = QPen(self.draw_pen_color, self.draw_pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            
            if self.draw_pen_color.alpha() == 0:
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
            
            painter.drawLine(from_point_frame, to_point_frame)
            painter.end()
            
            # --- PERBAIKAN: START ---
            if self.compare_split_ratio is None:
                # Mode Single: refresh internal
                self.display_frame(self.displayed_frame_source)
            else:
                # Mode Compare: beri tahu main_window untuk refresh
                # (Ini akan dipanggil oleh instance A atau B)
                self.viewNeedsRedraw.emit()
            # --- PERBAIKAN: END ---

    def finalize_drawing(self):
        """
        Dipanggil saat mouse dilepas setelah menggambar.
        """
        if self.current_frame_index >= 0:
            self.annotationAdded.emit(self.current_frame_index)
            
    def update_cursor(self):
        """Mengatur kursor berdasarkan state saat ini."""
        if self.video_label.panning:
            self.video_label.setCursor(Qt.ClosedHandCursor)
        elif self.drawing_enabled:
            self.video_label.setCursor(Qt.CrossCursor)
        elif self.zoom_scale > 1.0:
            self.video_label.setCursor(Qt.OpenHandCursor)
        else:
            self.video_label.setCursor(Qt.ArrowCursor)

    def pan(self, delta: QPoint):
        """Memindahkan pan offset dan menggambar ulang."""
        self.zoom_pan += delta
        self.display_frame(self.displayed_frame_source)

    def zoom(self, delta: int, widget_pos: QPoint):
        """Memperbesar/memperkecil di sekitar widget_pos."""
        old_scale = self.zoom_scale
        
        if delta > 0:
            self.zoom_scale *= 1.15
        else:
            self.zoom_scale /= 1.15
            
        self.zoom_scale = max(1.0, self.zoom_scale) 

        if self.zoom_scale == 1.0:
            self.zoom_pan = QPoint(0, 0)
        else:
            pixmap_relative_pos = widget_pos - self.pixmap_offset
            panned_pixmap_pos = pixmap_relative_pos - self.zoom_pan
            
            new_pan_x = pixmap_relative_pos.x() - (panned_pixmap_pos.x() * self.zoom_scale / old_scale)
            new_pan_y = pixmap_relative_pos.y() - (panned_pixmap_pos.y() * self.zoom_scale / old_scale)
            
            self.zoom_pan = QPoint(int(new_pan_x), int(new_pan_y))

        self.display_frame(self.displayed_frame_source)
        self.update_cursor()