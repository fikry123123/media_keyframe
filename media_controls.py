from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal

class MediaControls(QWidget):
    position_changed = pyqtSignal(int)
    compare_toggled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        button_style = """
            QPushButton {
                background-color: #444444;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 16px;
                font-weight: bold;
                min-width: 40px;
                min-height: 30px;
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
        
        layout.addStretch()
        
        self.first_frame_button = QPushButton("⏮")
        self.first_frame_button.setStyleSheet(button_style)
        self.first_frame_button.setToolTip("Go to First Frame (Home)")
        layout.addWidget(self.first_frame_button)

        self.prev_button = QPushButton("⏴")
        self.prev_button.setStyleSheet(button_style)
        self.prev_button.setToolTip("Previous Frame (Left Arrow)")
        layout.addWidget(self.prev_button)
        
        self.play_button = QPushButton("▶")
        self.play_button.setStyleSheet(button_style)
        self.play_button.setToolTip("Play/Pause (Space)")
        layout.addWidget(self.play_button)
        
        self.next_button = QPushButton("⏵")
        self.next_button.setStyleSheet(button_style)
        self.next_button.setToolTip("Next Frame (Right Arrow)")
        layout.addWidget(self.next_button)

        self.last_frame_button = QPushButton("⏭")
        self.last_frame_button.setStyleSheet(button_style)
        self.last_frame_button.setToolTip("Go to Last Frame (End)")
        layout.addWidget(self.last_frame_button)
        
        layout.addSpacing(20)

        self.playback_mode_button = QPushButton("→")
        self.playback_mode_button.setStyleSheet(button_style)
        self.playback_mode_button.setToolTip("Playback Mode: Normal (Stop at end)")
        layout.addWidget(self.playback_mode_button)

        self.compare_button = QPushButton("Compare")
        self.compare_button.setStyleSheet(button_style)
        self.compare_button.setToolTip("Switch to compare (side-by-side) view")
        self.compare_button.clicked.connect(self.compare_toggled.emit)
        layout.addWidget(self.compare_button)
        
        layout.addStretch()

    def set_play_state(self, is_playing):
        """Update play button based on playback state"""
        if is_playing:
            self.play_button.setText("⏸")
        else:
            self.play_button.setText("▶")

    def set_compare_state(self, is_comparing):
        """Update compare button based on state"""
        if is_comparing:
            self.compare_button.setText("Single View")
            self.compare_button.setToolTip("Switch to single media view")
        else:
            self.compare_button.setText("Compare")
            self.compare_button.setToolTip("Switch to compare (side-by-side) view")
            
    def set_playback_mode_state(self, icon, tooltip):
        self.playback_mode_button.setText(icon)
        self.playback_mode_button.setToolTip(tooltip)