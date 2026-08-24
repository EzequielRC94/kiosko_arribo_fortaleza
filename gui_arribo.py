# gui_arribo.py
import sys
import os
import ctypes
import time
from datetime import datetime, timedelta
import random # Para simular el resultado de "Arribo Correcto/Incorrecto"
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QHeaderView, QMessageBox, QStackedWidget, QFrame, QDialog
)
from PyQt5.QtGui import (QFont, QPixmap, QIcon)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize

# Importar módulos
from manager_sap import (SAPManager, SAPError)
from session_data import SessionData
from manager_logs import LogManager
from manager_cloudfort import CloudFortManager
from mailer import EmailManager            
from manager_arribos import ArribosManager
from prevent_sleep import evitar_bloqueo_windows, restaurar_energia_windows

# ====================================================================
# DEFINICIÓN DE VENTANAS (WIDGETS INDIVIDUALES)
# ====================================================================

# Ventana lay out arribo_gui.py

class Ventana0_Inicio(QWidget):
    """Ventana inicial con el botón 'Nuevo Arribo'."""
    nuevo_arribo_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 1. Mostrar un solo QPushButton
        btn_nuevo_arribo = QPushButton("+\nNuevo Arribo") 
        
        # 2. Tamaño fijo y fuente grande
        btn_nuevo_arribo.setFixedSize(450, 450) #
        #btn_nuevo_arribo.setFont(QFont("Arial Black", 30, QFont.Weight.Bold))
        
        btn_nuevo_arribo.setStyleSheet("""
            QPushButton {
                background-color: white; 
                color: #008080; 
                
                border-radius: 125px; 
                border: 10px solid #008080; 
                
                /* --- AQUI CONTROLAS LA LETRA SOLO PARA ESTE BOTÓN --- */
                font-family: "Arial Black";
                font-size: 40px; 
                font-weight: bold;
                /* ---------------------------------------------------- */
                
                padding: 10px; 
            }
            QPushButton:hover {
                background-color: #f0f0f0; 
            }
        """)
        
        layout.addWidget(btn_nuevo_arribo, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_nuevo_arribo.clicked.connect(self.nuevo_arribo_signal.emit)

class Ventana1_IngresoRemision(QWidget):
    """Ventana para ingresar la remisión y buscar."""
    buscar_remision_signal = pyqtSignal(str)
    cancelar_arribo_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- 1. Crear el portarretratos (QLabel) ---
        self.lbl_imagen_qr = QLabel(self)

        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_imagen = os.path.join(directorio_actual, "images", "logo_escaner.png")
        pixmap_qr = QPixmap(ruta_imagen)
        pixmap_escalado = pixmap_qr.scaled(
            200, 200, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )

        self.lbl_imagen_qr.setPixmap(pixmap_escalado)
        self.lbl_imagen_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_imagen_qr.setStyleSheet("margin-bottom: 10px;")

        lbl_titulo = QLabel("▣ Escanee QR o ingrese número de remisión")
        lbl_titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setStyleSheet("color: #008080; margin-bottom: 20px;")
        
        self.txt_remision = QLineEdit()
        self.txt_remision.setPlaceholderText("Ej. 7530000000")
        self.txt_remision.setFont(QFont("Arial", 24))
        self.txt_remision.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_remision.setFixedHeight(60)
        self.txt_remision.setMinimumWidth(450)
        self.txt_remision.setStyleSheet("border: 3px solid #008080; padding: 10px;")

        # Botón con Lupa 🔍 y texto "BUSCAR"
        btn_buscar = QPushButton("🔍 BUSCAR")
        #btn_buscar.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        #btn_buscar.setStyleSheet("background-color: #008080; color: white; margin-top: 20px;")
        btn_buscar.setFixedHeight(70)
        btn_buscar.setMinimumWidth(450)
        

        btn_cancelar_arribo = QPushButton("❌ CANCELAR")
        btn_cancelar_arribo.setFixedHeight(60)
        btn_cancelar_arribo.setMinimumWidth(450)
        btn_cancelar_arribo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        btn_cancelar_arribo.setStyleSheet("""
            QPushButton {
                background-color: #CC0000; 
                color: white; 
                margin-top: 10px; 
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #990000; /* Rojo más oscuro al pasar el mouse */
            }
            QPushButton:pressed {
                background-color: #660000; /* Rojo profundo al hacer clic */
            }
        """)

        layout.addWidget(self.lbl_imagen_qr, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.txt_remision, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_buscar, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_cancelar_arribo, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- NUEVAS CONEXIONES PARA ESCÁNER Y AUTOMATIZACIÓN ---
        btn_buscar.clicked.connect(self._on_buscar_clicked)
        btn_cancelar_arribo.clicked.connect(self.cancelar_arribo_signal.emit)
        # 1. Detectar si el usuario (o escáner) presiona "Enter"
        self.txt_remision.returnPressed.connect(self._on_buscar_clicked)
        # 2. Detectar cambios en tiempo real para auto-ejecutar a los 10 dígitos
        self.txt_remision.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text):
        """Se ejecuta cada vez que el texto cambia."""
        texto_limpio = text.strip()
        
        # Si llega exactamente a 10 caracteres y todos son números
        if len(texto_limpio) == 10 and texto_limpio.isdigit():
            
            # 1. (Opcional pero recomendado) Bloqueamos el input para evitar un dígito 11
            self.txt_remision.setDisabled(True) 
            
            # 2. Usamos QTimer para retrasar la búsqueda solo 100 milisegundos.
            # Esto le da tiempo a PyQt5 de repintar la pantalla y mostrar el último dígito.
            QTimer.singleShot(100, self._on_buscar_clicked)

    def _on_buscar_clicked(self):
        remision = self.txt_remision.text().strip()
        if remision.isdigit() and len(remision) == 10:
            self.buscar_remision_signal.emit(remision)
        else:
            QMessageBox.warning(self, "Error Formato", "La remisión debe ser un número de exactamente 10 dígitos.\n"
                f"Usted ingresó: {len(remision)} dígitos.")
            
    def limpiar(self):
        self.txt_remision.clear()
        self.txt_remision.setDisabled(False)
        self.txt_remision.setFocus() # Focus automatico al iniciar ventana

class Ventana2_datos_operador(QWidget):
    """Ventana para que el operador valide su nombre y placas."""
    confirmar_operador_signal = pyqtSignal()
    cancelar_arribo_signal = pyqtSignal()

    def __init__(self, session_data: SessionData, parent=None):
        super().__init__(parent)
        self.session_data = session_data
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_pregunta = QLabel("¿LOS DATOS SON CORRECTOS?")
        lbl_pregunta.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        lbl_pregunta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_pregunta.setStyleSheet("color: #333333; margin-bottom: 30px;")

        # Contenedor de datos (Reutilizando tu lógica de etiquetas grandes)
        self.lbl_operador = self._crear_lbl_grande("NOMBRE DEL OPERADOR:", "---")
        self.lbl_placa = self._crear_lbl_grande("PLACAS DEL VEHÍCULO:", "---")

        layout.addWidget(lbl_pregunta)
        layout.addWidget(self.lbl_operador)
        layout.addWidget(self.lbl_placa)

        # --- BOTONES CON ICONOS Y COLORES ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(50) # Espacio entre los dos botones
        
        # Botón NO (Amarillo con Tache)
        self.btn_no = QPushButton("✖  NO")
        self.btn_no.setFixedSize(300, 80)
        self.btn_no.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.btn_no.setStyleSheet("""
            QPushButton {
                background-color: #FFC000; 
                color: black; 
                border-radius: 10px;
                border: 2px solid #D4A017;
            }
            QPushButton:hover {
                background-color: #E6AC00;
            }
        """)
        
        # Botón SÍ (Verde con Palomita)
        self.btn_si = QPushButton("✔  SÍ, Si Soy")
        self.btn_si.setFixedSize(300, 80)
        self.btn_si.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.btn_si.setStyleSheet("""
            QPushButton {
                background-color: #28A745; 
                color: white; 
                border-radius: 10px;
                border: 2px solid #1E7E34;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_no)
        btn_layout.addWidget(self.btn_si)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)

        # Conexiones
        self.btn_si.clicked.connect(self.confirmar_operador_signal.emit)
        self.btn_no.clicked.connect(self.cancelar_arribo_signal.emit)

    def _crear_lbl_grande(self, titulo: str, valor: str) -> QWidget:
        widget = QWidget()
        v_layout = QVBoxLayout(widget)
        l1 = QLabel(titulo)
        l1.setFont(QFont("Arial", 12))
        l1.setStyleSheet("color: gray;")
        l2 = QLabel(valor)
        l2.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        l2.setStyleSheet("color: #333333; margin-bottom: 20px;")
        l2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(l1, alignment=Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(l2, alignment=Qt.AlignmentFlag.AlignCenter)
        return widget

    def actualizar_datos(self, session_real):
        """Actualiza los labels con la info de la sesión actual."""
        self.lbl_operador.findChildren(QLabel)[1].setText(session_real.operador)
        self.lbl_placa.findChildren(QLabel)[1].setText(session_real.placa)

class Ventana2_1_DatosOperadorFacecam(QWidget):
    """
    Ventana de simulación de Facecam (duración 10 segundos).
    Prepara al operador visualmente para la futura validación biométrica.
    """
    # Señal que se emite automáticamente cuando terminan los 10 segundos
    tiempo_terminado_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout Principal Vertical
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        # 1. Label Superior: Título del proceso
        lbl_titulo = QLabel("VALIDACIÓN POR CÁMARA")
        lbl_titulo.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setStyleSheet("color: #333333; margin-bottom: 20px;")
        layout.addWidget(lbl_titulo)

        # 2. Cuadro de Simulación (Ocupa 3/4 partes de la pantalla)
        # Usamos un QFrame para simular el recuadro negro/gris del visor de la cámara
        self.frame_camara = QFrame()
        self.frame_camara.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A; 
                
                border-radius: 15px;
            }
        """)
        
        # Intentamos que tome la mayor cantidad de espacio vertical (3/4 partes simuladas)
        layout.addWidget(self.frame_camara, stretch=3)

        # Layout interno para los mensajes dentro del cuadro de la cámara
        layout_interno_cam = QVBoxLayout(self.frame_camara)
        layout_interno_cam.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Ícono de advertencia o cámara desconectada en texto grande
        lbl_icono = QLabel("📷 ❌")
        lbl_icono.setFont(QFont("Arial", 48))
        lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_interno_cam.addWidget(lbl_icono)

        # Texto principal del estado del visor
        lbl_estado_cam = QLabel("NO SE HA DETECTADO CÁMARA ACTIVA")
        lbl_estado_cam.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        lbl_estado_cam.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_estado_cam.setStyleSheet("color: #D9534F; margin-top: 10px;") # Rojo de advertencia
        layout_interno_cam.addWidget(lbl_estado_cam)

        # Subtexto informativo para el operador
        lbl_subtexto = QLabel("Por favor, espere un momento...")
        lbl_subtexto.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_subtexto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_subtexto.setStyleSheet("color: #888888; margin-top: 5px;")
        layout_interno_cam.addWidget(lbl_subtexto)

        # 3. Label Inferior: Contador regresivo visual
        self.lbl_contador = QLabel("Iniciando validación alternativa en 10 segundos...")
        #self.lbl_contador = QLabel("Iniciando validación tradicional en 10 segundos...")
        self.lbl_contador.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.lbl_contador.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_contador.setStyleSheet("color: #008080; margin-top: 25px;")
        layout.addWidget(self.lbl_contador, stretch=1)

        # --- TIMER PARA CONTROLAR LOS 10 SEGUNDOS ---
        self.tiempo_restante = 10
        
        # Timer de 1 segundo para ir actualizando el texto del contador en pantalla
        self.timer_segundos = QTimer(self)
        self.timer_segundos.setInterval(1000) # Cada 1 segundo
        self.timer_segundos.timeout.connect(self._actualizar_contador)

    def iniciar_simulacion(self):
        """Método que debe llamar el controlador de la App al mostrar esta ventana"""
        self.tiempo_restante = 5
        self.lbl_contador.setText(f"Iniciando validación tradicional en {self.tiempo_restante} segundos...")
        self.timer_segundos.start()

    def _actualizar_contador(self):
        """Decrementa el contador y emite la señal al llegar a cero"""
        self.tiempo_restante -= 1
        if self.tiempo_restante > 0:
            self.lbl_contador.setText(f"Iniciando validación tradicional en {self.tiempo_restante} segundos...")
        else:
            self.timer_segundos.stop()
            # 🟢 TRANSMISIÓN: Avisamos al Kiosko que el tiempo terminó
            self.tiempo_terminado_signal.emit()

class Ventana3_Verificacion(QWidget):
    """Ventana de verificación de datos, tabla de materiales y botones de acción."""
    finalizar_arribo_signal = pyqtSignal()
    agregar_nueva_remision_signal = pyqtSignal()
    cancelar_arribo_signal = pyqtSignal()

    def __init__(self, session_data: SessionData, parent=None):
        super().__init__(parent)
        self.session_data = session_data
        layout = QVBoxLayout(self)

        # 1. Datos del Camión (Fila Superior)
        self.lbl_cliente = self._crear_lbl_data("CLIENTE:", "---")
        self.lbl_operador = self._crear_lbl_data("OPERADOR:", "---")
        self.lbl_placa = self._crear_lbl_data("PLACAS:", "---")
        self.lbl_peso_total = self._crear_lbl_data("PESO TOTAL:", "0.00 TON")
        
        data_layout = QHBoxLayout()
        data_layout.addWidget(self.lbl_cliente)
        data_layout.addWidget(self.lbl_operador)
        data_layout.addWidget(self.lbl_placa)
        data_layout.addWidget(self.lbl_peso_total)
        layout.addLayout(data_layout)

        # 1 Selección Clase Expedición
        layout_expedicion = QHBoxLayout()
        lbl_tipo = QLabel("CLASE EXPEDICIÓN:")
        lbl_tipo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_tipo.setStyleSheet("color: #008080;")
        
        self.cmb_clase_expedicion = QComboBox()
        self.cmb_clase_expedicion.addItems([
            "F1 - TOLVA SENCILLA", "F2 - PLANA SENCILLA", "F3 - TORTON", 
            "F4 - PLANA FULL", "F5 - TOLVITA", "F7 - TOLVA FULL"
        ])
        self.cmb_clase_expedicion.setMinimumWidth(250)
        self.cmb_clase_expedicion.setFont(QFont("Arial", 12))
        
        layout_expedicion.addWidget(lbl_tipo)
        layout_expedicion.addWidget(self.cmb_clase_expedicion)
        layout_expedicion.addStretch()
        layout.addLayout(layout_expedicion)

        # 2. Tabla de Remisiones (Central)
        self.tabla_materiales = QTableWidget()
        # Incluir Remisión porque la tabla puede tener varias
        columnas = ["Remisión", "Material", "Ton"] 
        self.tabla_materiales.setColumnCount(len(columnas))
        self.tabla_materiales.setHorizontalHeaderLabels(columnas)
        self.tabla_materiales.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #008080; color: white; font-weight: bold; border: 1px solid white; }")
        self.tabla_materiales.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla_materiales)

        # 3. Botones de Acción (Fila Inferior)
        btn_layout = QHBoxLayout()
    
        self.btn_finalizar_arribo = QPushButton("FINALIZAR ARRIBO")
        self.btn_finalizar_arribo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        #self.btn_finalizar_arribo.setStyleSheet("background-color: #008080; color: white; padding: 15px;")

        self.btn_add_remision = QPushButton("AGREGAR OTRA REMISIÓN")
        self.btn_add_remision.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        self.btn_add_remision.setStyleSheet("""
            QPushButton {
                background-color: #FFC000; 
                color: #333333; 
                padding: 10px;
                border: none; /* Recomendado para que no salga el borde gris de Windows */
                border-radius: 5px; /* Un pequeño redondeo opcional para modernizar */
            }
            QPushButton:hover {
                background-color: #E6AC00; /* Un tono un poco más oscuro y elegante */
            }
            QPushButton:pressed {
                background-color: #CC9900; /* Efecto al hacer clic */
            }
        """)
        
        self.btn_cancelar_arribo = QPushButton("CANCELAR")
        self.btn_cancelar_arribo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        self.btn_cancelar_arribo.setStyleSheet("""
            QPushButton {
                background-color: #CC0000; 
                color: white; 
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #990000; /* Un rojo más profundo al pasar el mouse */
            }
            QPushButton:pressed {
                background-color: #660000; /* Efecto al hacer clic */
            }
        """)
        

        btn_layout.addWidget(self.btn_finalizar_arribo)
        btn_layout.addWidget(self.btn_add_remision)
        btn_layout.addWidget(self.btn_cancelar_arribo)
        
        layout.addLayout(btn_layout)

        # Conexiones:
        self.btn_add_remision.clicked.connect(self.agregar_nueva_remision_signal.emit)
        self.btn_finalizar_arribo.clicked.connect(self._on_finalizar_arribo_clicked)
        self.btn_cancelar_arribo.clicked.connect(self.cancelar_arribo_signal.emit)

    def _crear_lbl_data(self, titulo: str, valor: str) -> QWidget:
        """Crea un widget compuesto para mostrar un dato."""
        widget = QWidget()
        v_layout = QVBoxLayout(widget)
        v_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #008080;")
        
        lbl_valor = QLabel(valor)
        lbl_valor.setFont(QFont("Arial", 16))
        lbl_valor.setStyleSheet("color: #333333; border-bottom: 2px solid gray; padding-bottom: 5px;")
        
        v_layout.addWidget(lbl_titulo)
        v_layout.addWidget(lbl_valor)
        return widget
        
    def _on_finalizar_arribo_clicked(self):
        """Guarda la selección y emite la señal de finalización."""
        self.session_data.clase_expedicion = self.cmb_clase_expedicion.currentText()
        self.finalizar_arribo_signal.emit()

    def actualizar_datos(self, session_real):
        """Recarga la información inyectando la sesión actual en la GUI."""
        # 1. Actualizar datos comunes
        self.lbl_cliente.findChildren(QLabel)[1].setText(session_real.destinatario_nombre)
        self.lbl_operador.findChildren(QLabel)[1].setText(session_real.operador)
        self.lbl_placa.findChildren(QLabel)[1].setText(session_real.placa)

        # Calculo del peso total
        peso_acumulado = session_real.obtener_peso_total()
        self.lbl_peso_total.findChildren(QLabel)[1].setText(f"{peso_acumulado:,.2f} TON")
        
        # PRESELECCIONAR CLASE DE EXPEDICIÓN DE CLOUDFORT
        clase_epx_cf = session_real.tipo_unidad_cloudfort.upper()[:2]
        for i in range(self.cmb_clase_expedicion.count()):
            if self.cmb_clase_expedicion.itemText(i).startswith(clase_epx_cf):
                self.cmb_clase_expedicion.setCurrentIndex(i)
                break

        # 2. Actualizar tabla de materiales
        self.tabla_materiales.setRowCount(0)
        
        for remision_data in session_real.remisiones_agregadas:
            remision_id = remision_data.get("remision", "N/A")
            materiales = remision_data.get("materiales", [])
            
            for material in materiales:
                row_pos = self.tabla_materiales.rowCount()
                self.tabla_materiales.insertRow(row_pos)
                
                self.tabla_materiales.setItem(row_pos, 0, QTableWidgetItem(remision_id))
                self.tabla_materiales.setItem(row_pos, 1, QTableWidgetItem(material.get("material_denominacion", "")))
                self.tabla_materiales.setItem(row_pos, 2, QTableWidgetItem(f"{material.get('peso_ton', 0):,.2f}"))

