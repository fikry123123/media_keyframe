import os
import glob
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QMenuBar, QAction,
                            QFileDialog, QHBoxLayout, QStatusBar, QLabel, QSplitter,
                            QListWidget, QListWidgetItem, QPushButton, QShortcut)
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

        self.media_player_A_fps = 0.0
        self.media_player_B_fps = 0.0
        self.show_timecode = False

        # Enable drag and drop
        self.setAcceptDrops(True)

        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)

        self.create_playlist_panel(self.main_splitter)
        self.create_media_panel(self.main_splitter)

        self.main_splitter.setSizes([250, 950])
        self.last_playlist_size = 250

        self.connect_signals()
        self.create_menu_bar()
        self.create_status_bar()
        self.setup_shortcuts()

    def create_menu_bar(self):
        menubar = self.menuBar()

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

        view_menu = menubar.addMenu('View')
        self.compare_action = QAction('Toggle Compare Mode', self)
        self.compare_action.setCheckable(True)
        self.compare_action.setShortcut('Ctrl+T')
        self.compare_action.triggered.connect(self.toggle_compare_mode_from_menu)
        view_menu.addAction(self.compare_action)

        self.hide_playlist_action = QAction("Hide Playlist Panel", self)
        self.hide_playlist_action.setShortcut('Ctrl+H')
        self.hide_playlist_action.triggered.connect(self.toggle_playlist_panel)
        view_menu.addAction(self.hide_playlist_action)

    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.frame_counter_label = QLabel("Frame: 0 / 0")
        self.frame_counter_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; font-size: 14px; padding: 2px 8px; background-color: #444444; border-radius: 3px; margin: 2px; }")
        self.status_bar.addPermanentWidget(self.frame_counter_label)

        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setStyleSheet("QLabel { color: #ffffff; font-weight: bold; font-size: 14px; padding: 2px 8px; background-color: #444444; border-radius: 3px; margin: 2px; }")
        self.status_bar.addPermanentWidget(self.fps_label)

        self.status_bar.setStyleSheet("QStatusBar { font-size: 12px; font-weight: bold; }")
        self.status_bar.showMessage("Ready")

    def create_playlist_panel(self, parent_splitter):
        self.playlist_widget_container = QWidget()
        playlist_layout = QVBoxLayout(self.playlist_widget_container)

        playlist_header = QLabel("Playlist")
        playlist_header.setStyleSheet("QLabel { color: #ffffff; font-size: 16px; font-weight: bold; padding: 8px; background-color: #444444; border-radius: 4px; margin-bottom: 5px; }")
        playlist_layout.addWidget(playlist_header)

        playlist_controls = QHBoxLayout()
        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self.add_files_to_playlist)
        add_files_btn.setStyleSheet("QPushButton { background-color: #0078d4; color: white; border: none; padding: 6px 12px; border-radius: 3px; font-weight: bold; } QPushButton:hover { background-color: #106ebe; }")
        playlist_controls.addWidget(add_files_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_playlist)
        clear_btn.setStyleSheet("QPushButton { background-color: #d13438; color: white; border: none; padding: 6px 12px; border-radius: 3px; font-weight: bold; } QPushButton:hover { background-color: #b71c1c; }")
        playlist_controls.addWidget(clear_btn)

        self.hide_panel_button = QPushButton("Hide")
        self.hide_panel_button.clicked.connect(self.toggle_playlist_panel)
        self.hide_panel_button.setStyleSheet("QPushButton { background-color: #4a4a4a; color: white; border: none; padding: 6px 12px; border-radius: 3px; font-weight: bold; } QPushButton:hover { background-color: #5d5d5d; }")
        playlist_controls.addWidget(self.hide_panel_button)
        playlist_layout.addLayout(playlist_controls)

        self.playlist_widget = QListWidget()
        self.playlist_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.playlist_widget.setDragDropMode(QListWidget.InternalMove)
        self.playlist_widget.setStyleSheet("""
            QListWidget { background-color: #2b2b2b; color: #ffffff; border: 2px solid #444444; border-radius: 4px; padding: 4px; font-size: 12px; }
            QListWidget::item { padding: 6px; border-bottom: 1px solid #444444; border-radius: 2px; margin: 1px; }
            QListWidget::item:selected { background-color: #0078d4; color: white; }
            QListWidget::item:hover { background-color: #444444; }
        """)
        self.playlist_widget.itemDoubleClicked.connect(self.load_from_playlist)
        playlist_layout.addWidget(self.playlist_widget)

        parent_splitter.addWidget(self.playlist_widget_container)

    def create_media_panel(self, parent_splitter):
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)

        self.media_container = QWidget()
        self.media_container_layout = QHBoxLayout(self.media_container)
        self.media_container_layout.setContentsMargins(0, 0, 0, 0)
        self.media_container_layout.setSpacing(2)  # Small spacing between players

        self.media_player = MediaPlayer()
        self.media_container_layout.addWidget(self.media_player)

        self.media_player_2 = MediaPlayer()
        self.media_player_2.hide()
        self.media_container_layout.addWidget(self.media_player_2)

        media_layout.addWidget(self.media_container, 1)

        self.timeline = TimelineWidget()
        media_layout.addWidget(self.timeline)

        self.controls = MediaControls()
        self.controls.set_compare_state(self.compare_mode)
        media_layout.addWidget(self.controls)

        parent_splitter.addWidget(media_widget)

    def connect_signals(self):
        self.controls.play_button.clicked.connect(self.toggle_play)
        self.controls.stop_button.clicked.connect(self.stop)
        self.controls.prev_button.clicked.connect(self.previous_frame)
        self.controls.next_button.clicked.connect(self.next_frame)
        self.controls.compare_toggled.connect(self.toggle_compare_mode_from_button)

        self.playlist_widget.model().rowsMoved.connect(self.sync_playlist_data)

        self.timeline.position_changed.connect(self.seek_to_position)
        self.timeline.display_mode_changed.connect(self.set_time_display_mode)

        self.media_player.frameIndexChanged.connect(self.update_frame_counter)
        self.media_player.playStateChanged.connect(self.controls.set_play_state)
        self.media_player_2.frameIndexChanged.connect(self.update_frame_counter)
        self.media_player_2.playStateChanged.connect(self.controls.set_play_state)

        self.media_player.fpsChanged.connect(lambda fps: self.update_fps_display(fps, 'A'))
        self.media_player_2.fpsChanged.connect(lambda fps: self.update_fps_display(fps, 'B'))

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Media File", "", "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.tiff);;All Files (*)")
        if file_path:
            self.add_files_to_playlist_from_paths([file_path])
            self.toggle_compare_mode(False)
            self.load_single_file(file_path)

    def open_image_sequence(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder with Image Sequence", "")
        if folder_path:
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif', '*.gif']
            self.image_sequence_files = []
            for ext in image_extensions:
                self.image_sequence_files.extend(glob.glob(os.path.join(folder_path, ext)))
                self.image_sequence_files.extend(glob.glob(os.path.join(folder_path, ext.upper())))

            self.image_sequence_files.sort(key=self.natural_sort_key)

            if self.image_sequence_files:
                self.current_sequence_index = 0
                self.toggle_compare_mode(False)
                self.load_sequence_frame(0)
                self.timeline.set_duration(len(self.image_sequence_files))
                self.update_frame_counter(0, len(self.image_sequence_files))
                self.status_bar.showMessage(f"Loaded sequence: {len(self.image_sequence_files)} frames")
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
                self.sequence_timer = QTimer()
                self.sequence_timer.timeout.connect(self.next_sequence_frame)
            if self.sequence_timer.isActive():
                self.sequence_timer.stop()
                self.controls.set_play_state(False)
            else:
                fps = self.media_player_A_fps
                interval = int(1000 / fps) if fps > 0 else 1000
                self.sequence_timer.start(interval)
                self.controls.set_play_state(True)
        else:
            if self.compare_mode:
                is_playing_before_toggle = self.media_player.is_playing
                self.media_player.toggle_play()
                self.media_player_2.toggle_play()
                self.controls.set_play_state(not is_playing_before_toggle)
            else:
                self.media_player.toggle_play()
                self.controls.set_play_state(self.media_player.is_playing)

    def next_sequence_frame(self):
        if self.current_sequence_index < len(self.image_sequence_files) - 1:
            self.load_sequence_frame(self.current_sequence_index + 1)
        else:
            self.sequence_timer.stop()
            self.controls.set_play_state(False)

    def stop(self):
        if hasattr(self, 'sequence_timer') and self.sequence_timer.isActive():
            self.sequence_timer.stop()
        self.controls.set_play_state(False)
        if self.image_sequence_files:
            self.load_sequence_frame(0)
        else:
            self.media_player.stop()
            if self.compare_mode:
                self.media_player_2.stop()

    def previous_frame(self):
        if self.image_sequence_files:
            if self.current_sequence_index > 0:
                self.load_sequence_frame(self.current_sequence_index - 1)
        else:
            self.media_player.previous_frame()
            if self.compare_mode:
                self.media_player_2.previous_frame()

    def next_frame(self):
        if self.image_sequence_files:
            if self.current_sequence_index < len(self.image_sequence_files) - 1:
                self.load_sequence_frame(self.current_sequence_index + 1)
        else:
            self.media_player.next_frame()
            if self.compare_mode:
                self.media_player_2.next_frame()

    def seek_to_position(self, position):
        if self.image_sequence_files:
            self.load_sequence_frame(int(position))
        else:
            self.media_player.seek_to_position(position)
            if self.compare_mode:
                self.media_player_2.seek_to_position(position)

    def update_frame_counter(self, current_frame, total_frames=None):
        active_player = self.media_player
        if total_frames is None:
            total_frames = active_player.total_frames

        self.timeline.set_marks(self.marks)
        fps_for_timecode = self.media_player_A_fps

        if self.show_timecode and fps_for_timecode > 0 and total_frames > 0:
            total_seconds_val = total_frames / fps_for_timecode
            current_seconds_val = current_frame / fps_for_timecode

            total_minutes = int(total_seconds_val // 60)
            total_seconds_part = int(total_seconds_val % 60)
            total_frames_part = int((total_seconds_val - int(total_seconds_val)) * fps_for_timecode)

            current_minutes = int(current_seconds_val // 60)
            current_seconds = int(current_seconds_val % 60)
            current_frames_rem = int((current_seconds_val - int(current_seconds_val)) * fps_for_timecode)

            self.frame_counter_label.setText(f"Time: {current_minutes:02d}:{current_seconds:02d}.{current_frames_rem:02d} / {total_minutes:02d}:{total_seconds_part:02d}.{total_frames_part:02d}")
            self.timeline.set_timecode_mode(True)
        else:
            self.frame_counter_label.setText(f"Frame: {current_frame + 1} / {total_frames}")
            self.timeline.set_timecode_mode(False)

        self.timeline.set_fps(fps_for_timecode)
        self.timeline.set_duration(total_frames)
        self.timeline.set_position(current_frame)

    def setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Space), self).activated.connect(self.toggle_play)
        QShortcut(QKeySequence(Qt.Key_Left), self).activated.connect(self.previous_frame)
        QShortcut(QKeySequence(Qt.Key_Right), self).activated.connect(self.next_frame)
        QShortcut(QKeySequence(Qt.Key_Home), self).activated.connect(self.go_to_first_frame)
        QShortcut(QKeySequence(Qt.Key_End), self).activated.connect(self.go_to_last_frame)
        QShortcut(QKeySequence(Qt.Key_PageUp), self).activated.connect(self.jump_backward)
        QShortcut(QKeySequence(Qt.Key_PageDown), self).activated.connect(self.jump_forward)
        QShortcut(QKeySequence('Ctrl+T'), self).activated.connect(self.toggle_compare_mode_from_button)
        QShortcut(QKeySequence(Qt.Key_F), self).activated.connect(self.toggle_mark)
        QShortcut(QKeySequence(Qt.Key_BracketLeft), self).activated.connect(self.jump_to_previous_mark)
        QShortcut(QKeySequence(Qt.Key_BracketRight), self).activated.connect(self.jump_to_next_mark)
        QShortcut(QKeySequence('Ctrl+H'), self).activated.connect(self.toggle_playlist_panel)

    def toggle_mark(self):
        current_frame = self.media_player.current_frame_index
        if current_frame in self.marks:
            self.marks.remove(current_frame)
        else:
            self.marks.append(current_frame)
            self.marks.sort()
        self.timeline.set_marks(self.marks)

    def jump_to_previous_mark(self):
        if not self.marks: return
        current_frame = self.media_player.current_frame_index
        prev_marks = [m for m in self.marks if m < current_frame]
        if prev_marks:
            self.seek_to_position(max(prev_marks))

    def jump_to_next_mark(self):
        if not self.marks: return
        current_frame = self.media_player.current_frame_index
        next_marks = [m for m in self.marks if m > current_frame]
        if next_marks:
            self.seek_to_position(min(next_marks))

    def set_time_display_mode(self, show_timecode):
        self.show_timecode = show_timecode
        self.update_frame_counter(self.media_player.current_frame_index)

    def toggle_playlist_panel(self):
        sizes = self.main_splitter.sizes()
        if sizes[0] > 0:
            self.last_playlist_size = sizes[0]
            self.main_splitter.setSizes([0, sum(sizes)])
            self.hide_playlist_action.setText("Show Playlist")
            self.hide_panel_button.setText("Show")
        else:
            total_size = sum(sizes)
            self.main_splitter.setSizes([self.last_playlist_size, total_size - self.last_playlist_size])
            self.hide_playlist_action.setText("Hide Playlist")
            self.hide_panel_button.setText("Hide")

    def go_to_first_frame(self):
        self.seek_to_position(0)

    def go_to_last_frame(self):
        total_frames = len(self.image_sequence_files) if self.image_sequence_files else (self.media_player.total_frames or 1)
        self.seek_to_position(total_frames - 1)

    def jump_backward(self, frames=10):
        current = self.media_player.current_frame_index
        self.seek_to_position(max(0, current - frames))

    def jump_forward(self, frames=10):
        current = self.media_player.current_frame_index
        total = len(self.image_sequence_files) if self.image_sequence_files else self.media_player.total_frames
        self.seek_to_position(min(total - 1, current + frames))

    # ===================================================================
    # --- FUNGSI DRAG AND DROP YANG SUDAH DIPERBAIKI ---
    # ===================================================================
    def dragEnterEvent(self, event: QDragEnterEvent):
        # PERBAIKAN: Jika sumber drag adalah playlist, kita usulkan aksi "Copy".
        # Ini PENTING untuk mencegah item asli dihapus dari playlist setelah di-drop.
        if event.source() == self.playlist_widget:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            return

        # Logika untuk menerima file dari luar (File Explorer)
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        # Cek jika sumber drop adalah dari playlist
        if event.source() == self.playlist_widget:
            item = self.playlist_widget.currentItem()
            if not item:
                return # Tidak ada item yang dipilih/di-drag

            file_path = item.data(Qt.UserRole)
            if not file_path:
                return
            
            # Tentukan target drop (Player A atau Player B) berdasarkan posisi mouse
            drop_pos = event.pos()
            pos_in_container = self.media_container.mapFrom(self, drop_pos)

            # Cek apakah drop terjadi di area Player B (dan sedang dalam compare mode)
            if self.compare_mode and self.media_player_2.geometry().contains(pos_in_container):
                self.media_player_2.load_media(file_path)
                self.reset_playlist_indicators()
                self.update_playlist_item_indicator(self.media_player.get_current_file_path(), "A")
                self.update_playlist_item_indicator(file_path, "B")
            # Jika tidak, anggap drop terjadi di area Player A
            elif self.media_player.geometry().contains(pos_in_container):
                self.media_player.load_media(file_path)
                self.reset_playlist_indicators()
                self.update_playlist_item_indicator(file_path, "A")
                if self.compare_mode:
                    self.update_playlist_item_indicator(self.media_player_2.get_current_file_path(), "B")

            # Terima event dropnya. Karena aksinya adalah Copy, item tidak akan hilang.
            event.accept()
            return

        # Logika jika drop berasal dari luar aplikasi (File Explorer)
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if files:
                self.add_files_to_playlist_from_paths(files)
                self.toggle_compare_mode(False) # Selalu masuk mode single view
                self.load_single_file(files[0]) # Putar file pertama yang di-drop
                event.accept()
        else:
            event.ignore()
    # ===================================================================

    def add_files_to_playlist(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Add Files", "", "Media Files (*.*)")
        if files:
            self.add_files_to_playlist_from_paths(files)

    def add_files_to_playlist_from_paths(self, file_paths):
        for file_path in file_paths:
            is_duplicate = any(self.playlist_widget.item(i).data(Qt.UserRole) == file_path for i in range(self.playlist_widget.count()))
            if os.path.exists(file_path) and not is_duplicate:
                item_info = {'path': file_path, 'name': os.path.basename(file_path)}
                self.playlist_items.append(item_info)
                list_item = QListWidgetItem(item_info['name'])
                list_item.setData(Qt.UserRole, file_path)
                self.playlist_widget.addItem(list_item)

    def clear_playlist(self):
        self.playlist_items.clear()
        self.playlist_widget.clear()
        self.media_player.clear_media()
        self.media_player_2.clear_media()
        self.toggle_compare_mode(False)
        self.status_bar.showMessage("Playlist cleared")

    def load_from_playlist(self, item):
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            self.toggle_compare_mode(False)
            self.load_single_file(file_path)

    def load_single_file(self, file_path):
        self.image_sequence_files = []
        self.marks = []
        success = self.media_player.load_media(file_path)
        if success:
            self.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}")
            self.reset_playlist_indicators()
            self.update_playlist_item_indicator(file_path, "A")
            self.timeline.set_marks(self.marks)
        else:
            self.status_bar.showMessage(f"Failed to load: {os.path.basename(file_path)}")

    def load_compare_files(self, file1, file2):
        self.marks = []
        self.media_player.load_media(file1)
        self.media_player_2.load_media(file2)
        self.status_bar.showMessage(f"Comparing: {os.path.basename(file1)} vs {os.path.basename(file2)}")
        self.reset_playlist_indicators()
        self.update_playlist_item_indicator(file1, "A")
        self.update_playlist_item_indicator(file2, "B")
        self.timeline.set_marks(self.marks)

    def sync_playlist_data(self):
        new_playlist_order = []
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            file_path = item.data(Qt.UserRole)
            found_item = next((p_item for p_item in self.playlist_items if p_item['path'] == file_path), None)
            if found_item:
                new_playlist_order.append(found_item)
        self.playlist_items = new_playlist_order
        print("Playlist order synchronized.")

    def toggle_compare_mode_from_button(self):
        if not self.compare_mode:
            self.toggle_compare_mode(True)
            selected_items = self.playlist_widget.selectedItems()
            if len(selected_items) == 2:
                file1 = selected_items[0].data(Qt.UserRole)
                file2 = selected_items[1].data(Qt.UserRole)
                self.load_compare_files(file1, file2)
            elif len(selected_items) == 1:
                file1 = selected_items[0].data(Qt.UserRole)
                self.media_player.load_media(file1)
                self.media_player_2.clear_media()
                self.reset_playlist_indicators()
                self.update_playlist_item_indicator(file1, "A")
            else:
                self.media_player_2.clear_media()
                self.reset_playlist_indicators()
                current_file_A = self.media_player.get_current_file_path()
                if current_file_A:
                    self.update_playlist_item_indicator(current_file_A, "A")
        else:
            self.toggle_compare_mode(False)

    def toggle_compare_mode_from_menu(self):
        self.toggle_compare_mode(self.compare_action.isChecked())

    def toggle_compare_mode(self, enabled):
        if enabled == self.compare_mode:
            return
        self.compare_mode = enabled
        self.compare_action.setChecked(self.compare_mode)
        self.controls.set_compare_state(self.compare_mode)

        # Set compare mode untuk kedua media player
        self.media_player.set_compare_mode(self.compare_mode)
        self.media_player_2.set_compare_mode(self.compare_mode)

        if self.compare_mode:
            self.media_player_2.show()
            # Force equal sizing immediately
            QTimer.singleShot(10, self.ensure_equal_video_sizes)
            self.status_bar.showMessage("Compare mode enabled.")
        else:
            self.media_player_2.hide()
            self.media_player_2.clear_media()
            # Reset sizing for single player - remove all size constraints completely
            self.media_player.setMinimumWidth(0)
            self.media_player.setMaximumWidth(16777215)
            self.media_player.setMinimumHeight(0)
            self.media_player.setMaximumHeight(16777215)
            
            # Clear any fixed sizing
            self.media_player.setFixedWidth(16777215)
            self.media_player.setFixedHeight(16777215)
            
            # Reset video label size constraints completely
            self.media_player.video_label.setMinimumSize(0, 0)
            self.media_player.video_label.setMaximumSize(16777215, 16777215)
            self.media_player.video_label.setFixedSize(16777215, 16777215)
            
            # Force widget to take full container space
            self.media_player.setSizePolicy(self.media_player.sizePolicy().Expanding, self.media_player.sizePolicy().Expanding)
            
            # Update layout to ensure proper sizing
            self.media_container_layout.invalidate()
            self.media_container.updateGeometry()
            
            # Force re-display with proper sizing
            if self.media_player.current_frame is not None:
                QTimer.singleShot(100, lambda: self.media_player.display_frame(self.media_player.current_frame))
                
            self.reset_playlist_indicators()
            current_file_A = self.media_player.get_current_file_path()
            if current_file_A:
                self.update_playlist_item_indicator(current_file_A, "A")
            self.status_bar.showMessage("Single view mode enabled.")

    def set_compare_mode_for_players(self, enabled):
        """Set mode compare untuk kedua media player."""
        self.media_player.set_compare_mode(enabled)
        self.media_player_2.set_compare_mode(enabled)

    def ensure_equal_video_sizes(self):
        """Pastikan kedua video player memiliki ukuran yang sama dalam mode compare."""
        if self.compare_mode:
            # Force equal width for both players
            container_width = self.media_container.width()
            player_width = (container_width - 10) // 2  # 10 adalah total spacing
            
            # Set fixed widths to ensure consistency
            self.media_player.setFixedWidth(player_width)
            self.media_player_2.setFixedWidth(player_width)
            
            # Set ukuran video label yang sama untuk kedua player
            self.media_player.video_label.setFixedSize(player_width, self.media_container.height() - 20)
            self.media_player_2.video_label.setFixedSize(player_width, self.media_container.height() - 20)
            
            # Update both players to display frames with same scaling
            if self.media_player.current_frame is not None:
                self.media_player.display_frame(self.media_player.current_frame)
            if self.media_player_2.current_frame is not None:
                self.media_player_2.display_frame(self.media_player_2.current_frame)

    def resizeEvent(self, event):
        """Handle window resize and maintain equal video sizes."""
        super().resizeEvent(event)
        if self.compare_mode:
            # Delay to ensure layout is updated
            QTimer.singleShot(50, self.ensure_equal_video_sizes)

    def reset_playlist_indicators(self):
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            text = item.text()
            item.setText(text.replace(" (A)", "").replace(" (B)", ""))

    def update_playlist_item_indicator(self, file_path, indicator):
        if not file_path: return
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            if item.data(Qt.UserRole) == file_path:
                text = item.text().replace(" (A)", "").replace(" (B)", "")
                item.setText(f"{text} ({indicator})")
                break

    def update_fps_display(self, fps, indicator):
        if indicator == 'A':
            self.media_player_A_fps = fps
        elif indicator == 'B':
            self.media_player_B_fps = fps

        if self.compare_mode:
            text_a = f"A: {self.media_player_A_fps:.2f} FPS"
            text_b = f"B: {self.media_player_B_fps:.2f} FPS"
            self.fps_label.setText(f"{text_a} | {text_b}")
        else:
            self.fps_label.setText(f"FPS: {self.media_player_A_fps:.2f}")