from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon

class DrawingToolbar(QWidget):
    """
    Toolbar vertikal yang dapat diciutkan untuk alat menggambar.
    """
    drawModeToggled = pyqtSignal(bool)
    eraseModeToggled = pyqtSignal(bool)
    colorButtonClicked = pyqtSignal()
    clearFrameDrawingClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(6) 
        self.main_layout.setAlignment(Qt.AlignTop) 

        # --- PERBAIKAN: Toolbar DIBUAT LEBIH RAMPING ---
        self.setFixedWidth(40) # <-- NAIK DARI 46 ke 40
        # --- AKHIR PERBAIKAN ---
        
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-right: 1px solid #444444;
            }
        """)

        # --- PERBAIKAN: Tombol diperkecil ---
        button_style = """
            QPushButton {
                background-color: #444444;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 6px;
                font-size: 14px; 
                font-weight: bold;
                min-width: 26px;
                min-height: 26px;
            }
            QPushButton:hover {
                background-color: #555555;
                border-color: #888888;
            }
            QPushButton:pressed {
                background-color: #333333;
                border-color: #999999;
            }
            QPushButton:checkable:checked {
                background-color: #a13d00; 
                border-color: #c45a1b;
                color: white;
            }
        """ 
        # --- AKHIR PERBAIKAN ---
        
        self.tool_button_style = button_style + """
            QPushButton:checkable:checked {
                background-color: #0078d4; 
                border-color: #005a9e;
                color: white;
            }
        """

        self.master_toggle_button = QPushButton("✏️") 
        self.master_toggle_button.setStyleSheet(button_style)
        self.master_toggle_button.setToolTip("Show/Hide Drawing Tools")
        self.master_toggle_button.setCheckable(True)
        self.main_layout.addWidget(self.master_toggle_button)

        self.tools_container = QWidget()
        tools_layout = QVBoxLayout(self.tools_container)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(6) 

        self.pen_button = QPushButton("🖊️") 
        self.pen_button.setStyleSheet(self.tool_button_style)
        self.pen_button.setToolTip("Activate Draw Mode (Pen)")
        self.pen_button.setCheckable(True)
        tools_layout.addWidget(self.pen_button)

        self.erase_button = QPushButton("🧹")
        self.erase_button.setStyleSheet(self.tool_button_style)
        self.erase_button.setToolTip("Activate Erase Mode")
        self.erase_button.setCheckable(True)
        tools_layout.addWidget(self.erase_button)

        self.line_sep = QFrame()
        self.line_sep.setFrameShape(QFrame.HLine)
        self.line_sep.setFrameShadow(QFrame.Sunken)
        self.line_sep.setStyleSheet("QFrame { color: #555555; }")
        tools_layout.addWidget(self.line_sep)

        self.color_button = QPushButton("🎨")
        self.color_button.setStyleSheet(button_style)
        self.color_button.setToolTip("Select Draw Color")
        tools_layout.addWidget(self.color_button)

        self.clear_drawing_button = QPushButton("❌")
        self.clear_drawing_button.setStyleSheet(button_style)
        self.clear_drawing_button.setToolTip("Clear Drawing on Current Frame")
        tools_layout.addWidget(self.clear_drawing_button)
        
        self.main_layout.addWidget(self.tools_container)
        self.tools_container.setVisible(False) 
        
        self.main_layout.addStretch() 

        self.master_toggle_button.toggled.connect(self._on_master_toggle)
        self.pen_button.clicked.connect(self._on_pen_selected)
        self.erase_button.clicked.connect(self._on_erase_selected)
        self.color_button.clicked.connect(self.colorButtonClicked)
        self.clear_drawing_button.clicked.connect(self.clearFrameDrawingClicked)

    def _on_master_toggle(self, checked):
        """Dipanggil saat tombol master (✏️) ditekan."""
        self.tools_container.setVisible(checked)
        
        if checked:
            if not self.pen_button.isChecked() and not self.erase_button.isChecked():
                 self.pen_button.setChecked(True) 
                 self.erase_button.setChecked(False)
                 self.drawModeToggled.emit(True)
                 self.eraseModeToggled.emit(False)
            elif self.pen_button.isChecked():
                 self.erase_button.setChecked(False)
                 self.drawModeToggled.emit(True)
                 self.eraseModeToggled.emit(False)
            else: # Erase yang aktif
                 self.pen_button.setChecked(False)
                 self.drawModeToggled.emit(False)
                 self.eraseModeToggled.emit(True)

        else:
            self.drawModeToggled.emit(False) 
            self.eraseModeToggled.emit(False)

    def _on_pen_selected(self):
        """Dipanggil saat tombol alat Pena (🖊️) ditekan."""
        if self.erase_button.isChecked():
            self.erase_button.setChecked(False)
        
        if not self.pen_button.isChecked():
            self.pen_button.setChecked(True) 

        self.drawModeToggled.emit(True)
        self.eraseModeToggled.emit(False) 


    def _on_erase_selected(self):
        """Dipanggil saat tombol alat Hapus (🧹) ditekan."""
        if self.pen_button.isChecked():
            self.pen_button.setChecked(False)

        if not self.erase_button.isChecked():
             self.erase_button.setChecked(True)

        self.eraseModeToggled.emit(True)
        self.drawModeToggled.emit(False) 


    def force_close(self):
        """Metode eksternal untuk menutup toolbar (misal saat play)."""
        if self.master_toggle_button.isChecked():
            self.master_toggle_button.setChecked(False) # Ini akan memicu _on_master_toggle(False)

    def set_draw_color_indicator(self, color):
        """Memperbarui latar belakang tombol warna untuk menunjukkan warna yang dipilih."""
        if not color.isValid():
            self.color_button.setStyleSheet(self.clear_drawing_button.styleSheet())
            self.color_button.setText("🎨")
            return

        text_color = 'black' if color.lightness() > 127 else 'white'
        
        # --- PERBAIKAN: Style tombol warna juga diperkecil ---
        style = f"""
            QPushButton {{
                background-color: {color.name()};
                color: {text_color};
                border: 1px solid #AAAAAA;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 26px;
                min-height: 26px;
            }}
            QPushButton:hover {{ background-color: {color.lighter(120).name()}; }}
            QPushButton:pressed {{ background-color: {color.darker(120).name()}; }}
        """
        # --- AKHIR PERBAIKAN ---
        
        self.color_button.setStyleSheet(style)
        self.color_button.setText("🎨")