import os
import sys
import time
import ctypes
from datetime import datetime, timedelta
from manager_sap import SAPManager


def configurar_icono_app(ventana=None, app_id: str = "kiosko.autoarribo.produccion.1.0"):
    """
    Homologa la configuración del ícono (.ico) en la barra de título y en la barra de tareas
    de Windows (tanto en ejecución normal de Python como empaquetado con PyInstaller).
    """
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception as e:
        print(f"Aviso: No se pudo forzar el ícono en la barra de tareas: {e}")

    try:
        from PyQt5.QtGui import QIcon
        from PyQt5.QtWidgets import QApplication

        directorio_base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        ruta_icono = os.path.join(directorio_base, "images", "logo_short_ico.ico")
        icono = QIcon(ruta_icono)

        app_actual = QApplication.instance()
        if app_actual is not None:
            app_actual.setWindowIcon(icono)

        if ventana is not None:
            ventana.setWindowIcon(icono)
    except Exception as e:
        print(f"Aviso: No se pudo cargar el archivo de ícono: {e}")

# --- LÓGICA DE VALIDACIÓN DE TIEMPO ---
def _requiere_descarga(ruta_archivo: str, limite_minutos: int = 10) -> bool:
    """Evalúa si el archivo no existe o si su última modificación superó el límite."""
    if not os.path.exists(ruta_archivo):
        return True
    
    # Obtiene el tiempo de la última modificación en segundos
    tiempo_modificacion = os.path.getmtime(ruta_archivo)
    tiempo_actual = time.time()
    diferencia_minutos = (tiempo_actual - tiempo_modificacion) / 60.0
    
    return diferencia_minutos > limite_minutos

