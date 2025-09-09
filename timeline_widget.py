from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel
from PyQt5.QtCore import Qt, pyqtSignal

class TimelineWidget(QWidget):
    position_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.duration = 0
        self.current_position = 0
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        # Timeline info layout
        info_layout = QHBoxLayout()
        
        # Current position label
        self.position_label = QLabel("00:00")
        self.position_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                background-color: #444444;
                padding: 4px 8px;
                border-radius: 3px;
                min-width: 60px;
            }
        """)
        info_layout.addWidget(self.position_label)
        
        # Spacer
        info_layout.addStretch()
        
        # Duration label
        self.duration_label = QLabel("00:00")
        self.duration_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                background-color: #444444;
                padding: 4px 8px;
                border-radius: 3px;
                min-width: 60px;
            }
        """)
        info_layout.addWidget(self.duration_label)
        
        layout.addLayout(info_layout)
        
        # Timeline slider
        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(100)
        self.timeline_slider.setValue(0)
        self.timeline_slider.setStyleSheet("""
            QSlider {
                height: 25px;
            }
            QSlider::groove:horizontal {
                border: 3px solid #666666;
                height: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2b2b2b, stop:1 #444444);
                border-radius: 6px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #cccccc);
                border: 2px solid #666666;
                width: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dddddd, stop:1 #aaaaaa);
                border-color: #888888;
            }
            QSlider::handle:horizontal:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #aaaaaa, stop:1 #888888);
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0078d4, stop:1 #005a9e);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.timeline_slider)
        
        # Connect signals
        self.timeline_slider.valueChanged.connect(self.on_position_changed)
        self.timeline_slider.sliderPressed.connect(self.on_slider_pressed)
        self.timeline_slider.sliderReleased.connect(self.on_slider_released)
        
        # Flags for handling slider interaction
        self.slider_being_dragged = False
        
    def set_duration(self, duration):
        """Set the total duration/frame count"""
        self.duration = duration
        self.timeline_slider.setMaximum(max(0, duration - 1))
        self.update_duration_label()
        
    def set_position(self, position):
        """Set current position without triggering signals"""
        if not self.slider_being_dragged:
            self.current_position = position
            self.timeline_slider.blockSignals(True)
            self.timeline_slider.setValue(position)
            self.timeline_slider.blockSignals(False)
            self.update_position_label()
            
    def on_slider_pressed(self):
        """Called when user starts dragging the slider"""
        self.slider_being_dragged = True
        
    def on_slider_released(self):
        """Called when user releases the slider"""
        self.slider_being_dragged = False
        self.position_changed.emit(self.timeline_slider.value())
        
    def on_position_changed(self, position):
        """Called when slider value changes"""
        self.current_position = position
        self.update_position_label()
        
        # Only emit signal if user is dragging (for real-time preview)
        if self.slider_being_dragged:
            self.position_changed.emit(position)
            
    def update_position_label(self):
        """Update the position display"""
        if self.duration > 1:
            # For video files or image sequences, show frame numbers
            self.position_label.setText(f"Frame {self.current_position + 1}")
        else:
            # For single images
            self.position_label.setText("Frame 1")
            
    def update_duration_label(self):
        """Update the duration display"""
        if self.duration > 1:
            # For video files or image sequences, show total frame count
            self.duration_label.setText(f"Total {self.duration}")
        else:
            # For single images
            self.duration_label.setText("Total 1")
            
    def format_time(self, seconds):
        """Format seconds into MM:SS format"""
        if seconds < 0:
            return "00:00"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"