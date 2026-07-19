#gui_bascula.py
import sys
import random
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QMessageBox, QCheckBox
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt, QTimer, QSize

# Simulación de importación de Managers (en producción usarás los reales)
# from sap_manager import SAPManager 

# ==============================================================================
# CONFIGURACIÓN DE VISTAS Y PLANTAS
# ==============================================================================

CATALOGO_PLANTAS = {
    "Planta Tula":      ["MX47", "MX57"],
    "Planta Palmar":    ["MX16"],
    "Planta Progreso":  ["MX76"],
    "Planta Vito":      ["MX46"],
    "CEDIS GDL":        ["MX83"]
}

# Configuración de las "Pestañas" o Vistas del Carrusel
# Clave: Nombre de la vista
# Valor: Lista de palabras clave para filtrar el material
VISTAS_CONFIG = [
    {"nombre": "GRANEL",                 "filtros": ["GRANEL"]},
    {"nombre": "BIG BAG",                "filtros": ["BIG BAG"]},
    {"nombre": "ENVASADO - CPC 30 RS",   "filtros": ["CPC 30 RS", "CPC30 RS"]},
    {"nombre": "ENVASADO - MAGNO",       "filtros": ["MAGNO"]},
    {"nombre": "ENVASADO - BLANCOS",     "filtros": ["BCO", "BLANCO", "MORTERO"]}
]

