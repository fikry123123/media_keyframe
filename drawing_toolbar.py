from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, 
                             QSlider, QLabel, QButtonGroup, QApplication) # <-- 1. IMPORT TAMBAHAN
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt5.QtGui import QIcon, QFocusEvent, QWheelEvent

# --- WIDGET POP-UP (Kita letakkan di file yang sama agar mudah) ---
class SizeSliderPopup(QFrame):
    """
    Widget pop-up yang berisi slider horizontal untuk mengatur ukuran.
    Akan otomatis tertutup saat kehilangan fokus.
    """
    sizeChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QFrame {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QLabel {
                color: #dddddd;
                font-size: 11px;
                border: none;
                background-color: transparent;
            }
        """)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 4, 8, 4)
        self.layout.setSpacing(6)
        
        self.label = QLabel("5px")
        self.label.setMinimumWidth(35) 
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimumWidth(120)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #444444; height: 6px; border-radius: 3px; margin: 4px 0;
            }
            QSlider::handle:horizontal {
                background: #0078d4; border: 1px solid #005a9e;
                width: 14px; margin: -4px 0; border-radius: 7px;
            }
        """)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.slider)
        self.slider.valueChanged.connect(self._on_slider_moved)

    def set_config(self, min_val, max_val, current_val):
        self.slider.blockSignals(True)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(current_val)
        self.label.setText(f"{current_val}px")
        self.slider.blockSignals(False)

    def set_value_blocked(self, value):
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.label.setText(f"{value}px")
        self.slider.blockSignals(False)

    def _on_slider_moved(self, value):
        self.label.setText(f"{value}px")
        self.sizeChanged.emit(value) 

    # --- 2. PERBAIKAN LOGIKA FOKUS ---
    def focusOutEvent(self, event: QFocusEvent):
        """
        Otomatis sembunyikan (hide) saat pop-up kehilangan fokus,
        KECUALI jika fokus pindah ke child widget (slider).
        """
        # Cek siapa yang mendapatkan fokus
        new_focus_widget = QApplication.focusWidget()
        
        # Jika widget baru BUKAN bagian dari pop-up ini (self)
        # atau BUKAN turunan (child) dari pop-up ini...
        if new_focus_widget is not self and not self.isAncestorOf(new_focus_widget):
            # ...maka kita benar-benar kehilangan fokus. Sembunyikan.
            self.hide()
        
        # Jika fokus pindah ke slider, jangan lakukan apa-apa.
        super().focusOutEvent(event)
    # --- AKHIR PERBAIKAN ---
# --- AKHIR WIDGET POP-UP ---


