#!/usr/bin/env python3
"""
Studio Media Player - Image Sequence Viewer
A PyQt5-based media player optimized for viewing image sequences and video files.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_window import MainWindow


def main():
    """Main application entry point"""
    # Enable high DPI scaling before creating QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("kenae Media Player")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("kenae Media Tools")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
