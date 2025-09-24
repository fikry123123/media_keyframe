from PyQt5.QtWidgets import QWidget, QMenu, QAction, QActionGroup
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont

class TimelineWidget(QWidget):
    position_changed = pyqtSignal(int)
    display_mode_changed = pyqtSignal(bool)
    markTourSpeedChanged = pyqtSignal(int)
    
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
        self.current_mark_tour_speed = 1500
        self.setFixedHeight(44)
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

    def _emit_speed_change(self, speed_ms):
        self.current_mark_tour_speed = speed_ms
        self.markTourSpeedChanged.emit(speed_ms)

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

        context_menu.addSeparator()

        speed_menu = context_menu.addMenu("Mark Tour Speed")
        speed_group = QActionGroup(self)
        speed_group.setExclusive(True)

        speeds = {
            "Slowest (3s)": 3000,
            "Slow (2s)": 2000,
            "Normal (1.5s)": 1500,
            "Fast (1s)": 1000,
            "Faster (0.5s)": 500,
            "Very Fast (0.25s)": 250,
            "Super Fast (0.1s)": 100,
            "Hyper (0.05s)": 50,
            "Max (~60fps)": 16
        }

        for text, speed_ms in speeds.items():
            action = QAction(text, self)
            action.setCheckable(True)
            action.setData(speed_ms)
            action.triggered.connect(lambda checked, s=speed_ms: self._emit_speed_change(s))
            if self.current_mark_tour_speed == speed_ms:
                action.setChecked(True)
            speed_menu.addAction(action)
            speed_group.addAction(action)

        context_menu.exec_(self.mapToGlobal(pos))


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Gambar latar belakang
        painter.setBrush(QBrush(QColor("#3a3a3a")))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        
        if self.duration > 0:
            # --- PERUBAHAN URUTAN GAMBAR ---
            # 2. Gambar semua garis penanda (marks) terlebih dahulu
            painter.setPen(QPen(QColor("#ffffff"), 2))
            for mark_frame in self.marks:
                if self.duration > 1:
                    mark_x = (mark_frame / (self.duration - 1)) * self.width()
                else:
                    mark_x = 0
                painter.drawLine(int(mark_x), 10, int(mark_x), self.height())

            # 3. Setelah itu, gambar playhead dan labelnya agar berada di lapisan atas
            marker_x = (self.current_position / (self.duration - 1)) * self.width() if self.duration > 1 else 0

            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawLine(int(marker_x), 10, int(marker_x), self.height())

            display_text = self._format_marker_label()
            if display_text:
                font = QFont("Segoe UI", 9, QFont.Bold)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                text_width = metrics.horizontalAdvance(display_text)
                text_height = metrics.height()
                bubble_padding = 8
                bubble_width = text_width + bubble_padding * 2
                bubble_height = text_height + 6
                bubble_x = int(marker_x) - bubble_width // 2
                bubble_y = 2
                if bubble_x < 4:
                    bubble_x = 4
                if bubble_x + bubble_width > self.width() - 4:
                    bubble_x = self.width() - bubble_width - 4

                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(20, 20, 20, 220))
                painter.drawRoundedRect(bubble_x, bubble_y, bubble_width, bubble_height, 6, 6)
                painter.setPen(QColor("#ffffff"))
                painter.drawText(bubble_x, bubble_y, bubble_width, bubble_height,
                                 Qt.AlignCenter | Qt.AlignVCenter, display_text)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.seek_to_mouse_position(event.pos())
            
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.seek_to_mouse_position(event.pos())

    def seek_to_mouse_position(self, pos):
        if self.duration > 0:
            x = pos.x()
            if self.duration > 1:
                new_position = int((x / self.width()) * (self.duration - 1))
            else:
                new_position = 0
            
            new_position = max(0, min(new_position, self.duration - 1))
            self.position_changed.emit(new_position)

    def _format_marker_label(self):
        if self.duration <= 0 or self.current_position < 0:
            return ""
        frame_current = self.current_position + 1
        
        if self.show_timecode and self.fps > 0:
            total_seconds = self.current_position / self.fps
            minutes = int(total_seconds // 60)
            seconds_float = total_seconds - minutes * 60
            seconds = int(seconds_float)
            fractional = seconds_float - seconds
            frames = int(round(fractional * self.fps))
            if frames >= self.fps:
                frames = 0
                seconds += 1
                if seconds >= 60:
                    seconds = 0
                    minutes += 1
            time_text = f"{minutes:02d}:{seconds:02d}.{frames:02d}"
            return time_text
            
        return f"{frame_current:,}"