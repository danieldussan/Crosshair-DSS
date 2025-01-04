from PyQt5.QtWidgets import (QApplication, QLabel, QInputDialog, QColorDialog, QMenu, QSystemTrayIcon, 
                            QAction, QSpinBox, QDialog, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel as QTextLabel, QStyle)
from PyQt5.QtCore import Qt, QStandardPaths
from PyQt5.QtGui import QPainter, QColor, QIcon

import sys
import json
import os

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class CrosshairSettingsDialog(QDialog):
    def __init__(self, current_size, current_thickness, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajustes de la Mira")
        layout = QVBoxLayout()
        
        # Spinbox para el tamaño
        size_layout = QHBoxLayout()
        size_layout.addWidget(QTextLabel("Tamaño:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(4, 50)
        self.size_spin.setValue(current_size)
        size_layout.addWidget(self.size_spin)
        layout.addLayout(size_layout)
        
        # Spinbox para el grosor
        thickness_layout = QHBoxLayout()
        thickness_layout.addWidget(QTextLabel("Grosor:"))
        self.thickness_spin = QSpinBox()
        self.thickness_spin.setRange(1, 5)
        self.thickness_spin.setValue(current_thickness)
        thickness_layout.addWidget(self.thickness_spin)
        layout.addLayout(thickness_layout)
        
        # Botones
        buttons = QHBoxLayout()
        ok_button = QPushButton("Aceptar")
        cancel_button = QPushButton("Cancelar")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        
        self.setLayout(layout)

class CrosshairApp(QLabel):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Configurar rutas
        self.documents_path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        self.config_folder = os.path.join(self.documents_path, "Crosshair Config")
        self.config_file = os.path.join(self.config_folder, "config.json")
        
        # Cargar configuración
        self.load_config()
        
        # Configurar el icono de la bandeja
        self.setup_tray_icon()
        
        # Posicionar en el centro
        self.move_to_center()

    def load_config(self):
        default_config = {
            "color": "#FF0000",
            "size": 16,
            "style": "cruz",
            "thickness": 1
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.color = QColor(config.get("color", default_config["color"]))
                    self.crosshair_size = config.get("size", default_config["size"])
                    self.crosshair_style = config.get("style", default_config["style"])
                    self.line_thickness = config.get("thickness", default_config["thickness"])
            else:
                self.color = QColor(default_config["color"])
                self.crosshair_size = default_config["size"]
                self.crosshair_style = default_config["style"]
                self.line_thickness = default_config["thickness"]
        except:
            self.color = QColor(default_config["color"])
            self.crosshair_size = default_config["size"]
            self.crosshair_style = default_config["style"]
            self.line_thickness = default_config["thickness"]
        
        self.setFixedSize(self.crosshair_size, self.crosshair_size)
        self.move_to_center()
        self.is_visible = True

    def save_config(self):
        if not os.path.exists(self.config_folder):
            os.makedirs(self.config_folder)
        config = {
            "color": self.color.name(),
            "size": self.crosshair_size,
            "style": self.crosshair_style,
            "thickness": self.line_thickness
        }
        with open(self.config_file, "w") as f:
            json.dump(config, f)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Usar resource_path para obtener la ruta correcta del icono
        icon_path = resource_path("public/icono-bandeja.png")
        if not os.path.exists(icon_path):
            # Fallback a un icono incorporado si no se encuentra el archivo
            self.tray_icon.setIcon(QIcon(self.style().standardIcon(QStyle.SP_ComputerIcon)))
        else:
            self.tray_icon.setIcon(QIcon(icon_path))
        
        self.tray_icon.setToolTip('Crosshair App')
        
        menu = QMenu()
        
        settings_action = QAction("Ajustes de Mira", self)
        settings_action.triggered.connect(self.show_settings)
        
        change_color_action = QAction("Cambiar Color", self)
        change_color_action.triggered.connect(self.change_color)
        
        style_menu = QMenu("Estilo de Mira", self)
        
        cruz_action = QAction("Cruz (+)", self)
        cruz_action.triggered.connect(lambda: self.change_style("cruz"))
        
        punto_action = QAction("Punto", self)
        punto_action.triggered.connect(lambda: self.change_style("punto"))
        
        style_menu.addAction(cruz_action)
        style_menu.addAction(punto_action)

        center_action = QAction("Centrar Mira", self)
        center_action.triggered.connect(self.center_crosshair)
        
        custom_position_action = QAction("Posición Personalizada", self)
        custom_position_action.triggered.connect(self.set_custom_position)
        
        self.toggle_visibility_action = QAction("Ocultar Crosshair", self)
        self.toggle_visibility_action.triggered.connect(self.toggle_visibility)
        
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.exit_app)
        
        menu.addAction(settings_action)
        menu.addAction(change_color_action)
        menu.addMenu(style_menu)
        menu.addAction(center_action)
        menu.addAction(custom_position_action)
        menu.addAction(self.toggle_visibility_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def center_crosshair(self):
        """Centra la mira en la pantalla."""
        self.move_to_center()

    def set_custom_position(self):
        """Abre un diálogo para establecer una posición personalizada."""
        current_pos = self.pos()
        current_x = current_pos.x()
        current_y = current_pos.y()

        # Obtener el tamaño de la pantalla para evitar posiciones fuera de ella
        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # Establecer límites según la pantalla
        max_x = screen_width - self.width()
        max_y = screen_height - self.height()
        
        # Mostrar la posición actual como valores predeterminados en el cuadro de entrada
        x, ok_x = QInputDialog.getInt(self, "Posición X", "Introduce la posición X:", current_x, 0, max_x, 1)
        y, ok_y = QInputDialog.getInt(self, "Posición Y", "Introduce la posición Y:", current_y, 0, max_y, 1)
        
        if ok_x and ok_y:
            self.move(x, y)  # Mover la mira a la posición personalizada

    def move_to_center(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.crosshair_style == "cruz":
            # Configurar el pincel para las líneas
            pen = painter.pen()
            pen.setColor(self.color)
            pen.setWidth(self.line_thickness)
            painter.setPen(pen)
            
            # Calcular las dimensiones
            center_x = self.width() // 2
            center_y = self.height() // 2
            length = self.width() // 3
            
            # Dibujar líneas centradas
            # Línea vertical
            painter.drawLine(center_x, center_y - length, 
                           center_x, center_y + length)
            # Línea horizontal
            painter.drawLine(center_x - length, center_y,
                           center_x + length, center_y)
            
        else:  # punto
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.color)
            radius = min(self.width(), self.height()) // 4
            center_x = self.width() // 2
            center_y = self.height() // 2
            painter.drawEllipse(center_x - radius, center_y - radius, 
                              radius * 2, radius * 2)

    def show_settings(self):
        dialog = CrosshairSettingsDialog(self.crosshair_size, self.line_thickness, self)
        if dialog.exec_() == QDialog.Accepted:
            self.crosshair_size = dialog.size_spin.value()
            self.line_thickness = dialog.thickness_spin.value()
            self.setFixedSize(self.crosshair_size, self.crosshair_size)
            self.move_to_center()
            self.update()
            self.save_config()

    def change_color(self):
        color = QColorDialog.getColor(self.color)
        if color.isValid():
            self.color = color
            self.update()
            self.save_config()

    def change_style(self, style):
        self.crosshair_style = style
        self.update()
        self.save_config()

    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.setVisible(self.is_visible)
        self.toggle_visibility_action.setText(
            "Mostrar Crosshair" if not self.is_visible else "Ocultar Crosshair"
        )

    def exit_app(self):
        """Asegurarse de limpiar el ícono de la bandeja antes de salir"""
        self.tray_icon.hide()
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Crosshair App")
    app.setQuitOnLastWindowClosed(False)
    
    # Usar resource_path para el ícono de la aplicación
    icon_path = resource_path("public/icono.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    crosshair = CrosshairApp()
    crosshair.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()