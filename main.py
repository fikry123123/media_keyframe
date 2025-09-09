# Studio Media Player Application

"""
Entry point untuk aplikasi Studio Media Player.
Aplikasi ini dibuat untuk kebutuhan studio profesional dengan dukungan
berbagai format media dan kemampuan frame-by-frame playback.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.main_window import MainWindow


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Studio Media Player")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Studio Tools")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
