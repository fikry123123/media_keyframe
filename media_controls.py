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
        
        # Improved button styling for better legibility
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
        
        # Previous frame button
        self.prev_button = QPushButton("⏮")
        self.prev_button.setStyleSheet(button_style)
        self.prev_button.setToolTip("Previous Frame (Left Arrow)")
        layout.addWidget(self.prev_button)
        
        # Play/Pause button
        self.play_button = QPushButton("▶")
        self.play_button.setStyleSheet(button_style)
        self.play_button.setToolTip("Play/Pause (Space)")
        layout.addWidget(self.play_button)
        
        # Stop button
        self.stop_button = QPushButton("⏹")
        self.stop_button.setStyleSheet(button_style)
        self.stop_button.setToolTip("Stop")
        layout.addWidget(self.stop_button)
        
        # Next frame button
        self.next_button = QPushButton("⏭")
        self.next_button.setStyleSheet(button_style)
        self.next_button.setToolTip("Next Frame (Right Arrow)")
        layout.addWidget(self.next_button)
        
        # Add stretch to push everything to the left
        layout.addStretch()
        
        # Speed control label
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                margin-right: 5px;
            }
        """)
        layout.addWidget(speed_label)
        
        # Speed slider for image sequences
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(30)
        self.speed_slider.setValue(10)  # Default 10 FPS
        self.speed_slider.setMaximumWidth(100)
        self.speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 2px solid #666666;
                height: 8px;
                background: #333333;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #666666;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #dddddd;
            }
        """)
        self.speed_slider.setToolTip("Playback Speed (FPS)")
        layout.addWidget(self.speed_slider)
        
        # Speed value label
        self.speed_value_label = QLabel("10 FPS")
        self.speed_value_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                min-width: 50px;
                margin-left: 5px;
            }
        """)
        layout.addWidget(self.speed_value_label)
        
        # Connect speed slider
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        
    def update_speed_label(self, value):
        self.speed_value_label.setText(f"{value} FPS")
        
    def get_playback_speed(self):
        """Get current playback speed in FPS"""
        return self.speed_slider.value()
        
    def set_play_state(self, is_playing):
        """Update play button based on playback state"""
        if is_playing:
            self.play_button.setText("⏸")
        else:
            self.play_button.setText("▶")