from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSlider, QLabel
from PyQt5.QtCore import Qt, pyqtSignal

class MediaControls(QWidget):
    position_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        button_style = """
            QPushButton {
                background-color: #444444;
                color: #ffffff;
                border: 2px solid #666666;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 16px;
                font-weight: bold;
                min-width: 70px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #555555;
                border-color: #888888;
            }
            QPushButton:pressed {
                background-color: #333333;
                border-color: #999999;
            }
            QPushButton:disabled {
                background-color: #222222;
                color: #666666;
                border-color: #444444;
            }
        """
        
        self.prev_button = QPushButton("⏮")
        self.prev_button.setStyleSheet(button_style)
        self.prev_button.setToolTip("Previous Frame (Left Arrow)")
        layout.addWidget(self.prev_button)
        
        self.play_button = QPushButton("▶")
        self.play_button.setStyleSheet(button_style)
        self.play_button.setToolTip("Play/Pause (Space)")
        layout.addWidget(self.play_button)
        
        self.stop_button = QPushButton("⏹")
        self.stop_button.setStyleSheet(button_style)
        self.stop_button.setToolTip("Stop")
        layout.addWidget(self.stop_button)
        
        self.next_button = QPushButton("⏭")
        self.next_button.setStyleSheet(button_style)
        self.next_button.setToolTip("Next Frame (Right Arrow)")
        layout.addWidget(self.next_button)
        
        layout.addStretch()

    def set_play_state(self, is_playing):
        """Update play button based on playback state"""
        if is_playing:
            self.play_button.setText("⏸")
        else:
            self.play_button.setText("▶")