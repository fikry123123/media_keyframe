#!/usr/bin/env python3
"""
Studio Media Player - Image Sequence Viewer
A PyQt5-based media player optimized for viewing image sequences and video files.
"""

import sys
import os
import glob
import json
import cv2
import numpy as np
import re 
from enum import Enum, auto
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QMenuBar, QAction, QMenu,
                            QFileDialog, QHBoxLayout, QStatusBar, QLabel, QSplitter,
                            QTreeWidget, QTreeWidgetItem, QPushButton, QShortcut,
                            QTreeWidgetItemIterator, QAbstractItemView, QMessageBox,
                            QColorDialog, QActionGroup) 
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QKeySequence, QPixmap, QDrag, QColor
from media_player import MediaPlayer
from media_controls import MediaControls
from timeline_widget import TimelineWidget
from drawing_toolbar import DrawingToolbar 
from sequence_capture import create_media_capture

# ... (Class ProjectTreeWidget tidak berubah, saya sembunyikan untuk keringkasan) ...
class ProjectTreeWidget(QTreeWidget):
    filesDroppedOnTarget = pyqtSignal(list, object)
    treeChanged = pyqtSignal()
    timelineOrderChanged = pyqtSignal() # <-- SINYAL BARU

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_item = None
        self.timeline_item = None
        self.custom_mime_type = "application/x-kenae-playlist-items"

    def startDrag(self, supportedActions):
        drag = QDrag(self)
        mime_data = QMimeData()
        
        selected_items = self.selectedItems()
        if not selected_items:
            return

        # --- Cek apakah ada path file yang valid untuk di-drag ---
        paths = []
        for item in selected_items:
            path = item.data(0, Qt.UserRole)
            if path:
                paths.append(path)
        
        # Jika tidak ada path (misal folder), biarkan super() menangani drag internal
        if not paths:
            super().startDrag(supportedActions)
            return

        # --- KITA DRAG FILE, SELALU TAMBAHKAN PATH UNTUK PLAYER ---
        mime_data.setData("application/x-playlist-paths", bytearray(",".join(paths), 'utf-8'))

        # 2. Cek apakah dari Source untuk data rename kustom
        is_from_source = all(item.parent() == self.source_item for item in selected_items)
        
        if is_from_source:
            # --- DARI SOURCE: Tambahkan data RENAME ---
            items_data = [] 
            for item in selected_items:
                path = item.data(0, Qt.UserRole) # Path sudah ada
                display_name = item.text(0)
                if path:
                    items_data.append((path, display_name))
            
            try:
                serialized_data = json.dumps(items_data)
                mime_data.setData(self.custom_mime_type, bytearray(serialized_data, 'utf-8'))
            except Exception as e:
                print(f"Error serializing drag data: {e}")
            
            drag.setMimeData(mime_data)
            # DARI SOURCE SELALU COPY
            drag.exec_(Qt.CopyAction)
        
        else:
            # --- DARI TIMELINE: Hanya perlu data path (sudah di-set) ---
            drag.setMimeData(mime_data)
            # DARI TIMELINE BISA MOVE (default) ATAU COPY (Ctrl)
            drag.exec_(supportedActions)

    def dragEnterEvent(self, event: QDragEnterEvent):
        # --- PERBAIKAN: Tambahkan pengecekan MIME kustom ---
        if (event.mimeData().hasUrls() or 
            event.mimeData().hasFormat("application/x-playlist-paths") or
            event.mimeData().hasFormat(self.custom_mime_type)):
        # --- AKHIR PERBAIKAN ---
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
        
        if not target_item:
             event.ignore()
             return

        if event.mimeData().hasUrls():
            is_valid_target = True # Izinkan drop file ke mana saja
        elif is_in_timeline(target_item):
             is_valid_target = True

        # Mencegah drop folder ke dalam dirinya sendiri (untuk InternalMove)
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
        source_changed = False
        timeline_reordered = False # <-- Flag baru (sudah ada)

        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if files:
                target = self.itemAt(event.pos())
                self.filesDroppedOnTarget.emit(files, target)
                source_changed = True
            event.accept()

        elif event.mimeData().hasFormat(self.custom_mime_type):
            # (Blok ini untuk 'rename', sudah benar, tidak diubah)
            target_item = self.itemAt(event.pos())
            if not target_item:
                event.ignore(); return

            try:
                serialized_data = bytes(event.mimeData().data(self.custom_mime_type)).decode('utf-8')
                items_to_add = json.loads(serialized_data)
            except Exception as e:
                print(f"Error parsing custom mime data: {e}"); event.ignore(); return

            drop_indicator = self.dropIndicatorPosition()
            if drop_indicator == QAbstractItemView.AboveItem:
                parent_item = target_item.parent()
                insert_index = parent_item.indexOfChild(target_item)
            elif drop_indicator == QAbstractItemView.BelowItem:
                parent_item = target_item.parent()
                insert_index = parent_item.indexOfChild(target_item) + 1
            elif drop_indicator == QAbstractItemView.OnItem:
                parent_item = target_item
                insert_index = -1
            else:
                event.ignore(); return
            
            if not parent_item:
                event.ignore(); return

            for file_path, display_name in reversed(items_to_add):
                is_duplicate = False
                for i in range(parent_item.childCount()):
                    if parent_item.child(i).data(0, Qt.UserRole) == file_path:
                        is_duplicate = True; break
                
                if not is_duplicate:
                    new_item = QTreeWidgetItem([display_name])
                    new_item.setData(0, Qt.UserRole, file_path)
                    new_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable)
                    new_item.setToolTip(0, file_path)
                    
                    if insert_index != -1:
                        parent_item.insertChild(insert_index, new_item)
                    else:
                        parent_item.addChild(new_item)
                        
                    source_changed = True
                    timeline_reordered = True
            event.accept()

        elif event.mimeData().hasFormat("application/x-playlist-paths"):
            
            # --- PERBAIKAN DIMULAI DI SINI ---
            # Cek apakah ini INTERNAL MOVE (dari Timeline ke Timeline)
            if event.source() == self and event.dropAction() == Qt.MoveAction:
                # Ini adalah reorder file di dalam timeline.
                # Kita harus memanggil 'super()' agar 'move' terjadi.
                super().dropEvent(event)
                if event.isAccepted():
                    source_changed = True
                    timeline_reordered = True
            else:
                # Ini adalah COPY (misal: Ctrl+Drag dari Timeline)
                # atau fallback. Gunakan logika 'copy' yang lama.
                target_item = self.itemAt(event.pos())
                if not target_item:
                    event.ignore()
                    return

                paths_data = event.mimeData().data("application/x-playlist-paths")
                paths = str(paths_data, 'utf-8').split(',')
                
                drop_indicator = self.dropIndicatorPosition()
                
                if drop_indicator == QAbstractItemView.AboveItem:
                    parent_item = target_item.parent()
                    insert_index = parent_item.indexOfChild(target_item)
                elif drop_indicator == QAbstractItemView.BelowItem:
                    parent_item = target_item.parent()
                    insert_index = parent_item.indexOfChild(target_item) + 1
                elif drop_indicator == QAbstractItemView.OnItem:
                    parent_item = target_item
                    insert_index = -1
                else:
                    event.ignore()
                    return

                if not parent_item:
                     event.ignore()
                     return

                for file_path in reversed(paths):
                    is_duplicate = False
                    for i in range(parent_item.childCount()):
                        if parent_item.child(i).data(0, Qt.UserRole) == file_path:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        display_name = os.path.basename(file_path)
                        match = re.match(r'^(.*?)%(\d+)d(\.[^.]+)$', display_name)
                        if match:
                             display_name = f"{match.groups()[0]}[...]{match.groups()[2]}"

                        new_item = QTreeWidgetItem([display_name])
                        new_item.setData(0, Qt.UserRole, file_path)
                        new_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable)
                        new_item.setToolTip(0, file_path)
                        
                        if insert_index != -1:
                            parent_item.insertChild(insert_index, new_item)
                        else:
                            parent_item.addChild(new_item)
                            
                        source_changed = True
                        timeline_reordered = True
                event.accept()
            # --- PERBAIKAN SELESAI ---

        else:
            # --- INI MENANGANI INTERNAL MOVE (FOLDER) ---
            super().dropEvent(event)
            if event.isAccepted():
                source_changed = True
                timeline_reordered = True
        
        if source_changed:
            self.treeChanged.emit()
        if timeline_reordered:
            self.timelineOrderChanged.emit()

