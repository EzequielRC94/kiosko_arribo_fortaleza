#gui_bascula.py
import sys
import random
import time
import os

from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QMessageBox, QCheckBox
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt, QTimer, QSize
from manager_arribos import ArribosManager
from prevent_sleep import evitar_bloqueo_windows, restaurar_energia_windows
from manager_sap import SAPManager
from session_data import SessionData

# Configuración de las "Pestañas" o Vistas del Carrusel
# Clave: Nombre de la vista
# Valor: Lista de palabras clave para filtrar el material

# ==============================================================================
# VENTANA PRINCIPAL DE OPERACIÓN
# ==============================================================================
class VentanaBasculaMain(QMainWindow):
    def __init__(self, session_data: SessionData):
        super().__init__()
        self.sap_manager = SAPManager()

        self.session_data = session_data
        self.nombre_planta = session_data.planta_gui_nombre # <--
        self.codigos_sap = session_data.planta_gui_codigos # <--


        # --- NUEVA LÓGICA: CONFIGURACIÓN DINÁMICA DE VISTAS ---
        if "Tula" in self.nombre_planta:
            self.vistas_config = [
                {"nombre": "GRANEL - LÍNEA 1 (MX47)",   "gpo": "GRANEL",   "ce": "MX47", "filtro_mat": ""},
                {"nombre": "GRANEL - LÍNEA 2 (MX57)",   "gpo": "GRANEL",   "ce": "MX57", "filtro_mat": ""},
                {"nombre": "ENVASADO - FORTALEZA (L2)","gpo": "ENVASADO", "ce": "MX57", "filtro_mat": "FORTALEZA"},
                {"nombre": "ENVASADO - MORTEROS (L2)", "gpo": "ENVASADO", "ce": "MX57", "filtro_mat": "MORTERO"},
                  {"nombre": "ENVASADO - BIG BAG (L2)", "gpo": "ENVASADO", "ce": "MX57", "filtro_mat": "BIG BAG"},
                {"nombre": "ENVASADO - MAGNOS (L1)",   "gpo": "ENVASADO", "ce": "MX47", "filtro_mat": "MAGNO"},
                {"nombre": "ENVASADO - BLANCOS (L1)",  "gpo": "ENVASADO", "ce": "MX47", "filtro_mat": "BCO"},
            ]
        else:
            self.vistas_config = [
                {"nombre": "GRANEL",  "gpo": "GRANEL",   "ce": "", "filtro_mat": ""},
                {"nombre": "ENVASADO","gpo": "ENVASADO", "ce": "", "filtro_mat": ""},

            ]

        
        # Estado
        self.indice_vista_actual = 0
        self.datos_totales = [] # Aquí vivirá la "Base de Datos" temporal
        
        # UI Config
        self.setWindowTitle(f"Control de Báscula - {session_data.planta_gui_nombre}")
        self.showMaximized()
        self.setStyleSheet("background-color: #FFFFFF;")

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

        # Botón LLAMAR
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
        columnas = ["Sel", "Estatus", "Turno", "Remision", "Transporte", "Material", "Ton", "Modalidad", "Placas", "Operador", "Destinatario"]
        self.tabla.setColumnCount(len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Lista de índices de las columnas que queremos auto-ajustar
        columnas_autoajuste = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11]
        for col in columnas_autoajuste:
            self.tabla.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        
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
        # ¡Magia! Ya no calculas la ruta aquí, solo la extraes de la sesión
        self.ruta_base_drive = self.session_data.ruta_base_drive

        # 2. Instanciar el manager de arribos
        self.arribos_manager = ArribosManager()

        # 3. Carga inicial de datos reales
        self.cargar_datos_reales()
        self.actualizar_interfaz_vista()

         # 💻 KEEP-ALIVE WINDOWS: Evitamos que la gui entre en reposo
        evitar_bloqueo_windows()
        self.sap_manager.iniciar_keep_alive(intervalo_minutos=13)
        
        # 4. Timer 
        # --- TEMPORIZADOR PARA PING DE INTERNET ---
        #self.timer_internet = QTimer(self)
        #self.timer_internet.timeout.connect(self._ping_internet)
        #intervalo_ping_minutos = 5
        #tiempo_de_revision_ms = intervalo_ping_minutos * 60 * 1000
        #print(f"🌐 [RED] Internet iniciado. Intervalo: {intervalo_ping_minutos} min")
        #self.timer_internet.start(tiempo_de_revision_ms)

        # --- TEMPORIZADOR PARA ROBOT DESCARGA ZSDMX389 ---
        self.timer_robot_sap = QTimer(self)
        intervalo_robot_minutos = 5  # minutos
        tiempo_robot_ms = intervalo_robot_minutos * 60 * 1000
        print(f"🤖 [SAP] Robot ZSDMX389 iniciado. Intervalo: {intervalo_robot_minutos} min")
        self.timer_robot_sap.start(tiempo_robot_ms)
        self.timer_robot_sap.timeout.connect(self._ejecutar_robot_zsdmx_bascula)
        self.timer_robot_sap.timeout.connect(self.cargar_datos_reales)
    

    # ==========================================================================
    # LÓGICA DE VISTAS
    # ==========================================================================
    
    def cambiar_vista(self):
        """Cicla entre las vistas configuradas en VISTAS_CONFIG."""
        self.indice_vista_actual = (self.indice_vista_actual + 1) % len(self.vistas_config)
        self.actualizar_interfaz_vista()

    def actualizar_interfaz_vista(self):
        """Filtra los datos globales y repuebla la tabla según la vista actual."""
        config_actual = self.vistas_config[self.indice_vista_actual]
        nombre_vista = config_actual["nombre"]
        filtro_gpo = config_actual["gpo"]
        filtro_ce = config_actual["ce"]
        filtro_mat = config_actual.get("filtro_mat", "")

        self.lbl_vista_titulo.setText(f"VISTA: {nombre_vista}")
        
        # Filtrado
        items_filtrados = []
        suma_toneladas = 0.0
        
        for x_remision in self.datos_totales:
            estatus = x_remision.get("estatus", "")
            
            # 1. Filtro de Estatus (Solo ESPERA o LLAMADO)
            if estatus not in ["ESPERA", "LLAMADO"]:
                continue

            # 2. Filtro por Grupo de Material (Envasado o Granel)
            if x_remision.get("gpo_material") != filtro_gpo:
                continue

            # 3. Filtro por Centro de Expedición (Solo aplica si la vista tiene un "ce" específico como Tula)
            if filtro_ce != "" and x_remision.get("c_exp") != filtro_ce:
                continue

            # 4. : Filtro por Familia de Material (Solo si la vista lo requiere)
            if filtro_mat != "" and filtro_mat not in str(x_remision.get("material", "")): 
                continue

            # Si pasa todos los filtros, lo agregamos a la tabla
            items_filtrados.append(x_remision)
            if estatus == "ESPERA": 
                suma_toneladas += float(x_remision.get("toneladas", 0.0))

        # Actualizar KPIs
        pendientes = len([x for x in items_filtrados if x.get("estatus") == "ESPERA"])
        self.lbl_kpi_unidades.setText(f"Pendientes: {pendientes}")
        self.lbl_kpi_toneladas.setText(f"Total Ton: {suma_toneladas:.2f} TON")

        # ordenar array
        items_filtrados.sort(key=lambda x: str(x.get("transporte", "")))

        # Poblar Tabla
        self._llenar_tabla(items_filtrados)

    def _llenar_tabla(self, lista_camiones):
        self.tabla.setRowCount(0)
        
        # 1. Asegurar que las columnas del encabezado sean las nuevas (puedes poner esto en tu __init__ también)
        columnas = ["Sel", "Estatus", "Turno", "Remision", "Transporte", "Material", "Ton", "Mod", "Placas", "Operador", "Destinatario", "Espera"]
        self.tabla.setColumnCount(len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        
        for i, datos in enumerate(lista_camiones):
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            
            # Columna 0: Checkbox
            chk_widget = QWidget()
            chk = QCheckBox()
            chk.setStyleSheet("margin-left: 10px;")
            if datos["estatus"] == "ESPERA":
                chk.setChecked(False)
            else:
                chk.setDisabled(True) 
            
            # Usamos la remisión como el ID infalible para no depender del transporte vacío
            chk.setProperty("id_identificador", datos["remision"])
            
            layout_chk = QHBoxLayout(chk_widget)
            layout_chk.addWidget(chk)
            layout_chk.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_chk.setContentsMargins(0,0,0,0)
            self.tabla.setCellWidget(row, 0, chk_widget)

            try:
                # OJO: Ajusta "%d.%m.%Y %H:%M:%S" al formato exacto que te da SAP en el CSV
                fch_obj = datetime.strptime(datos["fch_planif"], "%d.%m.%Y %H:%M:%S")
                delta = datetime.now() - fch_obj
                
                dias = delta.days
                horas = delta.seconds // 3600
                minutos = (delta.seconds % 3600) // 60
                
                if dias > 0:
                    tiempo_espera = f"{dias}d {horas}h"
                else:
                    tiempo_espera = f"{horas}h {minutos}m"
            except:
                tiempo_espera = "---" # Por si SAP manda un formato raro o vacío

            modalidad = str(datos.get("modalidad", ""))[:3].upper()

            # 2. Ensamblar la fila en el orden EXACTO de tus columnas (Índices 1 al 10)
            vals = [
                datos["estatus"],           # Columna 1: Estatus
                datos["turno"],             # Columna 2: Turno
                datos["remision"],          # Columna 3: Remision
                datos["transporte"],        # Columna 4: Transporte
                datos["material"],          # Columna 5: Material
                f"{datos['toneladas']:.2f}",# Columna 6: Ton
                modalidad,                  # Columna 7: Modalidad
                datos["placas"],            # Columna 8: Placas
                datos["operador"],          # Columna 9: Operador
                datos["destinatario_nom"],  # Columna 10: Destinatario
                tiempo_espera               # Columna 11: Espera
            ]

            for col_idx, valor in enumerate(vals, start=1):
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if datos["estatus"] == "LLAMADO":
                    item.setBackground(QColor("#D5F5E3")) 
                    item.setForeground(QColor("#145A32"))

                # --- FORMATO CONDICIONAL PARA MODALIDAD ---
                elif col_idx == 7: 
                    if valor == "ENT":
                        item.setBackground(QColor("#FFCBCE")) # Rosa/Rojo de tu VBA
                        item.setForeground(QColor("#943126")) # Texto rojo oscuro
                    elif valor == "AUT":
                        item.setBackground(QColor("#C6F3CE")) # Verde de tu VBA
                        item.setForeground(QColor("#1E8449")) # Texto verde oscuro
                    elif valor == "RET":
                        item.setBackground(QColor("#FFEB9C")) # Amarillo de tu VBA
                        item.setForeground(QColor("#7D6608")) # Texto café/dorado
                elif col_idx == 5: # <-- Asegúrate de que 5 sea tu columna de Material
                    from catalogos import CATALOGO_MATERIALES
                    
                    # Buscamos qué material del catálogo está contenido en el texto de la celda
                    for data in CATALOGO_MATERIALES.values():
                        if data["desc_nom_corto"] in str(valor):
                            # Si lo encuentra, aplica los colores configurados y rompe el ciclo
                            if "bg" in data:
                                item.setBackground(QColor(data["bg"]))
                            if "fg" in data:
                                item.setForeground(QColor(data["fg"]))
                            break
            
                self.tabla.setItem(row, col_idx, item)
        print(f"✅ [{time.strftime('%H:%M:%S')}] Tabla Actualizada")

    def accion_llamar_operadores(self):
        """Llama a los operadores seleccionados usando la Remisión como llave"""
        identificadores_a_llamar = []
        
        # Escanear Tabla
        filas = self.tabla.rowCount()
        for r in range(filas):
            widget_chk = self.tabla.cellWidget(r, 0)
            if widget_chk:
                chk = widget_chk.findChild(QCheckBox)
                if chk and chk.isChecked():
                    t_id = chk.property("id_identificador") # Sacamos la remisión
                    identificadores_a_llamar.append(t_id)

        if not identificadores_a_llamar:
            QMessageBox.warning(self, "Atención", "Seleccione al menos un operador de la lista para llamar.")
            return

        confirm = QMessageBox.question(
            self, "Confirmar Llamado",
            f"¿Desea llamar a {len(identificadores_a_llamar)} operadores a Báscula?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            print(f"📡 Marcando remisiones como LLAMADAS: {identificadores_a_llamar}")
            
            # Simulamos el guardado del estatus en tu base temporal
            for rem_id in identificadores_a_llamar:
                for x_remision in self.datos_totales:
                    if x_remision["remision"] == rem_id:
                        x_remision["estatus"] = "LLAMADO"
            
            QMessageBox.information(self, "Éxito", "Operadores llamados correctamente.")
            self.actualizar_interfaz_vista()

    # ==========================================================================
    # CARGA DE DATOS REALES
    # ==========================================================================
    def _ejecutar_robot_zsdmx_bascula(self):
        """
        Descarga EXCLUSIVAMENTE las remisiones EN PROCESO para actualizar el tablero de báscula.
        """
        import time
        if self.sap_manager.validar_conexion():
            print(f"⏳ [{time.strftime('%H:%M:%S')}] [ROBOT BÁSCULA] Iniciando actualización de ZSDMX389 (En Proceso)...")
            try:
                # Aquí inyectamos la orden de solo bajar los estatus "IGUAL_C"
                self.sap_manager.zsdmx389_robot(self.ruta_base_drive, tipo_descarga="en_proceso")
                
                # Después de descargar, refrescamos el tablero localmente
                self.cargar_datos_reales()
            except Exception as e:
                print(f"⚠️ [{time.strftime('%H:%M:%S')}] Error en ejecución automática del robot ZSDMX389 (Báscula): {e}")

    def cargar_datos_reales(self):
        """Extrae la data en vivo del Excel ZSDMX389 (En Proceso)
        Por eso hacemos el "truco" en 4 pasos:

        Paso 1 (La Foto): transportes_llamados = [...] -> Recorremos la tabla que está ahorita mismo
          en pantalla y anotamos en una libreta (la lista) solo las remisiones de los que están en verde.

        Paso 2 (La Revisión): for nuevo_cam in nuevos_datos: -> Recorremos la información fresquecita que acaba de llegar de SAP.

        Paso 3 (La Inyección): if nuevo_cam["remision"] in transportes_llamados: -> Le decimos a Python: 
         "Oye, si este camión nuevo resulta que está en mi libreta de los que ya llamé, cámbiale a la fuerza el estatus a LLAMADO antes de que lo mostremos".

        Paso 4 (El Reemplazo): self.datos_totales = nuevos_datos -> Ahora sí, 
         reemplazamos la información global con los datos frescos, pero ya llevan nuestra memoria inyectada."""

        try:
            # Pasamos rem=None para que traiga la lista completa y tipo_archivo="en_proceso"
            nuevos_datos = self.arribos_manager.leer_zsdmx389_local(
                ruta_base_drive=self.ruta_base_drive, 
                rem=None, 
                tipo_archivo="en_proceso",
                codigos_planta=self.session_data.planta_gui_codigos
            )
            
            # TRUCO: Conservar el estatus visual "LLAMADO"
            # Paso 1 (La Foto): transportes_llamados
            transportes_llamados = [x_remision["remision"] for x_remision in self.datos_totales if x_remision.get("estatus") == "LLAMADO"]

            # Paso 2 Recorremos la información fresquecita que acaba de llegar de SAP
            for nuevo_cam in nuevos_datos:
                if nuevo_cam["remision"] in transportes_llamados:
                    # Paso 3 Cambiar a la fuerza el estatus a LLAMADO antes de que lo mostremos
                    nuevo_cam["estatus"] = "LLAMADO"

            # Paso 4 Mostramos la informacion real
            self.datos_totales = nuevos_datos
            self.actualizar_interfaz_vista()
            
        except Exception as e:
            print(f"⚠️ Aviso: No se pudo refrescar el tablero de báscula: {e}")

    def _simular_update_sap(self, lista_transportes):
        """
        Simula la modificación del estatus en la 'base de datos' local.
        En el futuro: Iterar lista -> llamar SAP VT02N -> Guardar resultado.
        """
        # Actualizamos nuestra "BD" en memoria
        for t_id in lista_transportes:
            for x_remision in self.datos_totales:
                if x_remision["transporte"] == t_id:
                    x_remision["estatus"] = "LLAMADO"
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
    font = QFont("Arial", 12)
    app.setFont(font)
    
    # Usar el selector unificado
    from gui_selector_planta import obtener_configuracion_inicial
    session_config = obtener_configuracion_inicial()
    
    if session_config:
        ventana = VentanaBasculaMain(session_config)
        print(f"🏢 Kiosko iniciado en {ventana.session_data.planta_gui_nombre} {ventana.session_data.planta_gui_codigos}")
        ventana.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)