class DrawingToolbar(QWidget):
    """
    Toolbar vertikal (Master Toggle) yang berisi tombol pop-up ukuran
    dan merespons scroll wheel.
    """
    drawModeToggled = pyqtSignal(bool)
    eraseModeToggled = pyqtSignal(bool)
    colorButtonClicked = pyqtSignal()
    clearFrameDrawingClicked = pyqtSignal()
    sizeChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_min = 1
        self.current_max = 200
        self.current_val = 5

        self.size_popup = SizeSliderPopup(self)
        self.size_popup.hide()
        
        self.setup_ui()
        
        self.size_popup.sizeChanged.connect(self.sizeChanged)

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(6) 
        self.main_layout.setAlignment(Qt.AlignTop) 

        self.setFixedWidth(40) 
        
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; border-right: 1px solid #444444; }
        """)

        button_style = """
            QPushButton {
                background-color: #444444; color: #ffffff; border: 1px solid #666666;
                border-radius: 6px; font-size: 14px; font-weight: bold;
                min-width: 26px; min-height: 26px;
            }
            QPushButton:hover { background-color: #555555; border-color: #888888; }
            QPushButton:pressed { background-color: #333333; border-color: #999999; }
            QPushButton:checkable:checked {
                background-color: #a13d00; border-color: #c45a1b; color: white;
            }
        """ 
        
        self.tool_button_style = button_style + """
            QPushButton:checkable:checked {
                background-color: #0078d4; border-color: #005a9e; color: white;
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
        self.pen_button.setToolTip("Activate Draw Mode (Pen)\n(Scroll to change size)")
        self.pen_button.setCheckable(True)
        tools_layout.addWidget(self.pen_button)

        self.erase_button = QPushButton("🧹")
        self.erase_button.setStyleSheet(self.tool_button_style)
        self.erase_button.setToolTip("Activate Erase Mode\n(Scroll to change size)")
        self.erase_button.setCheckable(True)
        tools_layout.addWidget(self.erase_button)
        
        self.tool_button_group = QButtonGroup(self)
        self.tool_button_group.addButton(self.pen_button)
        self.tool_button_group.addButton(self.erase_button)
        self.tool_button_group.setExclusive(True)

        self.size_button = QPushButton("📏")
        self.size_button.setStyleSheet(button_style) 
        self.size_button.setToolTip("Adjust Pen/Eraser Size (Click)")
        tools_layout.addWidget(self.size_button)

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
        self.pen_button.toggled.connect(self._on_pen_toggled)
        self.erase_button.toggled.connect(self._on_erase_toggled)
        self.color_button.clicked.connect(self.colorButtonClicked)
        self.clear_drawing_button.clicked.connect(self.clearFrameDrawingClicked)
        self.size_button.clicked.connect(self._show_size_popup)


    def _on_master_toggle(self, checked):
        self.tools_container.setVisible(checked)
        if checked:
            if not self.pen_button.isChecked() and not self.erase_button.isChecked():
                self.pen_button.setChecked(True)
            elif self.pen_button.isChecked():
                self.drawModeToggled.emit(True)
            elif self.erase_button.isChecked():
                self.eraseModeToggled.emit(True)
        else:
            self.drawModeToggled.emit(False) 
            self.eraseModeToggled.emit(False)
            self.size_popup.hide() 

    def _on_pen_toggled(self, checked):
        if checked:
            self.drawModeToggled.emit(True)
            self.eraseModeToggled.emit(False)

    def _on_erase_toggled(self, checked):
        if checked:
            self.drawModeToggled.emit(False)
            self.eraseModeToggled.emit(True)

    def _show_size_popup(self):
        self.size_popup.set_config(self.current_min, self.current_max, self.current_val)
        button_global_pos = self.size_button.mapToGlobal(QPoint(0, 0))
        popup_pos = QPoint(button_global_pos.x() + self.width() + 5, 
                           button_global_pos.y())
        self.size_popup.move(popup_pos)
        self.size_popup.show()
        self.size_popup.raise_()
        self.size_popup.setFocus()

    def force_close(self):
        if self.master_toggle_button.isChecked():
            self.master_toggle_button.setChecked(False) 
        
        self.pen_button.blockSignals(True)
        self.erase_button.blockSignals(True)
        self.tool_button_group.setExclusive(False) 
        self.pen_button.setChecked(False)
        self.erase_button.setChecked(False)
        self.tool_button_group.setExclusive(True) 
        self.pen_button.blockSignals(False)
        self.erase_button.blockSignals(False)
        
        self.size_popup.hide() 

    def set_draw_color_indicator(self, color):
        if not color.isValid():
            self.color_button.setStyleSheet(self.clear_drawing_button.styleSheet())
            self.color_button.setText("🎨")
            return
        text_color = 'black' if color.lightness() > 127 else 'white'
        style = f"""
            QPushButton {{
                background-color: {color.name()}; color: {text_color};
                border: 1px solid #AAAAAA; border-radius: 6px;
                font-size: 14px; font-weight: bold;
                min-width: 26px; min-height: 26px;
            }}
            QPushButton:hover {{ background-color: {color.lighter(120).name()}; }}
            QPushButton:pressed {{ background-color: {color.darker(120).name()}; }}
        """
        self.color_button.setStyleSheet(style)
        self.color_button.setText("🎨")
        
    def set_size_range(self, min_val, max_val):
        self.current_min = min_val
        self.current_max = max_val
        
    def set_size_value(self, value):
        self.current_val = value
        if self.size_popup.isVisible():
            self.size_popup.set_value_blocked(value)

    def handle_slider_change(self, value):
        pass
        
    def wheelEvent(self, event: QWheelEvent):
        if not self.tools_container.isVisible():
            event.ignore() 
            return
            
        delta = event.angleDelta().y() / 120
        if delta == 0:
            event.accept()
            return
            
        new_size = self.current_val
        
        if self.pen_button.isChecked():
            step = 2 
            if delta > 0:
                new_size = self.current_val + step
            else:
                new_size = self.current_val - step
            new_size = max(self.current_min, min(new_size, self.current_max))
            
        elif self.erase_button.isChecked():
            step = 5 
            if delta > 0:
                new_size = self.current_val + step
            else:
                new_size = self.current_val - step
            new_size = max(self.current_min, min(new_size, self.current_max))

        if new_size != self.current_val:
            self.sizeChanged.emit(new_size)
            
        event.accept()