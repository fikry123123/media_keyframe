import os
import sys
import glob
import cv2
import numpy as np
from enum import Enum, auto
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QMenuBar, QAction, QMenu,
                            QFileDialog, QHBoxLayout, QStatusBar, QLabel, QSplitter,
                            QTreeWidget, QTreeWidgetItem, QPushButton, QShortcut, 
                            QTreeWidgetItemIterator, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QKeySequence, QPixmap, QDrag
from media_player import MediaPlayer
from media_controls import MediaControls
from timeline_widget import TimelineWidget


class ProjectTreeWidget(QTreeWidget):
    filesDroppedOnTarget = pyqtSignal(list, QTreeWidgetItem)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_item = None
        self.timeline_item = None

    def startDrag(self, supportedActions):
        drag = QDrag(self)
        mime_data = QMimeData()
        
        paths = []
        selected_items = self.selectedItems()
        
        is_from_source = all(item.parent() == self.source_item for item in selected_items)

        if is_from_source:
            for item in selected_items:
                paths.append(item.data(0, Qt.UserRole))
            if not paths:
                return
            mime_data.setData("application/x-playlist-paths", bytearray(",".join(paths), 'utf-8'))
            drag.setMimeData(mime_data)
            drag.exec_(supportedActions)
        else:
            super().startDrag(supportedActions)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-playlist-paths"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        target_item = self.itemAt(event.pos())
        is_valid_target = False

        def is_in_timeline(item):
            parent = item
            while parent:
                if parent == self.timeline_item:
                    return True
                parent = parent.parent()
            return False
        
        if event.mimeData().hasUrls():
            is_valid_target = True
        elif target_item and is_in_timeline(target_item):
             is_valid_target = True

        if event.source() == self and self.selectedItems():
            dragged_item = self.selectedItems()[0]
            if target_item:
                parent = target_item
                while parent:
                    if parent == dragged_item:
                        is_valid_target = False
                        break
                    parent = parent.parent()
        
        if is_valid_target:
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if files:
                target = self.itemAt(event.pos())
                self.filesDroppedOnTarget.emit(files, target)
            event.accept()
            return

        if event.mimeData().hasFormat("application/x-playlist-paths"):
            target_item = self.itemAt(event.pos())
            if not target_item:
                event.ignore()
                return

            if target_item.data(0, Qt.UserRole) is not None:
                target_folder = target_item.parent()
            else:
                target_folder = target_item
            
            paths_data = event.mimeData().data("application/x-playlist-paths")
            paths = str(paths_data, 'utf-8').split(',')
            
            for file_path in paths:
                is_duplicate = False
                for i in range(target_folder.childCount()):
                    if target_folder.child(i).data(0, Qt.UserRole) == file_path:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    new_item = QTreeWidgetItem(target_folder, [os.path.basename(file_path)])
                    new_item.setData(0, Qt.UserRole, file_path)
                    new_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable)
            event.accept()
        else:
            super().dropEvent(event)


