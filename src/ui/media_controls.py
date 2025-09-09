"""
Media Controls Widget.
Menyediakan kontrol untuk play, pause, stop, dan navigasi frame.
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, 
                            QSlider, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon


class MediaControls(QWidget):
    """Widget untuk kontrol media playback."""
    
    # Signals
    playPauseClicked = pyqtSignal()
    stopClicked = pyqtSignal()
    previousFrameClicked = pyqtSignal()
    nextFrameClicked = pyqtSignal()
    volumeChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_playing = False
        self.setupUI()
        
    def setupUI(self):
        """Setup user interface."""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Previous frame button
        self.prev_frame_btn = QPushButton("⏮")
        self.prev_frame_btn.setToolTip("Previous Frame (Left Arrow)")
        self.prev_frame_btn.setFixedSize(40, 40)
        self.prev_frame_btn.clicked.connect(self.previousFrameClicked.emit)
        layout.addWidget(self.prev_frame_btn)
        
        # Play/Pause button
        self.play_pause_btn = QPushButton("▶")
        self.play_pause_btn.setToolTip("Play/Pause (Space)")
        self.play_pause_btn.setFixedSize(50, 40)
        self.play_pause_btn.clicked.connect(self.playPauseClicked.emit)
        layout.addWidget(self.play_pause_btn)
        
        # Next frame button
        self.next_frame_btn = QPushButton("⏭")
        self.next_frame_btn.setToolTip("Next Frame (Right Arrow)")
        self.next_frame_btn.setFixedSize(40, 40)
        self.next_frame_btn.clicked.connect(self.nextFrameClicked.emit)
        layout.addWidget(self.next_frame_btn)
        
        # Stop button
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setToolTip("Stop")
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.clicked.connect(self.stopClicked.emit)
        layout.addWidget(self.stop_btn)
        
        # Add some spacing
        spacer1 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)
        layout.addItem(spacer1)
        
        # Time display
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(100)
        layout.addWidget(self.time_label)
        
        # Add flexible spacing
        spacer2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addItem(spacer2)
        
        # Volume control
        volume_label = QLabel("Volume:")
        layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.setToolTip("Volume")
        self.volume_slider.valueChanged.connect(self.volumeChanged.emit)
        layout.addWidget(self.volume_slider)
        
        self.volume_value_label = QLabel("50%")
        self.volume_value_label.setMinimumWidth(30)
        layout.addWidget(self.volume_value_label)
        
        # Connect volume slider to update label
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_value_label.setText(f"{v}%")
        )
        
        self.setLayout(layout)
        
        # Initially disable controls
        self.setEnabled(False)
        
        # Apply styling
        self.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 5px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #2c2c2c;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
            }
            QLabel {
                color: white;
                font-family: monospace;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
        """)
        
    def setPlayPauseIcon(self, is_playing):
        """Update play/pause button icon."""
        self.is_playing = is_playing
        if is_playing:
            self.play_pause_btn.setText("⏸")
            self.play_pause_btn.setToolTip("Pause (Space)")
        else:
            self.play_pause_btn.setText("▶")
            self.play_pause_btn.setToolTip("Play (Space)")
            
    def updateTimeDisplay(self, current_time, total_time):
        """Update time display."""
        current_str = self.formatTime(current_time)
        total_str = self.formatTime(total_time)
        self.time_label.setText(f"{current_str} / {total_str}")
        
    def formatTime(self, seconds):
        """Format time in MM:SS format."""
        if seconds < 0:
            return "00:00"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
        
    def setVolume(self, volume):
        """Set volume value."""
        self.volume_slider.setValue(volume)
        
    def getVolume(self):
        """Get current volume value."""
        return self.volume_slider.value()
