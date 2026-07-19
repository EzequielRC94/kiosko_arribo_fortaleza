#gui_tablero.py
import sys
import json
import random
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt, QTimer
from catalogos import CATALOGO_PLANTAS

# ==============================================================================
# V0: VENTANA DE SELECCIÓN DE PLANTA

class VentanaSeleccionPlanta(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración de Tablero")
        self.resize(600, 500)
        self.setStyleSheet("background-color: #f0f0f0;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)

        lbl_titulo = QLabel("SELECCIONE LA PLANTA\nPARA ESTE TABLERO")
        lbl_titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setStyleSheet("color: #333333; margin-bottom: 20px;")
        layout.addWidget(lbl_titulo)

        for nombre_planta, codigos in CATALOGO_PLANTAS.items():
            btn = QPushButton(f"{nombre_planta}")
            btn.setFont(QFont("Arial", 14))
            btn.setFixedHeight(60)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("codigos", codigos) 
            btn.setProperty("nombre", nombre_planta)
            
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #008080; 
                    color: white; 
                    border-radius: 8px;
                    border: 2px solid #006666;
                }
                QPushButton:hover {
                    background-color: #006666;
                }
            """)
            
            btn.clicked.connect(self.abrir_tablero)
            layout.addWidget(btn)
        layout.addStretch()

    def abrir_tablero(self):
        sender = self.sender()
        codigos = sender.property("codigos")
        nombre_planta = sender.property("nombre")
        self.ventana_tablero = TableroTurnos(nombre_planta, codigos)
        self.ventana_tablero.show()
        self.close()

# ==============================================================================
# V1: TABLERO DE TURNOS (DASHBOARD)

class TableroTurnos(QMainWindow):
    def __init__(self, nombre_planta, codigos_sap):
        super().__init__()
        self.nombre_planta = nombre_planta
        self.codigos_sap = codigos_sap
        
        # --- ESTADO INTERNO ---
        self.categorias = ["GRANEL", "ENVASADO", "BIG BAG"] # Las 3 vistas
        self.indice_categoria_actual = 0                    # Empezamos en Granel
        self.ultimo_json_recibido = []                      # Almacén de datos crudos
        
        # Configuración Ventana
        self.setWindowTitle(f"Monitor de Turnos - {nombre_planta}")
        self.showMaximized()
        self.setStyleSheet("background-color: #F4F7F6;")

        # Widget Central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # ------------------------------------------------------------------
        # SECCIÓN 1: ENCABEZADO
        # ------------------------------------------------------------------
        self.frame_top = QFrame()
        self.frame_top.setStyleSheet("background-color: white; border-radius: 15px; border: 1px solid #dcdcdc;")
        top_layout = QVBoxLayout(self.frame_top)
        
        # 1.1 Título Grande (Dinámico) + Info Planta
        header_h_layout = QHBoxLayout()
        
        self.lbl_categoria = QLabel("CARGANDO...") # Texto inicial
        self.lbl_categoria.setFont(QFont("Arial Black", 48, QFont.Weight.Bold))
        self.lbl_categoria.setStyleSheet("color: #2C3E50; border: none;")
        
        self.lbl_planta_info = QLabel(f"{self.nombre_planta}\n--:--")
        self.lbl_planta_info.setFont(QFont("Arial", 20))
        self.lbl_planta_info.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_planta_info.setStyleSheet("color: gray; border: none;")
        
        header_h_layout.addWidget(self.lbl_categoria)
        header_h_layout.addWidget(self.lbl_planta_info)
        top_layout.addLayout(header_h_layout)

        # 1.2 Estadísticas (Cards)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(40)
        self.lbl_card_espera = self._crear_card_info("🚛 EN ESPERA", "0", "#3498DB")
        self.lbl_card_promedio = self._crear_card_info("⏱️ TIEMPO PROM x Unidad", "-- min", "#27AE60")
        stats_layout.addWidget(self.lbl_card_espera)
        stats_layout.addWidget(self.lbl_card_promedio)
        top_layout.addLayout(stats_layout)

        # ------------------------------------------------------------------
        # SECCIÓN 2: TABLA
        # ------------------------------------------------------------------
        self.tabla_turnos = QTableWidget()
        self.configurar_tabla()

        self.main_layout.addWidget(self.frame_top, stretch=1)
        self.main_layout.addWidget(self.tabla_turnos, stretch=3)

        # ------------------------------------------------------------------
        # TIMERS
        # ------------------------------------------------------------------
        # 1. Reloj (1 seg)
        self.timer_reloj = QTimer()
        self.timer_reloj.timeout.connect(lambda: self.lbl_planta_info.setText(f"{self.nombre_planta}\n{datetime.now().strftime('%H:%M')}"))
        self.timer_reloj.start(1000)

        # 2. Datos Backend (20 seg)
        self.timer_datos = QTimer()
        self.timer_datos.timeout.connect(self._mock_backend_data)
        self.timer_datos.start(20000) 

        # 3. Rotación de Vista (Carrusel - 10 seg)
        # Cambia entre Granel -> Envasado -> Big Bag
        self.timer_rotacion = QTimer()
        self.timer_rotacion.timeout.connect(self.rotar_vista)
        self.timer_rotacion.start(10000) 

        # Carga inicial
        self._mock_backend_data()

    def _crear_card_info(self, titulo, valor_inicial, color_borde):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: #FAFAFA; border-left: 10px solid {color_borde}; border-radius: 5px;")
        v_layout = QVBoxLayout(frame)
        lbl_tit = QLabel(titulo)
        lbl_tit.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_tit.setStyleSheet("color: #7F8C8D; border: none;")
        lbl_val = QLabel(valor_inicial)
        lbl_val.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        lbl_val.setStyleSheet("color: #2C3E50; border: none;")
        lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        v_layout.addWidget(lbl_tit)
        v_layout.addWidget(lbl_val)
        return frame

    def configurar_tabla(self):
        columnas = ["ESTATUS", "TURNO", "MATERIAL", "PLACA", "NOMBRE OP", "ETA CARGA"]
        self.tabla_turnos.setColumnCount(len(columnas))
        self.tabla_turnos.setHorizontalHeaderLabels(columnas)
        self.tabla_turnos.setStyleSheet("""
            QTableWidget { background-color: white; gridline-color: #ecf0f1; font-size: 18px; border: 1px solid #dcdcdc; border-radius: 10px; }
            QHeaderView::section { background-color: #2C3E50; color: white; font-size: 18px; font-weight: bold; padding: 12px; border: none; }
            QTableWidget::item { padding: 8px; }
        """)
        self.tabla_turnos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_turnos.verticalHeader().setVisible(False)
        self.tabla_turnos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_turnos.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

# ==========================================================================
# LÓGICA DE ROTACIÓN Y FILTRADO
    
    def rotar_vista(self):
        """Avanza a la siguiente categoría y actualiza la tabla."""
        self.indice_categoria_actual = (self.indice_categoria_actual + 1) % len(self.categorias)
        self.actualizar_vista()

    def actualizar_vista(self):
        """Filtra los datos guardados según la categoría actual y repinta la tabla."""
        categoria_actual = self.categorias[self.indice_categoria_actual]
        
        # 1. Actualizar Título
        self.lbl_categoria.setText(categoria_actual)
        
        # Colores distintivos para el título según categoría (Opcional, ayuda visual)
        if categoria_actual == "GRANEL":
            self.lbl_categoria.setStyleSheet("color: #E67E22; border: none;") # Naranja
        elif categoria_actual == "ENVASADO":
            self.lbl_categoria.setStyleSheet("color: #2980B9; border: none;") # Azul
        elif categoria_actual == "BIG BAG":
            self.lbl_categoria.setStyleSheet("color: #8E44AD; border: none;") # Morado

        # 2. Filtrar Datos
        datos_filtrados = []
        
        for fila in self.ultimo_json_recibido:
            # Obtenemos campos clave para filtrar
            grupo = fila.get("grupo", "").upper()
            material_desc = fila.get("material", "").upper() # desc_nom_corto
            
            agregar = False
            
            # --- REGLAS DE NEGOCIO ---
            if categoria_actual == "GRANEL":
                if grupo == "GRANEL":
                    agregar = True
                    
            elif categoria_actual == "ENVASADO":
                # Grupo Envasado Y que NO sea Big Bag
                if grupo == "ENVASADO" and "BIG BAG" not in material_desc:
                    agregar = True
                    
            elif categoria_actual == "BIG BAG":
                # Grupo Envasado Y que SI sea Big Bag
                # (Nota: A veces Big Bag viene como grupo propio, pero seguimos tu regla: 
                # grupo Envasado + texto Big Bag)
                if grupo == "ENVASADO" and "BIG BAG" in material_desc:
                    agregar = True
            
            if agregar:
                datos_filtrados.append(fila)

        # 3. Llenar Tabla con los datos filtrados
        self._poblar_tabla(datos_filtrados)

    def recibir_nuevos_datos(self, json_data: list):
        """Método llamado cuando llegan datos nuevos del backend."""
        self.ultimo_json_recibido = json_data
        # Refrescamos la vista actual inmediatamente con los datos nuevos
        self.actualizar_vista()

    def _poblar_tabla(self, datos: list):
        """Dibuja las filas en la QTableWidget."""
        self.tabla_turnos.setRowCount(0)
        conteo_espera = 0
        
        for fila in datos:
            row_idx = self.tabla_turnos.rowCount()
            self.tabla_turnos.insertRow(row_idx)

            estatus = fila.get("estatus", "")
            if estatus == "ESPERA":
                conteo_espera += 1

            items = [
                QTableWidgetItem(estatus),
                QTableWidgetItem(fila.get("turno", "")),
                QTableWidgetItem(fila.get("material", "")),
                QTableWidgetItem(fila.get("placa", "")),
                QTableWidgetItem(fila.get("operador", "")),
                QTableWidgetItem(fila.get("eta_carga", ""))
            ]

            # Colores de Estatus
            bg, txt = QColor("white"), QColor("black")
            if estatus == "LLAMADO":   bg, txt = QColor("#6FE29F"), QColor("white")
            elif estatus == "CARGANDO": bg, txt = QColor("#117F2E"), QColor("black")

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0: # Solo coloreamos la celda de Estatus
                    item.setBackground(bg)
                    item.setForeground(QBrush(txt))
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                self.tabla_turnos.setItem(row_idx, col, item)

        # Actualizar KPIs
        self.lbl_card_espera.findChildren(QLabel)[1].setText(str(conteo_espera))
        # Simulamos un cambio aleatorio en el promedio para que se vea vivo
        self.lbl_card_promedio.findChildren(QLabel)[1].setText(f"{random.randint(35, 60)} min")

# ==========================================================================
# SIMULADOR DE DATOS (MOCK)

    def _mock_backend_data(self):
        """Genera datos simulados con estructura de GRUPO."""
        
        # Definición de materiales posibles para la simulación
        materiales_mock = [
            {"nombre": "CPC 40 S8", "grupo": "GRANEL"},
            {"nombre": "CPC 40 L2", "grupo": "GRANEL"},
            {"nombre": "MORTERO FZ 50KG", "grupo": "ENVASADO"},
            {"nombre": "CPC30 RS 25KG", "grupo": "ENVASADO"},
            {"nombre": "CPC30 RS 50KG", "grupo": "ENVASADO"},
            {"nombre": "BIG BAG", "grupo": "ENVASADO"}, # Caso especial
            {"nombre": "BIG BAG RS", "grupo": "ENVASADO"}, # Caso especial
        ]
        
        nombres = ["JUAN PEREZ", "LUIS GOMEZ", "CARLOS RUIZ", "ANA DIAZ", "PEDRO LOPEZ"]
        estatus_opts = ["ESPERA", "ESPERA", "LLAMADO", "CARGANDO"]

        mock_data = []
        # Generamos suficientes datos para poblar las 3 categorías
        for i in range(25): 
            mat_info = random.choice(materiales_mock)
            est = random.choice(estatus_opts)
            
            mock_data.append({
                "estatus": est,
                "turno": f"{datetime.now().strftime('%d')}-{i+1:03d}",
                "material": mat_info["nombre"], # Simula desc_nom_corto
                "grupo": mat_info["grupo"],     # IMPORTANTE PARA EL FILTRO
                "placa": f"{random.randint(100,999)}XX",
                "operador": random.choice(nombres),
                "eta_carga": "10 min" if est == "LLAMADO" else "--"
            })
        
        print("📥 Datos simulados recibidos del backend...")
        self.recibir_nuevos_datos(mock_data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana_seleccion = VentanaSeleccionPlanta()
    ventana_seleccion.show()
    sys.exit(app.exec_())