import os
import glob
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QMenuBar, QAction, 
                            QFileDialog, QHBoxLayout, QStatusBar, QLabel, QSplitter, 
                            QListWidget, QListWidgetItem, QPushButton, QCheckBox,
                            QGroupBox, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QKeySequence
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
            QPushButton {
                background-color: #5d5d5d;
                border: 1px solid #777777;
                padding: 5px;
                border-radius: 4px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #6a6a6a;
            }
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
        """)
        
        self.image_sequence_files = []
        self.current_sequence_index = 0
        self.playlist_items = []
        self.compare_mode = False
        self.marks = []
        
        # Inisialisasi FPS
        self.media_player_A_fps = 0.0
        self.media_player_B_fps = 0.0
        
        # Inisialisasi mode waktu
        self.show_timecode = False
        
        self.compare_timer = QTimer(self)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Left panel - Playlist
        self.create_playlist_panel(self.main_splitter)
        
        # Center panel - Media player(s)
        self.create_media_panel(self.main_splitter)
        
        # Set initial splitter sizes (playlist 20%, media 80%)
        self.main_splitter.setSizes([250, 950])
        self.last_playlist_size = 250
        
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

        self.hide_playlist_action = QAction("Hide Playlist Panel", self)
        self.hide_playlist_action.setShortcut('Ctrl+H')
        self.hide_playlist_action.triggered.connect(self.toggle_playlist_panel)
        view_menu.addAction(self.hide_playlist_action)
        
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

        # FPS label
        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setStyleSheet("""
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
        self.status_bar.addPermanentWidget(self.fps_label)
        
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
        self.playlist_widget_container = QWidget()
        playlist_layout = QVBoxLayout(self.playlist_widget_container)
        
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

        # Tombol untuk menyembunyikan panel
        self.hide_panel_button = QPushButton("Hide")
        self.hide_panel_button.clicked.connect(self.toggle_playlist_panel)
        self.hide_panel_button.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5d5d5d;
            }
        """)
        playlist_controls.addWidget(self.hide_panel_button)

        playlist_layout.addLayout(playlist_controls)
        
        # Playlist list
        self.playlist_widget = QListWidget()
        self.playlist_widget.setSelectionMode(QListWidget.ExtendedSelection)
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
        
        compare_button = QPushButton("Compare Selected")
        compare_button.clicked.connect(self.load_compare_files)
        compare_button.setStyleSheet("""
            QPushButton {
                background-color: #5d5d5d;
                border: 1px solid #777777;
                padding: 5px;
                border-radius: 4px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #6a6a6a;
            }
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
        """)
        playlist_layout.addWidget(compare_button)
        
        parent_splitter.addWidget(self.playlist_widget_container)
                
    def create_media_panel(self, parent_splitter):
        """Create the media player panel"""
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)
        
        # Media player container
        self.media_container = QWidget()
        self.media_container_layout = QHBoxLayout(self.media_container)
        self.media_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Menghilangkan celah antara kedua video player
        self.media_container_layout.setSpacing(0)
        
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
        # Sinyal baru untuk mode tampilan waktu
        self.timeline.display_mode_changed.connect(self.set_time_display_mode)

        # Media player signals
        if hasattr(self.media_player, 'frameIndexChanged'):
            self.media_player.frameIndexChanged.connect(self.update_frame_counter) 
            
        if hasattr(self.media_player, 'playStateChanged'):
            self.media_player.playStateChanged.connect(self.controls.set_play_state)

        # Connect second media player signals in compare mode
        if hasattr(self.media_player_2, 'frameIndexChanged'):
            self.media_player_2.frameIndexChanged.connect(self.update_frame_counter)
            
        if hasattr(self.media_player_2, 'playStateChanged'):
            self.media_player_2.playStateChanged.connect(self.controls.set_play_state)

        # HUBUNGKAN SINYAL FPS KE FUNGSI UPDATE BARU
        if hasattr(self.media_player, 'fpsChanged'):
            self.media_player.fpsChanged.connect(lambda fps: self.update_fps_display(fps, 'A'))
        if hasattr(self.media_player_2, 'fpsChanged'):
            self.media_player_2.fpsChanged.connect(lambda fps: self.update_fps_display(fps, 'B'))
            
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Media File", 
            "", 
            "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.tiff);;All Files (*)"
        )
        
        if file_path:
            self.add_files_to_playlist_from_paths([file_path])
            self.load_single_file(file_path)
            
    def open_image_sequence(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Image Sequence",
            ""
        )
        
        if folder_path:
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif', '*.gif']
            
            self.image_sequence_files = []
            for ext in image_extensions:
                pattern = os.path.join(folder_path, ext)
                self.image_sequence_files.extend(glob.glob(pattern))
                pattern = os.path.join(folder_path, ext.upper())
                self.image_sequence_files.extend(glob.glob(pattern))
            
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
        import re
        return [int(x) if x.isdigit() else x.lower() for x in re.split('([0-9]+)', text)]
        
    def load_sequence_frame(self, index):
        if 0 <= index < len(self.image_sequence_files):
            self.current_sequence_index = index
            self.media_player.load_media(self.image_sequence_files[index])
            self.timeline.set_position(index)
            self.update_frame_counter(index, len(self.image_sequence_files))
            
    def toggle_play(self):
        if self.image_sequence_files:
            if not hasattr(self, 'sequence_timer'):
                from PyQt5.QtCore import QTimer
                self.sequence_timer = QTimer()
                self.sequence_timer.timeout.connect(self.next_sequence_frame)
                
            if self.sequence_timer.isActive():
                self.sequence_timer.stop()
                self.controls.set_play_state(False)
                self.status_bar.showMessage("Paused")
            else:
                fps = self.controls.get_playback_speed()
                interval = int(1000 / fps)
                self.sequence_timer.start(interval)
                self.controls.set_play_state(True)
                self.status_bar.showMessage(f"Playing image sequence at {fps} FPS")
        else:
            if self.compare_mode and self.media_player_2.isVisible():
                self.media_player.toggle_play()
                self.media_player_2.toggle_play()
                
                if hasattr(self.media_player, 'is_playing'):
                    self.controls.set_play_state(self.media_player.is_playing)
                    if self.media_player.is_playing:
                        self.status_bar.showMessage("Playing comparison")
                    else:
                        self.status_bar.showMessage("Paused comparison")
            else:
                self.media_player.toggle_play()
                if hasattr(self.media_player, 'is_playing'):
                    self.controls.set_play_state(self.media_player.is_playing)
                    if self.media_player.is_playing:
                        self.status_bar.showMessage("Playing video")
                    else:
                        self.status_bar.showMessage("Paused")
                        
    def next_sequence_frame(self):
        if self.current_sequence_index < len(self.image_sequence_files) - 1:
            self.load_sequence_frame(self.current_sequence_index + 1)
        else:
            self.sequence_timer.stop()
            self.controls.set_play_state(False)
            self.status_bar.showMessage("End of sequence reached")
            
    def stop(self):
        if hasattr(self, 'sequence_timer') and self.sequence_timer.isActive():
            self.sequence_timer.stop()
            
        self.controls.set_play_state(False)
            
        if self.image_sequence_files:
            self.load_sequence_frame(0)
            self.status_bar.showMessage("Stopped - Back to first frame")
        else:
            self.media_player.stop()
            if self.compare_mode and self.media_player_2.isVisible():
                self.media_player_2.stop()
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
            frame_index = int(position)
            self.load_sequence_frame(frame_index)
        else:
            self.media_player.seek_to_position(position)
            if self.compare_mode and self.media_player_2.isVisible():
                self.media_player_2.seek_to_position(position)
            
    def update_frame_counter(self, current_frame, total_frames=None):
        if total_frames is None:
            if self.image_sequence_files:
                total_frames = len(self.image_sequence_files)
            else:
                total_frames = getattr(self.media_player, 'total_frames', 0)
        
        self.timeline.set_marks(self.marks)

        if self.show_timecode and self.media_player_A_fps > 0:
            total_seconds = total_frames / self.media_player_A_fps
            current_seconds = current_frame / self.media_player_A_fps
            
            minutes = int(current_seconds // 60)
            seconds = int(current_seconds % 60)
            frames = int((current_seconds - int(current_seconds)) * self.media_player_A_fps)
            
            total_minutes = int(total_seconds // 60)
            total_seconds_part = int(total_seconds % 60)
            total_frames_part = int((total_seconds - int(total_seconds)) * self.media_player_A_fps)
            
            self.frame_counter_label.setText(f"Time: {minutes:02d}:{seconds:02d}.{frames:02d} / {total_minutes:02d}:{total_seconds_part:02d}.{total_frames_part:02d}")
            self.timeline.set_timecode_mode(True)
        else:
            self.frame_counter_label.setText(f"Frame: {current_frame + 1} / {total_frames}")
            self.timeline.set_timecode_mode(False)

        self.timeline.set_fps(self.media_player_A_fps)
        self.timeline.set_duration(total_frames)
        self.timeline.set_position(current_frame)
        
    def setup_shortcuts(self):
        from PyQt5.QtWidgets import QShortcut
        
        play_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        play_shortcut.activated.connect(self.toggle_play)
        
        prev_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        prev_shortcut.activated.connect(self.previous_frame)
        
        next_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        next_shortcut.activated.connect(self.next_frame)
        
        home_shortcut = QShortcut(QKeySequence(Qt.Key_Home), self)
        home_shortcut.activated.connect(self.go_to_first_frame)
        
        end_shortcut = QShortcut(QKeySequence(Qt.Key_End), self)
        end_shortcut.activated.connect(self.go_to_last_frame)
        
        page_up_shortcut = QShortcut(QKeySequence(Qt.Key_PageUp), self)
        page_up_shortcut.activated.connect(self.jump_backward)
        
        page_down_shortcut = QShortcut(QKeySequence(Qt.Key_PageDown), self)
        page_down_shortcut.activated.connect(self.jump_forward)
        
        compare_shortcut = QShortcut(QKeySequence('Ctrl+T'), self)
        compare_shortcut.activated.connect(lambda: self.toggle_compare_mode(not self.compare_mode))

        # Shortcuts untuk mark dan jump
        mark_shortcut = QShortcut(QKeySequence(Qt.Key_F), self)
        mark_shortcut.activated.connect(self.toggle_mark)
        
        prev_mark_shortcut = QShortcut(QKeySequence(Qt.Key_BracketLeft), self)
        prev_mark_shortcut.activated.connect(self.jump_to_previous_mark)
        
        next_mark_shortcut = QShortcut(QKeySequence(Qt.Key_BracketRight), self)
        next_mark_shortcut.activated.connect(self.jump_to_next_mark)
        
        # Shortcut untuk hide/show sidebar
        hide_panel_shortcut = QShortcut(QKeySequence('Ctrl+H'), self)
        hide_panel_shortcut.activated.connect(self.toggle_playlist_panel)
        
    def toggle_mark(self):
        current_frame = getattr(self.media_player, 'current_frame_index', 0)
        
        if current_frame in self.marks:
            self.marks.remove(current_frame)
            self.status_bar.showMessage(f"Mark removed at frame: {current_frame}")
        else:
            self.marks.append(current_frame)
            self.marks.sort()
            self.status_bar.showMessage(f"Mark added at frame: {current_frame}")
        
        self.timeline.set_marks(self.marks)
        
    def jump_to_previous_mark(self):
        if not self.marks:
            self.status_bar.showMessage("No marks available.")
            return
            
        current_frame = getattr(self.media_player, 'current_frame_index', 0)
        
        # Cari mark sebelumnya
        prev_marks = [m for m in self.marks if m < current_frame]
        if prev_marks:
            target_frame = max(prev_marks)
            self.media_player.seek_to_position(target_frame)
        else:
            self.status_bar.showMessage("No previous mark found.")

    def jump_to_next_mark(self):
        if not self.marks:
            self.status_bar.showMessage("No marks available.")
            return
            
        current_frame = getattr(self.media_player, 'current_frame_index', 0)
        
        # Cari mark berikutnya
        next_marks = [m for m in self.marks if m > current_frame]
        if next_marks:
            target_frame = min(next_marks)
            self.media_player.seek_to_position(target_frame)
        else:
            self.status_bar.showMessage("No next mark found.")
            
    def set_time_display_mode(self, show_timecode):
        self.show_timecode = show_timecode
        current_frame = getattr(self.media_player, 'current_frame_index', 0)
        total_frames = getattr(self.media_player, 'total_frames', 0)
        self.update_frame_counter(current_frame, total_frames)

    def toggle_playlist_panel(self):
        sizes = self.main_splitter.sizes()
        if sizes[0] > 0:
            self.last_playlist_size = sizes[0] # Simpan ukuran saat ini
            self.main_splitter.setSizes([0, sizes[1]])
            self.hide_playlist_action.setText("Show Playlist Panel")
            self.hide_panel_button.setText("Show")
            self.status_bar.showMessage("Playlist panel hidden")
        else:
            # Jika sebelumnya disembunyikan, kembalikan ke ukuran terakhir
            self.main_splitter.setSizes([self.last_playlist_size, sizes[1]])
            self.hide_playlist_action.setText("Hide Playlist Panel")
            self.hide_panel_button.setText("Hide")
            self.status_bar.showMessage("Playlist panel shown")
            
    def go_to_first_frame(self):
        if self.image_sequence_files:
            self.load_sequence_frame(0)
            
    def go_to_last_frame(self):
        if self.image_sequence_files:
            self.load_sequence_frame(len(self.image_sequence_files) - 1)
            
    def jump_backward(self):
        if self.image_sequence_files:
            new_index = max(0, self.current_sequence_index - 10)
            self.load_sequence_frame(new_index)
        else:
            current_frame = getattr(self.media_player, 'current_frame_index', 0)
            target_frame = max(0, current_frame - 10)
            self.media_player.seek_to_position(target_frame)
            
    def jump_forward(self):
        if self.image_sequence_files:
            new_index = min(len(self.image_sequence_files) - 1, self.current_sequence_index + 10)
            self.load_sequence_frame(new_index)
        else:
            current_frame = getattr(self.media_player, 'current_frame_index', 0)
            total_frames = getattr(self.media_player, 'total_frames', 0)
            target_frame = min(total_frames - 1, current_frame + 10)
            self.media_player.seek_to_position(target_frame)
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
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
            
    def add_files_to_playlist(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Add Files to Playlist",
            "",
            "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.tiff);;All Files (*)"
        )
        
        if files:
            self.add_files_to_playlist_from_paths(files)
            
    def add_files_to_playlist_from_paths(self, file_paths):
        for file_path in file_paths:
            if os.path.exists(file_path):
                if not any(item['path'] == file_path for item in self.playlist_items):
                    item_info = {
                        'path': file_path,
                        'name': os.path.basename(file_path),
                        'type': self.get_file_type(file_path)
                    }
                    self.playlist_items.append(item_info)
                    
                    list_item = QListWidgetItem(f"{item_info['name']} ({item_info['type']})")
                    list_item.setData(Qt.UserRole, file_path)
                    self.playlist_widget.addItem(list_item)
                    
        self.status_bar.showMessage(f"Playlist: {len(self.playlist_items)} items")
        
    def get_file_type(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.mp4', '.avi', '.mov', '.mkv']:
            return 'Video'
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return 'Image'
        else:
            return 'Unknown'
            
    def clear_playlist(self):
        self.playlist_items.clear()
        self.playlist_widget.clear()
        self.status_bar.showMessage("Playlist cleared")
        self.update_frame_counter(0, 0)
        
    def load_from_playlist(self, item):
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            selected_items = self.playlist_widget.selectedItems()
            if self.compare_mode and len(selected_items) == 2:
                self.load_compare_files()
            else:
                self.load_single_file(file_path)
                
    def load_single_file(self, file_path):
        self.image_sequence_files = []
        self.current_sequence_index = 0
        self.marks = []
        success = self.media_player.load_media(file_path)
        if success:
            if hasattr(self.media_player, 'is_video') and self.media_player.is_video:
                self.timeline.set_duration(self.media_player.total_frames)
                self.timeline.set_position(0)
            self.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}")
            self.reset_playlist_indicators()
            self.update_playlist_item_indicator(file_path, "A")
            self.timeline.set_marks(self.marks)
        else:
            self.status_bar.showMessage(f"Failed to load: {os.path.basename(file_path)}")
            
    def load_compare_files(self):
        selected_items = self.playlist_widget.selectedItems()
        if len(selected_items) == 2:
            file1 = selected_items[0].data(Qt.UserRole)
            self.media_player.load_media(file1)
            
            file2 = selected_items[1].data(Qt.UserRole)
            self.media_player_2.load_media(file2)
            
            self.marks = []
            self.status_bar.showMessage(f"Comparing: {os.path.basename(file1)} vs {os.path.basename(file2)}")
            self.reset_playlist_indicators()
            self.update_playlist_item_indicator(file1, "A")
            self.update_playlist_item_indicator(file2, "B")
            self.timeline.set_marks(self.marks)
        else:
            self.status_bar.showMessage("Select exactly 2 items for comparison")
            
    def toggle_compare_mode(self, enabled=None):
            if enabled is None:
                enabled = self.compare_checkbox.isChecked()
            else:
                self.compare_checkbox.setChecked(enabled)
                
            self.compare_mode = enabled
            self.compare_action.setChecked(enabled)
            
            if enabled:
                self.media_player_2.show()
                self.status_bar.showMessage("Compare mode enabled - Select 2 items from playlist")
                if self.playlist_widget.count() >= 2:
                    file1 = self.playlist_widget.item(0).data(Qt.UserRole)
                    file2 = self.playlist_widget.item(1).data(Qt.UserRole)
                    
                    self.media_player.load_media(file1)
                    self.media_player_2.load_media(file2)
                    
                    self.media_player.play()
                    self.media_player_2.play()
                    
            else:
                self.media_player_2.hide()
                self.media_player_2.stop()
                self.status_bar.showMessage("Compare mode disabled")
                
    def reset_playlist_indicators(self):
        """Menghapus semua indikator (A) dan (B) dari item playlist."""
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            text = item.text()
            # Hapus indikator yang ada
            text = text.replace(" (A)", "").replace(" (B)", "")
            item.setText(text)
            
    def update_playlist_item_indicator(self, file_path, indicator):
        """
        Menambahkan indikator (A) atau (B) ke item playlist yang sesuai.
        """
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            if item.data(Qt.UserRole) == file_path:
                text = item.text()
                # Tambahkan indikator baru
                if f" ({indicator})" not in text:
                    item.setText(f"{text} ({indicator})")
                break

    def update_fps_display(self, fps, indicator):
        """
        Memperbarui tampilan FPS di status bar.
        """
        if indicator == 'A':
            self.media_player_A_fps = fps
        elif indicator == 'B':
            self.media_player_B_fps = fps

        if self.compare_mode:
            # Format tampilan untuk mode perbandingan
            text_a = f"A: {self.media_player_A_fps:.2f} FPS"
            text_b = f"B: {self.media_player_B_fps:.2f} FPS"
            self.fps_label.setText(f"{text_a} | {text_b}")
        else:
            # Format tampilan untuk mode tunggal
            self.fps_label.setText(f"FPS: {self.media_player_A_fps:.2f}")