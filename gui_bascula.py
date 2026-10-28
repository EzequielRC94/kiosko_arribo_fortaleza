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
from manager_descargas import DescargasManager  
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
        self.manager_descargas = DescargasManager()

        self.session_data = session_data
        self.nombre_planta = session_data.planta_gui_nombre # <--
        self.codigos_sap = session_data.planta_gui_codigos # <--


        # --- NUEVA LÓGICA: CONFIGURACIÓN DINÁMICA DE VISTAS ---
        if "Tula" in self.nombre_planta:
            self.vistas_config = [
                {"nombre": "GRANEL - LÍNEA 1 (MX47)",   "gpo": "GRANEL",   "ce": "MX47", "filtro_mat": ""},
                {"nombre": "GRANEL - LÍNEA 2 (MX57)",   "gpo": "GRANEL",   "ce": "MX57", "filtro_mat": ""},
                {"nombre": "ENVASADO - FORTALEZA (L2)", "gpo": "ENVASADO", "ce": "MX57", "filtro_mat": "FORTALEZA"},
                {"nombre": "ENVASADO - MORTEROS (L2)",  "gpo": "ENVASADO", "ce": "MX57", "filtro_mat": "MORTERO"},
                {"nombre": "ENVASADO - BIG BAG (L2)",   "gpo": "ENVASADO", "ce": "MX57", "filtro_mat": "BIG BAG"},
                {"nombre": "ENVASADO - MAGNOS (L1)",    "gpo": "ENVASADO", "ce": "MX47", "filtro_mat": "MAGNO"},
                {"nombre": "ENVASADO - BLANCOS (L1)",   "gpo": "ENVASADO", "ce": "MX47", "filtro_mat": "BCO"},
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
        # self.showMaximized() QUITAMOS de aquí (lo haremos al final cuando ya esté todo construido)
        self.setMinimumSize(1024, 700) # Un tamaño base seguro por si el usuario restaura la ventana
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
        layout_botones.setSpacing(10)

        # Botón Cambiar Vista
        self.btn_cambiar_vista = QPushButton("🔄 CAMBIAR VISTA (F5)")
        self.btn_cambiar_vista.setFixedHeight(70)
        self.btn_cambiar_vista.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.btn_cambiar_vista.setStyleSheet("""
            QPushButton { background-color: #2C3E50; color: white; border-radius: 10px; }
            QPushButton:hover { background-color: #34495E; }
        """)
        self.btn_cambiar_vista.clicked.connect(self.cambiar_vista)

        # Botón Nuevo Arribo (Pocket gui_arribo)
        self.btn_arribar_nvo = QPushButton("➕ NUEVO ARRIBO")
        self.btn_arribar_nvo.setFixedHeight(70)
        self.btn_arribar_nvo.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self.btn_arribar_nvo.setStyleSheet("""
            QPushButton { background-color: #008080; color: white; border-radius: 10px; border: 2px solid #006666; }
            QPushButton:hover { background-color: #006666; }
            QPushButton:pressed { background-color: #004d4d; }
        """)
        self.btn_arribar_nvo.clicked.connect(self.accion_nuevo_arribo)

        # Botón LLAMAR
        self.btn_llamar = QPushButton("📢 LLAMAR SELECCIONADOS")
        self.btn_llamar.setFixedHeight(85)
        self.btn_llamar.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.btn_llamar.setStyleSheet("""
            QPushButton { background-color: #27AE60; color: white; border-radius: 10px; border: 2px solid #1E8449; }
            QPushButton:hover { background-color: #2ECC71; }
            QPushButton:pressed { background-color: #1E8449; }
        """)
        self.btn_llamar.clicked.connect(self.accion_llamar_operadores)

        layout_botones.addWidget(self.btn_cambiar_vista)
        layout_botones.addWidget(self.btn_arribar_nvo)
        layout_botones.addWidget(self.btn_llamar)
        
        top_layout.addLayout(layout_info, stretch=2)
        top_layout.addLayout(layout_botones, stretch=1)

        # ---------------------------------------------------------
        # 2/3 INFERIOR: TABLA DE OPERADORES
        # ---------------------------------------------------------
        self.tabla = QTableWidget()
        # Definimos las 12 columnas definitivas desde el inicio (Índices 0 al 11)
        columnas = ["Sel", "Estatus", "Turno", "Remision", "Transporte", "Material", "Ton", "Mod", "Placas", "Operador", "Destinatario", "Espera"]
        self.tabla.setColumnCount(len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        
        # Ajustamos al contenido las columnas de datos cortos
        columnas_autoajuste = [0, 1, 2, 3, 4, 6, 7, 8, 9, 11]
        for col in columnas_autoajuste:
            self.tabla.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
            
        # Dejamos que Material (5) y Destinatario (10) se estiren dinámicamente para llenar el monitor sin cortar la GUI
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeMode.Stretch)
        
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
        # Extraes de la sesión
        self.ruta_base_drive = self.session_data.ruta_base_drive

        # 2. Instanciar el manager de arribos
        self.arribos_manager = ArribosManager()

        # 3. Carga inicial de datos reales
        self.cargar_datos_reales()
        self.actualizar_interfaz_vista()

         # 💻 KEEP-ALIVE WINDOWS: Evitamos que la gui entre en reposo
        evitar_bloqueo_windows()
        self.sap_manager.iniciar_keep_alive(intervalo_minutos=13)
        # No es necesario el keep alive, si estamos descargando el archivo cada 10 minutos
        
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
        intervalo_robot_minutos = 10  # minutos
        tiempo_robot_ms = intervalo_robot_minutos * 60 * 1000
        print(f"🤖 [SAP] Robot ZSDMX389 iniciado. Intervalo: {intervalo_robot_minutos} min")
        self.timer_robot_sap.start(tiempo_robot_ms)
        self.timer_robot_sap.timeout.connect(self._ejecutar_robot_zsdmx_bascula)
        #self.timer_robot_sap.timeout.connect(self.cargar_datos_reales) Esta accion ya la hace _ejecutar_robot_zsdmx_bascula
    
    def mostrar_mensaje_estado(self, msg: str, es_correcto: bool):
        """
        'aplicar_color_estado'.
        Muestra texto en la barra inferior (statusBar) con fondo y letra condicional.
        """
        if es_correcto:
            # Estado Válido / Éxito (Fondo Verde Claro, Texto Verde Oscuro)
            estilo = """
                QStatusBar { 
                    background-color: rgb(198, 239, 206); 
                    color: rgb(0, 97, 0); 
                    font-weight: bold; 
                }
            """
        else:
            # Estado Inválido / Error (Fondo Rosa, Texto Rojo Oscuro)
            estilo = """
                QStatusBar { 
                    background-color: rgb(255, 199, 206); 
                    color: rgb(156, 0, 6); 
                    font-weight: bold; 
                }
            """
        
        # Aplicamos el color y mandamos el texto a la pantalla
        self.statusBar().setStyleSheet(estilo)
        self.statusBar().showMessage(msg, 10000) # El 10000 indica que el mensaje se borrará solo a los 10 segundos
    # ==========================================================================
    # LÓGICA DE VISTAS
    # ==========================================================================
    
    def cambiar_vista(self):
        """Cicla entre las vistas configuradas en VISTAS_CONFIG."""
        self.indice_vista_actual = (self.indice_vista_actual + 1) % len(self.vistas_config)
        self.actualizar_interfaz_vista()

    def accion_nuevo_arribo(self):
        """
        Abre gui_arribo.py en modo satélite/pocket reutilizando los datos de planta
        de la sesión actual de Báscula. Al concluir el arribo, cierra la ventana
        y ejecuta cargar_datos_reales() para reflejar el camión en la tabla.
        """
        from gui_arribo import AppWindow

        # Creamos una sesión limpia para el arribo pero heredando la planta y ruta activas en Báscula
        session_arribo = SessionData()
        session_arribo.planta_gui_nombre = self.session_data.planta_gui_nombre
        session_arribo.planta_gui_codigos = list(self.session_data.planta_gui_codigos)
        session_arribo.planta_gui_letra = getattr(self.session_data, "planta_gui_letra", "X")
        session_arribo.ruta_base_drive = self.session_data.ruta_base_drive

        self.ventana_arribo_pocket = AppWindow(session_config=session_arribo, modo_bascula=True)
        self.ventana_arribo_pocket.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.ventana_arribo_pocket.arribo_completado_signal.connect(self.cargar_datos_reales)
        self.ventana_arribo_pocket.show()

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
            # Ezequiel del futuro, como saber que ya paso del estatus llamado a estatus "cargando..." o "cargado"
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
            if estatus in ["ESPERA", "LLAMADO"]:
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
        #columnas = ["Sel", "Estatus", "Turno", "Remision", "Transporte", "Material", "Ton", "Mod", "Placas", "Operador", "Destinatario", "Espera"]
        #self.tabla.setColumnCount(len(columnas))
        #self.tabla.setHorizontalHeaderLabels(columnas)
        
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
            """
            Orquesta el llamado de operadores:
            1. Obtiene las remisiones seleccionadas y sus transportes asociados.
            2. Arma el diccionario data = {"TEXT3": "02 llamado DD/MM/YYYY HH:MM:SS"}.
            3. Ejecuta modificar_transporte en SAP (VT02N) y actualiza la tabla si devuelve True.
            """
            remisiones_seleccionadas = []
            
            # 1. Escanear Tabla buscando checkboxes marcados
            filas = self.tabla.rowCount()
            for r in range(filas):
                widget_chk = self.tabla.cellWidget(r, 0)
                if widget_chk:
                    chk = widget_chk.findChild(QCheckBox)
                    if chk and chk.isChecked():
                        rem_id = str(chk.property("id_identificador")).strip()
                        remisiones_seleccionadas.append(rem_id)

            if not remisiones_seleccionadas:
                QMessageBox.warning(self, "Atención", "Seleccione al menos un operador de la lista para llamar.")
                return

            # 2. Agrupar remisiones por Número de Transporte (Evita entrar 2 veces a VT02N en un Full)
            # Estructura: { "4800123456": ["7530000001", "7530000002"] }
            mapa_transportes = {}
            sin_transporte = []

            for x_rem in self.datos_totales:
                rem_actual = str(x_rem.get("remision", "")).strip()
                if rem_actual in remisiones_seleccionadas:
                    num_trans = str(x_rem.get("transporte", "")).strip()
                    if num_trans and num_trans not in ["---", "PENDIENTE", "None", ""]:
                        if num_trans not in mapa_transportes:
                            mapa_transportes[num_trans] = []
                        mapa_transportes[num_trans].append(rem_actual)
                    else:
                        sin_transporte.append(rem_actual)

            if sin_transporte:
                QMessageBox.warning(
                    self, "Transporte Faltante",
                    f"Las siguientes remisiones aún no tienen número de transporte válido:\n{', '.join(sin_transporte)}"
                )
                if not mapa_transportes:
                    return

            # 3. Confirmación del usuario en Báscula
            confirm = QMessageBox.question(
                self, "Confirmar Llamado",
                f"¿Desea llamar a {len(mapa_transportes)} unidad(es) ({len(remisiones_seleccionadas)} remisiones) a Báscula?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm != QMessageBox.Yes:
                return

            # 4. Armar el diccionario con la estampa de tiempo al momento
            ahora_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            texto_llamado = f"02 llamado {ahora_str}"
            
            data_cambios = {
                "TEXT3": texto_llamado
            }

            # 5. Iterar sobre cada transporte único y mandarlo a SAP VT02N
            transportes_exitosos = []
            errores_sap = []

            # Importamos SAPError por si hay bloqueo en SAP
            from manager_sap import SAPError

            for num_transporte, lista_rems in mapa_transportes.items():
                try:
                    QApplication.processEvents() # Mantiene viva la ventana de Qt5 mientras trabaja SAP
                    exito = self.sap_manager.modificar_transporte(num_transporte, data_cambios)
                    
                    if exito:
                        transportes_exitosos.append(num_transporte)
                        # Actualizamos en memoria todas las remisiones asociadas a este transporte
                        for x_remision in self.datos_totales:
                            if str(x_remision.get("transporte", "")).strip() == num_transporte:
                                x_remision["estatus"] = "LLAMADO"
                                
                except SAPError as e_sap:
                    print(f"❌ Error SAP al llamar transporte {num_transporte}: {e_sap}")
                    errores_sap.append(f"• {e_sap}")
                except Exception as e_gen:
                    print(f"❌ Error inesperado con transporte {num_transporte}: {e_gen}")
                    errores_sap.append(f"Transporte {num_transporte}: {e_gen}")

            # 6. Refrescar interfaz y dar retroalimentación al usuario
            self.actualizar_interfaz_vista()

            if transportes_exitosos and not errores_sap:
                QMessageBox.information(
                    self, "Éxito", 
                    f"Se actualizaron correctamente {len(transportes_exitosos)} transporte(s) en SAP con:\n'{texto_llamado}'"
                )
            elif transportes_exitosos and errores_sap:
                detalle_err = "\n".join(errores_sap)
                QMessageBox.warning(
                    self, "Llamado Parcial",
                    f"Se llamaron {len(transportes_exitosos)} transporte(s), pero hubo errores en otros:\n\n{detalle_err}"
                )
            else:
                detalle_err = "\n".join(errores_sap)
                QMessageBox.critical(
                    self, "Error en SAP",
                    f"No se pudo modificar ningún transporte en VT02N:\n\n{detalle_err}"
                )
                
    # ==========================================================================
    # CARGA DE DATOS REALES
    # ==========================================================================
    def _ejecutar_robot_zsdmx_bascula(self):
        """Descarga EXCLUSIVAMENTE las remisiones EN PROCESO para actualizar el tablero de báscula."""
        import time
        if self.sap_manager.validar_conexion():
            print(f"⏳ [{time.strftime('%H:%M:%S')}] [ROBOT BÁSCULA] Iniciando actualización...")
            try:
                resultado = self.manager_descargas.zsdmx389_robot(self.ruta_base_drive, tipo_descarga="en_proceso")
                
                if resultado.get("estatus"):
                    # Solo recargamos la vista si la descarga fue exitosa o se omitió limpiamente
                    self.cargar_datos_reales()
                    
                    # Extraemos el mensaje de éxito del diccionario 
                    msg_exito = resultado.get("msg", "Descarga exitosa")
                    self.mostrar_mensaje_estado(msg=msg_exito, es_correcto=True)
                    
                else:
                    msg_error = resultado.get('msg', 'Error desconocido')
                    print(f"⚠️ [{time.strftime('%H:%M:%S')}] Error en SAP: {msg_error}")
                    
                    # Mandamos el error visual a la barra de estado con colores rojos
                    self.mostrar_mensaje_estado(msg=msg_error, es_correcto=False)
                    
            except Exception as e:
                print(f"⚠️ [{time.strftime('%H:%M:%S')}] Error crítico en ejecución de báscula: {e}")

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
        ventana.showMaximized()
        sys.exit(app.exec_())
    else:
        sys.exit(0)