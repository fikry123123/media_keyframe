"""
Main Window untuk Studio Media Player.
Window utama yang mengintegrasikan semua komponen UI.
"""

import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QMenuBar, QAction, QFileDialog, QLabel, QSplitter,
                            QStatusBar, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QKeySequence, QPixmap

from .media_controls import MediaControls
from .timeline import Timeline
from src.media.player import MediaPlayer
from src.media.formats import MediaFormats


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.media_player = MediaPlayer()
        self.current_file = None
        self.setupUI()
        self.connectSignals()
        
    def setupUI(self):
        """Setup the user interface."""
        self.setWindowTitle("Studio Media Player")
        self.setMinimumSize(1200, 800)
        
        # Apply global dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d2d;
                color: #f0f0f0;
            }
            QWidget {
                background-color: #2d2d2d;
                color: #f0f0f0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QMenuBar {
                background-color: #383838;
                color: #f0f0f0;
                border-bottom: 1px solid #606060;
                padding: 2px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #505050;
            }
            QMenu {
                background-color: #383838;
                color: #f0f0f0;
                border: 1px solid #606060;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
            QSplitter::handle {
                background-color: #606060;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # Media display area with frame counter overlay
        media_container = QWidget()
        media_container_layout = QVBoxLayout(media_container)
        media_container_layout.setContentsMargins(0, 0, 0, 0)
        media_container_layout.setSpacing(0)
        
        # Frame counter overlay
        self.frame_counter_overlay = QLabel("")
        self.frame_counter_overlay.setAlignment(Qt.AlignTop | Qt.AlignRight)
        self.frame_counter_overlay.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: #ffffff;
                border: none;
                padding: 8px 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                margin: 10px;
            }
        """)
        self.frame_counter_overlay.hide()  # Initially hidden
        
        # Media display area
        self.media_display = QLabel("Load media file to start...")
        self.media_display.setAlignment(Qt.AlignCenter)
        self.media_display.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 2px dashed #606060;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 18px;
                font-weight: 500;
                min-height: 400px;
            }
        """)
        
        # Stack the overlay on top of media display
        media_container_layout.addWidget(self.media_display)
        self.frame_counter_overlay.setParent(self.media_display)
        
        splitter.addWidget(media_container)
        
        # Bottom panel for controls
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        
        # Timeline
        self.timeline = Timeline()
        bottom_layout.addWidget(self.timeline)
        
        # Media controls
        self.media_controls = MediaControls()
        bottom_layout.addWidget(self.media_controls)
        
        splitter.addWidget(bottom_panel)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 3)  # Media display gets more space
        splitter.setStretchFactor(1, 1)  # Controls get less space
        
        # Setup menu bar
        self.setupMenuBar()
        
        # Setup status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #383838;
                color: #f0f0f0;
                border-top: 1px solid #606060;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                padding: 4px;
            }
            QStatusBar::item {
                border: none;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Load a media file to start")
        
    def setupMenuBar(self):
        """Setup the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Open action
        open_action = QAction('Open...', self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip('Open media file')
        open_action.triggered.connect(self.openFile)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('Exit', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        # Fullscreen action
        fullscreen_action = QAction('Fullscreen', self)
        fullscreen_action.setShortcut(QKeySequence('F11'))
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self.toggleFullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        # About action
        about_action = QAction('About', self)
        about_action.triggered.connect(self.showAbout)
        help_menu.addAction(about_action)
        
    def connectSignals(self):
        """Connect signals between components."""
        # Media controls signals
        self.media_controls.playPauseClicked.connect(self.togglePlayback)
        self.media_controls.stopClicked.connect(self.stopPlayback)
        self.media_controls.previousFrameClicked.connect(self.previousFrame)
        self.media_controls.nextFrameClicked.connect(self.nextFrame)
        
        # Timeline signals
        self.timeline.positionChanged.connect(self.seekToPosition)
        
        # Media player signals
        self.media_player.frameReady.connect(self.updateDisplay)
        self.media_player.positionChanged.connect(self.updateTimeline)
        self.media_player.durationChanged.connect(self.setDuration)
        self.media_player.frameIndexChanged.connect(self.updateFrameCounter)
        
    def openFile(self):
        """Open media file dialog."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Open Media File",
            "",
            "Media Files (*.jpg *.jpeg *.png *.exr *.mov *.mp4 *.mp3);;"\
            "Images (*.jpg *.jpeg *.png *.exr);;"\
            "Videos (*.mov *.mp4);;"\
            "Audio (*.mp3);;"\
            "All Files (*)"
        )
        
        if file_path:
            self.loadFile(file_path)
            
    def loadFile(self, file_path):
        """Load media file."""
        try:
            if MediaFormats.isSupported(file_path):
                self.current_file = file_path
                self.media_player.loadFile(file_path)
                
                # Update window title
                filename = os.path.basename(file_path)
                self.setWindowTitle(f"Studio Media Player - {filename}")
                
                # Update status
                file_size = os.path.getsize(file_path)
                file_size_mb = file_size / (1024 * 1024)
                self.status_bar.showMessage(f"Loaded: {filename} ({file_size_mb:.1f} MB) - Ready for playback")
                
                # Enable controls
                self.media_controls.setEnabled(True)
                self.timeline.setEnabled(True)
                
            else:
                QMessageBox.warning(self, "Unsupported Format", 
                                  "The selected file format is not supported.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
            
    def togglePlayback(self):
        """Toggle play/pause."""
        if self.media_player.isPlaying():
            self.media_player.pause()
            self.media_controls.setPlayPauseIcon(False)
        else:
            self.media_player.play()
            self.media_controls.setPlayPauseIcon(True)
            
    def stopPlayback(self):
        """Stop playback."""
        self.media_player.stop()
        self.media_controls.setPlayPauseIcon(False)
        
    def previousFrame(self):
        """Go to previous frame."""
        self.media_player.previousFrame()
        
    def nextFrame(self):
        """Go to next frame."""
        self.media_player.nextFrame()
        
    def seekToPosition(self, position):
        """Seek to specific position."""
        self.media_player.seekToPosition(position)
        
    def updateDisplay(self, frame):
        """Update media display with new frame."""
        if frame is not None:
            pixmap = QPixmap.fromImage(frame)
            scaled_pixmap = pixmap.scaled(
                self.media_display.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.media_display.setPixmap(scaled_pixmap)
            # Show frame counter overlay when media is loaded
            self.frame_counter_overlay.show()
            
    def updateFrameCounter(self, current_frame, total_frames, fps=0):
        """Update frame counter overlay."""
        if total_frames > 1:
            # For videos and image sequences
            counter_text = f"Frame: {current_frame + 1} / {total_frames}"
            if fps > 0:
                counter_text += f"\nFPS: {fps:.1f}"
        else:
            # For single images
            counter_text = "Single Image"
            
        self.frame_counter_overlay.setText(counter_text)
        
        # Position the overlay in the top-right corner
        parent_rect = self.media_display.rect()
        overlay_size = self.frame_counter_overlay.sizeHint()
        x = parent_rect.width() - overlay_size.width() - 10
        y = 10
        self.frame_counter_overlay.move(x, y)
            
    def updateTimeline(self, position):
        """Update timeline position."""
        self.timeline.setPosition(position)
        
    def setDuration(self, duration):
        """Set media duration."""
        self.timeline.setDuration(duration)
        
    def toggleFullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def showAbout(self):
        """Show about dialog."""
        QMessageBox.about(self, "About Studio Media Player", 
                         "Studio Media Player v1.0\n\n"
                         "Professional media player for studio use.\n"
                         "Supports frame-by-frame playback and multiple formats.")
                         
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key_Space:
            self.togglePlayback()
        elif event.key() == Qt.Key_Left:
            self.previousFrame()
        elif event.key() == Qt.Key_Right:
            self.nextFrame()
        elif event.key() == Qt.Key_Home:
            self.seekToPosition(0)
        elif event.key() == Qt.Key_End:
            if hasattr(self.media_player, 'duration'):
                self.seekToPosition(self.media_player.duration)
        else:
            super().keyPressEvent(event)
            
    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)
        # Update display if there's a current frame
        if hasattr(self.media_player, 'current_frame') and self.media_player.current_frame:
            self.updateDisplay(self.media_player.current_frame)
        # Reposition frame counter overlay
        if self.frame_counter_overlay.isVisible():
            parent_rect = self.media_display.rect()
            overlay_size = self.frame_counter_overlay.sizeHint()
            x = parent_rect.width() - overlay_size.width() - 10
            y = 10
            self.frame_counter_overlay.move(x, y)
