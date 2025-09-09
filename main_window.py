import os
import glob
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QMenuBar, QAction, 
                            QFileDialog, QHBoxLayout, QStatusBar, QLabel, QSplitter, 
                            QListWidget, QListWidgetItem, QPushButton, QCheckBox,
                            QGroupBox, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
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
        self.playlist_items = []
        self.compare_mode = False
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left panel - Playlist
        self.create_playlist_panel(main_splitter)
        
        # Center panel - Media player(s)
        self.create_media_panel(main_splitter)
        
        # Set initial splitter sizes (playlist 20%, media 80%)
        main_splitter.setSizes([250, 950])
        
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
        
        file_menu.addSeparator()
        
        clear_playlist_action = QAction('Clear Playlist', self)
        clear_playlist_action.triggered.connect(self.clear_playlist)
        file_menu.addAction(clear_playlist_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        self.compare_action = QAction('Compare Mode', self)
        self.compare_action.setCheckable(True)
        self.compare_action.setShortcut('Ctrl+T')
        self.compare_action.triggered.connect(self.toggle_compare_mode)
        view_menu.addAction(self.compare_action)
        
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
        
    def create_playlist_panel(self, parent_splitter):
        """Create the playlist panel"""
        playlist_widget = QWidget()
        playlist_layout = QVBoxLayout(playlist_widget)
        
        # Playlist header
        playlist_header = QLabel("Playlist")
        playlist_header.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
                background-color: #444444;
                border-radius: 4px;
                margin-bottom: 5px;
            }
        """)
        playlist_layout.addWidget(playlist_header)
        
        # Playlist controls
        playlist_controls = QHBoxLayout()
        
        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self.add_files_to_playlist)
        add_files_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        playlist_controls.addWidget(add_files_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_playlist)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #d13438;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        playlist_controls.addWidget(clear_btn)
        
        playlist_layout.addLayout(playlist_controls)
        
        # Playlist list
        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 2px solid #444444;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #444444;
                border-radius: 2px;
                margin: 1px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #444444;
            }
        """)
        self.playlist_widget.itemDoubleClicked.connect(self.load_from_playlist)
        playlist_layout.addWidget(self.playlist_widget)
        
        # Compare mode controls
        compare_group = QGroupBox("Compare Mode")
        compare_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 2px solid #444444;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        compare_layout = QVBoxLayout(compare_group)
        
        self.compare_checkbox = QCheckBox("Enable Compare")
        self.compare_checkbox.toggled.connect(self.toggle_compare_mode)
        self.compare_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #666666;
                background-color: #2b2b2b;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #0078d4;
                background-color: #0078d4;
                border-radius: 3px;
            }
        """)
        compare_layout.addWidget(self.compare_checkbox)
        
        compare_info = QLabel("Select two items from playlist\nto compare side by side")
        compare_info.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 11px;
                padding: 5px;
            }
        """)
        compare_layout.addWidget(compare_info)
        
        playlist_layout.addWidget(compare_group)
        
        parent_splitter.addWidget(playlist_widget)
        
    def create_media_panel(self, parent_splitter):
        """Create the media player panel"""
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)
        
        # Media player container
        self.media_container = QWidget()
        self.media_container_layout = QHBoxLayout(self.media_container)
        self.media_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Primary media player
        self.media_player = MediaPlayer()
        self.media_container_layout.addWidget(self.media_player)
        
        # Secondary media player (for compare mode)
        self.media_player_2 = MediaPlayer()
        self.media_player_2.hide()
        self.media_container_layout.addWidget(self.media_player_2)
        
        media_layout.addWidget(self.media_container, 1)
        
        # Timeline
        self.timeline = TimelineWidget()
        media_layout.addWidget(self.timeline)
        
        # Controls
        self.controls = MediaControls()
        media_layout.addWidget(self.controls)
        
        parent_splitter.addWidget(media_widget)
        
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
            
        # Connect second media player signals in compare mode
        if hasattr(self.media_player_2, 'frameIndexChanged'):
            self.media_player_2.frameIndexChanged.connect(self.update_frame_counter)
            
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Media File", 
            "", 
            "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.tiff);;All Files (*)"
        )
        
        if file_path:
            # Add to playlist and load
            self.add_files_to_playlist_from_paths([file_path])
            self.load_single_file(file_path)
            
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
            # For video files, use media player(s)
            if self.compare_mode and self.media_player_2.isVisible():
                # Control both players in compare mode
                self.media_player.toggle_play()
                self.media_player_2.toggle_play()
                
                if hasattr(self.media_player, 'is_playing'):
                    self.controls.set_play_state(self.media_player.is_playing)
                    if self.media_player.is_playing:
                        self.status_bar.showMessage("Playing comparison")
                    else:
                        self.status_bar.showMessage("Paused comparison")
            else:
                # Single player mode
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
            if self.compare_mode and self.media_player_2.isVisible():
                self.media_player_2.stop()
            self.controls.set_play_state(False)
            self.status_bar.showMessage("Stopped")
            
    def previous_frame(self):
        if self.image_sequence_files:
            if self.current_sequence_index > 0:
                self.load_sequence_frame(self.current_sequence_index - 1)
        else:
            self.media_player.previous_frame()
            if self.compare_mode and self.media_player_2.isVisible():
                self.media_player_2.previous_frame()
            
    def next_frame(self):
        if self.image_sequence_files:
            if self.current_sequence_index < len(self.image_sequence_files) - 1:
                self.load_sequence_frame(self.current_sequence_index + 1)
        else:
            self.media_player.next_frame()
            if self.compare_mode and self.media_player_2.isVisible():
                self.media_player_2.next_frame()
            
    def seek_to_position(self, position):
        if self.image_sequence_files:
            # For image sequences, position is frame index
            frame_index = int(position)
            self.load_sequence_frame(frame_index)
        else:
            self.media_player.seek_to_position(position)
            if self.compare_mode and self.media_player_2.isVisible():
                self.media_player_2.seek_to_position(position)
            
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
        
        # Compare mode toggle
        compare_shortcut = QShortcut(QKeySequence('Ctrl+T'), self)
        compare_shortcut.activated.connect(lambda: self.toggle_compare_mode(not self.compare_mode))
        
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
            
    # Drag and Drop functionality
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        """Handle drop events"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                files.append(file_path)
                
        if files:
            self.add_files_to_playlist_from_paths(files)
            event.accept()
        else:
            event.ignore()
            
    # Playlist management
    def add_files_to_playlist(self):
        """Add files to playlist via dialog"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Add Files to Playlist",
            "",
            "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.tiff);;All Files (*)"
        )
        
        if files:
            self.add_files_to_playlist_from_paths(files)
            
    def add_files_to_playlist_from_paths(self, file_paths):
        """Add files to playlist from file paths"""
        for file_path in file_paths:
            if os.path.exists(file_path):
                # Check if file is already in playlist
                if not any(item['path'] == file_path for item in self.playlist_items):
                    item_info = {
                        'path': file_path,
                        'name': os.path.basename(file_path),
                        'type': self.get_file_type(file_path)
                    }
                    self.playlist_items.append(item_info)
                    
                    # Add to list widget
                    list_item = QListWidgetItem(f"{item_info['name']} ({item_info['type']})")
                    list_item.setData(Qt.UserRole, file_path)
                    self.playlist_widget.addItem(list_item)
                    
        self.status_bar.showMessage(f"Playlist: {len(self.playlist_items)} items")
        
    def get_file_type(self, file_path):
        """Determine file type"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.mp4', '.avi', '.mov', '.mkv']:
            return 'Video'
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return 'Image'
        else:
            return 'Unknown'
            
    def clear_playlist(self):
        """Clear the playlist"""
        self.playlist_items.clear()
        self.playlist_widget.clear()
        self.status_bar.showMessage("Playlist cleared")
        
    def load_from_playlist(self, item):
        """Load file from playlist"""
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            if self.compare_mode:
                self.load_compare_files(file_path)
            else:
                self.load_single_file(file_path)
                
    def load_single_file(self, file_path):
        """Load single file in normal mode"""
        self.image_sequence_files = []
        self.current_sequence_index = 0
        success = self.media_player.load_media(file_path)
        if success:
            if hasattr(self.media_player, 'is_video') and self.media_player.is_video:
                self.timeline.set_duration(self.media_player.total_frames)
                self.timeline.set_position(0)
            self.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}")
        else:
            self.status_bar.showMessage(f"Failed to load: {os.path.basename(file_path)}")
            
    def load_compare_files(self, file_path):
        """Load files in compare mode"""
        selected_items = self.playlist_widget.selectedItems()
        if len(selected_items) == 2:
            # Load first file in left player
            file1 = selected_items[0].data(Qt.UserRole)
            self.media_player.load_media(file1)
            
            # Load second file in right player
            file2 = selected_items[1].data(Qt.UserRole)
            self.media_player_2.load_media(file2)
            
            self.status_bar.showMessage(f"Comparing: {os.path.basename(file1)} vs {os.path.basename(file2)}")
        else:
            self.status_bar.showMessage("Select exactly 2 items for comparison")
            
    # Compare mode functionality
    def toggle_compare_mode(self, enabled=None):
        """Toggle compare mode"""
        if enabled is None:
            enabled = self.compare_checkbox.isChecked()
        else:
            self.compare_checkbox.setChecked(enabled)
            
        self.compare_mode = enabled
        self.compare_action.setChecked(enabled)
        
        if enabled:
            # Show second media player
            self.media_player_2.show()
            self.status_bar.showMessage("Compare mode enabled - Select 2 items from playlist")
        else:
            # Hide second media player
            self.media_player_2.hide()
            self.status_bar.showMessage("Compare mode disabled")