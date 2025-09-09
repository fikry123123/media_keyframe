import os
import glob
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QMenuBar, QAction, QFileDialog, QHBoxLayout, QStatusBar, QLabel
from PyQt5.QtCore import Qt
from media_player import MediaPlayer
from media_controls import MediaControls
from timeline_widget import TimelineWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Studio Media Player")
        self.setGeometry(100, 100, 1200, 800)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #333333;
                color: #ffffff;
                border-bottom: 1px solid #555555;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #555555;
            }
            QMenu {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #555555;
            }
            QStatusBar {
                background-color: #333333;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
        """)
        
        self.image_sequence_files = []
        self.current_sequence_index = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Media player
        self.media_player = MediaPlayer()
        layout.addWidget(self.media_player, 1)
        
        # Timeline
        self.timeline = TimelineWidget()
        layout.addWidget(self.timeline)
        
        # Controls
        self.controls = MediaControls()
        layout.addWidget(self.controls)
        
        # Connect signals
        self.connect_signals()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar with frame counter
        self.create_status_bar()
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open File', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        open_folder_action = QAction('Open Image Sequence', self)
        open_folder_action.setShortcut('Ctrl+Shift+O')
        open_folder_action.triggered.connect(self.open_image_sequence)
        file_menu.addAction(open_folder_action)
        
    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Frame counter label
        self.frame_counter_label = QLabel("Frame: 0 / 0")
        self.frame_counter_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
                padding: 2px 8px;
                background-color: #444444;
                border-radius: 3px;
                margin: 2px;
            }
        """)
        self.status_bar.addPermanentWidget(self.frame_counter_label)
        
        # Status message
        self.status_bar.setStyleSheet("""
            QStatusBar {
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.status_bar.showMessage("Ready")
        
    def connect_signals(self):
        # Media controls
        self.controls.play_button.clicked.connect(self.toggle_play)
        self.controls.stop_button.clicked.connect(self.stop)
        self.controls.prev_button.clicked.connect(self.previous_frame)
        self.controls.next_button.clicked.connect(self.next_frame)
        
        # Timeline
        self.timeline.position_changed.connect(self.seek_to_position)
        
        # Media player signals
        if hasattr(self.media_player, 'frameIndexChanged'):
            self.media_player.frameIndexChanged.connect(self.update_frame_counter)
            
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Media File", 
            "", 
            "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.tiff);;All Files (*)"
        )
        
        if file_path:
            self.image_sequence_files = []
            self.current_sequence_index = 0
            success = self.media_player.load_media(file_path)
            if success:
                # Setup timeline for video
                if hasattr(self.media_player, 'is_video') and self.media_player.is_video:
                    self.timeline.set_duration(self.media_player.total_frames)
                    self.timeline.set_position(0)
                self.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}")
            else:
                self.status_bar.showMessage(f"Failed to load: {os.path.basename(file_path)}")
            
    def open_image_sequence(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Image Sequence",
            ""
        )
        
        if folder_path:
            # Supported image formats
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif', '*.gif']
            
            # Get all image files from the folder
            self.image_sequence_files = []
            for ext in image_extensions:
                pattern = os.path.join(folder_path, ext)
                self.image_sequence_files.extend(glob.glob(pattern))
                # Also check uppercase extensions
                pattern = os.path.join(folder_path, ext.upper())
                self.image_sequence_files.extend(glob.glob(pattern))
            
            # Sort files naturally (handles numbered sequences correctly)
            self.image_sequence_files.sort(key=self.natural_sort_key)
            
            if self.image_sequence_files:
                self.current_sequence_index = 0
                self.load_sequence_frame(0)
                self.timeline.set_duration(len(self.image_sequence_files))
                self.update_frame_counter(0, len(self.image_sequence_files))
                self.status_bar.showMessage(f"Loaded image sequence: {len(self.image_sequence_files)} frames from {os.path.basename(folder_path)}")
            else:
                self.status_bar.showMessage("No image files found in selected folder")
                
    def natural_sort_key(self, text):
        """
        Sort key for natural sorting of filenames with numbers
        """
        import re
        return [int(x) if x.isdigit() else x.lower() for x in re.split('([0-9]+)', text)]
        
    def load_sequence_frame(self, index):
        """Load a specific frame from the image sequence"""
        if 0 <= index < len(self.image_sequence_files):
            self.current_sequence_index = index
            self.media_player.load_media(self.image_sequence_files[index])
            self.timeline.set_position(index)
            self.update_frame_counter(index, len(self.image_sequence_files))
            
    def toggle_play(self):
        if self.image_sequence_files:
            # For image sequences, implement simple frame-by-frame playback
            if not hasattr(self, 'sequence_timer'):
                from PyQt5.QtCore import QTimer
                self.sequence_timer = QTimer()
                self.sequence_timer.timeout.connect(self.next_sequence_frame)
                
            if self.sequence_timer.isActive():
                self.sequence_timer.stop()
                self.controls.set_play_state(False)
                self.status_bar.showMessage("Paused")
            else:
                # Get speed from controls (FPS)
                fps = self.controls.get_playback_speed()
                interval = int(1000 / fps)  # Convert FPS to milliseconds
                self.sequence_timer.start(interval)
                self.controls.set_play_state(True)
                self.status_bar.showMessage(f"Playing image sequence at {fps} FPS")
        else:
            # For video files, use media player
            self.media_player.toggle_play()
            if hasattr(self.media_player, 'is_playing'):
                self.controls.set_play_state(self.media_player.is_playing)
                if self.media_player.is_playing:
                    self.status_bar.showMessage("Playing video")
                else:
                    self.status_bar.showMessage("Paused")
            
    def next_sequence_frame(self):
        """Move to next frame in sequence during playback"""
        if self.current_sequence_index < len(self.image_sequence_files) - 1:
            self.load_sequence_frame(self.current_sequence_index + 1)
        else:
            # End of sequence, stop playback
            self.sequence_timer.stop()
            self.controls.set_play_state(False)
            self.status_bar.showMessage("End of sequence reached")
            
    def stop(self):
        if hasattr(self, 'sequence_timer'):
            self.sequence_timer.stop()
            self.controls.set_play_state(False)
            
        if self.image_sequence_files:
            self.load_sequence_frame(0)
            self.status_bar.showMessage("Stopped - Back to first frame")
        else:
            self.media_player.stop()
            self.controls.set_play_state(False)
            self.status_bar.showMessage("Stopped")
            
    def previous_frame(self):
        if self.image_sequence_files:
            if self.current_sequence_index > 0:
                self.load_sequence_frame(self.current_sequence_index - 1)
        else:
            self.media_player.previous_frame()
            
    def next_frame(self):
        if self.image_sequence_files:
            if self.current_sequence_index < len(self.image_sequence_files) - 1:
                self.load_sequence_frame(self.current_sequence_index + 1)
        else:
            self.media_player.next_frame()
            
    def seek_to_position(self, position):
        if self.image_sequence_files:
            # For image sequences, position is frame index
            frame_index = int(position)
            self.load_sequence_frame(frame_index)
        else:
            self.media_player.seek_to_position(position)
            
    def update_frame_counter(self, current_frame, total_frames=None):
        """Update the frame counter display"""
        if total_frames is None:
            if self.image_sequence_files:
                total_frames = len(self.image_sequence_files)
            else:
                total_frames = getattr(self.media_player, 'total_frames', 0)
                
        self.frame_counter_label.setText(f"Frame: {current_frame + 1} / {total_frames}")
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        
        # Space for play/pause
        play_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        play_shortcut.activated.connect(self.toggle_play)
        
        # Left/Right arrows for frame navigation
        prev_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        prev_shortcut.activated.connect(self.previous_frame)
        
        next_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        next_shortcut.activated.connect(self.next_frame)
        
        # Home/End for first/last frame
        home_shortcut = QShortcut(QKeySequence(Qt.Key_Home), self)
        home_shortcut.activated.connect(self.go_to_first_frame)
        
        end_shortcut = QShortcut(QKeySequence(Qt.Key_End), self)
        end_shortcut.activated.connect(self.go_to_last_frame)
        
        # Page Up/Down for faster navigation
        page_up_shortcut = QShortcut(QKeySequence(Qt.Key_PageUp), self)
        page_up_shortcut.activated.connect(self.jump_backward)
        
        page_down_shortcut = QShortcut(QKeySequence(Qt.Key_PageDown), self)
        page_down_shortcut.activated.connect(self.jump_forward)
        
    def go_to_first_frame(self):
        """Go to the first frame"""
        if self.image_sequence_files:
            self.load_sequence_frame(0)
            
    def go_to_last_frame(self):
        """Go to the last frame"""
        if self.image_sequence_files:
            self.load_sequence_frame(len(self.image_sequence_files) - 1)
            
    def jump_backward(self):
        """Jump backward by 10 frames"""
        if self.image_sequence_files:
            new_index = max(0, self.current_sequence_index - 10)
            self.load_sequence_frame(new_index)
            
    def jump_forward(self):
        """Jump forward by 10 frames"""
        if self.image_sequence_files:
            new_index = min(len(self.image_sequence_files) - 1, self.current_sequence_index + 10)
            self.load_sequence_frame(new_index)