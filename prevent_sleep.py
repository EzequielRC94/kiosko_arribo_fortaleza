# prevent_sleep.py
import ctypes

# Constantes de la API de Windows para el control de energía
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

def evitar_bloqueo_windows():
    """
    Le dice a Windows que mantenga la pantalla y el sistema encendidos.
    Funciona como la reproducción de un video.
    """
    try:
        # Combinamos las banderas: Continuo + Sistema Requerido + Pantalla Requerida
        flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        
        # 🟢 LLAMADA A LA API DE WINDOWS
        ctypes.windll.kernel32.SetThreadExecutionState(flags)
        print("💻 [WINDOWS] Keep-Alive Activado: Pantalla y sistema bloqueados contra suspensión.")
        return True
    except Exception as e:
        print(f"⚠️ No se pudo activar el Keep-Alive de Windows: {e}")
        return False

def restaurar_energia_windows():
    """
    Restaurar el comportamiento normal de Windows (permite que se apague por inactividad).
    """
    try:
        # Al mandar solo ES_CONTINUOUS, se limpian las peticiones anteriores
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        print("💻 [WINDOWS] Keep-Alive Desactivado: El sistema vuelve a su comportamiento normal.")
        return True
    except Exception as e:
        print(f"⚠️ No se pudo restaurar el estado de energía de Windows: {e}")
        return False