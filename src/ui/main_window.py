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
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # Media display area
        self.media_display = QLabel("Load media file to start...")
        self.media_display.setAlignment(Qt.AlignCenter)
        self.media_display.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 2px dashed #555555;
                font-size: 16px;
                min-height: 400px;
            }
        """)
        splitter.addWidget(self.media_display)
        
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
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
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
                self.status_bar.showMessage(f"Loaded: {filename}")
                
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
