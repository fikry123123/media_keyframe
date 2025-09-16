import os
import glob
import cv2
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QMenuBar, QAction,
                            QFileDialog, QHBoxLayout, QStatusBar, QLabel, QSplitter,
                            QListWidget, QListWidgetItem, QPushButton, QShortcut)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QKeySequence, QPixmap
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
            QPushButton:disabled {
                background-color: #404040;
                color: #888888;
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

        self.setAcceptDrops(True)

        self.setup_ui()

    def setup_ui(self):
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QHBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0) 

            self.playlist_widget_container = QWidget()
            playlist_layout = QVBoxLayout(self.playlist_widget_container)
            playlist_header = QLabel("Playlist")
            playlist_header.setStyleSheet("QLabel { color: #ffffff; font-size: 16px; font-weight: bold; padding: 8px; background-color: #444444; border-radius: 4px; margin-bottom: 5px; }")
            playlist_layout.addWidget(playlist_header)
            self.playlist_widget = QListWidget()
            self.playlist_widget.setSelectionMode(QListWidget.ExtendedSelection)
            self.playlist_widget.setDragDropMode(QListWidget.DragOnly)
            self.playlist_widget.setDefaultDropAction(Qt.CopyAction)
            self.playlist_widget.setStyleSheet("""
                QListWidget { background-color: #2b2b2b; color: #ffffff; border: 2px solid #444444; border-radius: 4px; padding: 4px; font-size: 12px; }
                QListWidget::item { padding: 6px; border-bottom: 1px solid #444444; border-radius: 2px; margin: 1px; }
                QListWidget::item:selected { background-color: #0078d4; color: white; }
                QListWidget::item:hover { background-color: #444444; }
            """)
            self.playlist_widget.itemDoubleClicked.connect(self.load_from_playlist)
            playlist_layout.addWidget(self.playlist_widget)

            media_widget = QWidget()
            media_layout = QVBoxLayout(media_widget)
            self.media_container = QWidget()
            self.media_container_layout = QHBoxLayout(self.media_container)
            self.media_container_layout.setContentsMargins(0, 0, 0, 0)
            self.media_container_layout.setSpacing(0)
            self.media_player = MediaPlayer()
            self.media_container_layout.addWidget(self.media_player)
            self.media_player_2 = MediaPlayer()

            media_layout.addWidget(self.media_container, 1)
            self.timeline = TimelineWidget()
            media_layout.addWidget(self.timeline)
            self.controls = MediaControls()
            self.controls.set_compare_state(self.compare_mode)
            media_layout.addWidget(self.controls)
            
            main_layout.addWidget(self.playlist_widget_container)
            main_layout.addWidget(media_widget)

            main_layout.setStretch(0, 1)
            main_layout.setStretch(1, 4)
            
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

        self.open_folder_action = QAction('Open Image Sequence', self)
        self.open_folder_action.setShortcut('Ctrl+Shift+O')
        self.open_folder_action.triggered.connect(self.open_image_sequence)
        file_menu.addAction(self.open_folder_action)

        file_menu.addSeparator()

        clear_playlist_action = QAction('Clear Playlist', self)
        clear_playlist_action.triggered.connect(self.clear_playlist)
        file_menu.addAction(clear_playlist_action)

        view_menu = menubar.addMenu('View')
        self.compare_action = QAction('Compare Mode', self)
        self.compare_action.setCheckable(True)
        self.compare_action.setShortcut('Ctrl+T')
        self.compare_action.triggered.connect(lambda: self.toggle_compare_mode(self.compare_action.isChecked()))
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
            if self.compare_mode:
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
                if self.compare_mode: self.toggle_compare_mode(False)
                self.load_sequence_frame(0)
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
            self.status_bar.showMessage(f"Loaded sequence: {len(self.image_sequence_files)} frames")
            # Nonaktifkan mode compare jika image sequence aktif
            self.compare_action.setEnabled(False)
            self.controls.compare_button.setEnabled(False)

    def toggle_play(self):
        if self.image_sequence_files:
            if not hasattr(self, 'sequence_timer'):
                self.sequence_timer = QTimer()
                self.sequence_timer.timeout.connect(self.next_sequence_frame)
            if self.sequence_timer.isActive():
                self.sequence_timer.stop()
                self.controls.set_play_state(False)
            else:
                # fallback FPS untuk image sequence jika tidak tersedia
                fps = self.media_player_A_fps if self.media_player_A_fps > 0 else 24
                interval = int(1000 / fps) if fps > 0 else 41
                self.sequence_timer.start(interval)
                self.controls.set_play_state(True)
        else:
            is_playing_before_toggle = self.media_player.is_playing
            self.media_player.toggle_play()
            if self.compare_mode:
                self.media_player_2.toggle_play()
            self.controls.set_play_state(not is_playing_before_toggle)

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
        # Jika dipanggil dari media_player saat clear_media -> current_frame bisa -1
        active_player = self.media_player
        if total_frames is None and active_player.has_media():
            total_frames = active_player.total_frames
        elif not active_player.has_media():
             total_frames = 0
             current_frame = -1

        # Jika tidak ada media sama sekali
        if current_frame is None or current_frame < 0 or total_frames <= 0:
            self.frame_counter_label.setText("No Media Loaded")
            # beri timeline nilai aman
            self.timeline.set_timecode_mode(False)
            self.timeline.set_fps(0)
            self.timeline.set_duration(0)
            self.timeline.set_position(0)
            if self.compare_mode:
                self.update_composite_view()
            return

        # Timecode mode (hanya jika fps valid)
        fps_for_timecode = self.media_player_A_fps
        if self.show_timecode and fps_for_timecode > 0 and total_frames > 0:
            total_seconds_val = total_frames / fps_for_timecode
            current_seconds_val = current_frame / fps_for_timecode
            total_minutes, total_seconds_part = divmod(int(total_seconds_val), 60)
            total_frames_part = int((total_seconds_val - int(total_seconds_val)) * fps_for_timecode)
            current_minutes, current_seconds = divmod(int(current_seconds_val), 60)
            current_frames_rem = int((current_seconds_val - int(current_seconds_val)) * fps_for_timecode)
            self.frame_counter_label.setText(f"Time: {current_minutes:02d}:{current_seconds:02d}.{current_frames_rem:02d} / {total_minutes:02d}:{total_seconds_part:02d}.{total_frames_part:02d}")
            self.timeline.set_timecode_mode(True)
        else:
            # tampilkan frame-based counter
            self.frame_counter_label.setText(f"Frame: {current_frame + 1} / {total_frames}")
            self.timeline.set_timecode_mode(False)

        # update timeline data
        self.timeline.set_fps(fps_for_timecode if fps_for_timecode > 0 else 0)
        self.timeline.set_duration(total_frames)
        # pastikan posisi masuk rentang valid
        pos = int(max(0, min(current_frame, total_frames - 1)))
        self.timeline.set_position(pos)
        self.timeline.set_marks(self.marks)

        if self.compare_mode:
            self.update_composite_view()

    def setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Space), self).activated.connect(self.toggle_play)
        QShortcut(QKeySequence(Qt.Key_Left), self).activated.connect(self.previous_frame)
        QShortcut(QKeySequence(Qt.Key_Right), self).activated.connect(self.next_frame)
        QShortcut(QKeySequence(Qt.Key_Home), self).activated.connect(self.go_to_first_frame)
        QShortcut(QKeySequence(Qt.Key_End), self).activated.connect(self.go_to_last_frame)
        QShortcut(QKeySequence(Qt.Key_PageUp), self).activated.connect(self.jump_backward)
        QShortcut(QKeySequence(Qt.Key_PageDown), self).activated.connect(self.jump_forward)
        QShortcut(QKeySequence(Qt.Key_F), self).activated.connect(self.toggle_mark)
        QShortcut(QKeySequence(Qt.Key_BracketLeft), self).activated.connect(self.jump_to_previous_mark)
        QShortcut(QKeySequence(Qt.Key_BracketRight), self).activated.connect(self.jump_to_next_mark)
        # Peningkatan: Navigasi playlist dengan keyboard
        QShortcut(QKeySequence("Ctrl+Up"), self).activated.connect(self.play_previous_playlist_item)
        QShortcut(QKeySequence("Ctrl+Down"), self).activated.connect(self.play_next_playlist_item)

    def play_previous_playlist_item(self):
        if self.playlist_widget.count() == 0: return
        current_row = self.playlist_widget.currentRow()
        next_row = current_row - 1
        if next_row < 0:
            next_row = self.playlist_widget.count() - 1
        item = self.playlist_widget.item(next_row)
        if item:
            self.playlist_widget.setCurrentItem(item)
            self.load_from_playlist(item)
    
    def play_next_playlist_item(self):
        if self.playlist_widget.count() == 0: return
        current_row = self.playlist_widget.currentRow()
        next_row = (current_row + 1) % self.playlist_widget.count()
        item = self.playlist_widget.item(next_row)
        if item:
            self.playlist_widget.setCurrentItem(item)
            self.load_from_playlist(item)

    def toggle_mark(self):
        current_frame = self.media_player.current_frame_index
        if current_frame in self.marks: self.marks.remove(current_frame)
        else:
            self.marks.append(current_frame)
            self.marks.sort()
        self.timeline.set_marks(self.marks)

    def jump_to_previous_mark(self):
        if not self.marks: return
        current_frame = self.media_player.current_frame_index
        prev_marks = [m for m in self.marks if m < current_frame]
        if prev_marks: self.seek_to_position(max(prev_marks))

    def jump_to_next_mark(self):
        if not self.marks: return
        current_frame = self.media_player.current_frame_index
        next_marks = [m for m in self.marks if m > current_frame]
        if next_marks: self.seek_to_position(min(next_marks))

    def set_time_display_mode(self, show_timecode):
        self.show_timecode = show_timecode
        self.update_frame_counter(self.media_player.current_frame_index)

    def toggle_playlist_panel(self):
            if self.playlist_widget_container.isVisible():
                self.playlist_widget_container.hide()
                self.hide_playlist_action.setText("Show Playlist Panel")
            else:
                self.playlist_widget_container.show()
                self.hide_playlist_action.setText("Hide Playlist Panel")

    def go_to_first_frame(self): self.seek_to_position(0)

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

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.source() == self.playlist_widget:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            return
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event: QDropEvent):
        # Logika untuk drop dari playlist internal
        if event.source() == self.playlist_widget:
            item = self.playlist_widget.currentItem()
            if not item:
                event.ignore()
                return
            file_path = item.data(Qt.UserRole)
            if not file_path:
                event.ignore()
                return
            if self.compare_mode:
                if not self.media_player.has_media(): self.load_single_file(file_path)
                else: self.load_media_into_player_b(file_path)
            else: self.load_single_file(file_path)
            event.accept()
            return

        # Logika untuk drop dari luar aplikasi (File Explorer, dll)
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if files:
                self.add_files_to_playlist_from_paths(files)
                file_to_load = files[0]
                if self.compare_mode:
                    if not self.media_player.has_media(): self.load_single_file(file_to_load)
                    else: self.load_media_into_player_b(file_to_load)
                else: self.load_single_file(file_to_load)
                event.acceptProposedAction()
        else: event.ignore()

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
        if self.compare_mode: self.update_composite_view()
        # Aktifkan kembali semua kontrol yang mungkin dinonaktifkan
        self.compare_action.setEnabled(True)
        self.controls.compare_button.setEnabled(True)
        self.open_folder_action.setEnabled(True)
        self.image_sequence_files = [] # Pastikan mode sequence juga direset
        self.status_bar.showMessage("Playlist cleared")

    def load_from_playlist(self, item):
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            if self.compare_mode: self.toggle_compare_mode(False)
            self.load_single_file(file_path)

    def load_single_file(self, file_path):
        self.image_sequence_files = [] # Reset mode sequence
        self.marks = []
        success = self.media_player.load_media(file_path)
        if success:
            self.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}")
            self.reset_playlist_indicators()
            self.update_playlist_item_indicator(file_path, "A")
            self.timeline.set_marks(self.marks)
            # Aktifkan kembali kontrol compare
            self.compare_action.setEnabled(True)
            self.controls.compare_button.setEnabled(True)
        else:
            self.status_bar.showMessage(f"Failed to load: {os.path.basename(file_path)}")
    
    def load_media_into_player_b(self, file_path):
        self.media_player_2.load_media(file_path)
        self.reset_playlist_indicators()
        self.update_playlist_item_indicator(self.media_player.get_current_file_path(), "A")
        self.update_playlist_item_indicator(file_path, "B")

    def load_compare_files(self, file1, file2):
        self.marks = []
        self.media_player.load_media(file1)
        self.media_player_2.load_media(file2)
        self.status_bar.showMessage(f"Comparing: {os.path.basename(file1)} vs {os.path.basename(file2)}")
        self.reset_playlist_indicators()
        self.update_playlist_item_indicator(file1, "A")
        self.update_playlist_item_indicator(file2, "B")
        self.timeline.set_marks(self.marks)
        QTimer.singleShot(50, self.update_composite_view)

    def sync_playlist_data(self):
        new_playlist_order = []
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            file_path = item.data(Qt.UserRole)
            found_item = next((p_item for p_item in self.playlist_items if p_item['path'] == file_path), None)
            if found_item: new_playlist_order.append(found_item)
        self.playlist_items = new_playlist_order

    def toggle_compare_mode_from_button(self):
        is_entering_compare = not self.compare_mode
        self.toggle_compare_mode(is_entering_compare)
        if is_entering_compare:
            selected_items = self.playlist_widget.selectedItems()
            if len(selected_items) == 2:
                file1 = selected_items[0].data(Qt.UserRole)
                file2 = selected_items[1].data(Qt.UserRole)
                self.load_compare_files(file1, file2)
            elif len(selected_items) == 1 and self.media_player.has_media():
                file_b = selected_items[0].data(Qt.UserRole)
                file_a = self.media_player.get_current_file_path()
                if file_a != file_b: self.load_compare_files(file_a, file_b)
            else:
                self.media_player_2.clear_media()
                self.update_composite_view()

    def toggle_compare_mode(self, enabled):
        if enabled == self.compare_mode: return
        self.compare_mode = enabled
        self.compare_action.setChecked(self.compare_mode)
        self.controls.set_compare_state(self.compare_mode)
        if self.compare_mode:
            self.status_bar.showMessage("Compare mode enabled.")
            self.open_folder_action.setEnabled(False) # Nonaktifkan menu image sequence
            self.update_composite_view()
        else:
            self.media_player_2.clear_media()
            self.status_bar.showMessage("Single view mode enabled.")
            self.open_folder_action.setEnabled(True) # Aktifkan kembali menu image sequence
            if self.media_player.current_frame is not None:
                self.media_player.display_frame(self.media_player.current_frame)
            else:
                self.media_player.video_label.setText("Load media file to start...")
            self.reset_playlist_indicators()
            current_file_A = self.media_player.get_current_file_path()
            if current_file_A: self.update_playlist_item_indicator(current_file_A, "A")
    
    def create_placeholder_frame(self, text, width, height):
        placeholder = np.zeros((height, width, 3), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = min(width / 400, height / 300)
        if font_scale < 0.5: font_scale = 0.5
        font_thickness = 1
        color = (204, 204, 204)
        text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2
        cv2.putText(placeholder, text, (text_x, text_y), font, font_scale, color, font_thickness)
        return placeholder

    def update_composite_view(self):
        if not self.compare_mode:
            return

        frame_a = self.media_player.current_frame
        frame_b = self.media_player_2.current_frame

        # placeholder jika dua-duanya None
        if frame_a is None and frame_b is None:
            container_size = self.media_container.size()
            h, w = container_size.height(), container_size.width() // 2
            if h <= 10 or w <= 10:
                self.media_player.video_label.setPixmap(QPixmap())
                self.media_player.video_label.setText("")
                return
            placeholder_a = self.create_placeholder_frame("Load Media for A", w, h)
            placeholder_b = self.create_placeholder_frame("Load Media for B", w, h)
            composite_frame = cv2.hconcat([placeholder_a, placeholder_b])
        else:
            # isi placeholder bila salah satu None
            if frame_a is None:
                ref_h, ref_w = frame_b.shape[:2]
                frame_a = self.create_placeholder_frame("Load Media for A", ref_w, ref_h)
            if frame_b is None:
                ref_h, ref_w = frame_a.shape[:2]
                frame_b = self.create_placeholder_frame("Load Media for B", ref_w, ref_h)

            # resize keduanya ke tinggi terkecil agar sejajar
            h_a, w_a, _ = frame_a.shape
            h_b, w_b, _ = frame_b.shape
            target_h = min(h_a, h_b)
            if target_h <= 0:
                return

            new_w_a = int(w_a * (target_h / h_a))
            new_w_b = int(w_b * (target_h / h_b))
            frame_a_resized = cv2.resize(frame_a, (new_w_a, target_h), interpolation=cv2.INTER_AREA)
            frame_b_resized = cv2.resize(frame_b, (new_w_b, target_h), interpolation=cv2.INTER_AREA)

            composite_frame = cv2.hconcat([frame_a_resized, frame_b_resized])

        # --- PERBAIKAN: scale composite agar fit container Qt ---
        # scale composite agar fit container Qt dengan aspect ratio terjaga
        container_size = self.media_container.size()
        max_w, max_h = container_size.width(), container_size.height()
        if composite_frame.shape[1] > max_w or composite_frame.shape[0] > max_h:
            scale = min(max_w / composite_frame.shape[1],
                        max_h / composite_frame.shape[0])
            new_w = int(composite_frame.shape[1] * scale)
            new_h = int(composite_frame.shape[0] * scale)
            composite_frame = cv2.resize(
                composite_frame, (new_w, new_h), interpolation=cv2.INTER_AREA
            )


        self.media_player.display_frame(composite_frame)

    def reset_playlist_indicators(self):
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            text = item.text()
            cleaned_text = text
            if cleaned_text.endswith(" (A)"): cleaned_text = cleaned_text[:-4]
            elif cleaned_text.endswith(" (B)"): cleaned_text = cleaned_text[:-4]
            item.setText(cleaned_text)

    def update_playlist_item_indicator(self, file_path, indicator):
        if not file_path: return
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            if item.data(Qt.UserRole) == file_path:
                text = item.text()
                if text.endswith(" (A)"): text = text[:-4]
                elif text.endswith(" (B)"): text = text[:-4]
                item.setText(f"{text} ({indicator})")
                break

    def update_fps_display(self, fps, indicator):
        if indicator == 'A': self.media_player_A_fps = fps
        elif indicator == 'B': self.media_player_B_fps = fps
        if self.compare_mode:
            text_a = f"A: {self.media_player_A_fps:.2f} FPS"
            text_b = f"B: {self.media_player_B_fps:.2f} FPS"
            self.fps_label.setText(f"{text_a} | {text_b}")
        else: self.fps_label.setText(f"FPS: {self.media_player_A_fps:.2f}")
