#!/usr/bin/env python3
import os
import time
import cv2
import numpy as np
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QMimeData, QUrl, QPoint, QSize
from PyQt5.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QPainter, QPen, QColor

# --- Impor VLC ---
try:
    import vlc
except ImportError:
    print("="*50)
    print("ERROR: Pustaka 'python-vlc' tidak ditemukan.")
    print("Silakan instal dengan menjalankan: pip install python-vlc")
    print("="*50)
    vlc = None
# --- Akhir Impor ---


class DrawingLabel(QLabel):
    """
    Label kustom yang menangani input mouse untuk menggambar pada frame video.
    """
    def __init__(self, parent_media_player):
        super().__init__()
        self.media_player = parent_media_player
        self.drawing = False
        self.last_point_frame = None
        self.setMouseTracking(True) 
        self.panning = False
        self.last_pan_pos = QPoint(0, 0)

    def _map_widget_to_frame_coords(self, widget_pos):
        """
        Memetakan koordinat QPoint dari widget label ke koordinat (x, y) 
        pada frame video asli.
        """
        mp = self.media_player
        if not mp.pixmap_size or mp.pixmap_size.width() == 0 or mp.pixmap_size.height() == 0 or mp.frame_dims is None:
            return None
        pixmap_pos = widget_pos - mp.pixmap_offset
        if not (0 <= pixmap_pos.x() < mp.pixmap_size.width() and 0 <= pixmap_pos.y() < mp.pixmap_size.height()):
            return None
        h, w, ch = mp.frame_dims
        fx = pixmap_pos.x() * (w / mp.pixmap_size.width())
        fy = pixmap_pos.y() * (h / mp.pixmap_size.height())
        return QPoint(int(fx), int(fy))

    def mousePressEvent(self, event):
        # Prioritas 1: Panning Tombol Tengah
        if event.button() == Qt.MiddleButton:
            if self.media_player.zoom_factor > 1.001: 
                self.panning = True
                self.last_pan_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return 
                
        # Prioritas 2: Tombol Kiri
        if event.button() == Qt.LeftButton:
            if self.media_player.drawing_enabled and self.media_player.has_media():
                frame_pos = self._map_widget_to_frame_coords(event.pos())
                if frame_pos:
                    self.drawing = True
                    self.last_point_frame = frame_pos
                    self.media_player.get_current_annotation_image()
                    self.media_player.draw_on_annotation(frame_pos, frame_pos) 
                    event.accept()
                    return 
            elif not self.media_player.drawing_enabled and self.media_player.zoom_factor > 1.001:
                self.panning = True
                self.last_pan_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return
                
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.last_point_frame = None
            self.media_player.finalize_drawing() 
            event.accept()
            return 
        if (event.button() == Qt.LeftButton or event.button() == Qt.MiddleButton) and self.panning:
            self.panning = False
            if self.media_player.drawing_enabled:
                self.setCursor(Qt.CrossCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
        
    def mouseMoveEvent(self, event):
        if self.panning and (event.buttons() & Qt.LeftButton or event.buttons() & Qt.MiddleButton):
            if self.media_player.frame_dims is None:
                event.accept()
                return
            delta = event.pos() - self.last_pan_pos
            new_pan_offset = self.media_player.pan_offset + delta
            h, w, ch = self.media_player.frame_dims
            widget_size = self.media_player.size()
            scale_w = widget_size.width() / w if w > 0 else 0
            scale_h = widget_size.height() / h if h > 0 else 0
            base_scale = min(scale_w, scale_h) if min(scale_w, scale_h) > 0 else 1.0
            total_scale = base_scale * self.media_player.zoom_factor
            scaled_w = int(w * total_scale)
            scaled_h = int(h * total_scale)
            center_x = (widget_size.width() - scaled_w) // 2
            center_y = (widget_size.height() - scaled_h) // 2
            max_pan_x = -center_x
            min_pan_x = widget_size.width() - scaled_w - center_x
            max_pan_y = -center_y
            min_pan_y = widget_size.height() - scaled_h - center_y
            final_pan_x = max(min_pan_x, min(new_pan_offset.x(), max_pan_x))
            final_pan_y = max(min_pan_y, min(new_pan_offset.y(), max_pan_y))
            self.media_player.pan_offset = QPoint(final_pan_x, final_pan_y)
            self.last_pan_pos = event.pos()
            if self.media_player.displayed_frame_source is not None:
                self.media_player.display_frame(self.media_player.displayed_frame_source)
            event.accept()
            return
        elif self.drawing and self.media_player.drawing_enabled and (event.buttons() & Qt.LeftButton):
            frame_pos = self._map_widget_to_frame_coords(event.pos())
            if frame_pos:
                self.media_player.draw_on_annotation(self.last_point_frame, frame_pos)
                self.last_point_frame = frame_pos
                event.accept()
                return
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        if not self.media_player.has_media() or self.media_player.frame_dims is None:
            event.ignore()
            return
        zoom_delta = event.angleDelta().y() / 120
        zoom_step = 1.15
        old_zoom = self.media_player.zoom_factor
        if zoom_delta > 0:
            new_zoom = old_zoom * zoom_step
        else:
            new_zoom = old_zoom / zoom_step
        new_zoom = max(1.0, min(new_zoom, 20.0))
        if abs(new_zoom - old_zoom) < 0.001:
            event.accept()
            return
        self.media_player.zoom_factor = new_zoom
        widget_pos = event.pos()
        h, w, ch = self.media_player.frame_dims
        widget_size = self.media_player.size()
        scale_w = widget_size.width() / w if w > 0 else 0
        scale_h = widget_size.height() / h if h > 0 else 0
        base_scale = min(scale_w, scale_h) if min(scale_w, scale_h) > 0 else 1.0
        old_total_scale = base_scale * old_zoom
        new_total_scale = base_scale * new_zoom
        old_scaled_size = QSize(int(w * old_total_scale), int(h * old_total_scale))
        new_scaled_size = QSize(int(w * new_total_scale), int(h * new_total_scale))
        old_offset_x = (widget_size.width() - old_scaled_size.width()) // 2 + self.media_player.pan_offset.x()
        old_offset_y = (widget_size.height() - old_scaled_size.height()) // 2 + self.media_player.pan_offset.y()
        old_pixmap_x = widget_pos.x() - old_offset_x
        old_pixmap_y = widget_pos.y() - old_offset_y
        if old_scaled_size.width() == 0 or old_scaled_size.height() == 0:
            frac_x, frac_y = 0.5, 0.5
        else:
            frac_x = old_pixmap_x / old_scaled_size.width()
            frac_y = old_pixmap_y / old_scaled_size.height()
        new_pixmap_x = frac_x * new_scaled_size.width()
        new_pixmap_y = frac_y * new_scaled_size.height()
        new_center_x = (widget_size.width() - new_scaled_size.width()) // 2
        new_center_y = (widget_size.height() - new_scaled_size.height()) // 2
        new_pan_x = widget_pos.x() - new_center_x - new_pixmap_x
        new_pan_y = widget_pos.y() - new_center_y - new_pixmap_y
        if new_zoom <= 1.001:
            self.media_player.pan_offset = QPoint(0, 0)
        else:
            max_pan_x = -new_center_x
            min_pan_x = widget_size.width() - new_scaled_size.width() - new_center_x
            max_pan_y = -new_center_y
            min_pan_y = widget_size.height() - new_scaled_size.height() - new_center_y
            final_pan_x = max(min_pan_x, min(int(new_pan_x), max_pan_x))
            final_pan_y = max(min_pan_y, min(int(new_pan_y), max_pan_y))
            self.media_player.pan_offset = QPoint(final_pan_x, final_pan_y)
        if self.media_player.displayed_frame_source is not None:
            self.media_player.display_frame(self.media_player.displayed_frame_source)
        event.accept()

# --- Akhir dari class DrawingLabel ---


class MediaPlayer(QWidget):
    frameIndexChanged = pyqtSignal(int, int)
    frameReady = pyqtSignal()
    playStateChanged = pyqtSignal(bool)
    fpsChanged = pyqtSignal(float)
    playbackFinished = pyqtSignal(bool)
    fileDropped = pyqtSignal(str, str)
    annotationAdded = pyqtSignal(int)
    
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
        
        # --- KONEKSI TIMER (INI YANG GAGAL SEBELUMNYA) ---
        self.video_timer.timeout.connect(self.update_video_frame)
        
        self.fps = 30
        self.current_media_path = None
        self.has_finished = False
        self._volume = 50
        self.loop_in_point = None
        self.loop_out_point = None
        self.enable_audio = enable_audio
        self.playback_start_time = None
        self.compare_split_ratio = None
        
        # --- Inisialisasi VLC ---
        self.vlc_instance = None
        self.audio_player = None
        if self.enable_audio and vlc:
            try:
                # Opsi buffer untuk perbaiki "kretek-kretek"
                vlc_args = [
                    '--no-video',
                    '--quiet',
                    '--file-caching=1500', # Buffer 1.5 detik
                    '--aout=waveout' # Driver audio Windows yang stabil
                ]
                self.vlc_instance = vlc.Instance(vlc_args)
                self.audio_player = self.vlc_instance.media_player_new()
            except Exception as e:
                print(f"Error inisialisasi VLC: {e}")
                self.enable_audio = False
        # --- AKHIR VLC ---
        
        self.annotations = {} 
        self.drawing_enabled = False
        self.draw_pen_color = QColor(255, 0, 0, 255)
        self.draw_pen_width = 5
        self.pixmap_offset = QPoint(0, 0)
        self.pixmap_size = None
        self.frame_dims = None
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)

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

    def _prepare_audio(self, file_path):
        if not self.audio_player:
            return

        # --- PERBAIKAN DIMULAI DI SINI ---
        
        # 1. Hentikan pemutaran (jika sedang berjalan)
        self.audio_player.stop()
        
        # 2. Lepaskan media lama dari player
        # Ini adalah baris yang hilang dan menyebabkan bug
        self.audio_player.set_media(None)
        
        # --- AKHIR PERBAIKAN ---

        if file_path:
            try:
                media = self.vlc_instance.media_new(file_path)
                # Panggil .parse() pada MEDIA
                media.parse() 
                self.audio_player.set_media(media)
                self.audio_player.audio_set_volume(self._volume)
                
                video_track_count = self.audio_player.video_get_track_count()
                if video_track_count > 0:
                    self.audio_player.video_set_track(-1) 
                
                self._sync_audio_to_current_frame(force=True)
            except Exception as e:
                print(f"Error VLC saat memuat audio: {e}")

    def _current_time_ms(self):
        if self.fps <= 0 or self.current_frame_index < 0:
            return 0
        return int((self.current_frame_index / self.fps) * 1000)

    def _sync_audio_to_current_frame(self, force=False):
        # Fungsi ini HANYA akan dipanggil dengan force=True
        # (dari play, stop, seek_to_position, dll.)
        
        if not self.audio_player or not force:
            return # Jangan lakukan apa-apa jika tidak dipaksa

        target_ms = self._current_time_ms()
        
        try:
            # 1. Seek audio ke waktu yang benar
            self.audio_player.set_time(target_ms)
            
            # 2. Atur status play/pause BANYA PADA AUDIO
            if self.is_playing:
                self.audio_player.play()
            else:
                self.audio_player.pause()
                
        except Exception as e:
            print(f"Error saat sinkronisasi VLC (force=True): {e}")
            
    def scrub_audio_at_current_frame(self):
        """
        Memainkan cuplikan audio singkat di frame saat ini lalu berhenti.
        """
        if not self.audio_player or self.is_playing:
            # Jangan scrub jika audio sudah diputar (is_playing)
            # atau jika tidak ada audio player
            return 

        target_ms = self._current_time_ms()
        
        try:
            self.audio_player.set_time(target_ms)
            self.audio_player.play()
            
            # Atur timer untuk PAUSE setelah 60ms.
            # Ini akan memainkan audio ~1-2 frame lalu berhenti.
            QTimer.singleShot(60, self.audio_player.pause)
            
        except Exception as e:
            print(f"Error saat audio scrub: {e}")

    def _reset_playback_clock(self):
        if self.is_playing and self.fps > 0:
            self.playback_start_time = time.monotonic() - (self.current_frame_index / self.fps)
        elif not self.is_playing:
            self.playback_start_time = None

    def set_volume(self, value):
        self._volume = max(0, min(100, int(value)))
        if self.audio_player:
            self.audio_player.audio_set_volume(self._volume)

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
                    self.current_media_path = file_path 
                    self.current_frame_index = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                    self.display_frame(frame)
                    self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
                    self.fpsChanged.emit(self.fps)
                    self.frameReady.emit()
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
                self.current_media_path = file_path
                self.total_frames = 1
                self.current_frame_index = 0
                self.display_frame(frame)
                self.frameIndexChanged.emit(0, 1)
                self.fpsChanged.emit(0.0)
                self.frameReady.emit()
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
        scale_w = widget_size.width() / w if w > 0 else 0
        scale_h = widget_size.height() / h if h > 0 else 0
        base_scale = min(scale_w, scale_h) if min(scale_w, scale_h) > 0 else 1.0
        total_scale = base_scale * self.zoom_factor
        scaled_w = int(w * total_scale)
        scaled_h = int(h * total_scale)
        canvas_pixmap = QPixmap(widget_size)
        canvas_pixmap.fill(QColor("#1a1a1a"))
        draw_x = (widget_size.width() - scaled_w) // 2 + self.pan_offset.x()
        draw_y = (widget_size.height() - scaled_h) // 2 + self.pan_offset.y()
        painter = QPainter(canvas_pixmap)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        if scaled_w > 0 and scaled_h > 0:
            painter.drawPixmap(draw_x, draw_y, scaled_w, scaled_h, pixmap)
        annotation_image = self.annotations.get(self.current_frame_index)
        if annotation_image and scaled_w > 0 and scaled_h > 0:
            annotation_pixmap = QPixmap.fromImage(annotation_image)
            painter.drawPixmap(draw_x, draw_y, scaled_w, scaled_h, annotation_pixmap)
        painter.end()
        self.pixmap_size = QSize(scaled_w, scaled_h)
        self.pixmap_offset = QPoint(draw_x, draw_y)
        self.video_label.setPixmap(canvas_pixmap)
        
    def reset_zoom_pan(self):
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        if self.displayed_frame_source is not None:
            self.display_frame(self.displayed_frame_source)

    def zoom_at_center(self, factor):
        if not self.has_media() or self.frame_dims is None:
            return
        old_zoom = self.zoom_factor
        new_zoom = max(1.0, min(old_zoom * factor, 20.0))
        if abs(new_zoom - old_zoom) < 0.001:
            return
        self.zoom_factor = new_zoom
        if self.zoom_factor <= 1.001:
            self.pan_offset = QPoint(0, 0)
        else:
            scale_ratio = new_zoom / old_zoom
            new_pan_x = self.pan_offset.x() * scale_ratio
            new_pan_y = self.pan_offset.y() * scale_ratio
            h, w, ch = self.frame_dims
            widget_size = self.size()
            scale_w = widget_size.width() / w if w > 0 else 0
            scale_h = widget_size.height() / h if h > 0 else 0
            base_scale = min(scale_w, scale_h) if min(scale_w, scale_h) > 0 else 1.0
            total_scale = base_scale * self.zoom_factor
            scaled_w = int(w * total_scale)
            scaled_h = int(h * total_scale)
            center_x = (widget_size.width() - scaled_w) // 2
            center_y = (widget_size.height() - scaled_h) // 2
            max_pan_x = -center_x
            min_pan_x = widget_size.width() - scaled_w - center_x
            max_pan_y = -center_y
            min_pan_y = widget_size.height() - scaled_h - center_y
            final_pan_x = max(min_pan_x, min(int(new_pan_x), max_pan_x))
            final_pan_y = max(min_pan_y, min(int(new_pan_y), max_pan_y))
            self.pan_offset = QPoint(final_pan_x, final_pan_y)
        if self.displayed_frame_source is not None:
            self.display_frame(self.displayed_frame_source)    
        
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
            # --- Berhenti ---
            self.video_timer.stop()
            self.is_playing = False
            self.playback_start_time = None
            if self.audio_player:
                self.audio_player.pause()
        else:
            # --- Mulai ---
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
                
            if self.audio_player:
                # Sinkronkan dulu, baru play
                self._sync_audio_to_current_frame(force=True)
                # self.audio_player.play() <-- dipanggil di dalam sync

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
                self._sync_audio_to_current_frame(force=True) # Sync ke frame 0
                
        self.playStateChanged.emit(False)
        self.has_finished = False
        
    def previous_frame(self, _update_media_internals_only=False):
        if not self.is_video or not self.video_capture: return
        new_index = self.current_frame_index - 1
        if new_index >= 0:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, new_index)
            ret, frame = self.video_capture.read()
            if ret:
                # Perbarui state internal
                self.current_frame = frame
                self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                self.has_finished = False
                
                if not _update_media_internals_only:
                    self.display_frame(frame)
                    self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
                    
                    # --- PERBAIKAN DI SINI ---
                    self.scrub_audio_at_current_frame() # Panggil fungsi scrub
                    # self._sync_audio_to_current_frame(force=True) # <-- GANTI INI
                    # --- AKHIR PERBAIKAN ---
                    
                    self._reset_playback_clock()

    def next_frame(self, _update_media_internals_only=False):
        if not self.is_video or not self.video_capture: return
        if self.current_frame_index < self.total_frames - 1:
            ret, frame = self.video_capture.read()
            if ret:
                # Perbarui state internal
                self.current_frame = frame
                self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                self.has_finished = False
                
                if not _update_media_internals_only:
                    self.display_frame(frame)
                    self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
                    
                    # --- PERBAIKAN DI SINI ---
                    self.scrub_audio_at_current_frame() # Panggil fungsi scrub
                    # self._sync_audio_to_current_frame(force=True) # <-- GANTI INI
                    # --- AKHIR PERBAIKAN ---
                    
                    self._reset_playback_clock()
        
    def seek_to_position(self, position, _sync_audio=True):
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
                if _sync_audio:
                    self._sync_audio_to_current_frame(force=True)                
                self._reset_playback_clock()
                
    def update_video_frame(self):
        if not self.is_video or not self.video_capture or not self.is_playing:
            return
            
        if self.audio_player:
            # vlc.State.Ended == 6
            if self.audio_player.get_state() == vlc.State.Ended:
                # --- PERBAIKAN: Gunakan 'has_finished' sebagai 'lock' ---
                if not self.has_finished:
                    print("VLC: end of stream")
                    self.video_timer.stop()
                    self.is_playing = False
                    self.has_finished = True # Set 'lock'
                    self.playback_start_time = None
                    self.playStateChanged.emit(False)
                    self.playbackFinished.emit(True) # Kirim sinyal (Benar)
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
            # --- PERBAIKAN: Gunakan 'has_finished' sebagai 'lock' ---
            if not self.has_finished:
                self.video_timer.stop()
                self.is_playing = False
                self.has_finished = True # Set 'lock'
                self.playback_start_time = None
                if self.audio_player:
                    self.audio_player.pause()
                self.playStateChanged.emit(False)
                # TAMBAHKAN SINYAL INI KEMBALI
                self.playbackFinished.emit(False) # Kirim sinyal (karena video selesai)
            # --- AKHIR PERBAIKAN ---
            return
            
        if target_index > self.current_frame_index + 1:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, target_index)
            
        ret, frame = self.video_capture.read()
        if ret:
            self.current_frame = frame
            self.current_frame_index = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            self.display_frame(frame)
            self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
            # (Sync force=False sengaja dihapus untuk cegah 'kretek-kretek')
            self._reset_playback_clock()
        else:
            # --- PERBAIKAN: Gunakan 'has_finished' sebagai 'lock' ---
            if not self.has_finished:
                self.video_timer.stop()
                self.is_playing = False
                self.has_finished = True # Set 'lock'
                self.playback_start_time = None
                if self.audio_player:
                    self.audio_player.pause()
                self.playStateChanged.emit(False)
                # TAMBAHKAN SINYAL INI KEMBALI
                self.playbackFinished.emit(False) # Kirim sinyal (karena OpenCV gagal read)
            # --- AKHIR PERBAIKAN ---
            
    def closeEvent(self, event):
        if self.video_capture: self.video_capture.release()
        if self.audio_player:
            self.audio_player.stop()
            self.audio_player.release()
        if self.vlc_instance:
            self.vlc_instance.release()
        super().closeEvent(event)

    def has_media(self): return self.current_media_path is not None
    def get_current_file_path(self): return self.current_media_path

    def clear_media(self):
        self.stop()
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        
        self._prepare_audio(None) 
            
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
        self.compare_split_ratio = None
        self.annotations.clear()
        self.pixmap_offset = QPoint(0, 0)
        self.pixmap_size = None
        self.frame_dims = None
        self.drawing_enabled = False
        self.video_label.setCursor(Qt.ArrowCursor)
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)

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
        if self.current_frame_index < 0 or not self.frame_dims:
            return None
        image = self.annotations.get(self.current_frame_index)
        if image is None:
            h, w, ch = self.frame_dims
            image = QImage(w, h, QImage.Format_ARGB32)
            image.fill(Qt.transparent)
            self.annotations[self.current_frame_index] = image
        return image

    def draw_on_annotation(self, from_point_frame, to_point_frame):
        image = self.get_current_annotation_image()
        if image:
            painter = QPainter(image)
            pen = QPen(self.draw_pen_color, self.draw_pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            if self.draw_pen_color.alpha() == 0:
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.drawLine(from_point_frame, to_point_frame)
            painter.end()
            self.display_frame(self.displayed_frame_source)

    def finalize_drawing(self):
        if self.current_frame_index >= 0:
            self.annotationAdded.emit(self.current_frame_index)