class DescargasManager:
    def __init__(self, sap_manager: SAPManager = None):
        # Instanciar aquí ahorra memoria, ya que se crea una sola vez por sesión
        # y SAPManager comparte el mismo túnel y fila virtual a nivel clase
        self.sap_manager = sap_manager if sap_manager is not None else SAPManager()

    def zsdmx389_robot(self, ruta_base_drive: str, tipo_descarga: str = "ambos") -> dict:
        """
        Retorna: Diccionario estándar con estatus, mensaje y rutas generadas.
        """
        # --- 1. RUTAS DINÁMICAS (PLAN C) ---
        ruta_zsdmx = os.path.join(ruta_base_drive, "zsdmx389")
        ruta_pendientes = os.path.join(ruta_zsdmx, "pendientes")
        ruta_en_proceso = os.path.join(ruta_zsdmx, "en_proceso")
        
        # Validar y crear estructura de carpetas
        for carpeta in [ruta_pendientes, ruta_en_proceso]:
            if not os.path.exists(carpeta):
                try:
                    os.makedirs(carpeta, exist_ok=True)
                except Exception as e:
                    print(f"⚠️ Error creando carpeta {carpeta}: {e}")
        
        fecha_str = datetime.now().strftime("%Y%m%d")
        nom_pendientes = f"ZSDMX389_pendientes_{fecha_str}.csv" 
        nom_en_proceso = f"ZSDMX389_en_proceso_{fecha_str}.csv" 
        
        ruta_archivo_pendientes = os.path.join(ruta_pendientes, nom_pendientes)
        ruta_archivo_en_proceso = os.path.join(ruta_en_proceso, nom_en_proceso)

        # --- 3. RANGO DE FECHAS ---
        anio_actual = datetime.now().year
        fch_in = f"01.01.{anio_actual}"
        fch_fn = f"31.12.{anio_actual}"

        rutas_generadas = {}
        try:

            exito_final = True 
            msg_final = f"Descargas ZSDMX389 ({tipo_descarga}) procesadas correctamente."

            # --- 4A. DESCARGAR PENDIENTES ---
            if tipo_descarga in ["pendientes", "ambos"]:
                rutas_generadas['pendientes'] = {"ruta": ruta_archivo_pendientes, "actualizado": False}
                
                if _requiere_descarga(ruta_archivo_pendientes):
                    print(f"⬇️ Descargando {nom_pendientes} (Antigüedad > 10 min o no existe).")
                    
                    # 1. Guardamos el diccionario que devuelve SAP en una variable
                    respuesta_sap = self.sap_manager.zsdmx389(
                        path_descarga=ruta_pendientes, 
                        nom_archivo=nom_pendientes, 
                        extencion="csv",
                        fch_in=fch_in, 
                        fch_fn=fch_fn, 
                        filtro_transporte="" # Vacío: Trae todo lo pendiente
                    )
                    
                    # 2. Extraemos el booleano y actualizamos nuestras variables
                    estatus_descarga = respuesta_sap.get("estatus", False)
                    #print(f"manager descargas: {estatus_descarga}")
                    #rutas_generadas['pendientes']["actualizado"] = estatus_descarga #No entiendo esta linea de codigo, no creo se necesaria
                    
                    # Si SAP falló, cambiamos la bandera general a False y guardamos el error
                    if not estatus_descarga:
                        exito_final = False
                        msg_final = respuesta_sap.get("msg", "Error desconocido en SAP")
                        
                else:
                    print(f"⏭️ Omitiendo descarga de {nom_pendientes} (Reciente, < 10 min).")
            
            # --- 4B. DESCARGAR EN PROCESO ---
            if tipo_descarga in ["en_proceso", "ambos"]:
                rutas_generadas['en_proceso'] = {"ruta": ruta_archivo_en_proceso, "actualizado": False}
                
                if _requiere_descarga(ruta_archivo_en_proceso):
                    print(f"⬇️ Descargando {nom_en_proceso} (Antigüedad > 10 min o no existe).")
                    
                    respuesta_sap = self.sap_manager.zsdmx389(
                        path_descarga=ruta_en_proceso, 
                        nom_archivo=nom_en_proceso, 
                        extencion="csv",
                        fch_in=fch_in, 
                        fch_fn=fch_fn, 
                        filtro_transporte="IGUAL_C" # Solo C: Trae solo lo que está en proceso
                    )
                    
                    estatus_descarga = respuesta_sap.get("estatus", False)
                    
                    #print(f"manager descargas: estatus {estatus_descarga}: {exito_final}")

                    #rutas_generadas['en_proceso']["actualizado"] = estatus_descarga #No entiendo esta linea de codigo, no creo se necesaria
                    
                    if not estatus_descarga:
                        exito_final = False
                        msg_final = respuesta_sap.get("msg", "Error desconocido en SAP")
                        
                else:
                    print(f"⏭️ Omitiendo descarga de {nom_en_proceso} (Reciente, < 10 min).")
                    
            # --- RETORNO FINAL ---
            # Devolvemos el diccionario maestro para que la GUI reaccione
            return {
                "estatus": exito_final,
                "msg": msg_final,
                "rutas": rutas_generadas
            }
            
        except Exception as e:
            raise Exception(f"Falla crítica en evaluación/descarga ZSDMX389: {e}")

    def zsdmx249_robot(self, ruta_base_drive: str, dias_atras: int = 3, extension: str = "csv") -> dict:
        """
        Recorre desde hoy hasta -3 días para descargar la transacción ZSDMX249.
        - Si el archivo no existe en path_249, lo descarga.
        - Si ya existe, valida si su fecha de modificación (YYYYMMDD) es igual a fecha_str;
          si es la misma, lo descarga (actualiza el día en curso o actualiza el archivo de ayer hoy).
        """
        path_249 = os.path.join(ruta_base_drive, "zsdmx249")
        os.makedirs(path_249, exist_ok=True)

        centro_exp = "*"
        lay_out = "/ZQL_REPORT"
        hoy = datetime.now()

        rutas_generadas = {}
        exito_final = True
        msg_final = "Descargas ZSDMX249 procesadas correctamente."

        try:
            for i in range(dias_atras + 1):
                fecha_loop = hoy - timedelta(days=i)
                fecha_str = fecha_loop.strftime("%Y%m%d")
                fch_sap = fecha_loop.strftime("%d.%m.%Y")

                nom_249 = f"zsdmx249_{fecha_str}"
                ext_limpia = extension.strip().lower().replace(".", "")
                ruta_archivo = os.path.join(path_249, f"{nom_249}.{ext_limpia}")

                debe_descargar = False
                motivo = ""

                if not os.path.exists(ruta_archivo):
                    debe_descargar = True
                    motivo = "No existe el archivo"
                else:
                    fch_mod_str = datetime.fromtimestamp(os.path.getmtime(ruta_archivo)).strftime("%Y%m%d")
                    if fch_mod_str == fecha_str and _requiere_descarga(ruta_archivo):
                        debe_descargar = True
                        motivo = f"Antigüedad > 10 min y fecha modificación ({fch_mod_str}) == fecha archivo ({fecha_str})"

                rutas_generadas[fecha_str] = {"ruta": ruta_archivo, "actualizado": False}

                if debe_descargar:
                    print(f"⬇️ [ZSDMX249] Descargando {nom_249}.{ext_limpia} ({motivo})...")
                    respuesta_sap = self.sap_manager.zsdmx249(
                        path_descarga=path_249,
                        nom_archivo=nom_249,
                        extension=ext_limpia,
                        fch_in_sm_real=fch_sap,
                        fch_fn_sm_real=fch_sap,
                        lay_out=lay_out,
                        org_vta="0152",
                        c_exp=centro_exp,
                        descargar=True
                    )

                    estatus_descarga = respuesta_sap.get("estatus", False)
                    rutas_generadas[fecha_str]["actualizado"] = estatus_descarga

                    if not estatus_descarga:
                        exito_final = False
                        msg_final = respuesta_sap.get("msg", f"Error en SAP al descargar {nom_249}")
                        print(f"  ⚠️ [ZSDMX249] Falla en {fch_sap}: {msg_final}")
                    else:
                        print(f"  ✅ [ZSDMX249] {nom_249}.{ext_limpia}: {respuesta_sap.get('msg')}")

                    time.sleep(1)
                else:
                    print(f"⏭️ [ZSDMX249] Omitiendo {nom_249}.{ext_limpia} (Reciente < 10 min o ya actualizado posteriormente).")

            return {
                "estatus": exito_final,
                "msg": msg_final,
                "rutas": rutas_generadas
            }

        except Exception as e:
            raise Exception(f"Falla crítica en evaluación/descarga ZSDMX249: {e}")

    def zsdmx267_robot(self, ruta_base_drive: str = None, dias_atras: int = 3, extension: str = "xls") -> dict:
        """
        Robot para la descarga diaria/histórica de la transacción ZSDMX267 en formato XLS.
        Itera día por día en reversa desde hoy hasta -dias_atras.
        Utiliza _requiere_descarga para omitir archivos con menos de 10 minutos de haberse actualizado.
        """
        hoy = datetime.now()

        if not ruta_base_drive:
            perfil_usuario = os.environ.get("USERPROFILE", os.path.expanduser("~"))
            anno = hoy.strftime("%Y")
            ruta_base_drive = os.path.join(
                perfil_usuario,
                "Elementia S. A",
                "kiosko logistica cem - Documentos",
                anno
            )

        path_267 = os.path.join(ruta_base_drive, "zsdmx267")
        os.makedirs(path_267, exist_ok=True)

        centro_exp = "MX*"
        lay_out = "/0.TRAN_REP"
        ext_limpia = extension.strip().lower().replace(".", "")

        rutas_generadas = {}
        exito_final = True
        msg_final = "Descargas ZSDMX267 procesadas correctamente."

        try:
            for i in range(dias_atras + 1):
                fecha_loop = hoy - timedelta(days=i)
                fecha_str = fecha_loop.strftime("%Y%m%d")
                fch_sap = fecha_loop.strftime("%d.%m.%Y")

                nom_267 = f"zsdmx267_{fecha_str}"
                ruta_archivo = os.path.join(path_267, f"{nom_267}.{ext_limpia}")

                debe_descargar = False
                motivo = ""

                if not os.path.exists(ruta_archivo):
                    debe_descargar = True
                    motivo = "No existe el archivo"
                else:
                    fch_mod_str = datetime.fromtimestamp(os.path.getmtime(ruta_archivo)).strftime("%Y%m%d")
                    if fch_mod_str == fecha_str and _requiere_descarga(ruta_archivo):
                        debe_descargar = True
                        motivo = f"Antigüedad > 10 min y fecha modificación ({fch_mod_str}) == fecha archivo ({fecha_str})"

                rutas_generadas[fecha_str] = {"ruta": ruta_archivo, "actualizado": False}

                if debe_descargar:
                    print(f"⬇️ [ZSDMX267] Descargando {nom_267}.{ext_limpia} ({motivo})...")
                    respuesta_sap = self.sap_manager.zsdmx267(
                        path_descarga=path_267,
                        nom_archivo=nom_267,
                        extension=ext_limpia,
                        fch_in=fch_sap,
                        fch_fn=fch_sap,
                        lay_out=lay_out,
                        centro_exp=centro_exp,
                        descargar=True
                    )

                    estatus_descarga = respuesta_sap.get("estatus", False)
                    rutas_generadas[fecha_str]["actualizado"] = estatus_descarga

                    if not estatus_descarga:
                        exito_final = False
                        msg_final = respuesta_sap.get("msg", f"Error en SAP al descargar {nom_267}")
                        print(f"  ⚠️ [ZSDMX267] Falla en {fch_sap}: {msg_final}")
                    else:
                        print(f"  ✅ [ZSDMX267] {nom_267}.{ext_limpia}: {respuesta_sap.get('msg')}")

                    time.sleep(1)
                else:
                    print(f"⏭️ [ZSDMX267] Omitiendo {nom_267}.{ext_limpia} (Reciente < 10 min o ya actualizado posteriormente).")

            return {
                "estatus": exito_final,
                "msg": msg_final,
                "rutas": rutas_generadas
            }

        except Exception as e:
            raise Exception(f"Falla crítica en evaluación/descarga ZSDMX267: {e}")

    def vt16_robot(self, ruta_base_drive: str = None, centro_exp: str = "", mes: str = "", extension: str = "csv") -> dict:
        """
        Orquestador que prepara las variables para descargar la transacción VT16.
        - La variable 'mes' se espera en formato numérico 1-12; si no se pasa, toma el mes en curso.
        - Usa _requiere_descarga para omitir la descarga si el archivo tiene menos de 10 minutos.
        - Retorna un diccionario estándar con estatus, msg y rutas.
        """
        hoy = datetime.now()

        # --- 1. FECHAS Y MES (1-12 o mes en curso) ---
        if not mes:
            anio = hoy.year
            mes_num = hoy.month
            fecha_str = hoy.strftime("%Y%m")
            fch_in_mes = hoy.replace(day=1).strftime("%d.%m.%Y")  # Primer día del mes actual
            fch_fin_mes = hoy.strftime("%d.%m.%Y")               # Día en curso
        else:
            try:
                mes_num = int(mes)
                if not 1 <= mes_num <= 12:
                    raise ValueError("El parámetro 'mes' debe ser un número entre 1 y 12.")
                anio = hoy.year
                fecha_str = f"{anio}{mes_num:02d}"
                primer_dia_mes = datetime(anio, mes_num, 1)
                fch_in_mes = primer_dia_mes.strftime("%d.%m.%Y")
                # Último día del mes: primer día del siguiente mes menos 1 día
                primer_dia_siguiente_mes = (primer_dia_mes + timedelta(days=32)).replace(day=1)
                fch_fin_mes = (primer_dia_siguiente_mes - timedelta(days=1)).strftime("%d.%m.%Y")
            except ValueError:
                raise ValueError("El parámetro 'mes' debe tener formato numérico 1-12.")

        # --- 2. RUTAS Y NOMBRES ---
        if not ruta_base_drive:
            perfil_usuario = os.environ.get("USERPROFILE", os.path.expanduser("~"))
            ruta_base_drive = os.path.join(
                perfil_usuario,
                "Elementia S. A",
                "kiosko logistica cem - Documentos",
                str(anio)
            )

        path_vt16 = os.path.join(ruta_base_drive, "vt16")
        os.makedirs(path_vt16, exist_ok=True)

        ext_limpia = extension.strip().lower().replace(".", "")
        nom_vt16 = f"VT16_{fecha_str}"
        ruta_archivo = os.path.join(path_vt16, f"{nom_vt16}.{ext_limpia}")

        rutas_generadas = {
            fecha_str: {"ruta": ruta_archivo, "actualizado": False}
        }
        exito_final = True
        msg_final = "Descarga VT16 procesada correctamente."

        try:
            # --- 3. VALIDACIÓN DE TIEMPO (_requiere_descarga) Y EJECUCIÓN ---
            if _requiere_descarga(ruta_archivo):
                print(f"⬇️ [VT16] Descargando {nom_vt16}.{ext_limpia} (Antigüedad > 10 min o no existe)...")
                respuesta_sap = self.sap_manager.vt16(
                    path_descarga=path_vt16,
                    nom_archivo=nom_vt16,
                    extension=ext_limpia,
                    fch_in=fch_in_mes,
                    fch_fn=fch_fin_mes,
                    centro_exp=centro_exp,
                    status_global_in="1",
                    status_global_fn="7",
                    lay_out="/HORARIOS_FZ",
                    descargar=True
                )

                estatus_descarga = respuesta_sap.get("estatus", False)
                rutas_generadas[fecha_str]["actualizado"] = estatus_descarga

                if not estatus_descarga:
                    exito_final = False
                    msg_final = respuesta_sap.get("msg", f"Error en SAP al descargar {nom_vt16}")
                    print(f"  ⚠️ [VT16] Falla en {fecha_str}: {msg_final}")
                else:
                    print(f"  ✅ [VT16] {nom_vt16}.{ext_limpia}: {respuesta_sap.get('msg')}")
            else:
                print(f"⏭️ [VT16] Omitiendo {nom_vt16}.{ext_limpia} (Reciente, < 10 min).")

            return {
                "estatus": exito_final,
                "msg": msg_final,
                "rutas": rutas_generadas
            }

        except Exception as e:
            raise Exception(f"Falla crítica en evaluación/descarga VT16: {e}")

    def fbl4n_robot(self, ruta_base_drive: str = None, mes: str = "", extension: str = "xls") -> dict:
        """
        Orquestador que prepara las variables para descargar la transacción FBL4N en formato XLS mensual.
        - La variable 'mes' se espera en formato numérico 1-12; si no se especifica, toma el mes en curso.
        - Usa _requiere_descarga para omitir la descarga si el archivo tiene menos de 10 minutos.
        - Retorna un diccionario estándar con estatus, msg y rutas.
        """
        hoy = datetime.now()

        # --- 1. CONFIGURACIÓN FIJA ---
        sociedad = "3022"
        cuenta_mayor = "641211091"
        lay_out = "/ZQL_FLETES"

        # --- 2. FECHAS Y MES (1-12 o mes en curso) ---
        if not mes:
            anio = hoy.year
            mes_num = hoy.month
            fecha_str = hoy.strftime("%Y%m")
            fch_in_mes = hoy.replace(day=1).strftime("%d.%m.%Y")  # Primer día del mes actual
            fch_fin_mes = hoy.strftime("%d.%m.%Y")               # Día en curso
        else:
            try:
                mes_num = int(mes)
                if not 1 <= mes_num <= 12:
                    raise ValueError("El parámetro 'mes' debe ser un número entre 1 y 12.")
                anio = hoy.year
                fecha_str = f"{anio}{mes_num:02d}"
                primer_dia_mes = datetime(anio, mes_num, 1)
                fch_in_mes = primer_dia_mes.strftime("%d.%m.%Y")
                # Último día del mes: primer día del siguiente mes menos 1 día
                primer_dia_siguiente_mes = (primer_dia_mes + timedelta(days=32)).replace(day=1)
                fch_fin_mes = (primer_dia_siguiente_mes - timedelta(days=1)).strftime("%d.%m.%Y")
            except ValueError:
                raise ValueError("El parámetro 'mes' debe tener formato numérico 1-12.")

        # --- 3. RUTAS Y NOMBRES ---
        if not ruta_base_drive:
            perfil_usuario = os.environ.get("USERPROFILE", os.path.expanduser("~"))
            anio_actual = hoy.strftime("%Y")
            ruta_base_drive = os.path.join(
                perfil_usuario,
                "Elementia S. A",
                "kiosko logistica cem - Documentos",
                anio_actual
            )

        path_fbl4n = os.path.join(ruta_base_drive, "fbl4n")
        os.makedirs(path_fbl4n, exist_ok=True)

        ext_limpia = extension.strip().lower().replace(".", "")
        nom_fbl4n = f"FBL4N_{fecha_str}"
        ruta_archivo = os.path.join(path_fbl4n, f"{nom_fbl4n}.{ext_limpia}")

        rutas_generadas = {
            fecha_str: {"ruta": ruta_archivo, "actualizado": False}
        }
        exito_final = True
        msg_final = "Descarga FBL4N procesada correctamente."

        try:
            # --- 4. VALIDACIÓN DE TIEMPO (_requiere_descarga) Y EJECUCIÓN ---
            if _requiere_descarga(ruta_archivo):
                print(f"⬇️ [FBL4N] Descargando {nom_fbl4n}.{ext_limpia} (Antigüedad > 10 min o no existe)...")
                respuesta_sap = self.sap_manager.fbl4n(
                    path_descarga=path_fbl4n,
                    nom_archivo=nom_fbl4n,
                    extension=ext_limpia,
                    fch_in=fch_in_mes,
                    fch_fn=fch_fin_mes,
                    cta_mayor=cuenta_mayor,
                    sociedad=sociedad,
                    lay_out=lay_out,
                    descargar=True
                )

                estatus_descarga = respuesta_sap.get("estatus", False)
                rutas_generadas[fecha_str]["actualizado"] = estatus_descarga

                if not estatus_descarga:
                    exito_final = False
                    msg_final = respuesta_sap.get("msg", f"Error en SAP al descargar {nom_fbl4n}")
                    print(f"  ⚠️ [FBL4N] Falla en {fecha_str}: {msg_final}")
                else:
                    print(f"  ✅ [FBL4N] {nom_fbl4n}.{ext_limpia}: {respuesta_sap.get('msg')}")
            else:
                print(f"⏭️ [FBL4N] Omitiendo {nom_fbl4n}.{ext_limpia} (Reciente, < 10 min).")

            return {
                "estatus": exito_final,
                "msg": msg_final,
                "rutas": rutas_generadas
            }

        except Exception as e:
            raise Exception(f"Falla crítica en evaluación/descarga FBL4N: {e}")
