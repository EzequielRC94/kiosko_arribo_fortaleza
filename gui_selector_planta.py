# gui_selector_planta.py
import os
import sys
import ctypes
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QDialog, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QObject, QEvent, QTimer

from catalogos import CATALOGO_PLANTAS
from session_data import SessionData

# ==============================================================================
# CONFIGURACIÓN BASE Y HERENCIA DEL ÍCONO (.ICO) PARA TODOS LOS GUI
# ==============================================================================
APP_ID_UNIFICADO = "kiosko.autoarribo.produccion.1.0"
_APP_ID_CONFIGURADO = None
_HICON_CACHE = {"small": None, "big": None}
_FILTRO_ICONO_INSTALADO = None

# Fijar AppUserModelID en cuanto se importa el módulo para desvincular de python.exe
if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID_UNIFICADO)
        _APP_ID_CONFIGURADO = APP_ID_UNIFICADO
    except Exception:
        pass


def _obtener_ruta_icono() -> str:
    directorio_base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    ruta_ico = os.path.join(directorio_base, "images", "logo_short_ico.ico")
    if os.path.exists(ruta_ico):
        return ruta_ico
    return os.path.join(directorio_base, "images", "logo_short.png")


def _forzar_icono_win32(ventana: QWidget, ruta_icono: str):
    """Fuerza el ícono nativo (WM_SETICON y ClassLong) en el HWND de la ventana en Windows."""
    if sys.platform != "win32" or ventana is None or not os.path.exists(ruta_icono):
        return
    if not ruta_icono.lower().endswith(".ico"):
        return

    try:
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        user32.LoadImageW.argtypes = [
            wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
            ctypes.c_int, ctypes.c_int, wintypes.UINT
        ]
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.SendMessageW.argtypes = [
            wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
        ]
        user32.SendMessageW.restype = wintypes.LPARAM

        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        LR_DEFAULTSIZE = 0x00000040
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        GCL_HICON = -14
        GCL_HICONSM = -34

        if not _HICON_CACHE["small"]:
            _HICON_CACHE["small"] = user32.LoadImageW(
                None, ruta_icono, IMAGE_ICON, 16, 16, LR_LOADFROMFILE
            )
        if not _HICON_CACHE["big"]:
            _HICON_CACHE["big"] = user32.LoadImageW(
                None, ruta_icono, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
            )

        hwnd = int(ventana.winId())
        if _HICON_CACHE["small"]:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, _HICON_CACHE["small"])
        if _HICON_CACHE["big"]:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, _HICON_CACHE["big"])

        set_class_long = getattr(user32, "SetClassLongPtrW", getattr(user32, "SetClassLongW", None))
        if set_class_long is not None:
            if _HICON_CACHE["big"]:
                set_class_long(hwnd, GCL_HICON, _HICON_CACHE["big"])
            if _HICON_CACHE["small"]:
                set_class_long(hwnd, GCL_HICONSM, _HICON_CACHE["small"])
    except Exception:
        pass


class _FiltroIconoHerencia(QObject):
    """
    Filtro global en QApplication que detecta cualquier ventana/GUI que se muestre
    (DialogoSeleccionPlanta, VentanaBasculaMain, AppWindow, etc.) y le hereda el .ico
    automáticamente en barra de título y barra de tareas.
    """
    def __init__(self, icono: QIcon, ruta_icono: str, parent=None):
        super().__init__(parent)
        self.icono = icono
        self.ruta_icono = ruta_icono

    def eventFilter(self, obj, event):
        try:
            if isinstance(obj, QWidget) and obj.isWindow():
                tipo = event.type()
                if tipo in (QEvent.Type.Show, QEvent.Type.WindowStateChange):
                    if obj.windowIcon().isNull():
                        obj.setWindowIcon(self.icono)
                    _forzar_icono_win32(obj, self.ruta_icono)
                    QTimer.singleShot(50, lambda w=obj: _forzar_icono_win32(w, self.ruta_icono))
        except Exception:
            pass
        return False


def configurar_icono_app(ventana=None, app_id: str = None):
    """
    Configura el escenario visual del ícono (.ico) desde gui_selector_planta.py
    y lo hereda automáticamente a cualquier GUI que se mande llamar en la sesión.
    """
    global _APP_ID_CONFIGURADO, _FILTRO_ICONO_INSTALADO

    id_efectivo = APP_ID_UNIFICADO
    if _APP_ID_CONFIGURADO is None and sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(id_efectivo)
            _APP_ID_CONFIGURADO = id_efectivo
        except Exception as e:
            print(f"Aviso: No se pudo fijar AppUserModelID en barra de tareas: {e}")

    try:
        app_actual = QApplication.instance()
        if app_actual is None:
            return

        ruta_icono = _obtener_ruta_icono()
        icono = QIcon(ruta_icono)
        if icono.isNull():
            return

        # 1. Asignar a nivel QApplication para herencia automática en todas las ventanas
        app_actual.setWindowIcon(icono)

        # 2. Instalar el filtro de eventos global una sola vez para forzar el .ico al mostrar cualquier GUI
        if _FILTRO_ICONO_INSTALADO is None:
            _FILTRO_ICONO_INSTALADO = _FiltroIconoHerencia(icono, ruta_icono, app_actual)
            app_actual.installEventFilter(_FILTRO_ICONO_INSTALADO)

        # 3. Si se pasa una ventana específica, aplicarle su QIcon
        if ventana is not None:
            ventana.setWindowIcon(icono)
            if ventana.isVisible():
                _forzar_icono_win32(ventana, ruta_icono)
    except Exception as e:
        print(f"Aviso: No se pudo cargar el archivo de ícono: {e}")


class DialogoSeleccionPlanta(QDialog):
    def __init__(self):
        super().__init__()
        # Convertir el diálogo en ventana de nivel superior estándar (Qt.WindowType.Window)
        # para que Windows muestre su ícono en la barra de tareas igual que en QMainWindow
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowTitle("Configuración de Ubicación")
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("background-color: #f0f0f0;")
        configurar_icono_app(self)
        
        self.session_configurada = None
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)

        lbl_titulo = QLabel("SELECCIONE UBICACIÓN")
        lbl_titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)

        for nombre_planta, info in CATALOGO_PLANTAS.items():
            if not info.get("activo", True):
                continue
            codigos = info["codigos"]
            letra = info["letra"]
            
            btn = QPushButton(nombre_planta)
            btn.setFont(QFont("Arial", 14))
            btn.setFixedHeight(60)
            btn.setStyleSheet("""
                QPushButton { background-color: #008080; color: white; border-radius: 8px; }
                QPushButton:hover { background-color: #006666; }
            """)
            # Pasamos nombre (n), códigos (c) y letra (l) en el lambda
            btn.clicked.connect(lambda checked, n=nombre_planta, c=codigos, l=letra: self.confirmar_seleccion(n, c, l))
            layout.addWidget(btn)

    def confirmar_seleccion(self, nombre, codigos, letra):
        """Prepara el SessionData y calcula la ruta base antes de cerrar el diálogo."""
        # 1. Crear el SessionData centralizado
        session_data = SessionData()
        session_data.planta_gui_nombre = nombre
        session_data.planta_gui_codigos = codigos
        session_data.planta_gui_letra = letra #Letra identificadora de la planta
        
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
    """Función helper para inicializar el escenario base (.ico heredado) y llamar al diálogo desde cualquier archivo"""
    configurar_icono_app()
    dialogo = DialogoSeleccionPlanta()
    if dialogo.exec_() == QDialog.Accepted:
        return dialogo.session_configurada
    return None