class navegar_a_v_final(QWidget):
    """Ventana final de procesamiento: Muestra estado de espera/resultado."""
    regresar_inicio_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_estado = QLabel("ESPERE, ESTAMOS PROCESANDO SU ARRIBO...")
        self.lbl_estado.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setStyleSheet("color: orange;")
        self.lbl_estado.setWordWrap(True)

        # Agregamos el emoji al texto inicial
        self.btn_regresar = QPushButton("🔙 REGRESAR AL INICIO")
        self.btn_regresar.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.btn_regresar.setStyleSheet("""
            QPushButton {
                background-color: #CC0000; 
                color: white; 
                padding: 15px; 
                margin-top: 30px;
                border: none;
                border-radius: 5px; /* Bordes suaves */
            }
            QPushButton:hover {
                background-color: #990000; /* Rojo más oscuro al pasar el mouse */
            }
            QPushButton:pressed {
                background-color: #660000; /* Rojo profundo al dar clic */
            }
        """)
        
        self.btn_regresar.hide() # Oculto inicialmente
        
        layout.addWidget(self.lbl_estado)
        layout.addWidget(self.btn_regresar, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.btn_regresar.clicked.connect(self.regresar_inicio_signal.emit)

    def set_estado(self, mensaje: str, color: str, msg_ult_paso: str = "", mostrar_boton: bool = False):
        """Actualiza el mensaje y visibilidad del botón."""
        self.lbl_estado.setText(mensaje)
        self.lbl_estado.setStyleSheet(f"color: {color};")
        if mostrar_boton:
            self.btn_regresar.show()
        else:
            self.btn_regresar.hide()

# ====================================================================
# VENTANA PRINCIPAL (Contenedor de Ventanas y Lógica de Flujo)
# ====================================================================

class AppWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.sap_manager = SAPManager()
        self.session_data = SessionData() 
        self.logger = LogManager()
        self.cloudfort_manager = CloudFortManager()
        self.email_manager = EmailManager()   
        self.arribos_manager = ArribosManager()

        self.setWindowTitle("KIOSKO ARRIBO - Inicio")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("""
            /* Fondo principal blanco */
            QMainWindow {
                background-color: #FFFFFF;
            }
            
            /* Tipografía moderna para todos los textos */
            QLabel {
                font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
                color: #2D3748; /* Un gris muy oscuro es más moderno que el negro puro */
            }
            
            /* Botones modernos, sin bordes feos y con esquinas redondeadas */
            QPushButton {
                background-color: #008080; /* color institucional */
                color: white;
                border: none;
                border-radius: 8px; /* ¡La magia para quitar lo cuadrado! */
                padding: 12px 24px;
                font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
                font-weight: bold;
                font-size: 24px;
            }
            
            /* Efecto cuando el operador pasa el dedo o el mouse */
            QPushButton:hover {
                background-color: #006666;
            }
            
            QPushButton:pressed {
                background-color: #004d4d;
            }
            
            /* Cajas de texto y menús desplegables redondeados */
            QLineEdit, QComboBox {
                border: 2px solid #E2E8F0;
                border-radius: 6px;
                padding: 8px;
                background-color: #F7FAFC;
                font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
                font-size: 20px;
                color: #2D3748;
            }
            
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #008080; /* Se ilumina al escribir */
            }
        """)
        
        # ====================================================================
        # NUEVO: CONFIGURACIÓN DEL ÍCONO (TÍTULO Y BARRA DE TAREAS)
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_icono = os.path.join(directorio_actual, "images", "logo_short_ico.ico")
        self.setWindowIcon(QIcon(ruta_icono))
        
        # 3. TRUCO PRO: Forzar a Windows a mostrarlo en la barra de tareas
        # (Si no hacemos esto, Windows agrupa la app bajo el logo genérico de Python) #NO FUNCIONA
        try:
            myappid = 'kiosko.autoarribo.produccion.1.0' # ID único inventado para la app
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"Aviso: No se pudo forzar el ícono en la barra de tareas: {e}")

        # Poner el cursor de manita a todos los botones de esta ventana
        for boton in self.findChildren(QPushButton):
            boton.setCursor(Qt.CursorShape.PointingHandCursor)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self._setup_views()

        # ====================================================================
        # MONITOR DE CONEXION A SAP E INTERNET (PING-PONG)
        # ====================================================================
        # 💻 KEEP-ALIVE WINDOWS: Evitamos que el Kiosko entre en reposo
        evitar_bloqueo_windows()
        self.sap_manager.iniciar_keep_alive(intervalo_minutos=13)
        self.hay_internet = True  # Asumimos que inicia con conexión
        
        # --- TEMPORIZADOR PARA PING DE INTERNET ---
        self.timer_internet = QTimer(self)
        self.timer_internet.timeout.connect(self._ping_internet)
        intervalo_ping_minutos = 5
        tiempo_de_revision_ms = intervalo_ping_minutos * 60 * 1000
        print(f"🌐 [RED] Internet iniciado. Intervalo: {intervalo_ping_minutos} min")
        self.timer_internet.start(tiempo_de_revision_ms)


        # --- TEMPORIZADOR PARA ROBOT DESCARGA ZSDMX389 ---
        self.timer_robot_sap = QTimer(self)
        self.timer_robot_sap.timeout.connect(self._ejecutar_robot_zsdmx)
        
        intervalo_robot_minutos = 21  # minutos
        tiempo_robot_ms = intervalo_robot_minutos * 60 * 1000
        print(f"🤖 [SAP] Robot ZSDMX389 iniciado. Intervalo: {intervalo_robot_minutos} min")
        self.timer_robot_sap.start(tiempo_robot_ms)

        # Conexión SAP Keep-Alive SAP 
        self.sap_manager.emitter.keep_alive_signal.connect(self._actualizar_estado_sap)

        # --- TEMPORIZADOR DE AUTO-REINICIO ---
        self.timer_autoreset = QTimer(self)
        self.timer_autoreset.setSingleShot(True)
        self.timer_autoreset.timeout.connect(self.navegar_a_v0)

    def _setup_views(self):
        """Inicializa las 5 vistas (0 a 4) y las añade al QStackedWidget."""
        
        self.v0 = Ventana0_Inicio()
        self.v1 = Ventana1_IngresoRemision() # Ingresar remision
        self.v2 = Ventana2_datos_operador (self.session_data) # Verificar Datos
        self.v3 = Ventana3_Verificacion(self.session_data) #Verificar materiales
        self.v4 = navegar_a_v_final() # Pantalla de espera/resultado
        self.v2_1_facecam = Ventana2_1_DatosOperadorFacecam()
        
        self.stacked_widget.addWidget(self.v0)
        self.stacked_widget.addWidget(self.v1)
        self.stacked_widget.addWidget(self.v2)
        self.stacked_widget.addWidget(self.v3)
        self.stacked_widget.addWidget(self.v4)
        self.stacked_widget.addWidget(self.v2_1_facecam)

        # Conexión de señales de navegación
        self.v0.nuevo_arribo_signal.connect(self.navegar_a_v1)
        self.v1.buscar_remision_signal.connect(self.obtener_datos_remision)

        self.v1.cancelar_arribo_signal.connect(
            lambda: self.finalizar_con_error(
                paso_actual="Btn Cancelar V1", 
                mensaje_error="Cancelado por usuario al ingresar remisión.", 
                titulo_pantalla="ARRIBO CANCELADO"
            )
        )

        self.v2_1_facecam.tiempo_terminado_signal.connect(self.navegar_v2_validar_op)

        self.v2.confirmar_operador_signal.connect(self.validar_placa_CloudFort)
        self.v2.cancelar_arribo_signal.connect(
            lambda: self.finalizar_con_error(
                paso_actual="Btn Cancelar V2", 
                mensaje_error="Operador rechazó datos (No soy yo).", 
                titulo_pantalla="ARRIBO CANCELADO"
            )
        )
        self.v3.agregar_nueva_remision_signal.connect(self.navegar_a_v1_add_mode)
        self.v3.finalizar_arribo_signal.connect(self.navegar_a_v_final)
        self.v3.cancelar_arribo_signal.connect(
            lambda: self.finalizar_con_error(
                paso_actual="Btn Cancelar V3", 
                mensaje_error="Cancelado por el usuario durante verificación de materiales.", 
                titulo_pantalla="ARRIBO CANCELADO"
            )
        )
        self.v4.regresar_inicio_signal.connect(self.navegar_a_v0)
        
        self.stacked_widget.setCurrentIndex(0) # Iniciar en la Ventana 0

    def _ejecutar_robot_zsdmx(self):
        """
        Función disparada cada 20 minutos. Lanza el robot pasando la ruta global
        para mantener actualizada la contingencia local (Plan C) SOLO PENDIENTES.
        """
        if self.hay_internet and self.sap_manager.validar_conexion():
            print(f"[{time.strftime('%H:%M:%S')}]⏳ [ROBOT] Iniciando actualización programada de ZSDMX389 (Pendientes)...")
            try:
                # Le pasamos el nuevo parámetro 'tipo_descarga'
                self.sap_manager.zsdmx389_robot(self.session_data.ruta_base_drive, tipo_descarga="pendientes")
            except Exception as e:
                print(f"⚠️ [{time.strftime('%H:%M:%S')}] Error en ejecución automática del robot ZSDMX389: {e}")
        else:
            print(f"⚠️ [{time.strftime('%H:%M:%S')}] [ROBOT] Descarga de contingencia omitida (Sin internet o sin SAP).")


    # --- Métodos de Navegación ---

    def navegar_a_v0(self):
        """Navega a V0 y reinicia la sesión (nuevo arribo)."""
        self.session_data.reset_session()
        self.v1.limpiar()
        self.stacked_widget.setCurrentIndex(0)
        self.setWindowTitle("KIOSKO ARRIBO - Inicio")

    def navegar_a_v1(self):
        """Navega a V1 y reinicia la sesión (nuevo arribo)."""
        self._ping_internet()
        self.session_data.reset_session()
        self.session_data.ultimo_paso = "V1_Ingreso_Remision"
        nuevo_id = self.logger.generar_siguiente_id_movimiento()
        self.session_data.id_movimiento = nuevo_id
        print(f"🚀 Inició Nuevo Arribo. ID Generado: {nuevo_id}")

        self.v1.limpiar()
        self.stacked_widget.setCurrentIndex(1)
        self.setWindowTitle("KIOSKO ARRIBO - Paso 1: Ingresar Remisión")
        
    def navegar_a_v1_add_mode(self):
        """Navega a V1 sin reiniciar la sesión (agregar remisión)."""
        self.v1.limpiar()
        rem_count = len(self.session_data.remisiones_agregadas) + 1
        self.stacked_widget.setCurrentIndex(1)
        self.setWindowTitle(f"KIOSKO ARRIBO - Ingresar Remisión {rem_count}")

    def navegar_v2_1_validar_op_facecam (self):
        self.stacked_widget.setCurrentWidget(self.v2_1_facecam)
        # 3. ⏱️ Encendemos el reloj de 10 segundos
        self.v2_1_facecam.iniciar_simulacion()

    def navegar_v2_validar_op (self):
        """Navegar a V2 validar operador y placas"""
        self.v2.actualizar_datos(self.session_data)

        self.stacked_widget.setCurrentIndex(2)
        self.setWindowTitle(f"KIOSKO ARRIBO - Paso 2: Validar Operador: {self.session_data.operador} - {self.session_data.placa}")

    def navegar_a_v3(self):
        """Navega a v3 y actualiza los datos."""
        self.session_data.ultimo_paso = "V3_Verificacion_Materiales"
        self.v3.actualizar_datos(self.session_data)
        self.stacked_widget.setCurrentIndex(3)
        self.setWindowTitle("KIOSKO ARRIBO - Paso 3: Verificar Carga")
    
    def navegar_a_v_final(self):
        """
        Cambia a la Ventana 4 y le da un respiro al procesador antes de atacar SAP.
        """
        self.v4.set_estado("ESPERE, ESTAMOS PROCESANDO SU ARRIBO...", "orange", False)
        self.stacked_widget.setCurrentIndex(4) # V4 es el index 4
        self.setWindowTitle("KIOSKO ARRIBO - Paso 4: Procesando Arribo...")
        
        #print(f"DEBUG: Clase Expedición seleccionada en GUI: {self.session_data.clase_expedicion}")
        
        # ⏳ LA CLAVE: Esperamos 1 segundo para que la GUI se pinte y SAP respire
        QTimer.singleShot(1000, self._procesar_arribo_real)

    def _procesar_arribo_real(self):
        """
        Director de orquesta final: 
        Validación Infalible -> Robot SAP (Báscula + Transporte) -> Log Excel -> Correos.
        """
        QApplication.processEvents() # Refrescamos la GUI por si acaso

        try:
            # ================================================================
            # PASO A: VALIDACIÓN DE REGLAS DE EXPEDICIÓN (MÉTODO INFALIBLE)
            # ================================================================
            self.session_data.registrar_paso("SAP: Validando Reglas", "Verificando peso y material")
            self.v4.set_estado("Validando reglas operativas...", "blue", mostrar_boton=False)
            QApplication.processEvents()

            # Evaluamos con el método infalible de SAPManager
            clase_exp_calculada = self.sap_manager.validar_clase_expedicion(
                remisiones=self.session_data.remisiones_agregadas,
                tipo_unidad_cloudfort=self.session_data.tipo_unidad_cloudfort
            )
            
            # Aislamos solo los 2 caracteres técnicos (Ej. "F3")
            clase_exp_cmb = self.session_data.clase_expedicion[:2].upper()
            
            # Autocorrección del sistema
            if clase_exp_calculada != clase_exp_cmb:
                mensaje_correccion = f"Op. eligió {clase_exp_cmb}. Sistema forzó {clase_exp_calculada} por reglas operativas."
                self.session_data.registrar_paso("Sistema: Autocorrección", mensaje_correccion)
                clase_exp_final = clase_exp_calculada
            else:
                clase_exp_final = clase_exp_cmb
                
            self.session_data.clase_expedicion = clase_exp_final # Actualizamos la sesión real

            # ================================================================
            # PASO B: PREPARACIÓN DE DATOS
            # ================================================================
            remisiones = self.session_data.remisiones_agregadas
            modalidad = self.session_data.modalidad
            operador = self.session_data.operador
            placas = self.session_data.placa
            fch_checklist = self.session_data.fecha_checklist
            
            # Extraemos el centro de expedición asumiendo que está en el primer material
            centro = "MX47" # Valor fallback
            if remisiones and "materiales" in remisiones[0] and remisiones[0]["materiales"]:
                centro = remisiones[0]["materiales"][0].get("cen_exp", "MX47")
                
            clase_entrega = remisiones[0].get("clase_entrega", "")

            # ================================================================
            # PASO C y D: BIFURCACIÓN DE ORÍGENES DE DATOS
            # ================================================================
            origen = self.session_data.origen_datos

            if origen == "A: Web Service":
                # ----------------------------------------------------------------
                # MODO A: WEB SERVICE (CAMA PUESTA PARA EL FUTURO)
                # ----------------------------------------------------------------
                self.session_data.registrar_paso("API CF: Inicio Kiosko", "Registrando en Kiosko vía Web Service")
                self.v4.set_estado("Creando folio de báscula en CloudFort...", "blue", "Ejecutando API", mostrar_boton=False)
                QApplication.processEvents()

                # TODO: Implementar en manager_cloudfort.py
                # resultado_kiosko = self.cloudfort_manager.crear_folio_bascula(...)
                # self.session_data.registrar_paso("API CF: Folio Creado", f"Kiosko: {resultado_kiosko}")
                
                self.v4.set_estado("Creando transporte en CloudFort...", "blue", "Ejecutando API", mostrar_boton=False)
                QApplication.processEvents()
                
                # TODO: Implementar en manager_cloudfort.py
                # no_transporte = self.cloudfort_manager.crear_transporte(...)
                # self.session_data.transporte_sap = str(no_transporte).strip()
                # self.session_data.registrar_paso("API CF: Transporte Creado", f"Transporte: {self.session_data.transporte_sap}")

                # CIERRE EXITOSO (SIMULADO HASTA TENER WS)
                self.session_data.estatus_arribo_mensaje = "Proceso Web Service exitoso"
                self.session_data.estatus_arribo_ultimo_paso = "OK"
                mensaje_usuario = f"¡ARRIBO EXITOSO (WS)!\n Turno: {self.session_data.ticket_id}"
                color_final = "green"

            elif origen == "C: Contingencia":
                # ----------------------------------------------------------------
                # MODO C: CONTINGENCIA LOCAL
                # ----------------------------------------------------------------
                self.session_data.registrar_paso("MODO CONTINGENCIA", "Omitiendo folio y transporte en SAP.")
                self.v4.set_estado("Guardando arribo localmente (Modo Contingencia)...", "#D4A017", "Guardando Local", mostrar_boton=False)
                QApplication.processEvents()
                
                # CIERRE EXITOSO EN CONTINGENCIA
                self.session_data.estatus_arribo_mensaje = "Guardado Localmente (Contingencia)"
                
                # IMPORTANTE: Mantenemos "OK" para que el bloque 'finally' dispare el tablero y los correos
                self.session_data.estatus_arribo_ultimo_paso = "OK" 
                
                mensaje_usuario = f"¡ARRIBO EN CONTINGENCIA!\n Turno: {self.session_data.ticket_id}\n(Folio SAP Pendiente)"
                color_final = "#D4A017" # Dorado/Naranja
                
                # Pequeña pausa visual para que el operador lea el estado
                time.sleep(1) 

            else:
                # ----------------------------------------------------------------
                # MODO B: ROBOT SAP (DEFAULT / ACTUAL)
                # ----------------------------------------------------------------
                self.session_data.registrar_paso("SAP: Inicio Kiosko", "Registrando en Kiosko")
                self.v4.set_estado("Creando folio de báscula en SAP...", "blue", "Ejecutando Kiosko", mostrar_boton=False)
                QApplication.processEvents()

                resultado_kiosko = self.sap_manager.crear_folio_bascula(
                    remisiones=remisiones,
                    centro_expedicion=centro,
                    tipo_remision=clase_entrega, 
                    operador=operador,
                    placas=placas,
                    modalidad=modalidad
                )
                self.session_data.registrar_paso("SAP: Folio Creado", f"Kiosko: {resultado_kiosko}")

                # ⏳ PREVENCIÓN DEL ERROR COM (-2147483638): Dormimos el script medio segundo
                time.sleep(0.5)

                self.session_data.registrar_paso("SAP: Inicio Transporte", "Creando en VT01N")
                self.v4.set_estado("Creando transporte en SAP (VT01N)...", "blue", "Ejecutando VT01N", mostrar_boton=False)
                QApplication.processEvents()

                no_transporte = self.sap_manager.crear_transporte(
                    remisiones=remisiones,
                    centro_expedicion=centro,
                    modalidad=modalidad,
                    operador=operador,
                    placas=placas,
                    clase_expedicion_f=clase_exp_final, 
                    fecha_checklist= fch_checklist
                )

                # Validar y guardar transporte real
                if no_transporte and str(no_transporte).strip().startswith("48"):
                    self.session_data.transporte_sap = str(no_transporte).strip()
                    self.session_data.registrar_paso("SAP: Transporte Creado", f"Transporte: {self.session_data.transporte_sap}")
                else:
                    raise Exception(f"Transporte inválido generado por SAP: {no_transporte}")

                # CIERRE EXITOSO NORMAL
                self.session_data.estatus_arribo_mensaje = "Proceso SAP exitoso"
                self.session_data.estatus_arribo_ultimo_paso = "OK"
                mensaje_usuario = f"¡ARRIBO EXITOSO!\n Turno: {self.session_data.ticket_id}"
                color_final = "green"

        finally:
            # ================================================================
            # BLOQUE FINALLY: SIEMPRE SE EJECUTA (ÉXITO O ERROR)
            # ================================================================
            self.session_data.fin_arribo = datetime.now()
            self.v4.set_estado("Guardando registros del sistema...", "blue", "Guardando...", mostrar_boton=False)
            QApplication.processEvents()

            #print("💾 Guardando bitácora en Excel Histórico...")
            try:
                self.logger.guardar_evento(self.session_data)
            except Exception as e_log:
                print(f"⚠️ Error al guardar Excel Log: {e_log}")

            if self.session_data.estatus_arribo_ultimo_paso == "OK":
                #print("📡 Registrando en Tablero de Arribos...")
                try:
                    self.arribos_manager.registrar_nuevo_arribo(self.session_data)
                except Exception as e_arribos:
                    print(f"⚠️ Error al registrar en Arribos: {e_arribos}")

                print("✉️ Enviando notificación a Embarques...")
                try:
                    self.email_manager.enviar_aviso_arribo(self.session_data)
                except Exception as e_mail:
                    print(f"⚠️ Error envío correo (no crítico): {e_mail}")

            # ACTUALIZACIÓN VISUAL FINAL
            self.v4.set_estado(
                mensaje=mensaje_usuario, 
                color=color_final, 
                msg_ult_paso="Proceso Finalizado", 
                mostrar_boton=True
            )

            print("⏳ Iniciando temporizador de reinicio automático (3 min)...")
            self.timer_autoreset.start(180000)
            

    # --- Lógica de Procesamiento ---

    def validar_placa_CloudFort(self):
        """
        Valida las placas del operador.
        Soporta modo simulación (mock), modo real (Web Service) y modo CONTINGENCIA.
        """
        placa = self.session_data.placa
        self.session_data.ultimo_paso = "V2_Validacion_CloudFort"
        self.session_data.registrar_paso("[API CF] Validar Placa", f"Iniciando validación para {placa}")

        # ====================================================================
        # VARIABLE DE CONTROL (True = Simulación, False = Web Service Real)
        # ====================================================================
        mock_placa = False
        respuesta_cloudfort = {}

        if not self.hay_internet:
            # ====================================================================
            # 1A. MODO CONTINGENCIA (Sin red: Asumimos Checklist manual OK)
            # ====================================================================
            print("⚙️ [CONTINGENCIA] Sin internet. Omitiendo validación CloudFort...")
            self.session_data.registrar_paso("[API CF] Contingencia", "Validación WS omitida por falta de red. Check-list manual asumido OK.")
            
            # Simulamos un ofertamiento de hace 5 minutos para que pase la regla de tiempo (menor a 120 min)
            fecha_simulada_dt = datetime.now() - timedelta(minutes=5)
            
            respuesta_cloudfort = {
                "fch_hr_ofertamiento": fecha_simulada_dt.strftime("%Y-%m-%d %H:%M:%S"), 
                "checklist_ruleta": "VERDE",
                "dopping": "NEGATIVO",
                "clase_exp": "F1" # Este valor por defecto será corregido luego por SAPManager basado en el peso real
            }

        elif mock_placa:
            # ====================================================================
            # 1B. SIMULACIÓN DE RESPUESTA (Aleatoria para pruebas locales)
            # ====================================================================
            print("⚙️ [MOCK] Ejecutando validación simulada de CloudFort...")
            minutos_atras = random.randint(10, 150)
            fecha_simulada_dt = datetime.now() - timedelta(minutes=minutos_atras)

            respuesta_cloudfort = {
                "fch_hr_ofertamiento": fecha_simulada_dt.strftime("%Y-%m-%d %H:%M:%S"), 
                "checklist_ruleta": random.choices(["VERDE", "ROJO"], weights=[80, 20], k=1)[0],
                "dopping": random.choice(["0", "NEGATIVO", "POSITIVO", "FALSEO INFORMACIÓN", "NEGACIÓN PRUEBA"]),
                "tipo_unidad": random.choice(["F1", "F2", "F3", "F4", "F5", "F7"])
            }
        else:
            # ====================================================================
            # 1C. LLAMADA REAL AL WEB SERVICE
            # ====================================================================
            try:
                respuesta_cloudfort = self.cloudfort_manager.validar_placa(placa)
            except Exception as e:
                # Si falla la red de forma intermitente justo aquí, se bloquea. 
                self.session_data.registrar_paso("[API CF] Error", str(e))
                return self.finalizar_con_error(
                    paso_actual="V2_Validacion_CloudFort",
                    mensaje_error=f"Error de conexión con CloudFort:\n{str(e)}",
                    titulo_pantalla="ERROR DE RED"
                )

        # Validación de seguridad: Asegurar que la respuesta devuelta tenga los datos mínimos
        if not respuesta_cloudfort or "fch_hr_ofertamiento" not in respuesta_cloudfort:
            return self.finalizar_con_error(
                paso_actual="V2_Validacion_CloudFort",
                mensaje_error="La respuesta no contiene datos válidos para procesar el arribo.",
                titulo_pantalla="DATOS INVÁLIDOS"
            )
      
        # ====================================================================
        # 2. PROCESAMIENTO DE FECHA Y GENERACIÓN DE TICKET
        # ====================================================================
        
        # A. Convertimos el TEXTO a OBJETO DATETIME para poder calcular
        try:
            fecha_checklist = datetime.strptime(respuesta_cloudfort.get("fch_hr_ofertamiento", ""), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            fecha_checklist = datetime.now()

        # B. Generamos el Ticket ID basado en la fecha del checklist
        ticket_id = fecha_checklist.strftime("%Y%m%d_%H%M%S")
        
        # C. Guardamos en SessionData
        self.session_data.ticket_id = ticket_id
        self.session_data.fecha_checklist = respuesta_cloudfort.get("fch_hr_ofertamiento", "")
        self.session_data.tipo_unidad_cloudfort = str(respuesta_cloudfort.get("clase_exp", "F1"))
        
        self.session_data.registrar_paso("[API CF] Ticket Creado", f"ID: {ticket_id}")

        # ====================================================================
        # 3. CÁLCULO DE TIEMPO (AHORA - OFERTAMIENTO) Para determinar arribo válido
        # ====================================================================
        
        ahora = datetime.now()
        diferencia = ahora - fecha_checklist
        minutos_transcurridos = diferencia.total_seconds() / 60
        
        # ====================================================================
        # 4. REGLAS DE NEGOCIO
        # ====================================================================
        
        # Regla 1: Tiempo límite (120 min)
        # Nota: Aquí tienes 600, asumo que expandiste el margen a 10 horas en desarrollo.
        tiempo_ok = minutos_transcurridos <= 600
        
        # Reglas de Seguridad
        ruleta_verde = str(respuesta_cloudfort.get("checklist_ruleta", "")).upper() == "VERDE"
        dopping_negativo = str(respuesta_cloudfort.get("dopping", "")).upper() == "NEGATIVO"

        pasa_seguridad = False
        motivo_bloqueo = ""

        if not tiempo_ok:
            motivo_bloqueo = f"Tiempo para arribo excedido \n fecha de check-list: \n {fecha_checklist} > 120 min"
        else:
            if ruleta_verde:
                pasa_seguridad = True 
            else:
                if dopping_negativo:
                    pasa_seguridad = True 
                else:
                    estatus_dopping = str(respuesta_cloudfort.get("dopping", "DESCONOCIDO")).upper()
                    if estatus_dopping == "0":
                        motivo_bloqueo = "RULETA ROJA Y DOPPING PENDIENTE."
                    else:
                        motivo_bloqueo = f"BLOQUEO SEGURIDAD: DOPPING {estatus_dopping}."

        # ====================================================================
        # 5. RESULTADO Y LOGGING
        # ====================================================================
        
        if pasa_seguridad:
            print("✅ Validación DE SEGURIDAD Exitosa.")
            self.session_data.registrar_paso("[API CF] Resultado", "Validación Exitosa (Tiempo y Seguridad OK)")
            self.navegar_a_v3()
        else:
            print(f"❌: Acceso denegado. {motivo_bloqueo}")
            self.finalizar_con_error(
                paso_actual="V2_Validacion_CloudFort",
                mensaje_error=motivo_bloqueo,
                titulo_pantalla="ACCESO DENEGADO"
            )
    
    def finalizar_con_error(self, paso_actual: str, mensaje_error: str, titulo_pantalla: str):
            """
            Maneja centralizadamente cualquier error terminal (SAP, CloudFort, Validaciones).
            1. Registra el paso en memoria.
            2. Cierra el ciclo de tiempo (fin_arribo).
            3. Guarda el log en excel. (Proximante lo envía a CF)
            4. Muestra la pantalla roja (V4).
            """
            # 1. Registrar en Memoria (RAM)
            self.session_data.registrar_paso(paso_actual, f"Error: {mensaje_error}")
            
            # 2. Marcar hora de fin
            self.session_data.fin_arribo = datetime.now()

            # 3. GUARDAR EN EXCEL
            try:
                self.logger.guardar_evento(self.session_data)
            except Exception as e:
                pass

            # 4. Actualizar Interfaz (GUI) a Pantalla Roja
            self.v4.set_estado(
                mensaje=f"{titulo_pantalla}:\n{mensaje_error}",
                msg_ult_paso=f"Fallo en {paso_actual}",
                color="red",
                mostrar_boton=True
            )
            
            # 5. Navegar
            self.stacked_widget.setCurrentIndex(4) # Ir a pantalla final

            # 6. limpiar el log, pero el historial ya está a salvo.
            self.session_data.reset_session()
            
    def obtener_datos_remision(self, remision: str):
            """
            Director de orquesta. Busca datos (Plan A, B, C) y luego evalúa reglas de negocio.
            """
            # =================================================================
            # FUNCIONES INTERNAS (PLANES)
            # =================================================================
            def _metodo_a_ws(rem: str) -> dict:
                return self.cloudfort_manager.obtener_datos_remision(rem) 

            def _metodo_b_robot(rem: str) -> dict:
                return self.sap_manager.extraer_datos_remision(rem)

            
            def _metodo_c_excel(rem: str) -> dict:
                # Ahora simplemente llamamos a nuestro Manager parametrizado
                resultado_contingencia = self.arribos_manager.leer_zsdmx389_local(
                    ruta_base_drive=self.session_data.ruta_base_drive, 
                    rem=rem, 
                    tipo_archivo="pendientes"
                )
                return resultado_contingencia

            """
                #import json # import solo para ver el json en consola

                # Asignamos el diccionario a una variable temporal
                resultado_contingencia = {
                    "remision": rem_limpia,
                    "cliente": str(row_cabecera.get("Nombre Cliente", "")).strip(),
                    "cliente_num": str(row_cabecera.get("Cliente", "")).strip(),
                    "destinatario_nombre": str(row_cabecera.get("Nombre Destinatario", "")).strip(),
                    "destinatario_num": str(row_cabecera.get("Destinatar", "")).strip(),

                    "fch_cita_carga": str(row_cabecera.get("Destinatar", "")).strip(),

                    "operador": str(row_cabecera.get("Número de carta de p", "")).strip(), 
                    "placa": str(row_cabecera.get("Número de", "")).strip(),
                    "poblacion": str(row_cabecera.get("Población", "")).strip(),
                    "ruta": str(row_cabecera.get("Ruta", "")).strip(),
                    "modalidad": str(row_cabecera.get("Pto Descar", "")).strip().upper(),
                    "clase_expedicion": str(row_cabecera.get("Ex", "")).strip(), 
                    "clase_entrega": str(row_cabecera.get("Clase de e", "")).strip(), 
                    "st_transporte": "A",
                    "st_salida_merc": "A",
                    "st_factura": "A",
                    "materiales": materiales_lista
                }
                
                # 🕵️‍♂️ IMPRIMIR EL JSON FORMATEADO EN CONSOLA
                #print(f"\n📦 === DEBUG JSON CONTINGENCIA (Remisión: {rem_limpia}) ===")
                #print(json.dumps(resultado_contingencia, indent=4, ensure_ascii=False))
                #print("========================================================\n")
                
                return resultado_contingencia """
            # =================================================================
            # 1. INICIO Y EXTRACCIÓN DE DATOS
            # =================================================================
            self.v1.txt_remision.setDisabled(True)
            self.statusBar().showMessage(f"Buscando remisión {remision}...")
            
            # NUEVO PARADIGMA DE LOGS: Actor | Acción | Detalle
            self.session_data.registrar_paso("[USUARIO] Ingreso", f"Escaneó remisión: {remision}")

            datos_sap = None
            origen_datos = ""

            # --- PLAN A: API WEB CLOUDFORT ---
            try:
                self.statusBar().showMessage(f"Plan A: Consultando API CloudFort...")
                datos_sap = _metodo_a_ws(remision)
                origen_datos = "A: Web Service"
            except Exception as e_api:
                self.session_data.registrar_paso("[API CF] Falla", str(e_api))

                # --- PLAN B: ROBOT SAP ---
                if datos_sap is None:
                    try:
                        self.statusBar().showMessage(f"Plan B: Desplegando Robot SAP...")
                        self.session_data.registrar_paso("[SAP] Inicio Robot", "Buscando en SAP")
                        datos_sap = _metodo_b_robot(remision) 
                        origen_datos = "B: Robot SAP"

                    
                    except SAPError as e_sap:
                        # ERROR DE NEGOCIO (Ej. "La entrega ya ha sido procesada")
                        #self.session_data.registrar_paso("[SAP] Inicio Robot", f"Bloqueo de SAP: {str(e_sap)}")
                        self.v1.txt_remision.setDisabled(False) 
                        return self.finalizar_con_error(
                            paso_actual="[SAP] Validación",
                            mensaje_error=str(e_sap),
                            titulo_pantalla="MENSAJE DE SAP"
                        )
                
                    except Exception as e_robot:
                        # FALLA TÉCNICA (SAP Cerrado, Sin internet, Error de código)
                        self.session_data.registrar_paso("[SAP] Falla Técnica", str(e_robot))

                        # --- PLAN C: EXCEL CONTINGENCIA ---
                        if datos_sap is None:
                            try:
                                self.statusBar().showMessage(f"Plan C: Buscando en Archivo Local Excel...")
                                self.session_data.registrar_paso("[EXCEL] Inicio", "Buscando en zsdmx389")
                                datos_sap = self.arribos_manager.leer_zsdmx389_local(
                                    ruta_base_drive=self.session_data.ruta_base_drive, 
                                    rem=remision, 
                                    tipo_archivo="pendientes"
                                )
                                origen_datos = "C: Contingencia"

                            except Exception as e_excel:
                                self.session_data.registrar_paso("[EXCEL] Falla", str(e_excel))

            self.v1.txt_remision.setDisabled(False) # Reactivamos siempre el campo

            # =================================================================
            # 2. EVALUACIÓN DE REGLAS DE NEGOCIO
            # =================================================================
            if datos_sap is not None:
                self.session_data.registrar_paso(f"[SISTEMA] Extracción", f"Datos obtenidos vía {origen_datos}")
                
                # --- LÓGICA DE CONTINGENCIA ---
                self.session_data.origen_datos = origen_datos
                if origen_datos == "C: Contingencia":
                    self.session_data.estatus_contingencia = "PENDIENTE"
                    self.session_data.folio_contingencia = "EMB_1"

                # Extraemos los estatus para evaluar
                st_factura = datos_sap.get("st_factura", "")
                st_transporte = datos_sap.get("st_transporte", "")
                st_salida = datos_sap.get("st_salida_merc", "")
                modalidad = datos_sap.get("modalidad", "").upper()
                materiales = datos_sap.get("materiales", [])
                c_exp_sap = materiales[0].get("cen_exp", "") if materiales else ""
            
                errores_criticos = ["B", "C"]
                motivo_rechazo = ""
                
                # APLICAMOS LAS REGLAS DE NEGOCIO:
                if not materiales: 
                    motivo_rechazo = "Remisión sin materiales."
                elif modalidad == "ENTREGADO": 
                    motivo_rechazo = f"Modalidad no permitida: {modalidad} - Remisión NO aplica en KIOSKO."
                elif c_exp_sap and c_exp_sap not in self.session_data.planta_gui_codigos:
                    motivo_rechazo = f"Esta remisión es del centro ({c_exp_sap}) y no pertenece a {self.session_data.planta_gui_nombre}."
                elif st_factura in errores_criticos:
                    motivo_rechazo = f"Remisión ya Facturada (Estatus {st_factura})."
                elif st_transporte in errores_criticos:
                    motivo_rechazo = f"Remisión con número de transporte (Estatus {st_transporte})."
                elif st_salida in errores_criticos:
                    motivo_rechazo = f"Salida de Mercancías ya realizada (Estatus {st_salida})."
                
                
                # ¿PASÓ LAS REGLAS?
                if motivo_rechazo != "":
                    # RECHAZADO
                    #self.session_data.registrar_paso("[SISTEMA] Reglas Negocio", f"Bloqueo: {motivo_rechazo}")
                    return self.finalizar_con_error(
                        paso_actual="[SISTEMA] Reglas Negocio",
                        mensaje_error=motivo_rechazo,
                        titulo_pantalla="ESTATUS DE REMISIÓN"
                    )
                else:
                    # APROBADO: Avanzamos a la Ventana 2
                    self.session_data.registrar_paso("[SISTEMA] Reglas Negocio", "Remisión disponible OK")
                    # 🟢📝 
                    self.session_data.agregar_remision(datos_sap)  #--> Aqui mandamos a guardar toda la info de datos_sap
                    self.navegar_v2_1_validar_op_facecam()
                    
            else:
                # FRACASO TOTAL EN LA BÚSQUEDA
                mensaje_fatal = "No se pudo localizar la remisión en el sistema (API, SAP ni Local). Favor de pasar a ventanilla."
                self.session_data.registrar_paso("[SISTEMA] Error Crítico", "No se encontró información en ningún medio.")
                
                self.finalizar_con_error(
                    paso_actual="[SISTEMA] Extracción",
                    mensaje_error=mensaje_fatal,
                    titulo_pantalla="REMISIÓN NO ENCONTRADA"
                )

    def _actualizar_estado_sap(self, mensaje: str, estilo: str = "gray"):
        """Muestra el estado del sistema (SAP Keep-Alive) en la barra de estado."""
        self.statusBar().setStyleSheet(f"color: {estilo};")
        self.statusBar().showMessage(f"Estado del Sistema: {time.strftime('%H:%M:%S')} - {mensaje}")

    def closeEvent(self, event):
        """Detiene el Keep-Alive al cerrar."""
        self.sap_manager.detener_keep_alive()
        restaurar_energia_windows()
        super().close()

    def _ping_internet(self):
        """
        Revisa la conexión a Internet intentando alcanzar el DNS de Google.
        Actualiza la barra de estado y dispara sincronizaciones si regresa la red.
        """
        import socket
        estado_actual = False
        
        try:
            # Intenta conectarse al DNS de Google (8.8.8.8) en el puerto 53
            socket.setdefaulttimeout(2)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("8.8.8.8", 53))
            s.close()
            estado_actual = True
        except OSError:
            estado_actual = False

        # --- LÓGICA DE TRANSICIÓN Y ESTADOS ---
        
        if not estado_actual:
            # CASO 1: No hay internet (Ya sea que se acaba de caer o sigue caído)
            if self.hay_internet:
                self.hay_internet = False
                print(f"[{time.strftime('%H:%M:%S')}] 🌐 [RED] Conexión perdida. Cambiando a Modo Contingencia.")
                
            self.statusBar().setStyleSheet("color: red; font-weight: bold;")
            self.statusBar().showMessage(f"⚠️ [{time.strftime('%H:%M:%S')}] SIN CONEXIÓN A INTERNET. Kiosko operando en Modo Contingencia Local.")
            
        else:
            if not self.hay_internet:
                # CASO 2: No había internet pero ahora ya hay (El internet REGRESÓ)
                self.hay_internet = True
                self.statusBar().setStyleSheet("color: green;")
                self.statusBar().showMessage(f"✅ [{time.strftime('%H:%M:%S')}] Conexión a Internet RECUPERADA. Iniciando sincronización...")
                print(f"✅ [{time.strftime('%H:%M:%S')}] 🌐  [RED] Conexión recuperada. Ejecutando pendientes...")
                
                # Disparamos la lectura del Excel para procesar contingencias
                self._procesar_contingencias_pendientes()
                
            else:
                # CASO 3: Hay internet estable (Se mantiene la conexión)
                self.statusBar().setStyleSheet("color: green;")
                self.statusBar().showMessage(f"✅ [{time.strftime('%H:%M:%S')}] Trabajando con internet")
        # Nota: Internet caído (False y False), no hace nada.

    def _procesar_contingencias_pendientes(self):
        import pandas as pd
        """
        Lee arribos.xlsx con Pandas, busca estatus 'PENDIENTE', 
        ejecuta Robot SAP y Web Service, y actualiza a 'CERRADO'.
        """
        # 1. Validar conexión y recursos antes de arrancar
        if not self.hay_internet:
            return

        # Usamos la ruta operativa configurada en el manager de arribos
        ruta_excel = self.arribos_manager.ruta_completa
        import os
        if not os.path.exists(ruta_excel):
            return

        self.statusBar().showMessage("🔄 [SYNC] Buscando operaciones en contingencia para sincronizar...")
        print("⚙️ [SYNC] Buscando operaciones en contingencia para sincronizar...")

        try:
            # 1. pd.read_excel(...)
            df = pd.read_excel(ruta_excel, engine='openpyxl')
        except Exception as e:
            print(f"❌ [SYNC] Error leyendo excel de arribos: {e}")
            return

        # 2. Filtrar filas donde 'estatus_contingencia' == 'PENDIENTE'
        pendientes = df[df['estatus_contingencia'] == 'PENDIENTE']

        if pendientes.empty:
            print("✅ [SYNC] No hay contingencias pendientes.")
            self.statusBar().showMessage("✅ [SYNC] Contingencias al día.")
            return

        # Agrupar por 'ticket' (cada ticket es un camión único, aunque tenga varias filas de materiales)
        tickets_pendientes = pendientes.groupby('ticket')
        hubo_cambios = False

        for ticket_id, grupo in tickets_pendientes:
            try:
                print(f"🚀 [SYNC] Procesando ticket contingencia: {ticket_id}")
                self.statusBar().showMessage(f"🔄 Sincronizando arribo pendiente: {ticket_id}")
                
                # --- RECONSTRUCCIÓN DE VARIABLES DESDE EL DATAFRAME ---
                primera_fila = grupo.iloc[0]
                
                centro = primera_fila.get('c_exp', 'MX47')
                clase_entrega = primera_fila.get('clase_entrega', '')
                operador = primera_fila.get('operador', '')
                placas = primera_fila.get('placas', '')
                modalidad = primera_fila.get('modalidad', '')
                clase_exp_final = primera_fila.get('clase_expedicion', '')
                fch_checklist = str(primera_fila.get('fch_checklist', ''))
                origen_programado = primera_fila.get('origen_datos', '')

                # Reconstruir la lista de diccionarios de remisiones y materiales requerida por SAP/WS
                remisiones_dict = {}
                for _, row in grupo.iterrows():
                    rem = str(row['remision'])
                    if rem not in remisiones_dict:
                        remisiones_dict[rem] = {
                            'remision': rem,
                            'clase_entrega': str(row.get('clase_entrega', '')),
                            'materiales': []
                        }
                    remisiones_dict[rem]['materiales'].append({
                        'cen_exp': str(row.get('c_exp', '')),
                        'peso_ton': float(row.get('ton', 0.0)),
                        'material': str(row.get('material_cod', '')),
                        'gpo_material': str(row.get('gpo_material', ''))
                    })
                remisiones = list(remisiones_dict.values())

                # 3. Por cada fila, intentar Robot SAP / WS CloudFort.
                exito_sincronizacion = False
                transporte_generado = ""

                # ----------------------------------------------------------------
                # MODO A: WEB SERVICE (CAMA PUESTA PARA EL FUTURO)
                # ----------------------------------------------------------------
                if "Web Service" in origen_programado:
                    print(f"📡 [API CF] Registrando contingencia {ticket_id} vía Web Service")
                    
                    # TODO: Implementar en manager_cloudfort.py
                    # resultado_kiosko = self.cloudfort_manager.crear_folio_bascula(...)
                    # no_transporte = self.cloudfort_manager.crear_transporte(...)
                    # transporte_generado = str(no_transporte).strip()
                    
                    exito_sincronizacion = True # Simulado hasta tener WS

                # ----------------------------------------------------------------
                # MODO B: ROBOT SAP (DEFAULT / ACTUAL)
                # ----------------------------------------------------------------
                elif self.sap_manager.validar_conexion():
                    print(f"🤖 [SAP] Iniciando sincronización de {ticket_id} en Kiosko")
                    
                    # Crear Folio
                    resultado_kiosko = self.sap_manager.crear_folio_bascula(
                        remisiones=remisiones,
                        centro_expedicion=centro,
                        tipo_remision=clase_entrega, 
                        operador=operador,
                        placas=placas,
                        modalidad=modalidad
                    )
                    print(f"✅ [SAP] Folio creado en background: {resultado_kiosko}")

                    # ⏳ PREVENCIÓN DEL ERROR COM (-2147483638): Dormimos el script medio segundo
                    time.sleep(0.5)

                    # Crear Transporte
                    print(f"🤖 [SAP] Creando transporte en VT01N para {ticket_id}...")
                    no_transporte = self.sap_manager.crear_transporte(
                        remisiones=remisiones,
                        centro_expedicion=centro,
                        modalidad=modalidad,
                        operador=operador,
                        placas=placas,
                        clase_expedicion_f=clase_exp_final, 
                        fecha_checklist=fch_checklist
                    )

                    if no_transporte and str(no_transporte).strip().startswith("48"):
                        transporte_generado = str(no_transporte).strip()
                        exito_sincronizacion = True
                        print(f"✅ [SAP] Transporte creado en background: {transporte_generado}")
                    else:
                        print(f"❌ [SAP] Transporte inválido generado: {no_transporte}")
                else:
                    print("⚠️ [SYNC] SAP no está conectado. Se intentará en el siguiente ciclo.")

                # 4. Si es exitoso, cambiar estatus a 'CERRADO' y sobrescribir Excel.
                if exito_sincronizacion:
                    df.loc[df['ticket'] == ticket_id, 'estatus_contingencia'] = 'CERRADO'
                    
                    if transporte_generado:
                        df.loc[df['ticket'] == ticket_id, 'transporte'] = transporte_generado
                        
                    hubo_cambios = True
                    print(f"🎉 [SYNC] Ticket {ticket_id} cerrado exitosamente.")

            except Exception as e:
                print(f"❌ [SYNC] Error procesando ticket pendiente {ticket_id}: {e}")

            # Sobrescribir el archivo completo solo si logramos sincronizar al menos uno
            if hubo_cambios:
                try:
                    df.to_excel(ruta_excel, index=False, engine='openpyxl')
                    print("💾 [SYNC] Base de datos de Arribos actualizada y guardada correctamente.")
                    self.statusBar().showMessage("✅ Contingencias sincronizadas con SAP.", 5000)
                except Exception as e:
                    print(f"❌ [SYNC] Error crítico al sobrescribir {ruta_excel}: {e}")

    def _mocking_finalizar_simulacion_arribo(self):
            """
            Simula el grabado en SAP, actualiza el Log (Excel) y muestra el resultado en V4.
            """
             # QTimer para simular la espera (5 segundos)
            self.proceso_timer = QTimer(self)
            self.proceso_timer.setSingleShot(True)
            # 1. Registrar la hora de finalización
            self.session_data.fin_arribo = datetime.now()

            # --- Lógica Real: Aquí llamarías a self.sap_manager.crear_arribo(...) ---
            
            # 2. Simulación de éxito/error (70% probabilidad de éxito)
            exito = random.random() < 0.7 

            if exito:
                # === CASO ÉXITO ===
                mensaje_pantalla = "ARRIBO CORRECTO\nPUEDE PASAR A BÁSCULA."
                color = "green"
                
                # Datos para el Log
                self.session_data.mensaje_resultado = "EXITOSO"
                self.session_data.ultimo_paso = "Finalizado_Correctamente"
                
            else:
                # === CASO ERROR ===
                mensaje_pantalla = "ERROR AL GUARDAR ARRIBO.\nPASE A VENTANILLA."
                color = "red"
                
                # Datos para el Log
                self.session_data.mensaje_resultado = "ERROR DE SISTEMA (SIMULADO)"
                self.session_data.ultimo_paso = "Fallo_Grabado_SAP"

            # 3. GUARDAR EL LOG EN EXCEL
            # Este es el paso crucial que nos faltaba:
            print(f"Guardando evento final: {self.session_data.mensaje_resultado}")
            self.logger.guardar_evento(self.session_data)

            # 4. Actualizar la Interfaz Gráfica (V4)
            self.v4.set_estado(mensaje_pantalla, color, mostrar_boton=True)


if __name__ == "__main__":
    import ctypes
    
    app = QApplication(sys.argv)
    
    # 1. Mostrar el selector unificado
    from gui_selector_planta import obtener_configuracion_inicial
    session_config = obtener_configuracion_inicial()
    
    if session_config:
        ventana = AppWindow()
        
        # 2. Reemplazar la sesión vacía de la ventana por la configurada
        ventana.session_data = session_config
        
        # 3. Enrutar archivos
        ventana.arribos_manager.configurar_ruta(ventana.session_data)
        ventana.logger.configurar_ruta(ventana.session_data.ruta_base_drive)
        
        print(f"🏢 Kiosko iniciado en {ventana.session_data.planta_gui_nombre} {ventana.session_data.planta_gui_codigos}")
        ventana.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)