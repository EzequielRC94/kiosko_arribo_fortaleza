import sys
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from catalogos import CATALOGO_PLANTAS # Importamos tu catálogo central[cite: 8]

class DialogoSeleccionPlanta(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración de Ubicación")
        self.resize(600, 500)
        self.setStyleSheet("background-color: #f0f0f0;")
        
        # Variables para guardar la selección
        self.nombre_planta = ""
        self.codigos_planta = []
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)

        lbl_titulo = QLabel("OPERADOR SELECCIONE UBICACIÓN")
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
            # Usamos lambda para pasar el nombre y códigos específicos al hacer clic
            btn.clicked.connect(lambda checked, n=nombre_planta, c=codigos: self.confirmar_seleccion(n, c))
            layout.addWidget(btn)

    def confirmar_seleccion(self, nombre, codigos):
        """Guarda los datos y cierra el diálogo con éxito"""
        self.nombre_planta = nombre
        self.codigos_planta = codigos
        self.accept() # QDialog.Accepted