# ==============================================================================
# V0: SELECCIÓN DE PLANTA (Reutilizado)
# ==============================================================================
class VentanaSeleccionPlanta(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración de Báscula")
        self.resize(600, 500)
        self.setStyleSheet("background-color: #f0f0f0;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)

        lbl_titulo = QLabel("OPERADOR BÁSCULA\nSELECCIONE SU UBICACIÓN")
        lbl_titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)

        for nombre_planta, codigos in CATALOGO_PLANTAS.items():
            btn = QPushButton(f"{nombre_planta}")
            btn.setFont(QFont("Arial", 14))
            btn.setFixedHeight(60)
            btn.setProperty("codigos", codigos) 
            btn.setProperty("nombre", nombre_planta)
            btn.setStyleSheet("""
                QPushButton { background-color: #008080; color: white; border-radius: 8px; }
                QPushButton:hover { background-color: #006666; }
            """)
            btn.clicked.connect(self.abrir_bascula)
            layout.addWidget(btn)

    def abrir_bascula(self):
        sender = self.sender()
        self.ventana_main = VentanaBasculaMain(sender.property("nombre"), sender.property("codigos"))
        self.ventana_main.show()
        self.close()

# ==============================================================================
# VENTANA PRINCIPAL DE OPERACIÓN
# ==============================================================================
class VentanaBasculaMain(QMainWindow):
    def __init__(self, nombre_planta, codigos_sap):
        super().__init__()
        self.nombre_planta = nombre_planta
        self.codigos_sap = codigos_sap
        
        # Estado
        self.indice_vista_actual = 0
        self.datos_totales = [] # Aquí vivirá la "Base de Datos" temporal
        
        # UI Config
        self.setWindowTitle(f"Control de Báscula - {nombre_planta}")
        self.showMaximized()
        self.setStyleSheet("background-color: #E8E8E8;")

        # Layout Principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # ---------------------------------------------------------
        # 1/3 SUPERIOR: PANEL DE CONTROL Y KPI
        # ---------------------------------------------------------
        self.frame_top = QFrame()
        self.frame_top.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #aaa;")
        self.frame_top.setFixedHeight(280) # Aproximadamente 1/3 de pantalla FHD
        top_layout = QHBoxLayout(self.frame_top)
        
        # A. Info de Vista Actual (Izquierda)
        layout_info = QVBoxLayout()
        self.lbl_vista_titulo = QLabel("CARGANDO...")
        self.lbl_vista_titulo.setFont(QFont("Arial Black", 28, QFont.Weight.Bold))
        self.lbl_vista_titulo.setStyleSheet("color: #008080;")
        
        self.lbl_kpi_unidades = QLabel("Unidades: 0")
        self.lbl_kpi_unidades.setFont(QFont("Arial", 16))
        
        self.lbl_kpi_toneladas = QLabel("Toneladas: 0.00 ton")
        self.lbl_kpi_toneladas.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.lbl_kpi_toneladas.setStyleSheet("color: #D35400;") # Color óxido para resaltar
        
        layout_info.addWidget(self.lbl_vista_titulo)
        layout_info.addWidget(self.lbl_kpi_unidades)
        layout_info.addWidget(self.lbl_kpi_toneladas)
        layout_info.addStretch()
        
        # B. Botones de Acción (Derecha)
        layout_botones = QVBoxLayout()
        layout_botones.setSpacing(15)

        # Botón Cambiar Vista
        self.btn_cambiar_vista = QPushButton("🔄 CAMBIAR VISTA (F5)")
        self.btn_cambiar_vista.setFixedHeight(80)
        self.btn_cambiar_vista.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.btn_cambiar_vista.setStyleSheet("""
            QPushButton { background-color: #2C3E50; color: white; border-radius: 10px; }
            QPushButton:hover { background-color: #34495E; }
        """)
        self.btn_cambiar_vista.clicked.connect(self.cambiar_vista)

        # Botón LLAMAR (La Magia)
        self.btn_llamar = QPushButton("📢 LLAMAR SELECCIONADOS")
        self.btn_llamar.setFixedHeight(100)
        self.btn_llamar.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.btn_llamar.setStyleSheet("""
            QPushButton { background-color: #27AE60; color: white; border-radius: 10px; border: 2px solid #1E8449; }
            QPushButton:hover { background-color: #2ECC71; }
            QPushButton:pressed { background-color: #1E8449; }
        """)
        self.btn_llamar.clicked.connect(self.accion_llamar_operadores)

        layout_botones.addWidget(self.btn_cambiar_vista)
        layout_botones.addWidget(self.btn_llamar)
        
        top_layout.addLayout(layout_info, stretch=2)
        top_layout.addLayout(layout_botones, stretch=1)

        # ---------------------------------------------------------
        # 2/3 INFERIOR: TABLA DE OPERADORES
        # ---------------------------------------------------------
        self.tabla = QTableWidget()
        columnas = ["Sel", "Turno", "Transporte (SAP)", "Material", "Ton", "Operador", "Estatus"]
        self.tabla.setColumnCount(len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # La columna 0 (Sel) más pequeña
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        self.tabla.setStyleSheet("""
            QTableWidget { background-color: white; font-size: 14px; gridline-color: #ccc; }
            QHeaderView::section { background-color: #333; color: white; font-weight: bold; padding: 5px; }
            QCheckBox::indicator { width: 30px; height: 30px; }
        """)
        
        # Agregamos widgets al layout principal
        self.main_layout.addWidget(self.frame_top)
        self.main_layout.addWidget(self.tabla)

        # ---------------------------------------------------------
        # INICIALIZACIÓN
        # ---------------------------------------------------------
        self._mock_cargar_datos_iniciales() # Cargar datos falsos
        self.actualizar_interfaz_vista()    # Pintar V1
        
        # Timer para simular refresco automático de SAP cada 30s
        self.timer_refresh = QTimer()
        self.timer_refresh.timeout.connect(self._mock_refresco_sap)
        self.timer_refresh.start(30000)

    # ==========================================================================
    # LÓGICA DE VISTAS
    # ==========================================================================
    def cambiar_vista(self):
        """Cicla entre las vistas configuradas en VISTAS_CONFIG."""
        self.indice_vista_actual = (self.indice_vista_actual + 1) % len(VISTAS_CONFIG)
        self.actualizar_interfaz_vista()

    def actualizar_interfaz_vista(self):
        """Filtra los datos globales y repuebla la tabla según la vista actual."""
        config_actual = VISTAS_CONFIG[self.indice_vista_actual]
        nombre_vista = config_actual["nombre"]
        palabras_clave = config_actual["filtros"]

        self.lbl_vista_titulo.setText(f"VISTA: {nombre_vista}")
        
        # Filtrado
        items_filtrados = []
        suma_toneladas = 0.0
        
        for camion in self.datos_totales:
            mat_desc = camion["material"].upper()
            estatus = camion["estatus"]
            
            # Solo mostramos lo que está EN ESPERA o LLAMADO (no los que ya entraron)
            if estatus not in ["ESPERA", "LLAMADO"]:
                continue

            # Lógica de coincidencia (si alguna palabra clave está en la descripción)
            coincide = False
            for kw in palabras_clave:
                if kw in mat_desc:
                    coincide = True
                    break
            
            if coincide:
                items_filtrados.append(camion)
                if estatus == "ESPERA": # Solo sumamos pendientes reales
                    suma_toneladas += camion["toneladas"]

        # Actualizar KPIs
        self.lbl_kpi_unidades.setText(f"Pendientes: {len([x for x in items_filtrados if x['estatus']=='ESPERA'])}")
        self.lbl_kpi_toneladas.setText(f"Total Ton: {suma_toneladas:.2f} TON")

        # Poblar Tabla
        self._llenar_tabla(items_filtrados)

    def _llenar_tabla(self, lista_camiones):
        self.tabla.setRowCount(0)
        
        for i, datos in enumerate(lista_camiones):
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            
            # Columna 0: Checkbox (Solo si está en ESPERA)
            chk_widget = QWidget()
            chk = QCheckBox()
            chk.setStyleSheet("margin-left: 10px;")
            if datos["estatus"] == "ESPERA":
                chk.setChecked(False)
            else:
                chk.setDisabled(True) # Si ya está llamado, no se selecciona
            
            # Guardamos referencia al ID (transporte) en el checkbox para buscarlo luego
            chk.setProperty("id_transporte", datos["transporte"])
            
            layout_chk = QHBoxLayout(chk_widget)
            layout_chk.addWidget(chk)
            layout_chk.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_chk.setContentsMargins(0,0,0,0)
            self.tabla.setCellWidget(row, 0, chk_widget)

            # Resto de columnas
            vals = [
                datos["turno"],
                datos["transporte"],
                datos["material"],
                f"{datos['toneladas']:.2f}",
                datos["operador"],
                datos["estatus"]
            ]

            for col_idx, valor in enumerate(vals, start=1):
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Colorear fila si ya está llamado
                if datos["estatus"] == "LLAMADO":
                    item.setBackground(QColor("#D5F5E3")) # Verde claro
                    item.setForeground(QColor("#145A32"))
                
                self.tabla.setItem(row, col_idx, item)

    # ==========================================================================
    # LÓGICA DE ACCIÓN (MAGIA)
    # ==========================================================================
    def accion_llamar_operadores(self):
        """
        1. Recorre la tabla buscando checkboxes marcados.
        2. Obtiene los números de transporte.
        3. Llama a SAP Manager para actualizar estatus (Simulado).
        4. Actualiza la data local y refresca la tabla.
        """
        transportes_a_llamar = []
        
        # 1. Escanear Tabla
        filas = self.tabla.rowCount()
        for r in range(filas):
            widget_chk = self.tabla.cellWidget(r, 0)
            if widget_chk:
                chk = widget_chk.findChild(QCheckBox)
                if chk and chk.isChecked():
                    t_id = chk.property("id_transporte")
                    transportes_a_llamar.append(t_id)

        if not transportes_a_llamar:
            QMessageBox.warning(self, "Atención", "Seleccione al menos un operador de la lista para llamar.")
            return

        # Confirmación
        confirm = QMessageBox.question(
            self, "Confirmar Llamado",
            f"¿Desea llamar a {len(transportes_a_llamar)} operadores a Báscula?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            print(f"📡 Enviando solicitud a SAP/Backend para transportes: {transportes_a_llamar}")
            
            # 2. PROCESAMIENTO (Aquí iría self.sap_manager.actualizar_estatus(...))
            exito = self._simular_update_sap(transportes_a_llamar)
            
            if exito:
                QMessageBox.information(self, "Éxito", "Operadores llamados correctamente.\nEl tablero de espera se actualizará en breve.")
                self.actualizar_interfaz_vista()

    def _simular_update_sap(self, lista_transportes):
        """
        Simula la modificación del estatus en la 'base de datos' local.
        En el futuro: Iterar lista -> llamar SAP VT02N -> Guardar resultado.
        """
        # Actualizamos nuestra "BD" en memoria
        for t_id in lista_transportes:
            for camion in self.datos_totales:
                if camion["transporte"] == t_id:
                    camion["estatus"] = "LLAMADO"
                    # Aquí también guardaríamos en el archivo JSON/Excel compartido
                    # para que gui_tablero.py lo lea.
        return True

    # ==========================================================================
    # MOCKS DE DATOS
    # ==========================================================================
    def _mock_cargar_datos_iniciales(self):
        """Genera datos aleatorios para probar las vistas."""
        materiales = [
            "CPC 30 RS 50KG", "MORTERO FZ 50KG", "BIG BAG RS", 
            "GRANEL CPC 40", "GRANEL RS", "MAGNO 25KG", 
            "BCO 25KG", "ESTUCO BLANCO"
        ]
        nombres = ["JUAN PEREZ", "LUIS LOPEZ", "MARIA GOMEZ", "PEDRO RUIZ"]
        
        self.datos_totales = []
        for i in range(30):
            mat = random.choice(materiales)
            
            # Peso según material
            peso = random.randint(25, 55) if "GRANEL" in mat or "BIG BAG" in mat else random.randint(15, 35)
            
            self.datos_totales.append({
                "turno": f"{datetime.now().day}-{i+100}",
                "transporte": f"1000{random.randint(1000,9999)}", # ID Transporte SAP
                "material": mat,
                "toneladas": float(peso),
                "operador": random.choice(nombres),
                "estatus": random.choice(["ESPERA", "ESPERA", "LLAMADO"]) 
            })
            
    def _mock_refresco_sap(self):
        """Simula que llega información nueva de SAP (ej. nuevos arribos)."""
        # En la vida real, aquí leerías el Excel/JSON generado por el Kiosko
        if random.random() > 0.7:
            print("🔄 Refrescando datos del backend...")
            # Simulamos que llega uno nuevo
            self.datos_totales.append({
                "turno": f"{datetime.now().day}-{random.randint(500,999)}",
                "transporte": f"1000{random.randint(1000,9999)}",
                "material": "GRANEL EXTRA",
                "toneladas": 45.0,
                "operador": "NUEVO ARRIBO",
                "estatus": "ESPERA"
            })
            self.actualizar_interfaz_vista()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Fuente global un poco más grande para pantalla táctil/operador
    font = QFont("Arial", 12)
    app.setFont(font)
    
    ventana = VentanaSeleccionPlanta()
    ventana.show()
    sys.exit(app.exec_())