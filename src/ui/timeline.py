"""
Timeline Widget.
Menyediakan timeline scrubber untuk navigasi media.
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QSlider, QLabel, 
                            QFrame, QVBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor


class Timeline(QWidget):
    """Widget timeline untuk navigasi media."""
    
    # Signals
    positionChanged = pyqtSignal(float)  # Position as percentage (0.0 - 1.0)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 0.0
        self.current_position = 0.0
        self.is_dragging = False
        self.setupUI()
        
    def setupUI(self):
        """Setup user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        # Timeline info
        info_layout = QHBoxLayout()
        
        self.frame_label = QLabel("Frame: 0")
        self.frame_label.setMinimumWidth(80)
        info_layout.addWidget(self.frame_label)
        
        # Add spacer
        info_layout.addStretch()
        
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setMinimumWidth(60)
        info_layout.addWidget(self.fps_label)
        
        layout.addLayout(info_layout)
        
        # Timeline scrubber
        scrubber_layout = QHBoxLayout()
        scrubber_layout.setContentsMargins(0, 0, 0, 0)
        
        # Start time
        self.start_time_label = QLabel("00:00")
        self.start_time_label.setMinimumWidth(40)
        scrubber_layout.addWidget(self.start_time_label)
        
        # Timeline slider
        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setRange(0, 1000)  # Use 0-1000 for smooth scrubbing
        self.timeline_slider.setValue(0)
        self.timeline_slider.setTracking(True)  # Emit signals while dragging
        
        # Connect signals
        self.timeline_slider.sliderPressed.connect(self.onSliderPressed)
        self.timeline_slider.sliderReleased.connect(self.onSliderReleased)
        self.timeline_slider.valueChanged.connect(self.onSliderValueChanged)
        
        scrubber_layout.addWidget(self.timeline_slider)
        
        # End time
        self.end_time_label = QLabel("00:00")
        self.end_time_label.setMinimumWidth(40)
        scrubber_layout.addWidget(self.end_time_label)
        
        layout.addLayout(scrubber_layout)
        
        self.setLayout(layout)
        
        # Initially disable
        self.setEnabled(False)
        
        # Apply styling
        self.setStyleSheet("""
            QLabel {
                color: #f0f0f0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                font-weight: 500;
                background-color: transparent;
                padding: 2px 4px;
            }
            QSlider::groove:horizontal {
                border: 2px solid #606060;
                height: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #404040, stop:1 #303030);
                margin: 2px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #808080, stop:1 #606060);
                border: 3px solid #ffffff;
                width: 24px;
                margin: -7px 0;
                border-radius: 12px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #909090, stop:1 #707070);
                border-color: #f0f0f0;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #0078d4, stop:1 #005a9e);
                border: 2px solid #004578;
                height: 12px;
                border-radius: 6px;
            }
        """)
        
    def onSliderPressed(self):
        """Handle slider press."""
        self.is_dragging = True
        
    def onSliderReleased(self):
        """Handle slider release."""
        self.is_dragging = False
        position = self.timeline_slider.value() / 1000.0
        self.positionChanged.emit(position)
        
    def onSliderValueChanged(self, value):
        """Handle slider value change."""
        if self.is_dragging:
            position = value / 1000.0
            self.current_position = position
            self.updateDisplay()
            
    def setDuration(self, duration):
        """Set media duration in seconds."""
        self.duration = duration
        self.end_time_label.setText(self.formatTime(duration))
        self.updateDisplay()
        
    def setPosition(self, position):
        """Set current position (0.0 - 1.0)."""
        if not self.is_dragging:  # Only update if not being dragged by user
            self.current_position = position
            slider_value = int(position * 1000)
            self.timeline_slider.setValue(slider_value)
            self.updateDisplay()
            
    def setFrameInfo(self, current_frame, total_frames, fps):
        """Set frame information."""
        self.frame_label.setText(f"Frame: {current_frame}")
        if fps > 0:
            self.fps_label.setText(f"FPS: {fps:.1f}")
        else:
            self.fps_label.setText("FPS: --")
            
    def updateDisplay(self):
        """Update time display."""
        current_time = self.current_position * self.duration
        self.start_time_label.setText(self.formatTime(current_time))
        
    def formatTime(self, seconds):
        """Format time in MM:SS format."""
        if seconds < 0:
            return "00:00"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
            
    def reset(self):
        """Reset timeline to initial state."""
        self.duration = 0.0
        self.current_position = 0.0
        self.timeline_slider.setValue(0)
        self.start_time_label.setText("00:00")
        self.end_time_label.setText("00:00")
        self.frame_label.setText("Frame: 0")
        self.fps_label.setText("FPS: --")