class PlaybackMode(Enum):
    LOOP = auto()
    PLAY_NEXT = auto()
    PLAY_ONCE = auto()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Studio Media Player")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; color: #ffffff; }
            QMenuBar { background-color: #333333; color: #ffffff; border-bottom: 1px solid #555555; }
            QMenuBar::item { background-color: transparent; padding: 4px 8px; }
            QMenuBar::item:selected { background-color: #555555; }
            QMenu { background-color: #333333; color: #ffffff; border: 1px solid #555555; }
            QMenu::item:selected { background-color: #555555; }
            QStatusBar { background-color: #333333; color: #ffffff; border-top: 1px solid #555555; }
            QPushButton { background-color: #5d5d5d; border: 1px solid #777777; padding: 5px; border-radius: 4px; color: #ffffff; }
            QPushButton:hover { background-color: #6a6a6a; }
            QPushButton:pressed { background-color: #4a4a4a; }
            QPushButton:disabled { background-color: #404040; color: #888888; }
            QSplitter::handle { background-color: #444444; }
            QSplitter::handle:horizontal { width: 2px; }
            QTreeWidget { background-color: #2b2b2b; color: #ffffff; border: 2px solid #444444; border-radius: 4px; padding: 4px; font-size: 12px; }
            QTreeWidget::item { padding: 6px; border-radius: 2px; margin: 1px; }
            QTreeWidget::item:selected { background-color: #0078d4; color: white; }
            QTreeWidget::item:hover { background-color: #444444; }
            QHeaderView::section { background-color: #333333; color: #ffffff; padding: 4px; border: 1px solid #555555; }
            QTreeWidget::branch:has-siblings:!adjoins-item { border-image: url(none.png); }
            QTreeWidget::branch:has-siblings:adjoins-item { border-image: url(none.png); }
            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item { border-image: url(none.png); }
        """)
        self.image_sequence_files, self.marks, self.splitter_sizes = [], [], []
        self.current_sequence_index = 0
        self.compare_mode = False
        self.playback_mode = PlaybackMode.LOOP
        self.media_player_A_fps, self.media_player_B_fps = 0.0, 0.0
        self.show_timecode = False
        self.is_compare_playing = False
        self.compare_timer = QTimer(self)
        self.compare_timer.timeout.connect(self.update_compare_frames)
        self.setAcceptDrops(False)
        self.splitter_sizes = []
        self.setup_ui()
        self.set_playback_mode(PlaybackMode.LOOP)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.playlist_widget_container = QWidget()
        playlist_layout = QVBoxLayout(self.playlist_widget_container)
        playlist_layout.setContentsMargins(0, 0, 0, 0)
        playlist_layout.setSpacing(0)
        self.playlist_widget = ProjectTreeWidget(self)
        self.playlist_widget.setHeaderLabels(["Project"])
        self.playlist_widget.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.playlist_widget.setDragEnabled(True)
        self.playlist_widget.setAcceptDrops(True)
        self.playlist_widget.setDropIndicatorShown(True)
        self.playlist_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.playlist_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.playlist_widget.setEditTriggers(QAbstractItemView.EditKeyPressed)
        self.playlist_widget.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.source_item = QTreeWidgetItem(self.playlist_widget, ["Source"])
        self.timeline_item = QTreeWidgetItem(self.playlist_widget, ["Timeline"])
        root_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        self.source_item.setFlags(root_flags)
        self.timeline_item.setFlags(root_flags | Qt.ItemIsDropEnabled)
        self.playlist_widget.source_item = self.source_item
        self.playlist_widget.timeline_item = self.timeline_item
        self.source_item.setExpanded(True)
        self.timeline_item.setExpanded(True)
        self.playlist_widget.itemDoubleClicked.connect(self.load_from_tree)
        playlist_layout.addWidget(self.playlist_widget)
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)
        self.media_container = QWidget()
        self.media_container_layout = QHBoxLayout(self.media_container)
        self.media_container_layout.setContentsMargins(0,0,0,0)
        self.media_player = MediaPlayer()
        self.media_container_layout.addWidget(self.media_player)
        self.media_player_2 = MediaPlayer()
        media_layout.addWidget(self.media_container, 1)
        self.timeline = TimelineWidget()
        media_layout.addWidget(self.timeline)
        self.controls = MediaControls()
        self.controls.set_compare_state(self.compare_mode)
        media_layout.addWidget(self.controls)
        self.splitter.addWidget(self.playlist_widget_container)
        self.splitter.addWidget(media_widget)
        self.splitter.setSizes([280, 920])
        main_layout.addWidget(self.splitter)
        self.connect_signals()
        self.create_menu_bar()
        self.create_status_bar()
        self.setup_shortcuts()

    def connect_signals(self):
        self.controls.play_button.clicked.connect(self.toggle_play)
        self.controls.prev_button.clicked.connect(self.previous_frame)
        self.controls.next_button.clicked.connect(self.next_frame)
        self.controls.compare_toggled.connect(self.toggle_compare_mode_from_button)
        self.controls.first_frame_button.clicked.connect(self.go_to_first_frame)
        self.controls.last_frame_button.clicked.connect(self.go_to_last_frame)
        self.controls.playback_mode_button.clicked.connect(self.cycle_playback_mode)
        self.timeline.position_changed.connect(self.seek_to_position)
        self.timeline.display_mode_changed.connect(self.set_time_display_mode)
        self.media_player.frameIndexChanged.connect(self.update_frame_counter)
        self.media_player.playStateChanged.connect(self.controls.set_play_state)
        self.media_player.playbackFinished.connect(self.handle_playback_finished)
        self.media_player_2.frameIndexChanged.connect(self.update_frame_counter_B)
        self.media_player.fpsChanged.connect(lambda fps: self.update_fps_display(fps, 'A'))
        self.media_player_2.fpsChanged.connect(lambda fps: self.update_fps_display(fps, 'B'))
        self.media_player.fileDropped.connect(self.handle_file_drop_on_player)
        self.playlist_widget.filesDroppedOnTarget.connect(self.handle_files_dropped)

    def handle_files_dropped(self, file_paths, target_item):
        self.add_files_to_source(file_paths)
        is_in_timeline = False
        if target_item:
            parent = target_item
            while parent:
                if parent == self.timeline_item:
                    is_in_timeline = True
                    break
                parent = parent.parent()
        if is_in_timeline:
            drop_folder = target_item
            if target_item.data(0, Qt.UserRole) is not None:
                drop_folder = target_item.parent()
            for file_path in file_paths:
                is_duplicate = False
                for i in range(drop_folder.childCount()):
                    if drop_folder.child(i).data(0, Qt.UserRole) == file_path:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    new_item = QTreeWidgetItem(drop_folder, [os.path.basename(file_path)])
                    new_item.setData(0, Qt.UserRole, file_path)
                    new_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable)

    def show_tree_context_menu(self, pos):
        item = self.playlist_widget.itemAt(pos)
        if not item: return
        context_menu = QMenu(self)
        is_in_timeline = False
        parent = item
        while parent:
            if parent == self.timeline_item:
                is_in_timeline = True
                break
            parent = parent.parent()
        if is_in_timeline and (item.data(0, Qt.UserRole) is None):
            new_folder_action = context_menu.addAction("New Folder")
            parent_for_new_folder = item if item.data(0, Qt.UserRole) is None else item.parent()
            new_folder_action.triggered.connect(lambda: self.create_new_folder(parent_for_new_folder))
        if item.parent():
            if context_menu.actions(): context_menu.addSeparator()
            rename_action = context_menu.addAction("Rename")
            rename_action.triggered.connect(lambda: self.playlist_widget.editItem(item, 0))
            delete_action = context_menu.addAction("Delete")
            delete_action.triggered.connect(self.delete_selected_items_handler)
        if context_menu.actions():
            context_menu.exec_(self.playlist_widget.mapToGlobal(pos))
            
    def create_new_folder(self, parent_item):
        base_name, name, count = "New Folder", "New Folder", 1
        existing = {parent_item.child(i).text(0) for i in range(parent_item.childCount())}
        while name in existing:
            count += 1
            name = f"{base_name} ({count})"
        new_folder = QTreeWidgetItem(parent_item, [name])
        new_folder.setFlags(new_folder.flags() | Qt.ItemIsEditable | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled)
        self.playlist_widget.editItem(new_folder, 0)
        
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
        clear_action = QAction('Clear Project', self)
        clear_action.triggered.connect(self.clear_project_tree)
        file_menu.addAction(clear_action)
        view_menu = menubar.addMenu('View')
        self.compare_action = QAction('Compare Mode', self)
        self.compare_action.setCheckable(True)
        self.compare_action.setShortcut('Ctrl+T')
        self.compare_action.triggered.connect(lambda: self.toggle_compare_mode(self.compare_action.isChecked()))
        view_menu.addAction(self.compare_action)
        self.hide_playlist_action = QAction("Hide Project Panel", self)
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
        
    def handle_file_drop_on_player(self, file_path, target_view):
        self.add_files_to_source([file_path])
        if not self.compare_mode:
            self.load_single_file(file_path)
        else:
            if target_view == 'A':
                self.load_compare_files(file_path, self.media_player_2.get_current_file_path())
            else:
                self.load_compare_files(self.media_player.get_current_file_path(), file_path)
                
    def delete_selected_items_handler(self):
        selected_items = self.playlist_widget.selectedItems()
        if not selected_items: return
        for item in list(selected_items):
            if item.parent():
                item.parent().removeChild(item)
    
    def set_playback_mode(self, mode):
        self.playback_mode = mode
        if mode == PlaybackMode.LOOP:
            self.controls.set_playback_mode_state("🔁", "Playback Mode: Loop")
        elif mode == PlaybackMode.PLAY_NEXT:
            self.controls.set_playback_mode_state("⤵️", "Playback Mode: Play Next (Timeline only)")
        elif mode == PlaybackMode.PLAY_ONCE:
            self.controls.set_playback_mode_state("➡️|", "Playback Mode: Play Once")

    def cycle_playback_mode(self):
        if self.playback_mode == PlaybackMode.LOOP:
            self.set_playback_mode(PlaybackMode.PLAY_NEXT)
        elif self.playback_mode == PlaybackMode.PLAY_NEXT:
            self.set_playback_mode(PlaybackMode.PLAY_ONCE)
        else:
            self.set_playback_mode(PlaybackMode.LOOP)
            
    def handle_playback_finished(self):
        if self.is_compare_playing:
            self.is_compare_playing = False
            self.controls.set_play_state(False)
            return
        if self.playback_mode == PlaybackMode.LOOP:
            self.seek_to_position(0)
            if not self.compare_mode: self.media_player.toggle_play()
        elif self.playback_mode == PlaybackMode.PLAY_NEXT:
            current_path = self.media_player.get_current_file_path()
            item = self.find_item_by_path_recursive(current_path, self.timeline_item)
            if item: self.play_next_timeline_item()
            
    def open_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Media File", "", "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.png);;All Files (*)")
        if file_paths:
            self.handle_files_dropped(file_paths, self.source_item)
            
    def open_image_sequence(self, file_paths):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", "")
        if folder_path: pass
        
    def add_files_to_source(self, file_paths):
        for path in file_paths:
            if os.path.exists(path) and not self.find_item_by_path_recursive(path, self.source_item):
                item = QTreeWidgetItem(self.source_item, [os.path.basename(path)])
                item.setData(0, Qt.UserRole, path)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable)
                
    def clear_project_tree(self):
        self.playlist_widget.clear()
        self.source_item = QTreeWidgetItem(self.playlist_widget, ["Source"])
        self.timeline_item = QTreeWidgetItem(self.playlist_widget, ["Timeline"])
        root_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        self.source_item.setFlags(root_flags)
        self.timeline_item.setFlags(root_flags | Qt.ItemIsDropEnabled)
        self.playlist_widget.source_item = self.source_item
        self.playlist_widget.timeline_item = self.timeline_item
        self.source_item.setExpanded(True)
        self.timeline_item.setExpanded(True)
        self.media_player.clear_media()
        self.media_player_2.clear_media()
        if self.compare_mode: self.update_composite_view()
        self.status_bar.showMessage("Project cleared")
        self.update_playlist_item_indicator()
        
    def toggle_play(self):
            if self.compare_mode:
                if self.is_compare_playing:
                    self.compare_timer.stop()
                    self.is_compare_playing = False
                else:
                    is_a_fin = self.media_player.total_frames > 0 and self.media_player.current_frame_index >= self.media_player.total_frames - 1
                    is_b_fin = self.media_player_2.total_frames > 0 and self.media_player_2.current_frame_index >= self.media_player_2.total_frames - 1
                    if is_a_fin and is_b_fin:
                        self.media_player.seek_to_position(0)
                        self.media_player_2.seek_to_position(0)
                        # Reset penanda selesai untuk kedua player
                        self.media_player.has_finished = False
                        self.media_player_2.has_finished = False
                    fps_a = self.media_player.fps if self.media_player.fps > 0 else 30
                    fps_b = self.media_player_2.fps if self.media_player_2.fps > 0 else 30
                    self.compare_timer.start(int(1000 / min(fps_a, fps_b)))
                    self.is_compare_playing = True
                self.controls.set_play_state(self.is_compare_playing)
            else:
                # --- PERUBAHAN DI SINI ---
                # Logika kompleks dihapus, sekarang cukup panggil toggle_play dari media_player
                self.media_player.toggle_play()

            
    def update_compare_frames(self):
        self.media_player.next_frame()
        self.media_player_2.next_frame()
        self.update_composite_view()
        at_end_a = self.media_player.current_frame_index >= self.media_player.total_frames - 1
        at_end_b = self.media_player_2.current_frame_index >= self.media_player_2.total_frames - 1
        if (at_end_a and self.media_player.total_frames > 0) or (at_end_b and self.media_player_2.total_frames > 0):
            self.compare_timer.stop()
            self.handle_playback_finished()
            
    def previous_frame(self):
        if self.is_compare_playing: return
        self.media_player.previous_frame()
        if self.compare_mode:
            self.media_player_2.previous_frame()
            self.update_composite_view()
            
    def next_frame(self):
        if self.is_compare_playing: return
        self.media_player.next_frame()
        if self.compare_mode:
            self.media_player_2.next_frame()
            self.update_composite_view()
            
    def seek_to_position(self, position):
        self.media_player.seek_to_position(position)
        if self.compare_mode:
            self.media_player_2.seek_to_position(position)
            self.update_composite_view()
            
    def update_frame_counter(self, current_frame, total_frames):
        if self.compare_mode: return
        if total_frames <= 0:
            self.frame_counter_label.setText("No Media")
            self.timeline.set_duration(0)
            return
        self.frame_counter_label.setText(f"Frame: {current_frame + 1} / {total_frames}")
        self.timeline.set_duration(total_frames)
        self.timeline.set_position(current_frame)
        
    def update_frame_counter_B(self, cf, tf): pass
    
    def setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Space), self).activated.connect(self.toggle_play)
        QShortcut(QKeySequence(Qt.Key_Left), self).activated.connect(self.previous_frame)
        QShortcut(QKeySequence(Qt.Key_Right), self).activated.connect(self.next_frame)
        QShortcut(QKeySequence(Qt.Key_Home), self).activated.connect(self.go_to_first_frame)
        QShortcut(QKeySequence(Qt.Key_End), self).activated.connect(self.go_to_last_frame)
        QShortcut(QKeySequence("Ctrl+Up"), self).activated.connect(self.play_previous_timeline_item)
        QShortcut(QKeySequence("Ctrl+Down"), self).activated.connect(self.play_next_timeline_item)
        
    def find_item_by_path_recursive(self, path, root_item):
        if not path or not root_item: return None
        iterator = QTreeWidgetItemIterator(root_item)
        while iterator.value():
            item = iterator.value()
            if item.data(0, Qt.UserRole) == path:
                return item
            iterator += 1
        return None
        
    def play_next_timeline_item(self):
        current_path = self.media_player.get_current_file_path()
        current_item = self.find_item_by_path_recursive(current_path, self.timeline_item)
        if not current_item or not current_item.parent(): return
        parent = current_item.parent()
        current_index = parent.indexOfChild(current_item)
        next_item = None
        for i in range(current_index + 1, parent.childCount()):
            potential_next = parent.child(i)
            if potential_next.data(0, Qt.UserRole):
                next_item = potential_next
                break
        
        if next_item:
            self.playlist_widget.setCurrentItem(next_item)
            # --- PERBAIKAN BUG UTAMA ADA DI SINI ---
            # Panggil load_single_file secara langsung untuk menghindari reset mode playback
            next_file_path = next_item.data(0, Qt.UserRole)
            self.load_single_file(next_file_path)
            
            if self.playback_mode == PlaybackMode.PLAY_NEXT:
                QTimer.singleShot(100, self.media_player.toggle_play)
        else:
            self.set_playback_mode(PlaybackMode.PLAY_ONCE)
                
    def play_previous_timeline_item(self):
        current_path = self.media_player.get_current_file_path()
        current_item = self.find_item_by_path_recursive(current_path, self.timeline_item)
        if not current_item or not current_item.parent(): return
        parent = current_item.parent()
        current_index = parent.indexOfChild(current_item)
        prev_item = None
        for i in range(current_index - 1, -1, -1):
            potential_prev = parent.child(i)
            if potential_prev.data(0, Qt.UserRole):
                prev_item = potential_prev
                break
        if not prev_item:
            for i in range(parent.childCount() - 1, current_index, -1):
                potential_prev = parent.child(i)
                if potential_prev.data(0, Qt.UserRole):
                    prev_item = potential_prev
                    break
        if prev_item:
            self.playlist_widget.setCurrentItem(prev_item)
            self.load_from_tree(prev_item)
            
    def load_from_tree(self, item, column=0):
        file_path = item.data(0, Qt.UserRole)
        if file_path:
            self.set_playback_mode(PlaybackMode.PLAY_ONCE)
            if self.compare_mode: self.toggle_compare_mode(False)
            self.load_single_file(file_path)
        else:
            is_timeline_item = False
            parent = item
            while parent:
                if parent == self.timeline_item:
                    is_timeline_item = True
                    break
                parent = parent.parent()
            if is_timeline_item:
                first_playable_item = None
                for i in range(item.childCount()):
                    child = item.child(i)
                    if child.data(0, Qt.UserRole):
                        first_playable_item = child
                        break
                if first_playable_item:
                    path = first_playable_item.data(0, Qt.UserRole)
                    if self.compare_mode: self.toggle_compare_mode(False)
                    self.load_single_file(path)
                    self.set_playback_mode(PlaybackMode.PLAY_NEXT)

    def load_single_file(self, file_path):
        if self.compare_timer.isActive():
            self.compare_timer.stop()
            self.is_compare_playing = False
        success = self.media_player.load_media(file_path)
        if success: self.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}")
        else: self.status_bar.showMessage(f"Failed to load file")
        self.update_playlist_item_indicator()
            
    def load_compare_files(self, file1, file2):
        self.media_player.load_media(file1)
        self.media_player_2.load_media(file2)
        f1 = os.path.basename(file1) if file1 else "Empty"
        f2 = os.path.basename(file2) if file2 else "Empty"
        self.status_bar.showMessage(f"Comparing: {f1} vs {f2}")
        QTimer.singleShot(50, self.update_composite_view)
        self.update_playlist_item_indicator()
        
    def toggle_compare_mode(self, enabled):
        if enabled == self.compare_mode: return
        self.compare_mode = enabled
        self.controls.set_compare_state(self.compare_mode)
        if self.compare_mode:
            self.update_composite_view()
        else:
            if self.compare_timer.isActive():
                self.compare_timer.stop()
                self.is_compare_playing = False
            self.media_player_2.clear_media()
            self.media_player.display_frame(self.media_player.current_frame)
        self.update_playlist_item_indicator()
            
    def update_composite_view(self):
        frame_a = self.media_player.current_frame
        frame_b = self.media_player_2.current_frame
        total_f = self.media_player.total_frames if self.media_player.has_media() else self.media_player_2.total_frames
        current_f = self.media_player.current_frame_index if self.media_player.has_media() else self.media_player_2.current_frame_index
        self.timeline.set_duration(total_f)
        self.timeline.set_position(current_f)
        self.frame_counter_label.setText(f"Frame: {current_f + 1} / {total_f}")
        h_a, w_a = (frame_a.shape[0], frame_a.shape[1]) if frame_a is not None else (480, 640)
        h_b, w_b = (frame_b.shape[0], frame_b.shape[1]) if frame_b is not None else (480, 640)
        if frame_a is None: frame_a = self.create_placeholder_frame("View A", w_a, h_a)
        if frame_b is None: frame_b = self.create_placeholder_frame("View B", w_b, h_b)
        target_h = min(frame_a.shape[0], frame_b.shape[0])
        if target_h <= 0: return
        new_w_a = int(frame_a.shape[1] * (target_h / frame_a.shape[0])) if frame_a.shape[0] > 0 else 0
        new_w_b = int(frame_b.shape[1] * (target_h / frame_b.shape[0])) if frame_b.shape[0] > 0 else 0
        frame_a_res = cv2.resize(frame_a, (new_w_a, target_h), interpolation=cv2.INTER_AREA) if new_w_a > 0 else np.zeros((target_h, 1, 3), dtype=np.uint8)
        frame_b_res = cv2.resize(frame_b, (new_w_b, target_h), interpolation=cv2.INTER_AREA) if new_w_b > 0 else np.zeros((target_h, 1, 3), dtype=np.uint8)
        composite = cv2.hconcat([frame_a_res, frame_b_res])
        self.media_player.display_frame(composite)
        
    def update_playlist_item_indicator(self):
        path_a = self.media_player.get_current_file_path()
        path_b = self.media_player_2.get_current_file_path() if self.compare_mode else None
        iterator = QTreeWidgetItemIterator(self.playlist_widget)
        while iterator.value():
            item = iterator.value()
            item_path = item.data(0, Qt.UserRole)
            if item_path:
                base_name = item.text(0)
                if base_name.endswith(" (A/B)") or base_name.endswith(" (A)") or base_name.endswith(" (B)"):
                    base_name = base_name[:-5].strip() if base_name.endswith(" (A/B)") else base_name[:-4].strip()
                indicator = ""
                is_a = (item_path == path_a)
                is_b = (self.compare_mode and item_path == path_b)
                if is_a and is_b: indicator = " (A/B)"
                elif is_a: indicator = " (A)"
                elif is_b: indicator = " (B)"
                item.setText(0, base_name + indicator)
            iterator += 1
            
    def update_fps_display(self, fps, indicator):
        if indicator == 'A': self.media_player_A_fps = fps
        elif indicator == 'B': self.media_player_B_fps = fps
        if not self.compare_mode and indicator == 'A':
            self.timeline.set_fps(fps)
            self.fps_label.setText(f"FPS: {self.media_player_A_fps:.2f}")
        elif self.compare_mode:
            if indicator == 'A': self.timeline.set_fps(fps)
            text_a = f"A: {self.media_player_A_fps:.2f} FPS"
            text_b = f"B: {self.media_player_B_fps:.2f} FPS"
            self.fps_label.setText(f"{text_a} | {text_b}")
            
    def go_to_first_frame(self): self.seek_to_position(0)
    
    def go_to_last_frame(self):
        total = self.media_player.total_frames
        if total > 0: self.seek_to_position(total - 1)
        
    def create_placeholder_frame(self, text, width, height):
        placeholder = np.zeros((height, width, 3), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = min(width / 400, height / 300, 1.0)
        thickness = 1 if scale < 0.8 else 2
        (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
        text_x = (width - text_width) // 2
        text_y = (height + text_height) // 2
        cv2.putText(placeholder, text, (text_x, text_y), font, scale, (200, 200, 200), thickness)
        return placeholder
        
    def toggle_compare_mode_from_button(self):
        self.toggle_compare_mode(not self.compare_mode)
        if self.compare_mode:
            selected_items = self.playlist_widget.selectedItems()
            files = [item.data(0, Qt.UserRole) for item in selected_items if item.data(0, Qt.UserRole)]
            if len(files) >= 2: self.load_compare_files(files[0], files[1])
            elif len(files) == 1 and self.media_player.has_media(): self.load_compare_files(self.media_player.get_current_file_path(), files[0])
            elif not self.media_player.has_media() and len(files) == 1: self.load_compare_files(files[0], None)
                
    def set_time_display_mode(self, show_timecode):
        self.show_timecode = show_timecode
        self.timeline.set_timecode_mode(show_timecode)
        
    def toggle_playlist_panel(self):
        if self.playlist_widget_container.isVisible():
            self.splitter_sizes = self.splitter.sizes()
            self.playlist_widget_container.setVisible(False)
        else:
            self.playlist_widget_container.setVisible(True)
            if self.splitter_sizes:
                self.splitter.setSizes(self.splitter_sizes)