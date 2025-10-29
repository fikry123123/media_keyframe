#!/usr/bin/env python3
import os
import time
import cv2
import numpy as np
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QMimeData, QUrl, QPoint, QSize
from PyQt5.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QPainter, QPen, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

class DrawingLabel(QLabel):
    """
    Label kustom yang menangani input mouse untuk menggambar pada frame video.
    """
    def __init__(self, parent_media_player):
        super().__init__()
        self.media_player = parent_media_player
        self.drawing = False
        self.last_point_frame = None
        self.setMouseTracking(True) # Diperlukan untuk kursor
        
        # --- TAMBAHAN BARU ---
        self.panning = False
        self.last_pan_pos = QPoint(0, 0)
        # --- AKHIR TAMBAHAN ---

    def _map_widget_to_frame_coords(self, widget_pos):
        """
        Memetakan koordinat QPoint dari widget label ke koordinat (x, y) 
        pada frame video asli.
        """
        mp = self.media_player
        # Pastikan kita memiliki semua info yang diperlukan untuk pemetaan
        if not mp.pixmap_size or mp.pixmap_size.width() == 0 or mp.pixmap_size.height() == 0 or mp.frame_dims is None:
            return None

        # 1. Ubah koordinat widget ke koordinat pixmap (yang diskalakan)
        pixmap_pos = widget_pos - mp.pixmap_offset
        
        # 2. Periksa apakah klik berada di dalam area pixmap
        if not (0 <= pixmap_pos.x() < mp.pixmap_size.width() and 0 <= pixmap_pos.y() < mp.pixmap_size.height()):
            return None
        
        # 3. Ubah koordinat pixmap ke koordinat frame asli
        h, w, ch = mp.frame_dims
        fx = pixmap_pos.x() * (w / mp.pixmap_size.width())
        fy = pixmap_pos.y() * (h / mp.pixmap_size.height())
        
        return QPoint(int(fx), int(fy))

    def mousePressEvent(self, event):
        # Mulai menggambar hanya jika mode diaktifkan dan ada media
        if event.button() == Qt.LeftButton and self.media_player.drawing_enabled and self.media_player.has_media():
            frame_pos = self._map_widget_to_frame_coords(event.pos())
            if frame_pos:
                self.drawing = True
                self.last_point_frame = frame_pos
                self.media_player.get_current_annotation_image() # Pastikan layer anotasi ada
                # Gambar satu titik untuk klik tunggal
                self.media_player.draw_on_annotation(frame_pos, frame_pos) 
        
        # --- TAMBAHAN BARU: Logika Pan ---
        elif event.button() == Qt.MiddleButton:
            # Hanya pan jika di-zoom (faktor > 1.0)
            if self.media_player.zoom_factor > 1.001: 
                self.panning = True
                self.last_pan_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        # --- AKHIR TAMBAHAN ---
            
        else:
            super().mousePressEvent(event) # teruskan klik lain

    def mousePressEvent(self, event):
        # --- PERBAIKAN LOGIKA PANNING ---
        
        # Prioritas 1: Panning Tombol Tengah (Selalu berfungsi jika di-zoom)
        if event.button() == Qt.MiddleButton:
            # Hanya pan jika di-zoom (faktor > 1.0)
            if self.media_player.zoom_factor > 1.001: 
                self.panning = True
                self.last_pan_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return # Selesai
            
        # Prioritas 2: Tombol Kiri
        if event.button() == Qt.LeftButton:
            # Jika mode drawing AKTIF, mulai menggambar
            if self.media_player.drawing_enabled and self.media_player.has_media():
                frame_pos = self._map_widget_to_frame_coords(event.pos())
                if frame_pos:
                    self.drawing = True
                    self.last_point_frame = frame_pos
                    self.media_player.get_current_annotation_image() # Pastikan layer anotasi ada
                    # Gambar satu titik untuk klik tunggal
                    self.media_player.draw_on_annotation(frame_pos, frame_pos) 
                    event.accept()
                    return # Selesai

            # Jika mode drawing MATI dan di-zoom, mulai panning
            elif not self.media_player.drawing_enabled and self.media_player.zoom_factor > 1.001:
                self.panning = True
                self.last_pan_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return # Selesai
                
        # --- AKHIR PERBAIKAN ---
            
        # Jika tidak ada yg ditangani, teruskan
        super().mousePressEvent(event) # teruskan klik lain

    def mouseReleaseEvent(self, event):
        # --- PERBAIKAN LOGIKA PANNING ---

        # Cek 1: Selesai menggambar (HANYA tombol Kiri)
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.last_point_frame = None
            # Beri tahu media player bahwa gambar telah ditambahkan/diubah
            self.media_player.finalize_drawing() 
            event.accept()
            return # Selesai

        # Cek 2: Selesai panning (bisa dari Tombol Kiri ATAU Tengah)
        if (event.button() == Qt.LeftButton or event.button() == Qt.MiddleButton) and self.panning:
            self.panning = False
            # Kembalikan kursor ke status yang benar
            if self.media_player.drawing_enabled:
                self.setCursor(Qt.CrossCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            event.accept()
            return # Selesai
            
        # --- AKHIR PERBAIKAN ---
            
        super().mouseReleaseEvent(event)
        
    def mouseMoveEvent(self, event):
        
        # --- PERBAIKAN: Tambahkan pengecekan event.buttons() ---
        
        # Cek 1: Apakah kita sedang dalam mode Panning? (flag-nya True)
        # DAN Apakah Tombol Kiri ATAU Tengah sedang DITEKAN?
        if self.panning and (event.buttons() & Qt.LeftButton or event.buttons() & Qt.MiddleButton):
            
            if self.media_player.frame_dims is None:
                event.accept()
                return
                
            delta = event.pos() - self.last_pan_pos
            new_pan_offset = self.media_player.pan_offset + delta
            
            # --- Logika Batasan (Limiting) ---
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
            # --- Akhir Logika Batasan ---

            self.last_pan_pos = event.pos()
            
            if self.media_player.displayed_frame_source is not None:
                self.media_player.display_frame(self.media_player.displayed_frame_source)
            event.accept()
            return # Selesai
            
        # Cek 2: Apakah kita sedang dalam mode Drawing? (flag-nya True)
        # DAN Apakah Tombol Kiri sedang DITEKAN?
        elif self.drawing and self.media_player.drawing_enabled and (event.buttons() & Qt.LeftButton):
            frame_pos = self._map_widget_to_frame_coords(event.pos())
            if frame_pos:
                self.media_player.draw_on_annotation(self.last_point_frame, frame_pos)
                self.last_point_frame = frame_pos
                event.accept()
                return # Selesai
                
        # Cek 3: Jika tidak ada tombol yg ditekan (hanya mouse-over)
        # biarkan super() menanganinya (untuk update kursor, dll)
        super().mouseMoveEvent(event)

    # --- TAMBAHAN BARU: Fungsi WheelEvent ---
    def wheelEvent(self, event):
        """Menangani zoom dengan mouse scroll wheel."""
        if not self.media_player.has_media() or self.media_player.frame_dims is None:
            event.ignore()
            return

        # --- 1. Hitung Zoom ---
        zoom_delta = event.angleDelta().y() / 120
        zoom_step = 1.15 # 15% zoom per step
        old_zoom = self.media_player.zoom_factor

        if zoom_delta > 0:
            new_zoom = old_zoom * zoom_step
        else:
            new_zoom = old_zoom / zoom_step
        
        # Batasi zoom (Min 100% / 1.0)
        new_zoom = max(1.0, min(new_zoom, 20.0)) # Min 100%, Max 2000%
        
        if abs(new_zoom - old_zoom) < 0.001:
            event.accept()
            return # Tidak ada perubahan
            
        self.media_player.zoom_factor = new_zoom

        # --- 2. Hitung Pan (Zoom ke Kursor) ---
        widget_pos = event.pos() # Posisi kursor di widget

        # Dapatkan info frame/skala SEBELUM zoom
        h, w, ch = self.media_player.frame_dims
        widget_size = self.media_player.size()
        scale_w = widget_size.width() / w if w > 0 else 0
        scale_h = widget_size.height() / h if h > 0 else 0
        base_scale = min(scale_w, scale_h) if min(scale_w, scale_h) > 0 else 1.0
        
        old_total_scale = base_scale * old_zoom
        new_total_scale = base_scale * new_zoom
        
        old_scaled_size = QSize(int(w * old_total_scale), int(h * old_total_scale))
        new_scaled_size = QSize(int(w * new_total_scale), int(h * new_total_scale))
        
        # Offset (tengah + pan) LAMA
        old_offset_x = (widget_size.width() - old_scaled_size.width()) // 2 + self.media_player.pan_offset.x()
        old_offset_y = (widget_size.height() - old_scaled_size.height()) // 2 + self.media_player.pan_offset.y()

        # Posisi kursor relatif terhadap pixmap LAMA (yang di-zoom)
        old_pixmap_x = widget_pos.x() - old_offset_x
        old_pixmap_y = widget_pos.y() - old_offset_y

        # Hitung posisi (fraksional) kursor pada pixmap (0.0 - 1.0)
        if old_scaled_size.width() == 0 or old_scaled_size.height() == 0:
            frac_x, frac_y = 0.5, 0.5 # Default ke tengah
        else:
            frac_x = old_pixmap_x / old_scaled_size.width()
            frac_y = old_pixmap_y / old_scaled_size.height()

        # Hitung posisi kursor pada pixmap BARU
        new_pixmap_x = frac_x * new_scaled_size.width()
        new_pixmap_y = frac_y * new_scaled_size.height()

        # Offset (tengah) BARU
        new_center_x = (widget_size.width() - new_scaled_size.width()) // 2
        new_center_y = (widget_size.height() - new_scaled_size.height()) // 2
        
        # Kita ingin: widget_pos.x() == (new_center_x + pan_x) + new_pixmap_x
        # Jadi: pan_x = widget_pos.x() - new_center_x - new_pixmap_x
        
        new_pan_x = widget_pos.x() - new_center_x - new_pixmap_x
        new_pan_y = widget_pos.y() - new_center_y - new_pixmap_y
        
        # --- 3. Batasi Pan ---
        if new_zoom <= 1.001:
            self.media_player.pan_offset = QPoint(0, 0)
        else:
            # Hitung batas pan
            max_pan_x = -new_center_x
            min_pan_x = widget_size.width() - new_scaled_size.width() - new_center_x
            
            max_pan_y = -new_center_y
            min_pan_y = widget_size.height() - new_scaled_size.height() - new_center_y
            
            # Terapkan pan baru yang sudah dibatasi
            final_pan_x = max(min_pan_x, min(int(new_pan_x), max_pan_x))
            final_pan_y = max(min_pan_y, min(int(new_pan_y), max_pan_y))
            
            self.media_player.pan_offset = QPoint(final_pan_x, final_pan_y)
            
        # --- 4. Tampilkan ulang ---
        if self.media_player.displayed_frame_source is not None:
            self.media_player.display_frame(self.media_player.displayed_frame_source)
        
        event.accept()
    # --- AKHIR TAMBAHAN ---


class MediaPlayer(QWidget):
    frameIndexChanged = pyqtSignal(int, int)
    frameReady = pyqtSignal()
    playStateChanged = pyqtSignal(bool)
    fpsChanged = pyqtSignal(float)
    playbackFinished = pyqtSignal()
    fileDropped = pyqtSignal(str, str)
    annotationAdded = pyqtSignal(int) # Sinyal baru saat gambar ditambahkan
    
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
        
        # --- FITUR DRAWING BARU ---
        self.annotations = {} # Kamus untuk menyimpan: {frame_index: QImage}
        self.drawing_enabled = False
        self.draw_pen_color = QColor(255, 0, 0, 255) # Default: Merah
        self.draw_pen_width = 5
        
        # Info untuk pemetaan koordinat
        self.pixmap_offset = QPoint(0, 0)
        self.pixmap_size = None
        self.frame_dims = None # (h, w, ch)
        
        # --- TAMBAHAN BARU: Variabel State Zoom/Pan ---
        self.zoom_factor = 1.0  # 1.0 = fit to view
        self.pan_offset = QPoint(0, 0) # Pan offset dalam piksel widget
        # --- AKHIR TAMBAHAN ---
        
        # --- AKHIR FITUR DRAWING ---

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # Gunakan DrawingLabel kustom, bukan QLabel standar
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
                    # self.displayed_frame_source diatur dalam display_frame
                    self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
                    self.fps = cap.get(cv2.CAP_PROP_FPS) or 24 
                    if self.fps == 0: self.fps = 24
                    
                    # --- PERBAIKAN BUG: START ---
                    # Pindahkan ini *sebelum* sinyal frameIndexChanged
                    self.current_media_path = file_path 
                    # --- PERBAIKAN BUG: END ---
                    
                    self.current_frame_index = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                    self.display_frame(frame) # Ini akan mengatur self.displayed_frame_source
                    self.frameIndexChanged.emit(self.current_frame_index, self.total_frames)
                    self.fpsChanged.emit(self.fps)
                    self.frameReady.emit()
                    # self.current_media_path = file_path <-- POSISI LAMA
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
                
                # --- PERBAIKAN BUG: START ---
                # Pindahkan ini *sebelum* sinyal frameIndexChanged
                self.current_media_path = file_path
                # --- PERBAIKAN BUG: END ---
                
                # self.displayed_frame_source diatur dalam display_frame
                self.total_frames = 1
                self.current_frame_index = 0
                self.display_frame(frame) # Ini akan mengatur self.displayed_frame_source
                self.frameIndexChanged.emit(0, 1)
                self.fpsChanged.emit(0.0)
                self.frameReady.emit()
                # self.current_media_path = file_path <-- POSISI LAMA
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
            # Jika frame None, setidaknya perbarui info pemetaan agar tidak error
            self.pixmap_size = None
            self.pixmap_offset = QPoint(0, 0)
            self.frame_dims = None
            return
        
        # Buat salinan frame agar kita tidak menggambar di atas frame cache cv2
        self.displayed_frame_source = frame.copy() 
        
        rgb_frame = cv2.cvtColor(self.displayed_frame_source, cv2.COLOR_BGR2RGB)
        
        # Simpan dimensi frame asli
        h, w, ch = rgb_frame.shape
        self.frame_dims = (h, w, ch)
        
        widget_size = self.size()
        if widget_size.width() <= 0 or widget_size.height() <= 0: widget_size = self.video_label.size()
        if widget_size.width() <= 0 or widget_size.height() <= 0: widget_size = self.video_label.sizeHint()
        if widget_size.width() <= 0 or widget_size.height() <= 0: return

        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image) # <-- pixmap asli (full size)
        
        # --- AWAL PERBAIKAN: LOGIKA SCALING QPAINTER ---
        
        # 1. Hitung skala dasar (fit)
        scale_w = widget_size.width() / w if w > 0 else 0
        scale_h = widget_size.height() / h if h > 0 else 0
        base_scale = min(scale_w, scale_h) if min(scale_w, scale_h) > 0 else 1.0
        
        # 2. Hitung skala total (fit * zoom)
        total_scale = base_scale * self.zoom_factor
        
        scaled_w = int(w * total_scale)
        scaled_h = int(h * total_scale)
        
        # 3. Buat canvas seukuran widget
        canvas_pixmap = QPixmap(widget_size)
        canvas_pixmap.fill(QColor("#1a1a1a")) # Latar belakang player

        # 4. Hitung offset gambar (tengah + pan)
        draw_x = (widget_size.width() - scaled_w) // 2 + self.pan_offset.x()
        draw_y = (widget_size.height() - scaled_h) // 2 + self.pan_offset.y()
        
        # 5. Gambar pixmap video ke canvas MENGGUNAKAN QPAINTER
        painter = QPainter(canvas_pixmap)
        
        # Atur kualitas rendering untuk zoom (opsional, tapi bagus)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if scaled_w > 0 and scaled_h > 0:
            # Ini adalah overload drawPixmap(x, y, w, h, source_pixmap)
            # Ini jauh lebih cepat daripada pixmap.scaled()
            painter.drawPixmap(draw_x, draw_y, scaled_w, scaled_h, pixmap)

        # --- LOGIKA ANOTASI (DIPERBARUI) ---
        annotation_image = self.annotations.get(self.current_frame_index)
        if annotation_image and scaled_w > 0 and scaled_h > 0:
            # Ubah QImage anotasi (seukuran frame) menjadi QPixmap
            annotation_pixmap = QPixmap.fromImage(annotation_image)
            
            # Gambar anotasi di atas video, DENGAN CARA CEPAT YANG SAMA
            painter.drawPixmap(draw_x, draw_y, scaled_w, scaled_h, annotation_pixmap)
        
        painter.end()
        # --- AKHIR PERBAIKAN ---

        # 7. Simpan info penskalaan & offset untuk pemetaan mouse
        self.pixmap_size = QSize(scaled_w, scaled_h) # Gunakan ukuran yg dihitung
        self.pixmap_offset = QPoint(draw_x, draw_y) # Ini adalah offset top-left di widget

        # 8. Tampilkan pixmap gabungan
        self.video_label.setPixmap(canvas_pixmap)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Tampilkan ulang frame saat ini dengan ukuran baru
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
            # Pergi ke frame 0
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame = frame
                # self.displayed_frame_source diatur dalam display_frame
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
                # self.displayed_frame_source diatur dalam display_frame
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
                # self.displayed_frame_source diatur dalam display_frame
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
                # self.displayed_frame_source diatur dalam display_frame
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
            # self.displayed_frame_source diatur dalam display_frame
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
        
        # --- RESET FITUR DRAWING ---
        self.annotations.clear()
        self.pixmap_offset = QPoint(0, 0)
        self.pixmap_size = None
        self.frame_dims = None
        self.drawing_enabled = False
        self.video_label.setCursor(Qt.ArrowCursor)
        
        # --- TAMBAHAN BARU: Reset Zoom/Pan ---
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        # --- AKHIR TAMBAHAN ---
        
        # --- AKHIR RESET ---

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

    # --- FUNGSI HELPER DRAWING BARU ---
    
    def get_current_annotation_image(self):
        """
        Mengambil layer anotasi QImage untuk frame saat ini.
        Membuatnya jika belum ada.
        """
        if self.current_frame_index < 0 or not self.frame_dims:
            return None
        
        image = self.annotations.get(self.current_frame_index)
        
        if image is None:
            # Buat QImage transparan seukuran frame video
            h, w, ch = self.frame_dims
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
            
            # Jika alpha 0, gunakan mode "Clear" (penghapus)
            if self.draw_pen_color.alpha() == 0:
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
            
            painter.drawLine(from_point_frame, to_point_frame)
            painter.end()
            
            # Tampilkan ulang frame dengan anotasi yang diperbarui
            self.display_frame(self.displayed_frame_source)

    def finalize_drawing(self):
        """
        Dipanggil saat mouse dilepas setelah menggambar.
        Memberi sinyal ke MainWindow untuk menambahkan marka hijau.
        """
        if self.current_frame_index >= 0:
            self.annotationAdded.emit(self.current_frame_index)
    # --- AKHIR FUNGSI DRAWING ---