class PlaybackMode(Enum):
    LOOP = auto()
    PLAY_NEXT = auto()
    PLAY_ONCE = auto()
    LOOP_MARKED_RANGE = auto()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kenae Player")
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

        self.annotation_marks = set()
        self.media_data_cache = {}
        self.current_sequence_index = 0
        self.compare_mode = False
        self.playback_mode = PlaybackMode.LOOP
        self.loop_in_point = None
        self.loop_out_point = None
        self.media_player_A_fps, self.media_player_B_fps = 0.0, 0.0
        self.show_timecode = False
        self.is_compare_playing = False
        self.compare_timer = QTimer(self)
        self.compare_timer.timeout.connect(self.update_compare_frames)
        self.setAcceptDrops(False)
        self.splitter_sizes = []
        self.last_playlist_path = None
        self.media_info_cache = {}
        self.active_panel_for_duration = None

        self.is_mark_tour_active = False
        self.current_mark_tour_index = 0
        self.mark_tour_speed_ms = 1500
        self.mark_tour_timer = QTimer(self)
        self.mark_tour_timer.setTimerType(Qt.PreciseTimer)
        self.mark_tour_timer.setSingleShot(True)

        # --- Inisialisasi speed_actions dan speed_action_group ---
        self.speed_action_group = QActionGroup(self)
        self.speed_actions = {}
        self.speed_action_group.setExclusive(True)
        # --- Akhir Inisialisasi ---

        self.current_draw_color = QColor(255, 0, 0, 255) # Default Merah
        self.pen_size = 5
        self.eraser_size = 20

        # --- LOGIKA SEGMEN BARU ---
        # Peta segmen: list of dicts
        # [{'item': item, 'path': str, 'start_frame': int, 'duration': int}]
        self.segment_map = []
        self.current_segment_total_frames = 0
        self.current_segment_folder_item = None
        # --- AKHIR LOGIKA SEGMEN ---

        self.setup_ui()
        self.set_playback_mode(PlaybackMode.LOOP)
        self.active_panel_for_duration = self.source_item
        self.update_total_duration()

        self.drawing_toolbar.set_draw_color_indicator(self.current_draw_color)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0) 
        
        self.drawing_toolbar = DrawingToolbar()
        main_layout.addWidget(self.drawing_toolbar)

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
        self.delete_action = QAction("Delete", self)
        self.delete_action.setShortcut(QKeySequence.Delete)
        self.delete_action.setShortcutContext(Qt.WidgetShortcut) # Penting!
        self.delete_action.triggered.connect(self.delete_selected_items_handler)
        self.playlist_widget.addAction(self.delete_action)
        
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)
        self.media_container = QWidget()
        self.media_container_layout = QHBoxLayout(self.media_container)
        self.media_container_layout.setContentsMargins(0,0,0,0)
        self.media_player = MediaPlayer()
        self.media_container_layout.addWidget(self.media_player)
        self.media_player_2 = MediaPlayer(enable_audio=False)
        media_layout.addWidget(self.media_container, 1)
        self.timeline = TimelineWidget()
        media_layout.addWidget(self.timeline)
        self.controls = MediaControls() 
        self.controls.set_compare_state(self.compare_mode)
        self.controls.set_volume(self.media_player.volume())
        media_layout.addWidget(self.controls)
        
        self.splitter.addWidget(self.playlist_widget_container)
        self.splitter.addWidget(media_widget)
        self.splitter.setSizes([280, 920]) 
        
        main_layout.addWidget(self.splitter, 1) 
        
        self.connect_signals()
        self.create_menu_bar()
        self.create_status_bar()
        self.setup_shortcuts()

    def connect_signals(self):
        # Sinyal kontrol media
        self.controls.play_button.clicked.connect(self.toggle_play)
        self.controls.prev_button.clicked.connect(self.previous_frame)
        self.controls.next_button.clicked.connect(self.next_frame)
        self.controls.compare_toggled.connect(self.toggle_compare_mode_from_button)
        self.controls.first_frame_button.clicked.connect(self.go_to_first_frame)
        self.controls.last_frame_button.clicked.connect(self.go_to_last_frame)
        self.controls.playback_mode_button.clicked.connect(self.cycle_playback_mode)
        self.playlist_widget.timelineOrderChanged.connect(self.handle_timeline_reorder)
        self.controls.volume_changed.connect(self.handle_volume_change)
        
        # Sinyal lain
        self.timeline.position_changed.connect(self.seek_to_position)
        self.timeline.display_mode_changed.connect(self.set_time_display_mode)
        self.timeline.markTourSpeedChanged.connect(self.set_mark_tour_speed)
        self.media_player.frameIndexChanged.connect(self.update_frame_counter)
        self.media_player.playStateChanged.connect(self.controls.set_play_state)
        self.media_player.playbackFinished.connect(self.handle_playback_finished)
        self.media_player_2.frameIndexChanged.connect(self.update_frame_counter_B)
        self.media_player.fpsChanged.connect(lambda fps: self.update_fps_display(fps, 'A'))
        self.media_player_2.fpsChanged.connect(lambda fps: self.update_fps_display(fps, 'B'))
        self.media_player.fileDropped.connect(self.handle_file_drop_on_player)
        self.playlist_widget.filesDroppedOnTarget.connect(self.handle_files_dropped)
        self.playlist_widget.treeChanged.connect(self.update_total_duration)
        self.playlist_widget.itemClicked.connect(self.on_tree_item_clicked)
        self.mark_tour_timer.timeout.connect(self.advance_mark_tour)
        self.media_player.annotationAdded.connect(self.add_annotation_mark)
        self.media_player_2.annotationAdded.connect(self.add_annotation_mark)
        
        # --- KONEKSI SINYAL DRAWING BARU ---
        self.drawing_toolbar.drawModeToggled.connect(self.handle_draw_toggle)
        self.drawing_toolbar.eraseModeToggled.connect(self.handle_erase_toggle)
        self.drawing_toolbar.colorButtonClicked.connect(self.open_color_picker)
        self.drawing_toolbar.clearFrameDrawingClicked.connect(self.clear_current_frame_drawing)
        self.drawing_toolbar.sizeChanged.connect(self.handle_size_change)
        # --- AKHIR KONEKSI ---

    def setup_shortcuts(self):
        pass

    def _resolve_sequences_and_files(self, file_paths):
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.exr', '.dpx']
        processed_files = set()
        resolved_paths = []
        
        # Urutkan file input
        sorted_paths = sorted(file_paths)
        
        for path in sorted_paths:
            if path in processed_files:
                continue
            
            is_image = any(path.lower().endswith(ext) for ext in image_extensions)
            if not is_image:
                resolved_paths.append(path)
                processed_files.add(path)
                continue
            
            dirname = os.path.dirname(path)
            filename = os.path.basename(path)
            # Regex untuk "nama", "angka", "ekstensi"
            match = re.match(r'^(.*?)(\d+)(\.[^.]+)$', filename) 
            
            if not match:
                resolved_paths.append(path)
                processed_files.add(path)
                continue
                
            base_name, number_str, extension = match.groups()
            # Gunakan padding dari file PERTAMA yang kita temui sebagai "standar"
            padding = len(number_str) 
            
            sequence_files = []
            frame_numbers = []

            try:
                # Scan seluruh direktori tempat file ini berada
                all_files_in_dir = os.listdir(dirname)
            except OSError:
                resolved_paths.append(path)
                processed_files.add(path)
                continue

            for f in all_files_in_dir:
                seq_match = re.match(r'^(.*?)(\d+)(\.[^.]+)$', f)
                if seq_match:
                    s_base, s_num_str, s_ext = seq_match.groups()
                    
                    # Cek jika base, extension, DAN PADDING cocok
                    if s_base == base_name and s_ext.lower() == extension.lower() and len(s_num_str) == padding:
                        full_path = os.path.join(dirname, f)
                        
                        # --- PERBAIKAN DI SINI ---
                        # Hapus pengecekan 'if full_path in sorted_paths:'
                        # Kita ingin menemukan semua file yang cocok di direktori,
                        # tidak peduli apakah file itu ada di daftar input awal.
                        sequence_files.append(full_path)
                        frame_numbers.append(int(s_num_str))
                        # --- AKHIR PERBAIKAN ---

            if len(sequence_files) > 1:
                min_frame, max_frame = min(frame_numbers), max(frame_numbers)
                
                # Cek jika frame kontigu (berurutan tanpa jeda)
                if (max_frame - min_frame + 1) == len(frame_numbers):
                    # Ya, ini sequence kontigu
                    display_name = f"{base_name}[{min_frame:0{padding}d}-{max_frame:0{padding}d}]{extension}"
                    sequence_pattern_path = os.path.join(dirname, f"{base_name}%0{padding}d{extension}")
                    resolved_paths.append((sequence_pattern_path, display_name))
                    processed_files.update(sequence_files)
                else:
                    # Frame tidak kontigu, tambahkan sebagai file individual
                    for seq_file in sequence_files:
                        if seq_file not in processed_files:
                            resolved_paths.append(seq_file)
                            processed_files.add(seq_file)
            else:
                # Bukan sequence, tambahkan file ini saja
                resolved_paths.append(path)
                processed_files.add(path)
                
        return resolved_paths
    
    def handle_timeline_reorder(self):
        """
        Dipanggil ketika item di timeline dipindahkan (drag/drop)
        atau item baru ditambahkan dari source.
        """
        # Cek jika kita sedang dalam mode segmen dan folder yg aktif masih ada
        if not self.segment_map or not self.current_segment_folder_item:
            return # Tidak ada yg perlu dilakukan
        
        # Cek jika item folder masih ada di tree
        try:
            _ = self.current_segment_folder_item.text(0)
        except RuntimeError:
            # Item folder sudah dihapus, reset
            self.current_segment_folder_item = None
            return

        # Simpan posisi frame global saat ini
        current_global_frame = self.timeline.current_position
        
        # Muat ulang folder segmen. Ini akan membaca urutan item yg baru.
        self.load_folder_segments(self.current_segment_folder_item)
        
        # Kembalikan playhead ke posisi semula
        if current_global_frame < self.current_segment_total_frames:
            self.seek_to_position(current_global_frame)
        
        self.status_bar.showMessage("Timeline order updated", 2000)

    def handle_files_dropped(self, dropped_paths, target_item):
        resolved_media = self._resolve_sequences_and_files(dropped_paths)
        if not resolved_media:
            return
        self.add_files_to_source(resolved_media)
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
            for media_item in resolved_media:
                if isinstance(media_item, tuple):
                    file_path, display_name = media_item
                else:
                    file_path, display_name = media_item, os.path.basename(media_item)
                is_duplicate = False
                for i in range(drop_folder.childCount()):
                    if drop_folder.child(i).data(0, Qt.UserRole) == file_path:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    new_item = QTreeWidgetItem(drop_folder, [display_name])
                    new_item.setData(0, Qt.UserRole, file_path)
                    new_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable)
                    new_item.setToolTip(0, file_path)
        self.update_total_duration()

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

    def format_duration(self, seconds):
        if seconds is None or seconds < 0:
            return "00:00:00"
        secs = int(seconds)
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"

    def get_media_info(self, file_path):
        if file_path in self.media_info_cache:
            return self.media_info_cache[file_path]
        if not file_path or (not os.path.exists(file_path) and '%' not in file_path):
            self.media_info_cache[file_path] = (0.0, 0) # Cache kegagalan
            return (0.0, 0)
        duration, frame_count = 0.0, 0
        try:
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
            if '%' not in file_path and any(file_path.lower().endswith(ext) for ext in image_extensions):
                duration, frame_count = 0.0, 1
            else:
                capture = create_media_capture(file_path)
                if capture and capture.isOpened():
                    fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
                    frame_count_val = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
                    f_count = int(frame_count_val)
                    if fps > 0 and f_count > 0:
                        duration = f_count / fps
                        frame_count = f_count
                    # Jika f_count 0 (mungkin streaming/webcam), coba baca 1 frame
                    elif f_count <= 0:
                         ret, _ = capture.read()
                         if ret:
                             frame_count = 1 # Setidaknya 1 frame
                             duration = (1.0 / fps) if fps > 0 else 0.0
                if capture:
                    capture.release()
        except Exception as e:
            print(f"Could not get info for {file_path}: {e}")
            duration, frame_count = 0.0, 0
        
        # Jangan cache jika gagal (f_count 0) agar bisa dicoba lagi
        if frame_count > 0:
            self.media_info_cache[file_path] = (duration, frame_count)
            
        return (duration, frame_count)

    def _sum_media_info_recursive(self, parent_item):
        total_seconds, total_frames = 0.0, 0
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            path = child.data(0, Qt.UserRole)
            if path:
                duration, frames = self.get_media_info(path)
                total_seconds += duration
                total_frames += frames
            if child.childCount() > 0:
                sub_seconds, sub_frames = self._sum_media_info_recursive(child)
                total_seconds += sub_seconds
                total_frames += sub_frames
        return (total_seconds, total_frames)

    def on_tree_item_clicked(self, item, column):
        if item.data(0, Qt.UserRole) is None:
            self.update_total_duration(item)

    def update_total_duration(self, item_to_calculate=None):
            if item_to_calculate is None:
                item_to_calculate = self.active_panel_for_duration
            if not item_to_calculate:
                return
            self.active_panel_for_duration = item_to_calculate
            total_seconds, total_frames = self._sum_media_info_recursive(item_to_calculate)
            duration_str = self.format_duration(total_seconds)
            label_prefix = "Total Source"
            parent = item_to_calculate
            while parent:
                if parent == self.timeline_item:
                    label_prefix = "Total Timeline"
                    break
                parent = parent.parent()
            final_text = ""
            if item_to_calculate == self.source_item or item_to_calculate == self.timeline_item:
                final_text = f"{label_prefix}: {duration_str} ({total_frames})"
            else:
                folder_name = item_to_calculate.text(0)
                final_text = f"{label_prefix} [{folder_name}]: {duration_str} ({total_frames})"
            self.total_duration_label.setText(final_text)

    def create_menu_bar(self):
        menubar = self.menuBar()

        # --- File Menu (Tetap Sama) ---
        file_menu = menubar.addMenu('File')
        # ... (Kode File Menu tidak berubah) ...
        open_action = QAction('Open File', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        self.open_folder_action = QAction('Open Image Sequence', self)
        self.open_folder_action.setShortcut('Ctrl+Shift+O')
        self.open_folder_action.triggered.connect(self.open_image_sequence)
        file_menu.addAction(self.open_folder_action)
        save_playlist_action = QAction('Save Playlist', self)
        save_playlist_action.setShortcut('Ctrl+S')
        save_playlist_action.triggered.connect(self.save_playlist)
        file_menu.addAction(save_playlist_action)
        load_playlist_action = QAction('Load Playlist', self)
        load_playlist_action.setShortcut('Ctrl+L')
        load_playlist_action.triggered.connect(self.load_playlist)
        file_menu.addAction(load_playlist_action)
        file_menu.addSeparator()
        clear_action = QAction('Clear Project', self)
        clear_action.triggered.connect(self.clear_project_tree)
        file_menu.addAction(clear_action)


        # --- View Menu (Diperluas) ---
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
        
        view_menu.addSeparator()

        # Sub-menu Zoom (Tetap Sama)
        zoom_menu = view_menu.addMenu("Zoom")
        # ... (Kode Zoom Menu tidak berubah) ...
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut(QKeySequence(Qt.Key_Equal)) # Shortcut utama '='
        zoom_in_action.setShortcuts([QKeySequence(Qt.Key_Equal), QKeySequence(Qt.Key_Plus)]) # Tambah '+'
        zoom_in_action.triggered.connect(self._shortcut_zoom_in)
        zoom_menu.addAction(zoom_in_action)
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut(QKeySequence(Qt.Key_Minus))
        zoom_out_action.triggered.connect(self._shortcut_zoom_out)
        zoom_menu.addAction(zoom_out_action)
        reset_zoom_action = QAction("Reset Zoom (100%)", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self._shortcut_reset_zoom)
        zoom_menu.addAction(reset_zoom_action)

        # Sub-menu Drawing (Tetap Sama)
        draw_menu = view_menu.addMenu("Drawing")
        # ... (Kode Drawing Menu tidak berubah) ...
        toggle_draw_action = QAction("Toggle Pen", self)
        toggle_draw_action.setShortcut("D")
        toggle_draw_action.triggered.connect(self._shortcut_toggle_draw)
        draw_menu.addAction(toggle_draw_action)
        toggle_erase_action = QAction("Toggle Eraser", self)
        toggle_erase_action.setShortcut("E")
        toggle_erase_action.triggered.connect(self._shortcut_toggle_erase)
        draw_menu.addAction(toggle_erase_action)
        draw_menu.addSeparator()
        increase_size_action = QAction("Increase Size", self)
        increase_size_action.setShortcut("Ctrl+=")
        increase_size_action.setShortcuts([QKeySequence("Ctrl+="), QKeySequence("Ctrl++")]) # Tambah Ctrl++
        increase_size_action.triggered.connect(self._shortcut_increase_size)
        draw_menu.addAction(increase_size_action)
        decrease_size_action = QAction("Decrease Size", self)
        decrease_size_action.setShortcut("Ctrl+-")
        decrease_size_action.triggered.connect(self._shortcut_decrease_size)
        draw_menu.addAction(decrease_size_action)
        pick_color_action = QAction("Pick Color", self)
        pick_color_action.setShortcut("C")
        pick_color_action.triggered.connect(self.drawing_toolbar.color_button.click)
        draw_menu.addAction(pick_color_action)
        draw_menu.addSeparator()
        clear_frame_action = QAction("Clear Frame Drawing", self)
        clear_frame_action.setShortcut("Ctrl+Shift+X")
        clear_frame_action.triggered.connect(self.clear_current_frame_drawing)
        draw_menu.addAction(clear_frame_action)
        
        # --- SUBMENU BARU: Timeline & Marks (DILENGKAPI) ---
        view_menu.addSeparator()
        
        timeline_marks_menu = view_menu.addMenu("Timeline & Marks")

        # -- Grup Playback/Frame Navigation --
        play_pause_action = QAction("Play / Pause", self)
        play_pause_action.setShortcut("Space")
        play_pause_action.triggered.connect(self.toggle_play)
        timeline_marks_menu.addAction(play_pause_action)

        next_frame_action = QAction("Next Frame", self)
        next_frame_action.setShortcut(QKeySequence(Qt.Key_Right))
        next_frame_action.triggered.connect(self.next_frame)
        timeline_marks_menu.addAction(next_frame_action)

        prev_frame_action = QAction("Previous Frame", self)
        prev_frame_action.setShortcut(QKeySequence(Qt.Key_Left))
        prev_frame_action.triggered.connect(self.previous_frame)
        timeline_marks_menu.addAction(prev_frame_action)

        first_frame_action = QAction("Go to First Frame", self)
        first_frame_action.setShortcut("Home")
        first_frame_action.triggered.connect(self.go_to_first_frame)
        timeline_marks_menu.addAction(first_frame_action)

        last_frame_action = QAction("Go to Last Frame", self)
        last_frame_action.setShortcut("End")
        last_frame_action.triggered.connect(self.go_to_last_frame)
        timeline_marks_menu.addAction(last_frame_action)

        timeline_marks_menu.addSeparator()

        # -- Grup Navigasi Timeline/Segmen --
        next_item_action = QAction("Play Next Timeline Item", self)
        next_item_action.setShortcut("Ctrl+Down")
        next_item_action.triggered.connect(self.play_next_timeline_item)
        timeline_marks_menu.addAction(next_item_action)
        
        prev_item_action = QAction("Play Previous Timeline Item", self)
        prev_item_action.setShortcut("Ctrl+Up")
        prev_item_action.triggered.connect(self.play_previous_timeline_item)
        timeline_marks_menu.addAction(prev_item_action)

        next_segment_action = QAction("Jump to Next Segment", self)
        next_segment_action.setShortcut("Ctrl+Right")
        next_segment_action.triggered.connect(self.jump_to_next_segment)
        timeline_marks_menu.addAction(next_segment_action)

        prev_segment_action = QAction("Jump to Previous Segment", self)
        prev_segment_action.setShortcut("Ctrl+Left")
        prev_segment_action.triggered.connect(self.jump_to_previous_segment)
        timeline_marks_menu.addAction(prev_segment_action)
        
        timeline_marks_menu.addSeparator()

        # -- Grup Marking --
        toggle_f_mark_action = QAction("Toggle Mark", self)
        toggle_f_mark_action.setShortcut("F")
        toggle_f_mark_action.triggered.connect(self.toggle_mark_at_current_frame)
        timeline_marks_menu.addAction(toggle_f_mark_action)

        jump_next_mark_action = QAction("Jump to Next Mark", self)
        jump_next_mark_action.setShortcut("]")
        jump_next_mark_action.triggered.connect(self.jump_to_next_mark)
        timeline_marks_menu.addAction(jump_next_mark_action)

        jump_prev_mark_action = QAction("Jump to Previous Mark", self)
        jump_prev_mark_action.setShortcut("[")
        jump_prev_mark_action.triggered.connect(self.jump_to_previous_mark)
        timeline_marks_menu.addAction(jump_prev_mark_action)

        # Aksi Jump and Play Next Mark BARU
        jump_play_next_action = QAction("Jump and Play to Next Mark", self)
        jump_play_next_action.setShortcut("Shift+]")
        jump_play_next_action.triggered.connect(self.jump_and_play_next_mark)
        timeline_marks_menu.addAction(jump_play_next_action)

        # Aksi Jump and Play Previous Mark BARU
        jump_play_prev_action = QAction("Jump and Play to Previous Mark", self)
        jump_play_prev_action.setShortcut("Shift+[")
        jump_play_prev_action.triggered.connect(self.jump_and_play_previous_mark)
        timeline_marks_menu.addAction(jump_play_prev_action)

        loop_range_action = QAction("Toggle Loop Range", self)
        loop_range_action.setShortcut("L")
        loop_range_action.triggered.connect(self.toggle_marked_range_loop)
        timeline_marks_menu.addAction(loop_range_action)
        
        mark_tour_action = QAction("Toggle Mark Tour", self)
        mark_tour_action.setShortcut("Ctrl+Shift+P")
        mark_tour_action.triggered.connect(self.toggle_mark_tour)
        timeline_marks_menu.addAction(mark_tour_action)

        clear_marks_action = QAction("Clear All Marks (Current Video)", self)
        clear_marks_action.setShortcut("Ctrl+Shift+M")
        clear_marks_action.triggered.connect(self._shortcut_clear_all_marks)
        timeline_marks_menu.addAction(clear_marks_action)
        
        timeline_marks_menu.addSeparator()

        # Replikasi Menu Mark Tour Speed (Tetap Sama)
        speed_menu = timeline_marks_menu.addMenu("Mark Tour Speed")
        # ... (Kode menu speed tidak berubah) ...
        speeds = {
            "Slowest (3s)": 3000, "Slow (2s)": 2000, "Normal (1.5s)": 1500,
            "Fast (1s)": 1000, "Faster (0.5s)": 500, "Very Fast (0.25s)": 250,
            "Super Fast (0.1s)": 100, "Hyper (0.05s)": 50, "Max (~60fps)": 16
        }
        self.speed_actions.clear() 
        for text, speed_ms in speeds.items():
            action = QAction(text, self)
            action.setCheckable(True)
            action.setData(speed_ms)
            action.triggered.connect(lambda checked, s=speed_ms: self.set_mark_tour_speed(s))
            if self.mark_tour_speed_ms == speed_ms:
                action.setChecked(True)
            speed_menu.addAction(action)
            self.speed_action_group.addAction(action) 
            self.speed_actions[speed_ms] = action 
        
        view_menu.addSeparator()        
    # --- HANDLER SHORTCUT BARU ---

    def _shortcut_zoom_in(self):
        self.media_player.zoom_at_center(1.25)
        if self.compare_mode:
            self.media_player_2.zoom_at_center(1.25)

    def _shortcut_zoom_out(self):
        self.media_player.zoom_at_center(0.8)
        if self.compare_mode:
            self.media_player_2.zoom_at_center(0.8)

    def _shortcut_reset_zoom(self):
        self.media_player.reset_zoom_pan()
        if self.compare_mode:
            self.media_player_2.reset_zoom_pan()

    def _shortcut_toggle_draw(self):
        self.drawing_toolbar.toggle_pen_mode()

    def _shortcut_toggle_erase(self):
        self.drawing_toolbar.toggle_erase_mode()

    def _shortcut_increase_size(self):
        """Menaikkan ukuran alat via shortcut (meniru wheelEvent)."""
        # Hanya berfungsi jika panel alat terlihat
        if not self.drawing_toolbar.tools_container.isVisible():
            return

        tb = self.drawing_toolbar
        new_size = tb.current_val

        if tb.pen_button.isChecked():
            step = 2 # Langkah ukuran pena
            new_size = max(tb.current_min, min(tb.current_val + step, tb.current_max))
        elif tb.erase_button.isChecked():
            step = 5 # Langkah ukuran penghapus
            new_size = max(tb.current_min, min(tb.current_val + step, tb.current_max))

        if new_size != tb.current_val:
            tb.sizeChanged.emit(new_size) # Kirim sinyal seolah-olah slider digerakkan

    def _shortcut_decrease_size(self):
        """Menurunkan ukuran alat via shortcut (meniru wheelEvent)."""
        if not self.drawing_toolbar.tools_container.isVisible():
            return

        tb = self.drawing_toolbar
        new_size = tb.current_val

        if tb.pen_button.isChecked():
            step = 2
            new_size = max(tb.current_min, min(tb.current_val - step, tb.current_max))
        elif tb.erase_button.isChecked():
            step = 5
            new_size = max(tb.current_min, min(tb.current_val - step, tb.current_max))

        if new_size != tb.current_val:
            tb.sizeChanged.emit(new_size)
    # --- AKHIR HANDLER ---    
        
    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        style = "QLabel { color: #ffffff; font-weight: bold; font-size: 14px; padding: 2px 8px; background-color: #444444; border-radius: 3px; margin: 2px; }"
        self.total_duration_label = QLabel("Total Source: 00:00:00 (0)")
        self.total_duration_label.setStyleSheet(style)
        self.status_bar.addPermanentWidget(self.total_duration_label)
        self.frame_counter_label = QLabel("Frame: 0 / 0")
        self.frame_counter_label.setStyleSheet(style)
        self.status_bar.addPermanentWidget(self.frame_counter_label)
        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setStyleSheet(style)
        self.status_bar.addPermanentWidget(self.fps_label)
        self.status_bar.setStyleSheet("QStatusBar { font-size: 12px; font-weight: bold; }")
        self.status_bar.showMessage("Ready")
        
    def show_shortcuts_dialog(self):
        # --- PERBARUI TEKS SHORTCUT ---
        shortcuts_text = """
            <h3>Playback</h3>
            <b>Space</b>: Play / Pause<br>
            <b>Right Arrow</b>: Next Frame<br>
            <b>Left Arrow</b>: Previous Frame<br>
            <b>Home</b>: Go to First Frame<br>
            <b>End</b>: Go to Last Frame<br>

            <h3>Timeline Navigation</h3>
            <b>Ctrl + Right Arrow</b>: Jump to Next Segment (Folder/Segment Mode)<br>
            <b>Ctrl + Left Arrow</b>: Jump to Previous Segment (Folder/Segment Mode)<br>
            <b>Ctrl + Down Arrow</b>: Play Next Item in Timeline (Old Tree Mode)<br>
            <b>Ctrl + Up Arrow</b>: Play Previous Item in Timeline (Old Tree Mode)<br>

            <h3>Marking</h3>
            <b>F</b>: Toggle Mark at Current Frame (White)<br>
            <b>Ctrl + Shift + M</b>: Clear All Marks (White & Green) & All Drawings<br>
            <b>]</b>: Jump to Next Mark (White or Green)<br>
            <b>[</b>: Jump to Previous Mark (White or Green)<br>
            <b>Shift + ]</b>: Jump and Play to Next Mark (White or Green)<br>
            <b>Shift + [</b>: Jump and Play to Previous Mark (White or Green)<br>
            <b>L</b>: Toggle Loop for Marked Range (White)<br>
            <b>Ctrl + Shift + P</b>: Start / Stop Mark Tour (Looping, White Marks)<br>

            <h3>Drawing (View A)</h3>
            Use the <b>Drawing Toolbar</b> (✏️) on the left side of the window.<br>
            (Drawing on a frame automatically adds a Green Mark)
            <b>Ctrl + Shift + X</b>: Clear Drawing on Current Frame<br>
            <h3>File</h3>
            <b>Ctrl + O</b>: Open File<br>
            <b>Ctrl + Shift + O</b>: Open Image Sequence<br>
            <b>Ctrl + S</b>: Save Playlist<br>
            <b>Ctrl + L</b>: Load Playlist<br>

            <h3>View</h3>
            <b>Ctrl + T</b>: Toggle Compare Mode<br>
            <b>Ctrl + H</b>: Show / Hide Project Panel & Drawing Toolbar<br> 
        """
        # --- AKHIR PERBARUAN ---
        QMessageBox.information(
            self,
            "Keyboard Shortcuts",
            shortcuts_text
        )
    
    # --- SLOT-SLOT KONTROL DRAWING (DIPERBARUI) ---
    
    def handle_draw_toggle(self, checked):
        """Menangani sinyal 'drawModeToggled' dari toolbar."""
        # --- PERBAIKAN ---
        if checked:
            self.set_draw_mode()
        else:
            # Hanya matikan jika erase *juga* tidak aktif
            if not self.drawing_toolbar.erase_button.isChecked():
                self.set_drawing_off()
        # --- AKHIR PERBAIKAN ---

    def handle_erase_toggle(self, checked):
        """Menangani sinyal 'eraseModeToggled' dari toolbar."""
        # --- PERBAIKAN ---
        if checked:
            self.set_erase_mode()
        else:
            # Hanya matikan jika draw *juga* tidak aktif
            if not self.drawing_toolbar.pen_button.isChecked():
                self.set_drawing_off()
        # --- AKHIR PERBAIKAN ---

    def open_color_picker(self):
        """Membuka dialog QColorDialog untuk memilih warna."""
        color = QColorDialog.getColor(self.current_draw_color, self, "Select Draw Color")
        
        if color.isValid():
            self.current_draw_color = color
            self.drawing_toolbar.set_draw_color_indicator(self.current_draw_color)
            
            # Jika mode draw sudah aktif, perbarui warnanya
            if self.media_player.drawing_enabled and self.media_player.draw_pen_color.alpha() > 0:
                self.set_draw_mode() 

    def clear_current_frame_drawing(self):
        """Menghapus anotasi (drawing) dan marka hijau terkait."""
        
        current_global_frame = self.timeline.current_position
        if current_global_frame < 0: return
        
        annotation_removed = False
        mark_removed = False # Flag apakah marka hijau dihapus dari cache
        
        target_path_a = self.media_player.get_current_file_path() 
        target_local_frame_a = -1 # Frame lokal untuk gambar di player A
        
        paths_to_modify_marks = [] # Path cache untuk marka hijau
        target_local_frames_marks = [] # Frame lokal untuk marka hijau
        is_segment_mode = bool(self.segment_map)

        # --- 1. Tentukan target & frame lokal ---
        if is_segment_mode:
            target_segment = None
            for segment in self.segment_map:
                seg_end_frame = segment['start_frame'] + segment['duration']
                if current_global_frame >= segment['start_frame'] and current_global_frame < seg_end_frame:
                    target_segment = segment
                    break
            if target_segment:
                if target_path_a == target_segment['path']:
                    target_local_frame_a = current_global_frame - target_segment['start_frame']
                    paths_to_modify_marks.append(target_path_a)
                    target_local_frames_marks.append(target_local_frame_a)
                else: return # Error
            else: return # Gagal
                 
        elif self.compare_mode:
            path_b = self.media_player_2.get_current_file_path()
            target_local_frame_a = current_global_frame 
            
            if target_path_a:
                 paths_to_modify_marks.append(target_path_a)
                 target_local_frames_marks.append(current_global_frame)
            if path_b:
                 paths_to_modify_marks.append(path_b)
                 target_local_frames_marks.append(current_global_frame)
                 
        elif target_path_a: # Mode Single
            target_local_frame_a = current_global_frame 
            paths_to_modify_marks.append(target_path_a)
            target_local_frames_marks.append(current_global_frame)
        
        if target_local_frame_a < 0 and not paths_to_modify_marks: return

        # --- 2. Hapus GAMBAR (drawing) hanya dari Player A ---
        if target_path_a and target_local_frame_a >= 0:
            if target_local_frame_a in self.media_player.annotations:
                self.media_player.annotations.pop(target_local_frame_a)
                annotation_removed = True
                data_a = self._get_or_create_media_data(target_path_a)
                if target_local_frame_a in data_a["annotations"]:
                    data_a["annotations"].pop(target_local_frame_a)
            
        # --- 3. Hapus MARKA (hijau) dari semua cache file yang relevan ---
        for i, path in enumerate(paths_to_modify_marks):
            local_frame = target_local_frames_marks[i]
            data = self._get_or_create_media_data(path)
            if local_frame in data["annotation_marks"]:
                data["annotation_marks"].remove(local_frame)
                mark_removed = True # Set flag jika ada yg benar-benar dihapus

        # --- 4. Update state global & UI ---
        if mark_removed: # Hanya update jika ada perubahan di cache
            if is_segment_mode:
                # Bangun ulang state global dari semua cache segmen
                self._rebuild_global_marks_from_segments()
            else:
                 # Mode single/compare: Update state global langsung
                if current_global_frame in self.annotation_marks:
                    self.annotation_marks.remove(current_global_frame)
                # Update UI timeline dari state global
                self.timeline.set_annotation_marks(self.annotation_marks) 

        # --- 5. Tampilkan pesan & refresh player jika gambar dihapus ---
        if annotation_removed:
            if self.compare_mode:
                self.update_composite_view()
            else:
                self.media_player.display_frame(self.media_player.displayed_frame_source)
            self.status_bar.showMessage(f"Drawing cleared from frame {target_local_frame_a + 1}", 2000)
        elif mark_removed:
             self.status_bar.showMessage(f"Annotation mark cleared from frame {current_global_frame + 1}", 2000)
        else:
             local_idx_display = target_local_frame_a if target_local_frame_a >=0 else self.media_player.current_frame_index
             self.status_bar.showMessage(f"No drawing found on frame {local_idx_display + 1}", 2000)

    def _shortcut_clear_all_marks(self):
        """
        Handler shortcut untuk 'Ctrl+Shift+M'.
        Menghapus semua marka dari cache untuk file yang sedang aktif.
        """
        paths_to_clear = []
        
        if self.compare_mode:
            path_a = self.media_player.get_current_file_path()
            path_b = self.media_player_2.get_current_file_path()
            if path_a: paths_to_clear.append(path_a)
            if path_b: paths_to_clear.append(path_b)
        else:
            path_a = self.media_player.get_current_file_path()
            if path_a: paths_to_clear.append(path_a)
            
        if not paths_to_clear:
            self.status_bar.showMessage("No media loaded to clear marks from.", 2000)
            return

        cleared_count = 0
        for path in paths_to_clear:
            if path in self.media_data_cache:
                self.media_data_cache[path]["marks"].clear()
                self.media_data_cache[path]["annotation_marks"].clear()
                self.media_data_cache[path]["annotations"].clear()
                cleared_count += 1
        
        # 1. Panggil clear_all_marks() untuk membersihkan state UI aktif
        #    (Ini akan membersihkan self.marks, self.annotation_marks, 
        #    self.media_player.annotations, dan timeline UI)
        self.clear_all_marks(clear_segments=False)
        
        # --- PERBAIKAN: Panggil refresh player secara manual ---
        # 2. Muat ulang frame saat ini (untuk menghapus gambar anotasi)
        if self.compare_mode:
            # update_composite_view akan mengambil frame A dan B
            # (yang datanya sudah bersih) dan memanggil display_frame()
            self.update_composite_view() 
        else:
            # Kita harus memanggil display_frame() secara manual
            # dengan frame ASLI (self.media_player.current_frame)
            if self.media_player.current_frame is not None:
                self.media_player.display_frame(self.media_player.current_frame)
            else:
                self.media_player.display_frame(None) # Kosongkan player
        # --- AKHIR PERBAIKAN ---

        if cleared_count > 0:
            self.status_bar.showMessage(f"All marks and drawings cleared for {cleared_count} item(s).", 3000)
        else:
            self.status_bar.showMessage("No marks found to clear.", 2000)
    
    def set_draw_mode(self):
        """Mengaktifkan mode menggambar (pena) pada player A."""
        # --- TAMBAHAN BARU ---
        # Atur slider toolbar ke nilai dan jangkauan Pena
        self.drawing_toolbar.set_size_range(1, 200) # Min 1, Max 200
        self.drawing_toolbar.set_size_value(self.pen_size)
        # --- AKHIR TAMBAHAN ---

        player = self.media_player 
        player.drawing_enabled = True
        player.draw_pen_color = self.current_draw_color
        player.draw_pen_width = self.pen_size 
        self.status_bar.showMessage(f"Draw Mode ON (Pen Size: {self.pen_size})", 3000)
        player.video_label.setCursor(Qt.CrossCursor)

    def set_erase_mode(self):
        """Mengaktifkan mode menghapus pada player A."""
        # --- TAMBAHAN BARU ---
        # Atur slider toolbar ke nilai dan jangkauan Penghapus
        self.drawing_toolbar.set_size_range(5, 500) # Min 5, Max 500
        self.drawing_toolbar.set_size_value(self.eraser_size)
        # --- AKHIR TAMBAHAN ---
        
        player = self.media_player 
        player.drawing_enabled = True
        player.draw_pen_color = QColor(0, 0, 0, 0) 
        player.draw_pen_width = self.eraser_size 
        self.status_bar.showMessage(f"Erase Mode ON (Size: {self.eraser_size})", 3000)
        player.video_label.setCursor(Qt.CrossCursor)

    def set_drawing_off(self):
        """Menonaktifkan semua mode menggambar/menghapus."""
        player = self.media_player
        player.drawing_enabled = False
        self.status_bar.showMessage("Drawing Mode OFF", 3000)
        player.video_label.setCursor(Qt.ArrowCursor)
        
        # --- PERBAIKAN ---
        # Panggil force_close() di toolbar, yang akan
        # menonaktifkan master_toggle_button secara visual.
        self.drawing_toolbar.force_close()
        # --- AKHIR PERBAIKAN ---
        
    # (Letakkan ini di dekat set_draw_mode, set_erase_mode, dll.)

    def handle_size_change(self, value):
        """
        Slot untuk sinyal 'sizeChanged' dari toolbar.
        Dipanggil saat pengguna menggeser slider.
        """
        # Cek alat mana yang aktif (dilihat dari state tombol di toolbar)
        if self.drawing_toolbar.pen_button.isChecked():
            self.pen_size = value
            self.set_draw_mode() # Terapkan lagi (akan update status bar)
        elif self.drawing_toolbar.erase_button.isChecked():
            self.eraser_size = value
            self.set_erase_mode()

    def add_annotation_mark(self, frame_index):
        """Slot untuk menerima sinyal 'annotationAdded' dari MediaPlayer."""
        
        current_global_frame = self.timeline.current_position
        if current_global_frame < 0: return
            
        target_path = None
        target_local_frame = -1
        is_segment_mode = bool(self.segment_map)

        # --- 1. Tentukan target & frame lokal ---
        if is_segment_mode:
            target_segment = None
            for segment in self.segment_map:
                seg_end_frame = segment['start_frame'] + segment['duration']
                if current_global_frame >= segment['start_frame'] and current_global_frame < seg_end_frame:
                    target_segment = segment
                    break
            if target_segment:
                target_path = target_segment['path']
                target_local_frame = current_global_frame - target_segment['start_frame']
            else: return # Gagal
                 
        elif self.compare_mode:
            path_a = self.media_player.get_current_file_path()
            path_b = self.media_player_2.get_current_file_path()
            target_local_frame = current_global_frame 
            target_path = path_a # Target utama A
            
            # Modifikasi cache B (jika ada)
            if path_b:
                data_b = self._get_or_create_media_data(path_b)
                data_b["annotation_marks"].add(target_local_frame)
                
        elif self.media_player.has_media(): # Mode Single
            target_path = self.media_player.get_current_file_path()
            target_local_frame = current_global_frame
        
        if not target_path or target_local_frame < 0: return

        # --- 2. Modifikasi cache target utama ---
        data = self._get_or_create_media_data(target_path)
        # Hanya tambahkan jika belum ada di cache (mencegah duplikasi jika sinyal terkirim ganda)
        if target_local_frame in data["annotation_marks"]:
             return 
        data["annotation_marks"].add(target_local_frame)
        
        # --- 3. Update state global & UI ---
        if is_segment_mode:
            # Bangun ulang state global dari semua cache segmen
            self._rebuild_global_marks_from_segments()
        else:
            # Mode single/compare: Update state global langsung
            self.annotation_marks.add(current_global_frame)
            # Update UI timeline dari state global
            self.timeline.set_annotation_marks(self.annotation_marks)
    
    def handle_file_drop_on_player(self, file_path, target_view):
        resolved_media = self._resolve_sequences_and_files([file_path])
        if not resolved_media:
            return
        self.add_files_to_source(resolved_media)
        self.update_total_duration()
        item_to_load = resolved_media[0]
        path_to_load = item_to_load[0] if isinstance(item_to_load, tuple) else item_to_load
        
        if not self.compare_mode:
            # --- PERBAIKAN: Hapus argumen 'clear_marks' ---
            self.load_single_file(path_to_load, clear_segments=True)
        else:
            # load_compare_files sudah memanggil _save_current_media_data()
            if target_view == 'A':
                self.load_compare_files(path_to_load, self.media_player_2.get_current_file_path())
            else:
                self.load_compare_files(self.media_player.get_current_file_path(), path_to_load)
           
    def _collect_media_paths_recursive(self, parent_item):
        """Mengumpulkan semua path media dari item ini dan anak-anaknya."""
        paths = set()
        path = parent_item.data(0, Qt.UserRole)
        if path:
            paths.add(path)
        
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            paths.update(self._collect_media_paths_recursive(child))
        return paths

    def _is_in_timeline_branch(self, item):
        """Helper: Cek apakah item adalah Timeline root atau di dalamnya."""
        if not item: return False
        if item == self.timeline_item: return True
        parent = item.parent()
        while parent:
            if parent == self.timeline_item:
                return True
            parent = parent.parent()
        return False

    def _normalize_media_path(self, path):
        """Menghilangkan bagian sekuens untuk perbandingan cache."""
        if path is None:
            return None
        if '%' in path:
            # Mengubah "path/to/file.%04d.exr" menjadi "path/to/file..exr"
            return re.sub(r'%\d*d', '', path)
        return path       
                
    def delete_selected_items_handler(self):
            if not self.playlist_widget.hasFocus():
                return


            selected_items = self.playlist_widget.selectedItems()
            if not selected_items: return
            removed_paths = set()
            timeline_modified = False
            for item in list(selected_items):
                parent = item.parent()
                if not parent:
                    continue
                removed_paths.update(self._collect_media_paths_recursive(item))
                if not timeline_modified and self._is_in_timeline_branch(item):
                    timeline_modified = True
                parent.removeChild(item)

            removed_paths_normalized = removed_paths
            if removed_paths_normalized:
                cache_keys_to_remove = [
                    key for key in list(self.media_info_cache.keys())
                    if self._normalize_media_path(key) in removed_paths_normalized
                ]
                for key in cache_keys_to_remove:
                    self.media_info_cache.pop(key, None)
            current_a = self._normalize_media_path(self.media_player.get_current_file_path())
            current_b = self._normalize_media_path(self.media_player_2.get_current_file_path()) if self.compare_mode else None

            cleared_media = False
            if current_a and current_a in removed_paths_normalized:
                self.media_player.clear_media()
                cleared_media = True
            if self.compare_mode and current_b and current_b in removed_paths_normalized:
                self.media_player_2.clear_media()
                cleared_media = True

            if cleared_media:
                self.clear_all_marks(clear_segments=True)

            if removed_paths_normalized and self.segment_map:
                if any(self._normalize_media_path(segment['path']) in removed_paths_normalized for segment in self.segment_map):
                    self.segment_map.clear()
                    self.current_segment_total_frames = 0
                    self.timeline.set_segments([], 0)

            self.update_total_duration()
            self.update_playlist_item_indicator()
            if removed_paths_normalized or timeline_modified:
                self.status_bar.showMessage("Selected items removed.", 2000)
    
    def set_playback_mode(self, mode):
        self.playback_mode = mode
        if mode != PlaybackMode.LOOP_MARKED_RANGE:
            self.loop_in_point = None
            self.loop_out_point = None
            if mode == PlaybackMode.LOOP:
                self.controls.set_playback_mode_state("🔁", "Playback Mode: Loop")
            elif mode == PlaybackMode.PLAY_NEXT:
                self.controls.set_playback_mode_state("⤵️", "Playback Mode: Play Next (Timeline only)")
            elif mode == PlaybackMode.PLAY_ONCE:
                self.controls.set_playback_mode_state("➡️|", "Playback Mode: Play Once")
        else:
            if self.loop_in_point is not None and self.loop_out_point is not None:
                 # Gunakan frame global untuk tooltip
                 in_point_display = self.loop_in_point + 1
                 out_point_display = self.loop_out_point + 1
                 self.controls.set_playback_mode_state("[🔁]", f"Playback Mode: Loop Range ({in_point_display} - {out_point_display})")

        # --- PERBAIKAN: START ---
        # Hanya set loop range di internal player jika TIDAK dalam mode segmen.
        # Looping mode segmen ditangani oleh update_frame_counter.
        # Looping mode compare ditangani oleh update_compare_frames.
        if not self.segment_map:
            self.media_player.set_loop_range(self.loop_in_point, self.loop_out_point)
            if self.compare_mode:
                 self.media_player_2.set_loop_range(self.loop_in_point, self.loop_out_point)
        else:
             # Jika kita dalam mode segmen, pastikan internal player TIDAK punya loop point
             self.media_player.set_loop_range(None, None)
        # --- PERBAIKAN: END ---

        # Terapkan jangkauan loop ke *kedua* player
        self.media_player.set_loop_range(self.loop_in_point, self.loop_out_point)
        if self.compare_mode:
             self.media_player_2.set_loop_range(self.loop_in_point, self.loop_out_point)

    def cycle_playback_mode(self):
        if self.playback_mode == PlaybackMode.LOOP:
            self.set_playback_mode(PlaybackMode.PLAY_NEXT)
        elif self.playback_mode == PlaybackMode.PLAY_NEXT:
            self.set_playback_mode(PlaybackMode.PLAY_ONCE)
        else:
            self.set_playback_mode(PlaybackMode.LOOP)

    def toggle_marked_range_loop(self):
        if self.playback_mode == PlaybackMode.LOOP_MARKED_RANGE:
            self.set_playback_mode(PlaybackMode.LOOP)
            self.status_bar.showMessage("Marked range loop disabled.", 2000)
            return
        if len(self.marks) < 2:
            self.status_bar.showMessage("Cannot set loop range. Please add at least two marks.", 3000)
            return
            
        # --- PERBAIKAN: Gunakan frame global (posisi timeline) ---
        current_frame = self.timeline.current_position
        # --- AKHIR PERBAIKAN ---
        
        start_mark = None
        for mark in reversed(self.marks):
            if mark <= current_frame:
                start_mark = mark
                break
        if start_mark is None:
            start_mark = self.marks[0]
        end_mark = None
        try:
            start_index = self.marks.index(start_mark)
            if start_index < len(self.marks) - 1:
                end_mark = self.marks[start_index + 1]
            else:
                self.status_bar.showMessage("Cannot start loop from the last mark.", 3000)
                return
        except ValueError:
            return 
        if start_mark is not None and end_mark is not None:
            self.loop_in_point = start_mark
            self.loop_out_point = end_mark
            self.set_playback_mode(PlaybackMode.LOOP_MARKED_RANGE)
            self.status_bar.showMessage(f"Looping between frame {start_mark + 1} and {end_mark + 1}.", 3000)

    def handle_volume_change(self, value):
        self.media_player.set_volume(value)

    def handle_playback_finished(self, audio_has_ended):
        if self.is_compare_playing:
            self.is_compare_playing = False
            self.controls.set_play_state(False)
            
            if self.playback_mode == PlaybackMode.LOOP_MARKED_RANGE:
                 return # Ditangani oleh update_compare_frames
            
            if self.playback_mode == PlaybackMode.LOOP:
                self.seek_to_position(0)
                self.toggle_play() # Mulai ulang compare play
                return
            
            return

        if self.playback_mode == PlaybackMode.LOOP:
            if not self.compare_mode: 
                self.media_player.toggle_play()
        
        elif self.playback_mode == PlaybackMode.PLAY_NEXT:
            
            # --- LOGIKA SEGMEN (Sudah Benar) ---
            if self.segment_map:
                current_path = self.media_player.get_current_file_path()
                current_index = -1
                for i, segment in enumerate(self.segment_map):
                    if segment['path'] == current_path:
                        current_index = i
                        break
                
                if current_index != -1 and (current_index + 1) < len(self.segment_map):
                    next_segment = self.segment_map[current_index + 1]
                    self.load_single_file(next_segment['path'], clear_segments=False)
                    QTimer.singleShot(100, self.media_player.toggle_play)
                else:
                    self.set_playback_mode(PlaybackMode.PLAY_ONCE)
            
            else:
                current_path = self.media_player.get_current_file_path()
                item = self.find_item_by_path_recursive(current_path, self.timeline_item)
                if item: 
                    self.play_next_timeline_item()
                else:
                    self.set_playback_mode(PlaybackMode.PLAY_ONCE)
            
    def open_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Media File", "", "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.png *.jpeg *.bmp *.tiff);;All Files (*)")
        if file_paths:
            resolved_media = self._resolve_sequences_and_files(file_paths)
            self.add_files_to_source(resolved_media)
            if resolved_media:
                item_to_load = resolved_media[0]
                path_to_load = item_to_load[0] if isinstance(item_to_load, tuple) else item_to_load
                self.load_single_file(path_to_load, clear_segments=True)
            
    def open_image_sequence(self, file_paths=None): # 'file_paths' tidak terpakai
        folder_path = QFileDialog.getExistingDirectory(self, "Select Image Sequence Folder", "")
        if not folder_path:
            return

        all_image_paths = []
        try:
            all_files_in_dir = sorted(os.listdir(folder_path))
        except OSError as e:
            self.status_bar.showMessage(f"Error reading folder: {e}", 3000)
            return
            
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.exr', '.dpx']
        
        for f in all_files_in_dir:
            if any(f.lower().endswith(ext) for ext in image_extensions):
                all_image_paths.append(os.path.join(folder_path, f))

        if not all_image_paths:
            self.status_bar.showMessage("No image files found in the selected folder.", 3000)
            return

        # Kirim SEMUA file gambar ke resolver
        resolved_media = self._resolve_sequences_and_files(all_image_paths)
        self.add_files_to_source(resolved_media)
        
        if resolved_media:
            # Muat item pertama yang ditemukan
            item_to_load = resolved_media[0]
            path_to_load = item_to_load[0] if isinstance(item_to_load, tuple) else item_to_load
            
            # Panggil load_single_file (yang sudah benar)
            self.load_single_file(path_to_load, clear_segments=True)
        
    def save_playlist(self):
        default_path = self.last_playlist_path or os.getcwd()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Playlist", default_path, "Kenae Playlist (*.kenae)")
        if not file_path:
            return
        if not file_path.lower().endswith(".kenae"):
            file_path += ".kenae"
        base_dir = os.path.dirname(file_path)
        playlist_data = {
            "version": 1,
            "source": self._serialize_playlist_branch(self.source_item, base_dir),
            "timeline": self._serialize_playlist_branch(self.timeline_item, base_dir),
        }
        try:
            with open(file_path, "w", encoding="utf-8") as handle:
                json.dump(playlist_data, handle, indent=2)
        except OSError as exc:
            QMessageBox.critical(self, "Save Playlist Failed", f"Tidak bisa menyimpan playlist:\n{exc}")
            return
        self.last_playlist_path = file_path
        self.status_bar.showMessage(f"Playlist saved: {os.path.basename(file_path)}", 4000)

    def load_playlist(self):
        default_path = self.last_playlist_path or os.getcwd()
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Playlist", default_path, "Kenae Playlist (*.kenae)")
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                playlist_data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            QMessageBox.critical(self, "Load Playlist Failed", f"Tidak bisa membuka playlist:\n{exc}")
            return
        self.clear_project_tree()
        base_dir = os.path.dirname(file_path)
        self._load_playlist_branch(self.source_item, playlist_data.get("source", []), base_dir)
        self._load_playlist_branch(self.timeline_item, playlist_data.get("timeline", []), base_dir)
        self.source_item.setExpanded(True)
        self.timeline_item.setExpanded(True)
        self.playlist_widget.expandAll()
        self.last_playlist_path = file_path
        missing = self._count_missing_entries(self.source_item) + self._count_missing_entries(self.timeline_item)
        if missing:
            self.status_bar.showMessage(f"Playlist loaded dengan {missing} file yang belum ditemukan", 5000)
        else:
            self.status_bar.showMessage(f"Playlist loaded: {os.path.basename(file_path)}", 4000)
        self.update_playlist_item_indicator()
        self.active_panel_for_duration = self.source_item
        self.update_total_duration()

    def _serialize_playlist_branch(self, parent_item, base_dir):
        return [self._serialize_playlist_item(parent_item.child(i), base_dir) for i in range(parent_item.childCount())]

    def _serialize_playlist_item(self, item, base_dir):
        node = {"name": item.text(0)}
        path = item.data(0, Qt.UserRole)
        if path:
            node["path"] = path
            try:
                if '%' not in path:
                    node["relative_path"] = os.path.relpath(path, base_dir)
            except ValueError:
                pass
        children = [self._serialize_playlist_item(item.child(i), base_dir) for i in range(item.childCount())]
        if children:
            node["children"] = children
        return node

    def _load_playlist_branch(self, parent_item, nodes, base_dir):
        for node in nodes:
            item = QTreeWidgetItem(parent_item, [node.get("name", "Untitled")])
            resolved_path = self._resolve_playlist_path(node, base_dir)
            if resolved_path:
                item.setData(0, Qt.UserRole, resolved_path)
                item.setToolTip(0, resolved_path)
                exists = os.path.exists(resolved_path) if '%' not in resolved_path else os.path.exists(os.path.dirname(resolved_path))
                if not exists:
                    item.setForeground(0, QColor("#ff8a80"))
            else:
                item.setData(0, Qt.UserRole, None)
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable
            if not resolved_path:
                flags |= Qt.ItemIsDropEnabled
            item.setFlags(flags)
            children = node.get("children", [])
            if children:
                self._load_playlist_branch(item, children, base_dir)

    def _resolve_playlist_path(self, node, base_dir):
        path = node.get("path")
        if path and '%' in path: 
            return os.path.abspath(path)
        candidates = []
        relative = node.get("relative_path")
        if relative:
            candidates.append(os.path.abspath(os.path.join(base_dir, relative)))
        if path:
            candidates.append(os.path.abspath(path))
        seen = set()
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            if os.path.exists(candidate):
                return candidate
        return candidates[0] if candidates else None

    def _count_missing_entries(self, parent_item):
        missing = 0
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            path = child.data(0, Qt.UserRole)
            if path:
                exists = os.path.exists(path) if '%' not in path else os.path.exists(os.path.dirname(path))
                if not exists:
                    missing += 1
            missing += self._count_missing_entries(child)
        return missing
        
    def add_files_to_source(self, media_items):
        for item_data in media_items:
            if isinstance(item_data, tuple):
                path, display_name = item_data
            else:
                path, display_name = item_data, os.path.basename(item_data)
            exists = os.path.exists(path) if '%' not in path else os.path.exists(os.path.dirname(path))
            if exists and not self.find_item_by_path_recursive(path, self.source_item):
                item = QTreeWidgetItem(self.source_item, [display_name])
                item.setData(0, Qt.UserRole, path)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable)
                item.setToolTip(0, path)
        
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
        self.clear_all_marks(clear_segments=True) # Pastikan segmen juga bersih
        self.media_info_cache.clear()
        self.active_panel_for_duration = self.source_item
        self.update_total_duration()
        
    def toggle_play(self):
        if self.is_mark_tour_active: self.toggle_mark_tour()
        if self.media_player.drawing_enabled:
            self.set_drawing_off()
            
        if self.compare_mode:
            if self.is_compare_playing:
                # --- BERHENTI COMPARE ---
                self.compare_timer.stop()
                self.is_compare_playing = False
                
                # PERBAIKAN: Beri tahu player A untuk berhenti & sync (pause) audio
                self.media_player.is_playing = False # Set flag-nya
                self.media_player._sync_audio_to_current_frame(force=True) # Paksa sync (akan pause)

            else:
                # --- MULAI COMPARE ---
                is_a_fin = self.media_player.total_frames > 0 and self.media_player.current_frame_index >= self.media_player.total_frames - 1
                is_b_fin = self.media_player_2.total_frames > 0 and self.media_player_2.current_frame_index >= self.media_player_2.total_frames - 1
                is_in_loop_range = (self.playback_mode == PlaybackMode.LOOP_MARKED_RANGE and
                                    self.loop_out_point is not None and
                                    self.media_player.current_frame_index >= self.loop_out_point)
                
                # PERBAIKAN: Reset *kedua* player jika KEDUANYA selesai
                if (is_a_fin and is_b_fin) and not is_in_loop_range:
                    self.media_player.seek_to_position(0)
                    self.media_player_2.seek_to_position(0)
                    self.media_player.has_finished = False
                    self.media_player_2.has_finished = False # <-- INI PENTING
                elif is_in_loop_range:
                     pass
                     
                fps_a = self.media_player.fps if self.media_player.fps > 0 else 30
                fps_b = self.media_player_2.fps if self.media_player_2.fps > 0 else 30
                self.compare_timer.start(int(1000 / min(fps_a, fps_b)))
                self.is_compare_playing = True

                # PERBAIKAN: Beri tahu player A untuk mulai & sync (play) audio
                self.media_player.is_playing = True # Set flag-nya
                self.media_player._sync_audio_to_current_frame(force=True) # Paksa sync (akan play)
                
            self.controls.set_play_state(self.is_compare_playing)
        else:
            # Mode non-compare (logika ini sudah benar)
            is_in_loop_range = (self.playback_mode == PlaybackMode.LOOP_MARKED_RANGE and
                                self.loop_out_point is not None and
                                self.media_player.current_frame_index >= self.loop_out_point)
            
            if self.media_player.has_finished and not is_in_loop_range:
                if self.segment_map:
                    self.seek_to_position(0) 
                else:
                    self.media_player.seek_to_position(0)
                self.media_player.has_finished = False 
            
            elif is_in_loop_range:
                 pass
            
            self.media_player.toggle_play()
            
    def update_compare_frames(self):
        # --- PERBAIKAN: Cek loop logic *sebelum* melompat ke frame berikutnya ---
        if (self.playback_mode == PlaybackMode.LOOP_MARKED_RANGE and
                self.loop_out_point is not None and
                self.media_player.current_frame_index >= self.loop_out_point):
            
            loop_start_frame = self.loop_in_point if self.loop_in_point is not None else 0
            
            # Panggil seek_to_position *internal* player
            self.media_player.seek_to_position(loop_start_frame)
            self.media_player_2.seek_to_position(loop_start_frame)
            self.update_composite_view() # Tampilkan frame awal loop
            return # Selesai untuk frame "tick" ini
        # --- AKHIR PERBAIKAN LOOP ---

        finished_a = not self.media_player.has_media() or \
                     (self.media_player.total_frames > 0 and self.media_player.current_frame_index >= self.media_player.total_frames - 1)
        
        finished_b = not self.media_player_2.has_media() or \
                     (self.media_player_2.total_frames > 0 and self.media_player_2.current_frame_index >= self.media_player_2.total_frames - 1)

        if finished_a and finished_b:
            self.compare_timer.stop()
            # PERBAIKAN: Kirim argumen boolean
            self.handle_playback_finished(False) 
            return 

        # PERBAIKAN: Panggil next_frame mode "internal"
        if not finished_a:
            self.media_player.next_frame(_update_media_internals_only=True)
        
        if not finished_b:
            self.media_player_2.next_frame(_update_media_internals_only=True)
        # --- AKHIR PERBAIKAN ---

        # Sekarang update_composite_view akan mengambil frame baru
        # dan menjadi satu-satunya yang memperbarui UI/Timeline
        self.update_composite_view()

    def previous_frame(self):
        if self.is_compare_playing: return
        if self.media_player.drawing_enabled: self.set_drawing_off() 
        if self.media_player.is_playing:
            self.toggle_play()

        if not self.segment_map:
            # --- PERBAIKAN: Gunakan flag saat mode compare ---
            is_compare = self.compare_mode
            self.media_player.previous_frame(_update_media_internals_only=is_compare)
            if self.compare_mode:
                self.media_player_2.previous_frame(_update_media_internals_only=True)
                self.update_composite_view() # Perbarui UI/Timeline secara manual
            # --- AKHIR PERBAIKAN ---
        else:
            # Mode segmen
            current_global_frame = self.timeline.current_position
            if current_global_frame > 0:
                self.seek_to_position(current_global_frame - 1)
            
    def next_frame(self):
        if self.is_compare_playing: return
        if self.media_player.drawing_enabled: self.set_drawing_off() 
        if self.media_player.is_playing:
            self.toggle_play()

        if not self.segment_map:
            # --- PERBAIKAN: Gunakan flag saat mode compare ---
            is_compare = self.compare_mode
            self.media_player.next_frame(_update_media_internals_only=is_compare)
            if self.compare_mode:
                self.media_player_2.next_frame(_update_media_internals_only=True)
                self.update_composite_view() # Perbarui UI/Timeline secara manual
            # --- AKHIR PERBAIKAN ---
        else:
            # Mode segmen
            current_global_frame = self.timeline.current_position
            if current_global_frame < self.current_segment_total_frames - 1:
                self.seek_to_position(current_global_frame + 1)
            
    def seek_to_position(self, position, _internal_call=False):
        # --- PERBAIKAN: Jangan hentikan tour jika dipanggil oleh tour itu sendiri ---
        if self.is_mark_tour_active and not _internal_call:
            self.toggle_mark_tour()
        # --- AKHIR PERBAIKAN ---
            
        if self.media_player.drawing_enabled: self.set_drawing_off() 
        
        # --- LOGIKA SEEKING SEGMEN BARU ---
        if not self.segment_map:
            # Mode Normal (File Tunggal)
            self.media_player.seek_to_position(position)
            if self.compare_mode:
                self.media_player_2.seek_to_position(position)
                self.update_composite_view()
        else:
            # Mode Segmen (Folder Timeline)
            if self.compare_mode:
                self.toggle_compare_mode(False) # Mode segmen = single view
            
            # Pastikan posisi valid
            position = max(0, min(position, self.current_segment_total_frames - 1))
            
            target_segment = None
            # Cari segmen mana yang berisi 'position' (frame global)
            for segment in self.segment_map:
                seg_end_frame = segment['start_frame'] + segment['duration']
                if position >= segment['start_frame'] and position < seg_end_frame:
                    target_segment = segment
                    break
            
            # Jika tidak ketemu (misal, klik di frame terakhir), gunakan segmen terakhir
            if not target_segment and self.segment_map and position == self.current_segment_total_frames - 1:
                 target_segment = self.segment_map[-1]
            
            if not target_segment:
                print(f"Seek error: Tidak bisa menemukan segmen untuk frame global {position}")
                return # Tidak ada segmen untuk di-seek

            # Hitung frame lokal di dalam segmen
            local_frame = position - target_segment['start_frame']
            
            # Cek apakah kita perlu memuat file baru
            current_path = self.media_player.get_current_file_path()
            if target_segment['path'] != current_path:
                # --- PERBAIKAN: Hapus argumen 'clear_marks' ---
                self.load_single_file(target_segment['path'], clear_segments=False)
            
            # Seek ke frame lokal
            self.media_player.seek_to_position(local_frame)
            
            # Update manual frame counter (karena sinyal frameIndexChanged
            # akan mengirim frame LOKAL, tapi kita perlu update GLOBAL)
            self.update_frame_counter(local_frame, target_segment['duration'])
        # --- AKHIR LOGIKA SEEKING SEGMEN ---
            
    def update_frame_counter(self, current_frame, total_frames):
        # current_frame dan total_frames di sini adalah LOKAL (dari media_player)
        
        if not self.segment_map:
            # Mode Normal
            if self.compare_mode:
                return # Diurus oleh update_composite_view
            if total_frames <= 0:
                self.frame_counter_label.setText("No Media")
                self.timeline.set_duration(0)
                self.timeline.set_position(0)
                return
            self.frame_counter_label.setText(f"Frame: {current_frame + 1} / {total_frames}")
            self.timeline.set_duration(total_frames)
            self.timeline.set_position(current_frame)
        else:
            # Mode Segmen
            current_path = self.media_player.get_current_file_path()
            if not current_path: 
                return 
                
            segment_start_frame = 0
            
            for segment in self.segment_map:
                if segment['path'] == current_path:
                    segment_start_frame = segment['start_frame']
                    break
            
            # Hitung frame global
            global_frame = segment_start_frame + current_frame
            
            # Update UI dengan data global
            self.frame_counter_label.setText(f"Frame: {global_frame + 1} / {self.current_segment_total_frames}")
            self.timeline.set_duration(self.current_segment_total_frames)
            self.timeline.set_position(global_frame)
            
            if self.timeline.fps != self.media_player.fps:
                 self.timeline.set_fps(self.media_player.fps)
                 
            # --- PERBAIKAN: Pindahkan Logika Loop ke Sini ---
            # Cek logika loop range di sini menggunakan frame GLOBAL
            if (self.media_player.is_playing and # Hanya jika sedang play
                self.playback_mode == PlaybackMode.LOOP_MARKED_RANGE and
                self.loop_out_point is not None and
                global_frame >= self.loop_out_point):
                
                loop_start_frame = self.loop_in_point if self.loop_in_point is not None else 0
                
                # Gunakan self.seek_to_position() yang mengerti frame GLOBAL
                self.seek_to_position(loop_start_frame)
            # --- AKHIR PERBAIKAN ---
        
    def update_frame_counter_B(self, cf, tf): pass
    
    def toggle_mark_at_current_frame(self):
        current_global_frame = self.timeline.current_position
        if current_global_frame < 0: return

        target_path = None
        target_local_frame = -1
        is_segment_mode = bool(self.segment_map)
        
        # --- 1. Tentukan target & frame lokal ---
        if is_segment_mode:
            target_segment = None
            for segment in self.segment_map:
                seg_end_frame = segment['start_frame'] + segment['duration']
                if current_global_frame >= segment['start_frame'] and current_global_frame < seg_end_frame:
                    target_segment = segment
                    break
            if target_segment:
                target_path = target_segment['path']
                target_local_frame = current_global_frame - target_segment['start_frame']
            else: return # Gagal
                 
        elif self.compare_mode:
            path_a = self.media_player.get_current_file_path()
            path_b = self.media_player_2.get_current_file_path()
            target_local_frame = current_global_frame # global == local di compare
            target_path = path_a # Target utama A
            
            # Modifikasi cache B (jika ada)
            if path_b:
                data_b = self._get_or_create_media_data(path_b)
                if current_global_frame in data_b["marks"]: 
                    data_b["marks"].remove(target_local_frame)
                elif target_local_frame not in data_b["marks"]:
                    data_b["marks"].append(target_local_frame); data_b["marks"].sort()
            
        elif self.media_player.has_media(): # Mode Single
            target_path = self.media_player.get_current_file_path()
            target_local_frame = current_global_frame # global == local di single
        
        if not target_path or target_local_frame < 0: return

        # --- 2. Modifikasi cache target utama ---
        data = self._get_or_create_media_data(target_path)
        is_removing = target_local_frame in data["marks"] # Cek state di cache

        if is_removing:
            data["marks"].remove(target_local_frame)
            self.status_bar.showMessage(f"Mark removed from frame {current_global_frame + 1}", 2000)
        else:
            data["marks"].append(target_local_frame)
            data["marks"].sort()
            self.status_bar.showMessage(f"Mark added at frame {current_global_frame + 1}", 2000)

        # --- 3. Update state global & UI ---
        if is_segment_mode:
            # Bangun ulang state global dari semua cache segmen
            self._rebuild_global_marks_from_segments() 
        else:
            # Mode single/compare: Update state global langsung
            if is_removing:
                if current_global_frame in self.marks: self.marks.remove(current_global_frame)
            else:
                if current_global_frame not in self.marks: self.marks.append(current_global_frame); self.marks.sort()
            # Update UI timeline dari state global
            self.timeline.set_marks(self.marks)
            
    def clear_all_marks(self, clear_segments=True):
        marks_cleared = len(self.marks) > 0
        annotations_cleared = len(self.annotation_marks) > 0
        self.marks.clear()
        self.annotation_marks.clear()
        
        # Hapus anotasi dari player A (dan B jika ada)
        self.media_player.annotations.clear()
        self.media_player_2.annotations.clear()
        
        # --- PERBAIKAN: HAPUS BLOK INI ---
        # if self.media_player.displayed_frame_source is not None:
        #     self.media_player.display_frame(self.media_player.displayed_frame_source)
        # --- AKHIR PERBAIKAN ---
            
        self.timeline.set_marks(self.marks)
        self.timeline.set_annotation_marks(self.annotation_marks)
        
        # --- LOGIKA CLEAR SEGMEN BARU ---
        if clear_segments:
            self.segment_map.clear()
            self.current_segment_total_frames = 0
            self.timeline.set_segments([], 0)
            self.current_segment_folder_item = None 
        # --- AKHIR LOGIKA CLEAR SEGMEN ---

        if marks_cleared or annotations_cleared:
            self.status_bar.showMessage("All marks and drawings cleared", 2000)
        
    def jump_to_next_mark(self):
        all_marks = sorted(list(set(self.marks) | self.annotation_marks))
        if not all_marks: return
        
        # --- PERBAIKAN: Gunakan frame global (posisi timeline) ---
        current_frame = self.timeline.current_position
        # --- AKHIR PERBAIKAN ---

        next_mark = None
        for mark in all_marks:
            if mark > current_frame:
                next_mark = mark
                break
        if next_mark is None:
            next_mark = all_marks[0]
        if next_mark is not None:
            self.seek_to_position(next_mark)

    def jump_to_previous_mark(self):
        all_marks = sorted(list(set(self.marks) | self.annotation_marks))
        if not all_marks: return
        
        # --- PERBAIKAN: Gunakan frame global (posisi timeline) ---
        current_frame = self.timeline.current_position
        # --- AKHIR PERBAIKAN ---
        
        prev_mark = None
        for mark in reversed(all_marks):
            if mark < current_frame:
                prev_mark = mark
                break
        if prev_mark is None:
            prev_mark = all_marks[-1]
        if prev_mark is not None:
            self.seek_to_position(prev_mark)

    # --- FUNGSI NAVIGASI SEGMEN BARU ---
    def jump_to_next_segment(self):
        """(Shortcut: Ctrl+Right) Jumps to the start of the next segment."""
        if not self.segment_map:
            return # Only works in segment mode
            
        if self.media_player.is_playing or self.is_compare_playing:
            self.toggle_play() # Stop playback
        if self.media_player.drawing_enabled: 
            self.set_drawing_off() 
            
        current_global_frame = self.timeline.current_position
        
        next_segment_start_frame = -1
        
        # Cari frame awal segmen berikutnya
        for segment in self.segment_map:
            if segment['start_frame'] > current_global_frame:
                next_segment_start_frame = segment['start_frame']
                break
                
        if next_segment_start_frame != -1:
            self.seek_to_position(next_segment_start_frame)
        else:
            # Kita ada di segmen terakhir, lompat ke awal (frame 0)
            self.seek_to_position(0)

    def jump_to_previous_segment(self):
        """(Shortcut: Ctrl+Left) Jumps to the start of the previous segment."""
        if not self.segment_map:
            return # Only works in segment mode

        if self.media_player.is_playing or self.is_compare_playing:
            self.toggle_play() # Stop playback
        if self.media_player.drawing_enabled: 
            self.set_drawing_off() 

        current_global_frame = self.timeline.current_position
        
        prev_segment_start_frame = -1
        
        # Cari frame awal segmen *sebelumnya*
        # Iterasi terbalik
        for segment in reversed(self.segment_map):
            # Kita cari segmen pertama yang mulainya SEBELUM frame kita saat ini
            if segment['start_frame'] < current_global_frame:
                prev_segment_start_frame = segment['start_frame']
                break
                
        if prev_segment_start_frame != -1:
            self.seek_to_position(prev_segment_start_frame)
        else:
            # Kita ada di segmen pertama (atau frame 0)
            # Lompat ke awal segmen TERAKHIR
            if self.segment_map:
                self.seek_to_position(self.segment_map[-1]['start_frame'])
    # --- AKHIR FUNGSI NAVIGASI SEGMEN ---

    def jump_and_play_next_mark(self):
        self.jump_to_next_mark()
        if not self.media_player.is_playing:
            QTimer.singleShot(50, self.toggle_play)

    def jump_and_play_previous_mark(self):
        self.jump_to_previous_mark()
        if not self.media_player.is_playing:
            QTimer.singleShot(50, self.toggle_play)

    def toggle_mark_tour(self):
        if self.is_mark_tour_active:
            self.is_mark_tour_active = False
            self.mark_tour_timer.stop()
            self.status_bar.showMessage("Mark tour stopped.", 3000)
        else:
            if not self.marks:
                self.status_bar.showMessage("No marks available to start a tour.", 3000)
                return
            if self.playback_mode == PlaybackMode.LOOP_MARKED_RANGE:
                self.set_playback_mode(PlaybackMode.LOOP)
            
            # --- PERBAIKAN MARK TOUR: START ---
            if self.compare_mode:
                if self.is_compare_playing:
                    self.compare_timer.stop()
                    self.is_compare_playing = False
                    self.controls.set_play_state(False)
            else:
                if self.media_player.is_playing:
                    self.media_player.toggle_play() 
            # --- PERBAIKAN MARK TOUR: END ---

            if self.media_player.drawing_enabled: 
                self.set_drawing_off()
            
            self.is_mark_tour_active = True
            self.current_mark_tour_index = 0
            self.status_bar.showMessage("Mark tour started (looping). Press Ctrl+Shift+P to stop.", 5000)
            self.show_current_mark_frame()

    def show_current_mark_frame(self):
        if not self.is_mark_tour_active or not self.marks:
            return
        
        if self.compare_mode:
            if self.is_compare_playing:
                self.compare_timer.stop()
                self.is_compare_playing = False
                self.controls.set_play_state(False)
        else:
            if self.media_player.is_playing:
                self.media_player.toggle_play()

        target_frame = self.marks[self.current_mark_tour_index]
        
        # --- PERBAIKAN MARK TOUR: START ---
        # Panggil seek_to_position (global) dengan flag _internal_call
        self.seek_to_position(target_frame, _internal_call=True)
        # --- PERBAIKAN MARK TOUR: END ---
        
        self.mark_tour_timer.start(self.mark_tour_speed_ms)

    def advance_mark_tour(self):
        if not self.is_mark_tour_active:
            return
        self.current_mark_tour_index += 1
        if self.current_mark_tour_index >= len(self.marks):
            self.current_mark_tour_index = 0
        self.show_current_mark_frame()

    def set_mark_tour_speed(self, speed_ms):
        self.mark_tour_speed_ms = speed_ms
        speed_s = speed_ms / 1000.0
        self.status_bar.showMessage(f"Mark tour speed set to {speed_s} seconds.", 3000)
        self.timeline.current_mark_tour_speed = speed_ms
    
    def find_item_by_path_recursive(self, path, root_item):
        if not path or not root_item: return None
        iterator = QTreeWidgetItemIterator(root_item)
        while iterator.value():
            item = iterator.value()
            if item.data(0, Qt.UserRole) == path:
                return item
            iterator += 1
        return None
        
    def open_image_sequence(self, file_paths=None): # 'file_paths' tidak terpakai
        folder_path = QFileDialog.getExistingDirectory(self, "Select Media Folder", "") # Ubah judul
        if not folder_path:
            return

        all_media_paths = []
        try:
            all_files_in_dir = sorted(os.listdir(folder_path))
        except OSError as e:
            self.status_bar.showMessage(f"Error reading folder: {e}", 3000)
            return
            
        # --- PERBAIKAN: Tambahkan ekstensi video ---
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.exr', '.dpx']
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv'] # Tambahkan video
        all_extensions = image_extensions + video_extensions
        # --- AKHIR PERBAIKAN ---
        
        for f in all_files_in_dir:
            # Cek jika file_name diakhiri dengan ekstensi media
            if any(f.lower().endswith(ext) for ext in all_extensions):
                all_media_paths.append(os.path.join(folder_path, f))

        if not all_media_paths:
            self.status_bar.showMessage("No media files found in the selected folder.", 3000)
            return

        # Kirim SEMUA file media ke resolver
        # _resolve_sequences_and_files akan memisahkan sequence dan video individual
        resolved_media = self._resolve_sequences_and_files(all_media_paths)
        self.add_files_to_source(resolved_media)
        
        if resolved_media:
            # Muat item pertama yang ditemukan
            item_to_load = resolved_media[0]
            path_to_load = item_to_load[0] if isinstance(item_to_load, tuple) else item_to_load
            
            # Panggil load_single_file (yang sudah benar)
            self.load_single_file(path_to_load, clear_segments=True)
                
    def play_previous_timeline_item(self):
        # Fungsi ini HANYA untuk mode tree (non-segmen)
        if self.segment_map: return 

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
            self.load_from_tree(prev_item) # Panggil load_from_tree
            
    def play_next_timeline_item(self):
        # Fungsi ini HANYA untuk mode tree (non-segmen)
        if self.segment_map: return # Ditangani oleh handle_playback_finished
        
        current_path = self.media_player.get_current_file_path()
        current_item = self.find_item_by_path_recursive(current_path, self.timeline_item)
        if not current_item or not current_item.parent(): return
        
        parent = current_item.parent()
        current_index = parent.indexOfChild(current_item)
        next_item = None
        
        # Cari item file berikutnya di dalam folder yang sama
        for i in range(current_index + 1, parent.childCount()):
            potential_next = parent.child(i)
            if potential_next.data(0, Qt.UserRole):
                next_item = potential_next
                break
        
        if next_item:
            self.playlist_widget.setCurrentItem(next_item)
            next_file_path = next_item.data(0, Qt.UserRole)
            
            # --- PERBAIKAN: Hapus 'clear_marks=False' ---
            self.load_single_file(next_file_path, clear_segments=True)
            # --- AKHIR PERBAIKAN ---
            
            if self.playback_mode == PlaybackMode.PLAY_NEXT:
                QTimer.singleShot(100, self.media_player.toggle_play)
        else:
            self.set_playback_mode(PlaybackMode.PLAY_ONCE)        
            
    def load_from_tree(self, item, column=0):
        file_path = item.data(0, Qt.UserRole)
        
        if file_path:
            # --- Ini adalah FILE ---
            self.set_playback_mode(PlaybackMode.PLAY_ONCE)
            if self.compare_mode: self.toggle_compare_mode(False)
            
            # Panggil load_single_file versi baru (tanpa clear_marks)
            self.load_single_file(file_path, clear_segments=True)
        else:
            # --- Ini adalah FOLDER ---
            is_timeline_item = False
            parent = item
            while parent:
                if parent == self.timeline_item:
                    is_timeline_item = True
                    break
                parent = parent.parent()
            
            if is_timeline_item:
                # --- FOLDER DI TIMELINE: AKTIFKAN MODE SEGMEN ---
                self.load_folder_segments(item)
            else:
                # --- Folder di Source (atau Timeline root): tidak ada aksi ---
                pass

    # --- FUNGSI BARU UNTUK MENGUMPULKAN VIDEO ---
    def _collect_videos_recursive(self, parent_item, video_list):
        """Mencari semua item video di dalam folder, secara rekursif."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            path = child.data(0, Qt.UserRole)
            if path:
                # Cek jika file ada
                exists = os.path.exists(path) if '%' not in path else os.path.exists(os.path.dirname(path))
                if exists:
                    video_list.append(child)
            else:
                # Ini adalah sub-folder, cari di dalamnya
                self._collect_videos_recursive(child, video_list)

    def load_folder_segments(self, folder_item):
        """Memuat semua video dalam folder sebagai segmen virtual."""
        if self.compare_mode:
            self.toggle_compare_mode(False)
        
        # 1. Simpan data file sebelumnya
        self._save_current_media_data()
        
        # 2. Bersihkan state aktif awal (termasuk timeline UI)
        self.clear_all_marks(clear_segments=True) 
            
        self.current_segment_folder_item = folder_item 
        self.segment_map.clear()
        self.current_segment_total_frames = 0
        
        video_items = []
        self._collect_videos_recursive(folder_item, video_items)
        
        if not video_items:
            self.status_bar.showMessage(f"Folder '{folder_item.text(0)}' contains no playable media.", 3000)
            self.media_player.clear_media() 
            self.update_frame_counter(-1, 0) 
            self.update_total_duration(self.timeline_item) 
            self.update_playlist_item_indicator() 
            return

        # 3. Bangun peta segmen
        for item in video_items:
            path = item.data(0, Qt.UserRole)
            duration, frame_count = self.get_media_info(path)
            if frame_count > 0:
                self.segment_map.append({
                    'item': item, 
                    'path': path, 
                    'start_frame': self.current_segment_total_frames, 
                    'duration': frame_count
                })
                self.current_segment_total_frames += frame_count
        
        if not self.segment_map:
             self.status_bar.showMessage(f"Could not read media in '{folder_item.text(0)}'.", 3000)
             self.media_player.clear_media() 
             self.update_frame_counter(-1, 0) 
             self.update_total_duration(self.timeline_item) 
             self.update_playlist_item_indicator() 
             return

        # 4. Bangun ulang marka global DARI CACHE
        #    (Ini akan memanggil self.timeline.set_marks)
        self._rebuild_global_marks_from_segments() 

        # --- PERBAIKAN: Atur timeline SEBELUM memuat video pertama ---
        # 5. Dapatkan batas segmen
        segment_boundaries = [s['start_frame'] for s in self.segment_map]
        
        # 6. Atur durasi total DAN batas segmen di timeline SEKARANG
        self.timeline.set_duration(self.current_segment_total_frames) 
        self.timeline.set_segments(segment_boundaries, self.current_segment_total_frames)
        # --- AKHIR PERBAIKAN ---

        # 7. Muat file pertama (load_single_file versi baru TIDAK akan memuat marka/durasi timeline)
        first_video_path = self.segment_map[0]['path']
        self.load_single_file(first_video_path, clear_segments=False) 
        # (Sinyal frameIndexChanged(0, ...) dari sini akan memanggil update_frame_counter
        # yang kemudian akan memanggil self.timeline.set_position(0))
        
        # 8. Update UI lainnya
        self.status_bar.showMessage(f"Loaded folder '{folder_item.text(0)}' ({len(self.segment_map)} items)", 3000)
        self.set_playback_mode(PlaybackMode.PLAY_NEXT)
        self.update_playlist_item_indicator()
            
    def load_single_file(self, file_path, clear_segments=True):
        if self.compare_timer.isActive():
            self.compare_timer.stop()
            self.is_compare_playing = False
            
        # 1. SIMPAN DATA LAMA (dari file sebelumnya)
        self._save_current_media_data()
            
        # 2. HAPUS SEGMENT JIKA DIMINTA
        if clear_segments:
            self.segment_map.clear()
            self.current_segment_total_frames = 0
            self.timeline.set_segments([], 0)
            self.current_segment_folder_item = None 
            
        # 3. MUAT MEDIA BARU
        # (Ini akan memanggil media_player.clear_media(), 
        # yang mengosongkan self.media_player.annotations)
        success = self.media_player.load_media(file_path)
        
        # 4. TERAPKAN DATA BARU
        if success:
            # Muat data dari cache ke state aktif (self.marks, dll.)
            self._load_media_data(file_path)
            
            # Tampilkan ulang frame saat ini agar anotasi (jika ada) muncul
            self.media_player.display_frame(self.media_player.current_frame) 
            
            # Update UI
            self.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}")
            if not self.segment_map:
                duration, frames = self.get_media_info(file_path)
                self.total_duration_label.setText(f"Duration: {self.format_duration(duration)} ({frames})")
            else:
                duration_str = self.format_duration(self.current_segment_total_frames / self.media_player.fps if self.media_player.fps > 0 else 0)
                self.total_duration_label.setText(f"Folder Total: {duration_str} ({self.current_segment_total_frames})")
        else:
            self.status_bar.showMessage(f"Failed to load file")
            if not self.segment_map: # Hanya update jika tidak dalam mode segmen
                self.update_total_duration()
                
        self.update_playlist_item_indicator()
            
    def _get_or_create_media_data(self, file_path):
        """Mendapat atau membuat blok data untuk file path tertentu."""
        if file_path not in self.media_data_cache:
            self.media_data_cache[file_path] = {
                "marks": [],
                "annotation_marks": set(),
                "annotations": {}
            }
        return self.media_data_cache[file_path]

    def _rebuild_global_marks_from_segments(self):
        """
        Membangun ulang daftar marka global (self.marks, self.annotation_marks)
        dengan membaca cache dari semua segmen. HANYA dipanggil saat
        dalam mode segmen.
        """
        if not self.segment_map:
            # Jika tidak ada segmen, pastikan marka aktif kosong
            self.marks.clear()
            self.annotation_marks.clear()
            # Perbarui UI timeline
            self.timeline.set_marks(self.marks)
            self.timeline.set_annotation_marks(self.annotation_marks)
            return

        all_global_marks = []
        all_global_annotation_marks = set()

        for segment in self.segment_map:
            path = segment['path']
            start_frame = segment['start_frame']
            # Dapatkan data dari cache (jangan buat jika tidak ada,
            # meskipun _get_or_create seharusnya aman)
            data = self.media_data_cache.get(path, {"marks": [], "annotation_marks": set()})

            # Konversi marka lokal di cache ke global
            for local_mark in data["marks"]:
                all_global_marks.append(start_frame + local_mark)
            for local_ann_mark in data["annotation_marks"]:
                all_global_annotation_marks.add(start_frame + local_ann_mark)

        # Perbarui state aktif dengan marka gabungan
        # Gunakan set() untuk menghapus duplikat potensial
        self.marks = sorted(list(set(all_global_marks)))
        self.annotation_marks = all_global_annotation_marks

        # Perbarui UI timeline
        self.timeline.set_marks(self.marks)
        self.timeline.set_annotation_marks(self.annotation_marks)

    def _save_current_media_data(self):
        """Menyimpan marka/anotasi aktif ke cache."""
        current_path = self.media_player.get_current_file_path()
        if current_path:
            # Dapatkan data untuk path saat ini (atau buat)
            data = self._get_or_create_media_data(current_path) 
            
            # --- PERBAIKAN: Hanya simpan marka jika TIDAK di mode segmen ---
            if not self.segment_map:
                # Mode Single atau Compare: Simpan state aktif saat ini ke cache
                data["marks"] = list(self.marks) # Simpan salinan
                data["annotation_marks"] = set(self.annotation_marks) # Simpan salinan
            # --- AKHIR PERBAIKAN ---
                
            # Selalu simpan anotasi (gambar) karena itu lokal untuk player
            data["annotations"] = dict(self.media_player.annotations) # Simpan salinan
            
    def _load_media_data(self, file_path):
        """
        Memuat data dari cache ke state aktif player (anotasi).
        HANYA update timeline jika TIDAK dalam mode segmen.
        """
        # Dapatkan data dari cache (atau buat jika ini file baru)
        data = self._get_or_create_media_data(file_path)

        # --- PERBAIKAN: Hapus pembaruan state marka global di sini ---
        # # Terapkan data dari cache ke state aktif
        # self.marks = data["marks"]
        # self.annotation_marks = data["annotation_marks"]
        # --- AKHIR PERBAIKAN ---

        # Terapkan anotasi (gambar) ke player
        self.media_player.annotations = dict(data["annotations"]) 

        # --- PERBAIKAN: Update timeline HANYA jika TIDAK dalam mode segmen ---
        if not self.segment_map:
            # Mode Single atau Compare: Update timeline secara lengkap
            new_duration = self.media_player.total_frames if self.media_player.has_media() else 0
            new_fps = self.media_player.fps if self.media_player.has_media() else 0.0
            new_position = self.media_player.current_frame_index if self.media_player.has_media() else 0 
            new_position = max(0, new_position) 

            # Muat marka LOKAL dari cache ke state global KARENA kita di mode single/compare
            self.marks = data["marks"]
            self.annotation_marks = data["annotation_marks"]

            # Set SEMUA properti timeline
            self.timeline.set_duration(new_duration) 
            self.timeline.set_fps(new_fps) 
            self.timeline.set_marks(self.marks)
            self.timeline.set_annotation_marks(self.annotation_marks)
            self.timeline.set_position(new_position) 
            self.timeline.update() # Paksa repaint
            
    def _load_media_data_for_compare(self, file1=None, file2=None):
        """Memuat dan MENGGABUNGKAN data untuk compare mode."""
        
        # Jika file tidak disediakan, gunakan yang sudah ada
        if file1 is None:
            file1 = self.media_player.get_current_file_path()
        if file2 is None:
            file2 = self.media_player_2.get_current_file_path()

        data1 = self._get_or_create_media_data(file1) if file1 else None
        data2 = self._get_or_create_media_data(file2) if file2 else None
        
        # Gabungkan marka untuk timeline
        marks1 = set(data1["marks"]) if data1 else set()
        marks2 = set(data2["marks"]) if data2 else set()
        self.marks = sorted(list(marks1 | marks2))
        
        ann_marks1 = data1["annotation_marks"] if data1 else set()
        ann_marks2 = data2["annotation_marks"] if data2 else set()
        self.annotation_marks = ann_marks1 | ann_marks2
        
        # Terapkan ke UI
        self.timeline.set_marks(self.marks)
        self.timeline.set_annotation_marks(self.annotation_marks)        
            
    def load_compare_files(self, file1, file2):
        # 1. Simpan data file sebelumnya (jika ada)
        self._save_current_media_data()
        
        # 2. Bersihkan state aktif & hapus mode segmen
        self.clear_all_marks(clear_segments=True) 
        
        # --- PERBAIKAN: Panggil fungsi helper baru ---
        self._load_media_data_for_compare(file1, file2)
        # --- AKHIR PERBAIKAN ---
        
        # Muat media (ini akan me-reset anotasi internal player)
        self.media_player.load_media(file1)
        self.media_player_2.load_media(file2)
        
        # Terapkan anotasi yang sudah di-cache ke player
        # (Data sudah dimuat oleh _load_media_data_for_compare)
        self.media_player.annotations = self._get_or_create_media_data(file1)["annotations"]
        self.media_player_2.annotations = self._get_or_create_media_data(file2)["annotations"]

        f1 = os.path.basename(file1) if file1 else "Empty"
        f2 = os.path.basename(file2) if file2 else "Empty"
        self.status_bar.showMessage(f"Comparing: {f1} vs {f2}")
        dur1, frames1 = self.get_media_info(file1) if file1 else (0, 0)
        dur2, frames2 = self.get_media_info(file2) if file2 else (0, 0)
        dur1_str = self.format_duration(dur1)
        dur2_str = self.format_duration(dur2)
        self.total_duration_label.setText(f"A: {dur1_str} ({frames1}) | B: {dur2_str} ({frames2})")
        QTimer.singleShot(50, self.update_composite_view)
        self.update_playlist_item_indicator()
        
    def toggle_compare_mode(self, enabled):
        if enabled == self.compare_mode: return
        self.compare_mode = enabled
        self.controls.set_compare_state(self.compare_mode)
        self.set_drawing_off() 
        
        # Keluar dari mode compare akan mematikan mode segmen
        if not self.compare_mode:
            if self.compare_timer.isActive():
                self.compare_timer.stop()
                self.is_compare_playing = False
            
            # --- PERBAIKAN: Simpan data (kosong) dari compare mode ---
            # dan bersihkan player B
            self._save_current_media_data() 
            self.media_player_2.clear_media()
            # --- AKHIR PERBAIKAN ---

            self.media_player.display_frame(self.media_player.current_frame)
            self.media_player.set_compare_split()
            
            # Reset timeline ke file A saat ini
            # --- PERBAIKAN: Hapus argumen 'clear_marks' ---
            self.load_single_file(self.media_player.get_current_file_path(), clear_segments=True)
        
        # Masuk ke mode compare
        else:
            # --- PERBAIKAN: Simpan data dari mode single ---
            self._save_current_media_data()
            # --- AKHIR PERBAIKAN ---

            # Matikan mode segmen jika aktif
            if self.segment_map:
                # Panggil clear_all_marks untuk membersihkan state aktif
                self.clear_all_marks(clear_segments=True)
                # Muat ulang file A saat ini (yang mungkin bagian dari segmen)
                self.media_player.load_media(self.media_player.get_current_file_path())
                
            self.update_composite_view() # Akan menggambar tampilan A vs B (kosong)
            
        self.update_playlist_item_indicator()
            
    def update_composite_view(self):
        # --- PERBAIKAN LOGIKA COMPARE MODE ---
        frame_a_orig = self.media_player.current_frame
        frame_b_orig = self.media_player_2.current_frame
        total_f = max(self.media_player.total_frames, self.media_player_2.total_frames)
        current_f = max(self.media_player.current_frame_index, self.media_player_2.current_frame_index)

        self.timeline.set_duration(total_f)
        self.timeline.set_position(current_f)
        
        if total_f > 0 and current_f >= 0:
            self.frame_counter_label.setText(f"Frame: {current_f + 1} / {total_f}")
        else:
            self.frame_counter_label.setText("No Media")
            
        h_a, w_a = (frame_a_orig.shape[0], frame_a_orig.shape[1]) if frame_a_orig is not None else (480, 640)
        h_b, w_b = (frame_b_orig.shape[0], frame_b_orig.shape[1]) if frame_b_orig is not None else (480, 640)

        # --- FUNGSI HELPER UNTUK MENGGAMBAR ANOTASI ---
        def apply_annotation(source_frame, annotation_image, frame_h, frame_w):
            if source_frame is None or annotation_image is None:
                return source_frame
            
            h_ann, w_ann = annotation_image.height(), annotation_image.width()
            if h_ann <= 0 or w_ann <= 0:
                return source_frame
            
            ptr = annotation_image.bits()
            ptr.setsize(h_ann * w_ann * 4)
            arr = np.frombuffer(ptr, np.uint8).reshape((h_ann, w_ann, 4)) # BGRA
            
            bgr_ann = arr[:, :, :3]
            alpha_ann = arr[:, :, 3] / 255.0
            
            if (frame_h, frame_w) != (h_ann, w_ann):
                bgr_ann = cv2.resize(bgr_ann, (frame_w, frame_h), interpolation=cv2.INTER_NEAREST)
                alpha_ann = cv2.resize(alpha_ann, (frame_w, frame_h), interpolation=cv2.INTER_NEAREST)

            alpha_ann = alpha_ann.astype(np.float32) 
            alpha_ann = cv2.cvtColor(alpha_ann, cv2.COLOR_GRAY2BGR) 
            
            # Terapkan ke frame
            return (source_frame * (1 - alpha_ann) + bgr_ann * alpha_ann).astype(np.uint8)
        # --- AKHIR FUNGSI HELPER ---

        # Terapkan Anotasi A (Player 1)
        annotation_image_a = self.media_player.annotations.get(self.media_player.current_frame_index)
        frame_a_orig = apply_annotation(frame_a_orig, annotation_image_a, h_a, w_a)

        # --- PERBAIKAN: Terapkan Anotasi B (Player 2) ---
        annotation_image_b = self.media_player_2.annotations.get(self.media_player_2.current_frame_index)
        frame_b_orig = apply_annotation(frame_b_orig, annotation_image_b, h_b, w_b)
        # --- AKHIR PERBAIKAN ---

        # Buat Placeholder JIKA DIPERLUKAN
        frame_a = frame_a_orig if frame_a_orig is not None else self.create_placeholder_frame("View A", w_a, h_a)
        frame_b = frame_b_orig if frame_b_orig is not None else self.create_placeholder_frame("View B", w_b, h_b)
        
        # Lanjutkan Penskalaan dan Penggabungan
        target_h = min(frame_a.shape[0], frame_b.shape[0])
        if target_h <= 0: 
            # Jika kedua frame tidak valid, coba tampilkan placeholder
            if frame_a_orig is None and frame_b_orig is None:
                self.media_player.display_frame(self.create_placeholder_frame("No Media", 640, 480))
            return
        
        new_w_a = int(frame_a.shape[1] * (target_h / frame_a.shape[0])) if frame_a.shape[0] > 0 else 0
        new_w_b = int(frame_b.shape[1] * (target_h / frame_b.shape[0])) if frame_b.shape[0] > 0 else 0
        
        frame_a_res = cv2.resize(frame_a, (new_w_a, target_h), interpolation=cv2.INTER_AREA) if new_w_a > 0 else np.zeros((target_h, 1, 3), dtype=np.uint8)
        frame_b_res = cv2.resize(frame_b, (new_w_b, target_h), interpolation=cv2.INTER_AREA) if new_w_b > 0 else np.zeros((target_h, 1, 3), dtype=np.uint8)
        
        self.media_player.set_compare_split(frame_a_res.shape[1], frame_b_res.shape[1])
        composite = cv2.hconcat([frame_a_res, frame_b_res])
        self.media_player.display_frame(composite)
        
    def update_playlist_item_indicator(self):
        path_a = self.media_player.get_current_file_path()
        path_b = self.media_player_2.get_current_file_path() if self.compare_mode else None
        
        # --- LOGIKA INDIKATOR SEGMEN BARU ---
        # Jika dalam mode segmen, tandai semua item di segmen
        segment_paths = set()
        if self.segment_map:
            for segment in self.segment_map:
                segment_paths.add(segment['path'])
        # --- AKHIR LOGIKA SEGMEN ---
        
        iterator = QTreeWidgetItemIterator(self.playlist_widget)
        while iterator.value():
            item = iterator.value()
            item_path = item.data(0, Qt.UserRole)
            if item_path:
                base_name = item.text(0)
                # Bersihkan indikator lama
                base_name = re.sub(r'\s\((A|B|A/B|S)\)$', '', base_name)
                
                indicator = ""
                is_a = (item_path == path_a)
                is_b = (self.compare_mode and item_path == path_b)
                
                if is_a and is_b: indicator = " (A/B)"
                elif is_a: indicator = " (A)"
                elif is_b: indicator = " (B)"
                elif item_path in segment_paths: # Tandai sebagai bagian dari segmen
                    indicator = " (S)"
                    
                item.setText(0, base_name + indicator)
            iterator += 1
            
    def update_fps_display(self, fps, indicator):
        if indicator == 'A': self.media_player_A_fps = fps
        elif indicator == 'B': self.media_player_B_fps = fps
        
        # Tampilkan FPS A jika tidak dalam mode compare
        if not self.compare_mode and indicator == 'A':
            # Jika mode segmen, FPS bisa ganti-ganti
            if self.segment_map:
                self.timeline.set_fps(fps) # Update timeline untuk timecode
            self.fps_label.setText(f"FPS: {self.media_player_A_fps:.2f}")
            
        elif self.compare_mode:
            if indicator == 'A': self.timeline.set_fps(fps)
            text_a = f"A: {self.media_player_A_fps:.2f} FPS"
            text_b = f"B: {self.media_player_B_fps:.2f} FPS"
            self.fps_label.setText(f"{text_a} | {text_b}")
            
    def go_to_first_frame(self):
        if self.media_player.is_playing or self.is_compare_playing:
            self.toggle_play()
        if self.media_player.drawing_enabled: self.set_drawing_off() 
        
        # seek_to_position(0) akan otomatis menangani mode segmen atau normal
        self.seek_to_position(0)
        
        if self.compare_mode:
            self.media_player.has_finished = False
            self.media_player_2.has_finished = False
        else:
            self.media_player.has_finished = False
    
    def go_to_last_frame(self):
        if self.is_compare_playing:
            self.compare_timer.stop()
            self.is_compare_playing = False
            self.controls.set_play_state(False)
        elif self.media_player.is_playing:
            self.media_player.toggle_play()
        if self.media_player.drawing_enabled: self.set_drawing_off() 
        
        # --- PERBAIKAN: Gunakan durasi global ---
        if self.compare_mode:
            total = max(self.media_player.total_frames, self.media_player_2.total_frames)
            if total > 0:
                self.seek_to_position(total - 1)
        elif self.segment_map:
            total = self.current_segment_total_frames
            if total > 0:
                self.seek_to_position(total - 1)
        else:
            total = self.media_player.total_frames
            if total > 0:
                self.seek_to_position(total - 1)
        # --- AKHIR PERBAIKAN ---

        # Tandai sebagai selesai (penting untuk logika 'play')
        self.media_player.has_finished = True
        if self.compare_mode:
             self.media_player_2.has_finished = True
        
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
        # --- PERBAIKAN UNTUK SHOW/HIDE ---
        if self.playlist_widget_container.isVisible():
            self.splitter_sizes = self.splitter.sizes()
            self.playlist_widget_container.setVisible(False)
            self.drawing_toolbar.setVisible(False) # <--- TAMBAHAN
        else:
            self.playlist_widget_container.setVisible(True)
            self.drawing_toolbar.setVisible(True) # <--- TAMBAHAN
            if self.splitter_sizes:
                self.splitter.setSizes(self.splitter_sizes)
        # --- AKHIR PERBAIKAN ---
