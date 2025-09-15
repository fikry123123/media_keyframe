from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont

class TimelineWidget(QWidget):
    position_changed = pyqtSignal(int)
    display_mode_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        self.duration = 0
        self.current_position = 0
        self.marks = []
        self.fps = 0.0
        self.show_timecode = False
        self.setFixedHeight(30)
        self.setStyleSheet("""
            QWidget {
                background-color: #3a3a3a;
                border-top: 1px solid #555555;
            }
        """)
        
    def set_duration(self, duration):
        self.duration = duration
        self.update()
        
    def set_position(self, position):
        if self.current_position != position:
            self.current_position = position
            self.update()

    def set_marks(self, marks):
        self.marks = marks
        self.update()

    def set_fps(self, fps):
        self.fps = fps
        self.update()
        
    def set_timecode_mode(self, enabled):
        self.show_timecode = enabled
        self.update()

    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        
        frame_action = QAction("Show Frame Number", self)
        frame_action.setCheckable(True)
        frame_action.setChecked(not self.show_timecode)
        context_menu.addAction(frame_action)

        timecode_action = QAction("Show Timecode (MM:SS.FF)", self)
        timecode_action.setCheckable(True)
        timecode_action.setChecked(self.show_timecode)
        context_menu.addAction(timecode_action)

        frame_action.triggered.connect(lambda: self.display_mode_changed.emit(False))
        timecode_action.triggered.connect(lambda: self.display_mode_changed.emit(True))

        context_menu.exec_(self.mapToGlobal(pos))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.setBrush(QBrush(QColor("#3a3a3a")))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        
        # Cek apakah durasi lebih dari 0 untuk menghindari pembagian nol
        if self.duration > 0:
            # Hitung posisi horizontal untuk penanda (marker)
            marker_x = (self.current_position / (self.duration - 1)) * self.width() if self.duration > 1 else 0

            # --- Gambar penanda posisi sebagai garis ---
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawLine(int(marker_x), 0, int(marker_x), self.height())
            
            # --- Gambar teks di atas garis ---
            font = QFont("Arial", 9)
            painter.setFont(font)
            painter.setPen(QColor("#ffffff"))
            
            # Tentukan teks yang akan ditampilkan berdasarkan mode
            if self.show_timecode and self.fps > 0:
                current_seconds = self.current_position / self.fps
                minutes = int(current_seconds // 60)
                seconds = int(current_seconds % 60)
                frames = int((current_seconds - int(current_seconds)) * self.fps)
                frame_text = f"{minutes:02d}:{seconds:02d}.{frames:02d}"
            else:
                # Tampilkan nomor frame mulai dari 1 (bukan 0)
                frame_text = str(self.current_position + 1)

            text_rect = painter.fontMetrics().boundingRect(frame_text)
            
            # Atur posisi teks di atas garis (terpusat di atas playhead '|')
            text_x = int(marker_x) - text_rect.width() // 2
            text_y = text_rect.height() + 2
            
            # Pastikan teks tidak keluar dari widget
            if text_x < 0:
                text_x = 0
            if text_x + text_rect.width() > self.width():
                text_x = self.width() - text_rect.width()

            painter.drawText(text_x, text_y, frame_text)

            # --- Gambar mark pada timeline sebagai garis vertikal tipis ---
            painter.setPen(QPen(QColor("#ffffff"), 2))
            
            for mark_frame in self.marks:
                if self.duration > 1:
                    mark_x = (mark_frame / (self.duration - 1)) * self.width()
                else:
                    mark_x = 0
                
                # Gambar garis vertikal tipis sebagai mark
                painter.drawLine(int(mark_x), 0, int(mark_x), self.height())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.seek_to_mouse_position(event.pos())
            
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.seek_to_mouse_position(event.pos())

    def seek_to_mouse_position(self, pos):
        if self.duration > 0:
            x = pos.x()
            # Handle division by zero for single-frame duration
            if self.duration > 1:
                new_position = int((x / self.width()) * (self.duration - 1))
            else:
                new_position = 0
            
            new_position = max(0, min(new_position, self.duration - 1))
            self.position_changed.emit(new_position)
