# gui_selector_planta.py
import os
from datetime import datetime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from catalogos import CATALOGO_PLANTAS
from session_data import SessionData

class DialogoSeleccionPlanta(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración de Ubicación")
        self.resize(600, 500)
        self.setStyleSheet("background-color: #f0f0f0;")
        
        self.session_configurada = None
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)

        lbl_titulo = QLabel("SELECCIONE UBICACIÓN")
        lbl_titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)

        for nombre_planta, codigos in CATALOGO_PLANTAS.items():
            btn = QPushButton(nombre_planta)
            btn.setFont(QFont("Arial", 14))
            btn.setFixedHeight(60)
            btn.setStyleSheet("""
                QPushButton { background-color: #008080; color: white; border-radius: 8px; }
                QPushButton:hover { background-color: #006666; }
            """)
            btn.clicked.connect(lambda checked, n=nombre_planta, c=codigos: self.confirmar_seleccion(n, c))
            layout.addWidget(btn)

    def confirmar_seleccion(self, nombre, codigos):
        """Prepara el SessionData y calcula la ruta base antes de cerrar el diálogo."""
        # 1. Crear el SessionData centralizado
        session_data = SessionData()
        session_data.planta_gui_nombre = nombre
        session_data.planta_gui_codigos = codigos
        
        # 2. Calcular la ruta dinámica
        user_profile = os.path.expanduser("~")
        """
        carpetas_plantas = {
            "Planta Tula": "Cementos Tula Embarques - Documentos",
            "Planta Palmar": "Cementos Palmar Embarques - Documentos",
            "Planta Vito": "Cementos Vito Embarques - Documentos",
            "Planta Progreso": "Cementos Progreso Embarques - Documentos",
            "CEDIS GDL": "CEDIS GDL Embarques - Documentos" 
        }
        carpeta_planta = carpetas_plantas.get(nombre, "Documentos Kiosko")
        """
        anio_actual = datetime.now().strftime("%Y")
        
        ruta_calculada = os.path.join(
            user_profile, 
            "Elementia S. A", 
            "kiosko logistica cem - Documentos", 
            anio_actual
        )
        
        # 3. Guardar en SessionData y cerrar
        session_data.ruta_base_drive = ruta_calculada
        self.session_configurada = session_data
        self.accept()

def obtener_configuracion_inicial():
    """Función helper para llamar al diálogo desde cualquier archivo"""
    dialogo = DialogoSeleccionPlanta()
    if dialogo.exec_() == QDialog.Accepted:
        return dialogo.session_configurada
    return None