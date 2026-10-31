#manager_sap.py
import win32com.client
import sys
import unicodedata
import time, datetime
import threading
import pythoncom
import re
import ctypes
from collections import deque
from contextlib import contextmanager
from functools import wraps
from typing import Optional, Callable, Any
from PyQt5.QtCore import QObject, pyqtSignal
from catalogos import CATALOGO_MATERIALES

class SignalEmitter (QObject):
    keep_alive_signal = pyqtSignal(str, str)

class SAPError(Exception):
    """Excepción personalizada para errores de negocio en SAP."""
    pass


def tunel_sap(nombre_tarea: str = ""):
    """
    Decorador que asegura que cualquier función de SAPScripting se ejecute
    en Modo Túnel (una sola tarea a la vez en orden FIFO).
    """
    def decorador(func: Callable):
        etiqueta = nombre_tarea or func.__name__

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            with self.tunel(etiqueta):
                return func(self, *args, **kwargs)
        return wrapper
    return decorador


class SAPManager:
    """
    Clase para gestionar la conexión con SAP GUI, mantener la sesión viva y
    orquestar una Fila Virtual en Modo Túnel para evitar colisiones en SAPScripting.
    """
    # ==========================================================================
    # ESTADO COMPARTIDO DE TÚNEL Y FILA VIRTUAL (NIVEL CLASE / PROCESO + OS)
    # ==========================================================================
    _cond_tunel = threading.Condition(threading.Lock())
    _fila_hilos = deque()           # Cola FIFO de tickets (hilos esperando entrar al túnel)
    _cola_diferida = deque()        # Cola FIFO de tareas diferidas (ej. QTimers disparados mientras SAP trabaja)
    _drenando_cola = False          # Evita recursión al vaciar _cola_diferida
    _hilo_propietario = None        # ID del hilo que actualmente tiene tomado el túnel
    _profundidad_tunel = 0          # Permite llamadas anidadas legítimas (ej. crear_folio -> eliminar_transportista)
    _tarea_activa = ""              # Nombre de la tarea que está usando SAP en este instante
    _ultima_actividad_ts = 0.0      # Timestamp de la última operación SAP completada
    _os_mutex_handle = None         # Mutex de Windows para sincronizar múltiples procesos (.exe/.py)
    _seq_ticket = 0

    def __init__(self):
        # Bandera para controlar la detención del hilo Keep-Alive
        self.stop_thread = False
        # Referencia al hilo de Keep-Alive
        self.keep_alive_thread = None
        # Referencia a la sesión (no se almacena persistentemente, solo se usa temporalmente)
        self.session = None
        # Inicializar el emisor de señales
        self.emitter = SignalEmitter()

    # ==========================================================================
    # MODO TÚNEL Y FILA VIRTUAL DE EJECUCIÓN SAP
    # ==========================================================================
    @classmethod
    def esta_ocupado(cls) -> bool:
        """Indica si el túnel de SAP está siendo utilizado actualmente."""
        with cls._cond_tunel:
            return cls._profundidad_tunel > 0

    @classmethod
    def tarea_en_curso(cls) -> str:
        """Devuelve el nombre de la tarea que está ejecutándose actualmente en el túnel."""
        with cls._cond_tunel:
            return cls._tarea_activa

    @classmethod
    def _adquirir_mutex_os(cls):
        """Adquiere un Named Mutex de Windows para evitar colisiones entre procesos distintos (ej. Arribos + Báscula)."""
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.CreateMutexW(None, False, "Local\\CementosFortaleza_SAPScripting_Tunnel")
            if handle:
                # WAIT_OBJECT_0 (0) o WAIT_ABANDONED (0x80), timeout 120 seg (120000 ms)
                kernel32.WaitForSingleObject(handle, 120000)
                cls._os_mutex_handle = handle
        except Exception:
            pass

    @classmethod
    def _liberar_mutex_os(cls):
        """Libera el Named Mutex de Windows."""
        try:
            if cls._os_mutex_handle:
                kernel32 = ctypes.windll.kernel32
                kernel32.ReleaseMutex(cls._os_mutex_handle)
                kernel32.CloseHandle(cls._os_mutex_handle)
                cls._os_mutex_handle = None
        except Exception:
            pass

    @contextmanager
    def tunel(self, nombre_tarea: str = "Operación SAP"):
        """
        Context manager de Modo Túnel con Fila Virtual FIFO.
        Garantiza que solo una actividad controle SAP GUI a la vez, formando en fila
        cualquier solicitud subsecuente hasta que la tarea actual termine.
        """
        cls = self.__class__
        tid = threading.get_ident()
        es_entrada_raiz = False
        tarea_anterior = ""

        with cls._cond_tunel:
            if cls._hilo_propietario == tid and cls._profundidad_tunel > 0:
                # Llamada anidada dentro de la misma operación activa (ej. crear_folio -> eliminar_transportista)
                cls._profundidad_tunel += 1
                tarea_anterior = cls._tarea_activa
                cls._tarea_activa = f"{tarea_anterior} -> {nombre_tarea}"
            else:
                # Nueva tarea: se forma en la Fila Virtual FIFO
                es_entrada_raiz = True
                cls._seq_ticket += 1
                mi_ticket = (cls._seq_ticket, tid, nombre_tarea)
                cls._fila_hilos.append(mi_ticket)
                posicion = len(cls._fila_hilos)

                if cls._profundidad_tunel > 0 or posicion > 1:
                    print(
                        f"⏳ [FILA VIRTUAL SAP] '{nombre_tarea}' en espera "
                        f"(Turno #{posicion}, en curso: '{cls._tarea_activa or ' Liberando...'}')."
                    )

                # Esperar turno estricto en la cabeza de la fila y que el túnel esté libre
                while cls._profundidad_tunel > 0 or cls._fila_hilos[0][0] != mi_ticket[0]:
                    cls._cond_tunel.wait(timeout=1.0)

                # Turno asignado: salir de la fila de espera y tomar el túnel
                cls._fila_hilos.popleft()
                cls._hilo_propietario = tid
                cls._profundidad_tunel = 1
                cls._tarea_activa = nombre_tarea

        if es_entrada_raiz:
            # Sincronización inter-proceso a nivel Sistema Operativo
            cls._adquirir_mutex_os()
            print(f"🚇 [TÚNEL SAP] ▶ Iniciando: '{nombre_tarea}'")

        try:
            yield
        finally:
            cls._ultima_actividad_ts = time.time()
            ejecutar_diferidas = False

            if es_entrada_raiz:
                print(f"🚇 [TÚNEL SAP] ⏹ Finalizó: '{nombre_tarea}'")
                cls._liberar_mutex_os()

            with cls._cond_tunel:
                cls._profundidad_tunel -= 1
                if cls._profundidad_tunel <= 0:
                    cls._profundidad_tunel = 0
                    cls._hilo_propietario = None
                    cls._tarea_activa = ""
                    cls._cond_tunel.notify_all()
                    if cls._cola_diferida and not cls._drenando_cola:
                        ejecutar_diferidas = True
                else:
                    cls._tarea_activa = tarea_anterior

            # Si se encolaron tareas diferidas (ej. QTimers de robots mientras la GUI operaba SAP),
            # las despachamos una por una en orden FIFO al liberarse el túnel.
            if ejecutar_diferidas:
                self._procesar_cola_diferida()

    def ejecutar_o_encolar(self, nombre_tarea: str, funcion: Callable, *args, **kwargs) -> Any:
        """
        Ideal para Robots y Timers de interfaz (QTimer):
        - Si el túnel SAP está libre, ejecuta la tarea de inmediato dentro del túnel.
        - Si el túnel SAP está ocupado (ej. el operador está registrando un arribo o llamando unidades
          y un QTimer se disparó durante QApplication.processEvents()), NO interrumpe a SAP:
          forma la tarea en la Fila Virtual (_cola_diferida) para ejecutarla automáticamente
          en cuanto concluya la actividad actual.
        """
        cls = self.__class__
        with cls._cond_tunel:
            ocupado = cls._profundidad_tunel > 0 or len(cls._fila_hilos) > 0
            if ocupado:
                # Evitar duplicar exactamente la misma tarea periódica en la fila de espera
                ya_encolada = any(item[0] == nombre_tarea for item in cls._cola_diferida)
                if not ya_encolada:
                    cls._cola_diferida.append((nombre_tarea, funcion, args, kwargs))
                    pos = len(cls._cola_diferida)
                    print(
                        f"⏳ [FILA VIRTUAL SAP] Tarea '{nombre_tarea}' formada en cola (Posición #{pos}) "
                        f"porque SAP está ocupado con '{cls._tarea_activa}'."
                    )
                else:
                    print(f"⏭️ [FILA VIRTUAL SAP] '{nombre_tarea}' ya se encuentra formada en la fila de espera.")
                return None

        # Si el túnel está libre, se ejecuta inmediatamente dentro del túnel
        with self.tunel(nombre_tarea):
            return funcion(*args, **kwargs)

    def _procesar_cola_diferida(self):
        """Despacha en orden FIFO todas las tareas que se formaron en la fila virtual mientras SAP estaba ocupado."""
        cls = self.__class__
        with cls._cond_tunel:
            if cls._drenando_cola:
                return
            cls._drenando_cola = True

        try:
            while True:
                with cls._cond_tunel:
                    if not cls._cola_diferida or cls._profundidad_tunel > 0:
                        break
                    nombre_tarea, funcion, args, kwargs = cls._cola_diferida.popleft()
                    restantes = len(cls._cola_diferida)

                print(f"▶️ [FILA VIRTUAL SAP] Despachando tarea encolada: '{nombre_tarea}' (Pendientes en fila: {restantes})")
                try:
                    with self.tunel(nombre_tarea):
                        funcion(*args, **kwargs)
                except Exception as e_cola:
                    print(f"⚠️ [FILA VIRTUAL SAP] Error ejecutando tarea encolada '{nombre_tarea}': {e_cola}")
        finally:
            with cls._cond_tunel:
                cls._drenando_cola = False

    def obtener_sesion(self) -> Optional[win32com.client.Dispatch]:
        """
        Intenta conectar con la instancia activa de SAP.
        SIEMPRE obtiene una referencia fresca a los objetos COM.
        """
        try:
            # 1. Obtenemos el objeto SAPGUI
            SapGuiAuto = win32com.client.GetObject("SAPGUI")
            
            # 2. Obtenemos el motor de scripting
            application = SapGuiAuto.GetScriptingEngine
            
            # 3. Obtenemos la conexión (primer child, típicamente la única conexión)
            if application.Children.Count == 0:
                print("Error: No hay conexiones SAP activas.")
                return None
            connection = application.Children(0)
            
            # 4. Obtenemos la sesión (primer child, típicamente la ventana de SAP)
            if connection.Children.Count == 0:
                print("Error: No hay sesiones/ventanas SAP abiertas.")
                return None
            session = connection.Children(0)
            
            # Validación rápida: Intentamos leer el título de la ventana
            _ = session.Id 
            
            return session

        except Exception as e:
            # print(f"Debug: No se pudo conectar a SAP: {e}") 
            return None

    def acceder_a_transaccion(self, session, transaccion: str) -> bool:
        """
        Intenta ingresar a una transacción de SAP y valida si el usuario tiene permisos.
        """
        try:
            # 1. Ejecutar el comando para ir a la transacción
            session.findById("wnd[0]/tbar[0]/okcd").text = f"/n {transaccion}"
            session.findById("wnd[0]").sendVKey(0)

            # 2. Leer la barra de estado (sbar)
            sap_msg = session.findById("wnd[0]/sbar").text
            
            # 3. Validar mensajes de error de Basis/Permisos
            # En Python usamos una lista para poder agregar más errores fácilmente en el futuro
            errores_acceso = ["Falta autorización", "La transacción", "No tiene autorización"]
            
            if any(error in sap_msg for error in errores_acceso):
                # Si detecta que no hay permiso, lanzamos un SAPError para que el Kiosko lo atrape
                raise SAPError(f"Acceso denegado a {transaccion}: {sap_msg}")
            
            return True
            
        except Exception as e:
            # Si el error ya es nuestro SAPError controlado, lo dejamos pasar hacia arriba
            if isinstance(e, SAPError):
                raise e
            # Si es un error de conexión, lo empaquetamos
            raise SAPError(f"Error técnico al intentar abrir {transaccion}: {e}")

    def validar_conexion(self) -> bool:
        """
        Devuelve True si hay una sesión SAP lista para usar.
        """
        session = self.obtener_sesion()
        return session is not None

    def iniciar_keep_alive(self, intervalo_minutos=13):
        """
        Inicia un hilo en segundo plano que manda el '/n' a SAP cada X minutos.
        """
        if self.keep_alive_thread is not None and self.keep_alive_thread.is_alive():
            print("El servicio de Keep-Alive ya está corriendo.")
            return

        self.stop_thread = False
        self.keep_alive_thread = threading.Thread(
            target=self._proceso_keep_alive, 
            args=(intervalo_minutos,),
            daemon=True 
        )
        self.keep_alive_thread.start()
        print(f"SAP Keep-Alive iniciado. Intervalo: {intervalo_minutos} min.")

    def detener_keep_alive(self):
        """Detiene el hilo de Keep-Alive de forma segura."""
        self.stop_thread = True

    def _proceso_keep_alive(self, minutos):
        """Lógica interna del hilo Keep-Alive."""
        # Necesario para usar COM en un hilo separado
        pythoncom.CoInitialize() 
        
        segundos = minutos * 60
        
        while not self.stop_thread:
            # Esperamos el tiempo de forma gradual para poder detener el hilo rápidamente
            for _ in range(segundos):
                if self.stop_thread:
                    return
                time.sleep(1)
            
            # Si SAP está ocupado en el túnel o tuvo actividad reciente (< 80% del intervalo),
            # omitimos el Keep-Alive para no interrumpir transacciones en curso.
            if self.esta_ocupado() or (time.time() - self.__class__._ultima_actividad_ts) < (segundos * 0.8):
                print(f"⏭️ [{time.strftime('%H:%M:%S')}] Keep-Alive omitido (SAP tuvo actividad reciente o está en uso).")
                continue

            # Tiempo cumplido y sin actividad reciente: Mandar ping a SAP dentro del túnel
            with self.tunel("Keep-Alive (/n)"):
                session = self.obtener_sesion()
                if session:
                    try:
                        session.findById("wnd[0]/tbar[0]/okcd").Text = "/n"
                        session.findById("wnd[0]").sendVKey(0) #(Enter)
                        
                        self.emitter.keep_alive_signal.emit ("Conexión con SAP exitosa. Keep-Alive enviado.", 
                            "green"
                            )
                        print(f"✅ [{time.strftime('%H:%M:%S')}] Keep-Alive enviado a SAP (/n)")
                    except Exception as e:
                        self.emitter.keep_alive_signal.emit("Falla al enviar Keep-Alive. SAP puede estar ocupado o desconectado.", 
                                                            "orange")
                        print(f"Error al enviar Keep-Alive: {e}")
                        pass # Silenciamos errores si SAP está ocupado en ese instante
                else:
                    self.emitter.keep_alive_signal.emit("ADVERTENCIA: SAP GUI no detectado. Keep-Alive no se pudo enviar.",
                                                        "red")
                    print(f"[{time.strftime('%H:%M:%S')}] SAP no detectado. Reintentando en {minutos} min...")

    # ==============================================================================
    # Extraer Datos de Remisión
    # ==============================================================================
    @tunel_sap("VL03N: Extraer Datos Remisión")
    def extraer_datos_remision(self, num_remision: str) -> Optional[dict]:
        """
        Traducción de Extraer datos de remision SAP GUI Scripting.
        """
        session = self.obtener_sesion()
        if not session:
            raise Exception("No hay sesión abierta en SAP.")
        
        try:
            self.emitter.keep_alive_signal.emit("Conexión con SAP correcta, trabajando...", "blue")
            
            # --- 1. NAVEGACIÓN INICIAL ---
            self.acceder_a_transaccion(session, "VL03N")

            session.findById("wnd[0]/usr/ctxtLIKP-VBELN").text = num_remision
            session.findById("wnd[0]").sendVKey(0)

            # --- 2. VALIDACIÓN DE ERRORES EN BARRA DE ESTADO ---
            sap_msg = session.findById("wnd[0]/sbar").text
            if sap_msg != "":
                errores_criticos = ["Se ha expedido", "no está disponible", "La entrada es"]
                error_bloqueo = ["El usuario"]
                
                if any(x in sap_msg for x in errores_criticos):
                    raise SAPError(sap_msg)
                elif any(x in sap_msg for x in error_bloqueo):
                    raise SAPError(f"{sap_msg} Intente más tarde.")

            # Validar Popup "Carga en proceso"
            if session.Children.Count > 1:
                try:
                    sap_msg = session.findById("wnd[1]/usr/txtMESSTXT1").text
                    if "La carga del transporte" in sap_msg:
                        raise SAPError(sap_msg)
                    # Si es otro popup no crítico, intentamos cerrarlo o ignorarlo
                    session.findById("wnd[1]").sendVKey(0) 
                except:
                    pass

            # --- 3. DATOS DE CABECERA ---
            session.findById("wnd[0]/tbar[1]/btn[8]").press() # Visualizar cabecera

            # Validar Estatus (Pestaña T\01) GESTION
            session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\01").select()
            
            st_transporte = session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\01/ssubSUBSCREEN_BODY:SAPMV50A:2102/ctxtVBUK-TRSTA").text
            st_salida_merc = session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\01/ssubSUBSCREEN_BODY:SAPMV50A:2102/ctxtVBUK-WBSTK").text
            st_factura = session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\01/ssubSUBSCREEN_BODY:SAPMV50A:2102/ctxtVBUK-FKSTK").text

            #print(f"SAP Estatus Transporte: {st_transporte}")
            #print(f"SAP Estatus Sal Mercancia: {st_transporte}")
            #print(f"SAP Estatus Facturacion: {st_transporte}")

            # --- DATOS DE FECHAS (CITA DE CARGA) ---
            fch_cita_str = ""
            
            fecha_cita = session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\01/ssubSUBSCREEN_BODY:SAPMV50A:2102/ctxtLIKP-LDDAT").text.strip()
            hora_cita = session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\01/ssubSUBSCREEN_BODY:SAPMV50A:2102/ctxtLIKP-LDUHR").text.strip()
            
            if fecha_cita:
                # 1. Unimos el texto que llega de SAP
                fch_cruda = f"{fecha_cita} {hora_cita}".strip()
                
                try:
                    # 2. Parseamos asumiendo el formato de SAP (Día.Mes.Año Hora:Minuto)
                    dt_obj = datetime.datetime.strptime(fch_cruda, "%d.%m.%Y %H:%M")
                    
                    # 3. Formateamos al estándar timestamp requerido
                    fch_cita_str = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                    
                except ValueError:
                    # Si SAP envía algo raro (ej. fechas vacías tipo '00.00.0000'), 
                    # evitamos que el programa colapse y guardamos lo que llegó.
                    print(f"⚠️ Aviso: No se pudo formatear la fecha de SAP '{fch_cruda}'.")
                    fch_cita_str = fch_cruda
                #print(f"Cita carga: {fch_cita_str}")
            

            # --- DATOS DE TRANSPORTE (Pestaña T\04) ---
            session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\04").select()
            ruta_transporte = "wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\04/ssubSUBSCREEN_BODY:SAPMV50A:2108/"

            def leer(campo_base):
                """
                Intenta leer el campo inteligentemente probando prefijos ctxt y txt.
                Evita que el programa colapse si un campo está oculto o vacío.
                """
                try:
                    # Intenta primero como campo con buscador (ctxt)
                    return session.findById(f"{ruta_transporte}ctxt{campo_base}").text.strip()
                except:
                    try:
                        # Si falla, intenta como campo de texto normal (txt)
                        return session.findById(f"{ruta_transporte}txt{campo_base}").text.strip()
                    except:
                        print(f"⚠️ Aviso: Campo {campo_base} no visible en layout.")
                        return ""

            # Ahora solo le pasamos el nombre puro de la base de datos (sin txt/ctxt)
            placas = leer("LIKP-XABLN")
            operador = leer("LIKP-BOLNR")
            clase_exp_sap = leer("LIKP-VSART")
            ruta = leer("LIKP-ROUTE")
            modalidad = leer("LIKP-ABLAD")
            modalidad = modalidad.upper()

            #print(f"SAP Placas Obtenidas: {placas}")
            #print(f"SAP Operador Obtenido: {operador}")
            #print(f"SAP Modalidad Obtenida: {modalidad}")


            # Datos de Entrega (Pestaña T\07)
            session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\07").select()
            clase_entrega = session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\07/ssubSUBSCREEN_BODY:SAPMV50A:2110/ctxtLIKP-LFART").text.strip()
            #print(f"SAP Clase de Remision: {clase_entrega}")

            # ===== Interlocutores (Pestaña T\08) =====
            session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\08").select()

            ruta_interlocutores = (
                "wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/"
                "tabpT\\08/ssubSUBSCREEN_BODY:SAPMV50A:2114/"
                "subSUBSCREEN_PARTNER_OVERVIEW:SAPLV09C:1000/"
                "tblSAPLV09CGV_TC_PARTNER_OVERVIEW/"
            )

            def leer_tabla(prefijo_columna, fila_num):
                """
                Ensambla correctamente el ID de la tabla.
                Ej: prefijo "cmbGVS_TC_DATA-REC-PARVW[0," + "0]" = "[0,0]"
                """
                return session.findById(f"{ruta_interlocutores}{prefijo_columna}{fila_num}]").text.strip()

            cliente_num = ""
            cliente_nombre = ""
            destinatario_num = ""
            destinatario_nombre = ""
            poblacion = ""

            for fila in range(12):
                try:
                    funcion = leer_tabla("cmbGVS_TC_DATA-REC-PARVW[0,", fila)
                except Exception as e:
                    # Imprimimos el error por si la tabla cambia en SAP
                    # print(f"Fin de tabla o error en fila {fila}: {e}")
                    break

                if not funcion:
                    break

                if "Solicitante" in funcion and not cliente_nombre:
                    cliente_num = leer_tabla("ctxtGVS_TC_DATA-REC-PARTNER[1,", fila)
                    cliente_nombre = leer_tabla("txtGVS_TC_DATA-REC-NAME1[3,", fila)

                elif "Destinatario mcía" in funcion:
                    destinatario_num = leer_tabla("ctxtGVS_TC_DATA-REC-PARTNER[1,", fila)
                    destinatario_nombre = leer_tabla("txtGVS_TC_DATA-REC-NAME1[3,", fila)
                    poblacion = leer_tabla("txtGVS_TC_DATA-REC-CITY1[6,", fila)

            #print(f"SAP Razon Social Obtenida: {cliente_nombre}")
            #print(f"SAP Destinatario Obtenido: {destinatario_nombre}")
            #print(f"SAP Poblacion Obtenida: {poblacion}")

            # Regresar a pantalla principal
            session.findById("wnd[0]").sendVKey(3)

            # --- 4. EXTRACCIÓN DE POSICIONES ---
            session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_OVERVIEW/tabpT\\01").select()
            # Validar si existe la fila
            base_table_id = "wnd[0]/usr/tabsTAXI_TABSTRIP_OVERVIEW/tabpT\\01/ssubSUBSCREEN_BODY:SAPMV50A:1102/tblSAPMV50ATC_LIPS_OVER"
                        
            # Creamos nuestra lista de materiales vacia
            materiales_lista = []

            for i in range(10): # Leemos hasta 10 filas
                try:
                    # Intentamos leer la posición, si falla es que no hay mas filas
                    try:
                        pos_txt = session.findById(f"{base_table_id}/txtLIPS-POSNR[0,{i}]").text.strip()
                    except:
                        break # Fin de la tabla

                    if pos_txt.strip() == "" or pos_txt == "0" or pos_txt == "______":
                        #print(f"SAP No hay mas posciciones: {pos_txt}")
                        break
                    
                    #print(f"SAP Posicion Obtenida: {pos_txt}")
                    try:
                        material_cod = session.findById(f"{base_table_id}/ctxtLIPS-MATNR[1,{i}]").text.strip()
                        info_material = self.obtener_info_material(material_cod)
                        #print(f"SAP Material obtenido: {material_cod}")
                    except:
                        pass

                    try:
                        cen_exp = session.findById(f"{base_table_id}/ctxtLIPS-WERKS[2,{i}]").text.strip()
                        #print(f"SAP C de Expedicion Obtenido: {cen_exp}")
                    except:
                        pass

                    try:
                        almacen = session.findById(f"{base_table_id}/ctxtLIPS-LGORT[3,{i}]").text.strip()
                        #print(f"SAP Almacen obtenido: {almacen}")
                    except:
                        pass

                    try:
                        str_cantidad = session.findById(f"{base_table_id}/txtLIPSD-G_LFIMG[4,{i}]").text.strip()
                        #print(f"SAP Cantidad str obtenida: {str_cantidad}")
                        cant_mat = float(str_cantidad.replace(",", ""))
                        #print(f"SAP Cantidad str convertida: {cant_mat}")
                    except:
                        #print(f"SAP NO se logró obtener o convertir el peso:")
                        pass

                    try:
                        material_denominacion = session.findById(f"{base_table_id}/txtLIPS-ARKTX[6,{i}]").text.strip()
                        #print(f"SAP Denominacion: {material_denominacion}")
                    except:
                        pass

                    materiales_lista.append({
                        "posicion": pos_txt,
                        "material": material_cod,
                        "cen_exp": cen_exp,
                        "almacen": almacen,
                        "peso_ton": cant_mat,
                        "material_denominacion" : material_denominacion,
                        "material_desc_corto" : info_material.get("desc_nom_corto", material_denominacion),
                        "gpo_material": info_material.get("grupo")
                    })
        
                except Exception as e_row:
                    print(f"❌ Error leyendo fila {i}: {e_row}")
                    # Importante: No hacemos break aquí para intentar leer la siguiente fila si es posible,
                    # o si es un error fatal, el break de arriba ya actuó.
                    break

            print(f"✅ Informacion extraida correctamente")
            return {

                "remision": num_remision,

                "cliente_num": cliente_num,
                "cliente": cliente_nombre,
                "destinatario_num": destinatario_num,
                "destinatario_nombre": destinatario_nombre,

                "operador": operador,
                "placa": placas,
                "poblacion": poblacion,
                "modalidad": modalidad,
                "ruta": ruta,

                "clase_entrega": clase_entrega,
                "clase_expedicion": clase_exp_sap,

                "fch_cita_carga": fch_cita_str,

                "materiales": materiales_lista,

                "st_transporte": st_transporte,
                "st_salida_merc": st_salida_merc,
                "st_factura": st_factura
            }

        except SAPError as e:
            # Reenviamos errores de negocio (pantalla roja)
            raise e
        except Exception as e:
            # Envolvemos errores técnicos inesperados
            print(f"Error técnico detallado: {e}") # Para ver en consola
            raise Exception(f"Error técnico en SAP: {str(e)}")

    # Folios de bascula
    # ==============================================================================
    # ELIMINAR TRANSPORTISTA (Requisito previo)
    # ==============================================================================
    @tunel_sap("VL02N: Eliminar Transportista")
    def eliminar_transportista(self, remision: str):
        """
        Entra a la VL02N y elimina el interlocutor 'Transportista' si existe.
        """
        session = self.obtener_sesion()
        if not session: raise SAPError("Sin sesión SAP.")

        try:
            # Navegar a VL02N
            self.acceder_a_transaccion(session, "VL02N")
            session.findById("wnd[0]/usr/ctxtLIKP-VBELN").text = remision
            session.findById("wnd[0]").sendVKey(0)

            # Ir a cabecera -> Interlocutores
            session.findById("wnd[0]/tbar[1]/btn[8]").press() # Cabecera
            session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\08").select() # Pestaña Interlocutores

            # Buscar Transportista en la tabla
            encontrado = False
            # Iteramos las primeras 8 filas
            for x in range(8):
                try:
                    # ID de la tabla de interlocutores
                    tabla_id = "wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\08/ssubSUBSCREEN_BODY:SAPMV50A:2114/subSUBSCREEN_PARTNER_OVERVIEW:SAPLV09C:1000/tblSAPLV09CGV_TC_PARTNER_OVERVIEW"
                    
                    rol = session.findById(f"{tabla_id}/cmbGVS_TC_DATA-REC-PARVW[0,{x}]").text
                    
                    if "Transportista" in rol:
                        # Seleccionar fila
                        session.findById(tabla_id).getAbsoluteRow(x).selected = True
                        # Botón borrar fila
                        session.findById("wnd[0]/usr/tabsTAXI_TABSTRIP_HEAD/tabpT\\08/ssubSUBSCREEN_BODY:SAPMV50A:2114/subSUBSCREEN_PARTNER_OVERVIEW:SAPLV09C:1000/btnDELETE").press()
                        # Confirmar Popup "Sí"
                        session.findById("wnd[1]/usr/btnSPOP-OPTION1").press()
                        encontrado = True
                        break
                except:
                    break # Si falla leer la fila, terminamos el loop

            # Guardar cambios
            session.findById("wnd[0]").sendVKey(11)
            
            # Verificar mensaje de grabado
            msg = session.findById("wnd[0]/sbar").text
            if "grabado" not in msg and "guardado" not in msg and encontrado:
                print(f"Advertencia: ✅ Interlocutor Eliminado")

        except Exception as e:
            print(f"Nota: No se pudo eliminar transportista o no existía: {e}")
            # No hacemos raise SAPError aquí porque a veces no es crítico si ya no estaba

    # ==============================================================================
    # CREAR FOLIO BÁSCULA (Lógica Principal)
    # ==============================================================================
    @tunel_sap("ZSDMX1270/1109: Crear Folio Báscula")
    def crear_folio_bascula(self, remisiones: list, centro_expedicion: str, 
                            tipo_remision: str, operador: str, placas: str, modalidad: str) -> str:
        """
        Crea el folio de báscula en ZSDMX1270 o ZSDMX1109.
        Retorna: Folio de bascula.
        """
        session = self.obtener_sesion()
        if not session: raise SAPError("Sin sesión SAP.")
        
        # 1. Limpieza previa
        # Extraemos solo los números de remisión de la lista de diccionarios
        lista_solo_numeros = [rem['remision'] for rem in remisiones]
        
        # Usamos set() para eliminar duplicados instantáneamente
        remisiones_unicas = set(lista_solo_numeros)
        # Recorremos todas las remisiones para quitarles el transportista
        for num_remision in remisiones_unicas:
            self.eliminar_transportista(num_remision)

        # 2. Determinar Transacción y Tablas
        es_mx47_mx57 = centro_expedicion in ["MX47", "MX57"]
        transaccion = "ZSDMX1270" if es_mx47_mx57 else "ZSDMX1109"
        #print(f"Se ingresa a transaccion {transaccion}")
    
        # 3. Iniciar Transacción
        self.acceder_a_transaccion(session, transaccion)

        # 4. Seleccionar Tipo (Radio Button)
        # Asumiendo: "ZAM1" (Venta Cliente) -> Venta Local
        # Si es "TRASPASO" -> Salida Traspaso
        
        # 4. Seleccionar Tipo (Radio Button) basado en la Clase de Entrega
        # Definimos los grupos de validación
        rem_traspaso = ["NL", "ZCCD"]
        rem_interco  = ["YUNC"]
        clase_actual = remisiones[0].get("clase_entrega", "").upper()
        
        try:
            if clase_actual in rem_traspaso:
                print(f"📦 Clase {clase_actual} detectada: Seleccionando Salida Traspaso")
                session.findById("wnd[1]/usr/radRB_SALTRA").select()
                
            elif clase_actual in rem_interco:
                print(f"🏢 Clase {clase_actual} detectada: Seleccionando Salida Intercompañía")
                session.findById("wnd[1]/usr/radRB_SALINT").select()
                
            else:
                # Por defecto SAP suele dejar seleccionado "Venta Local" (ZAM1)
                pass
        except Exception as e:
            print(f"⚠️ No se pudo cambiar el RadioButton de tipo de venta: {e}")
            pass

        # 5. Ingresar Centro o Báscula
        if es_mx47_mx57:
            session.findById("wnd[1]/usr/cmbLV_BASCULA").key = "1"
        else:
            session.findById("wnd[1]/usr/ctxtT001W-WERKS").text = centro_expedicion
        
        session.findById("wnd[1]").sendVKey(0) # Enter

        # Validar Autorización
        msg = session.findById("wnd[0]/sbar").text
        if "Sin autori" in msg:
            raise SAPError(f"Sin autorización para transacción {transaccion}")

        # ID tabla posiciones de la remision a cargar, cambia segun la transacción
        id_tabla_posiciones = "wnd[1]/usr/tblZSDMXR1116TC_POSPOS_110" if es_mx47_mx57 else "wnd[1]/usr/tblZSDMXR1039TC_POSPOS_110"
        # 6. AGREGAR REMISIONES (Loop)
        for num_remision in remisiones_unicas:
            
            # Poner número remisión
            session.findById("wnd[0]/usr/ctxtVG_VBELN").text = num_remision
            # Botón Seleccionar Posiciones
            session.findById("wnd[0]/usr/btnBTN_SEL_PO").press()
            #print(f"SAP Se agregó remisiones a báscula {num_remision}")
            # Manejo del Popup de posiciones
            if session.Children.Count > 1:
                try:
                    # Seleccionar las primeras 5 filas
                    grid_pos = session.findById(id_tabla_posiciones)
                    for row_idx in range(5):
                        try:
                            grid_pos.getAbsoluteRow(row_idx).selected = True
                        except:
                            break # No hay más filas
                    
                    session.findById("wnd[1]/usr/btnBTN_OK").press() # OK interno
                    
                    # A veces hay un segundo OK o validación error 619 en VBA
                    try:
                        session.findById("wnd[1]/usr/btnBTN_OK").press()
                    except:
                        pass
                except Exception as e:
                    #print(f"Debug: Error en popup posiciones: {e}")
                    pass

            # Validar Errores de carga
            msg = session.findById("wnd[0]/sbar").text
            if "La entrega ya ha sido procesada" in msg or "No se puede procesar" in msg:
                raise SAPError(f"Error al agregar remisión {num_remision}: {msg}")
            
            

        # 7. AGREGAR OPERADOR
        # Llenar placas
        session.findById("wnd[0]/usr/ctxtWA_1105-PLACAS").text = placas
        session.findById("wnd[0]").sendVKey(0)
        
        # Buscar Operador (F4 en campo transporte)
        session.findById("wnd[0]/usr/ctxtWA_1105-TRANSPO").setFocus()
        session.findById("wnd[0]").sendVKey(4) # F4
        
        # Llamamos a la función auxiliar de búsqueda
        operador_encontrado = self._zsd_buscar_operador(session, operador, modalidad)
        
        if not operador_encontrado:
             # Si falla la búsqueda automática, intentamos dejarlo o error
             raise SAPError(f"No se encontró el operador '{operador}' en la lista de SAP.")

        # Guardar cambios intermedios (VKey 11) y salir de popups
        session.findById("wnd[0]").sendVKey(11) 
        session.findById("wnd[1]/tbar[0]/btn[0]").press()

        # 8. FINALIZAR
        # Si folio_txt es vacio quiere decir que NO se generó el folio de bascula
        folio_txt = session.findById("wnd[0]/usr/ctxtVG_CONTROL").text
        #print(f"Folio Bascula: {folio_txt}")
        if folio_txt == "":
             raise SAPError("No se generó el folio de bascula (VG_CONTROL vacío)")

        else:
            # Si folio_txt NO es vacio, se creó el folio de báscula
            # Seleccionar todas las filas en la tabla principal para **reprocesar transporte**
            # IDs de tablas cambian según la transacción
            id_tabla_final = "wnd[0]/usr/tblZSDMXR1116TC_100" if es_mx47_mx57 else "wnd[0]/usr/tblZSDMXR1039TC_100"
            total_remisiones = len(remisiones)
            #print(f"✅ Remisiones a reprocesar: {total_remisiones}")
            # Corresponde al número de remisiones agregadas.

            for i in range(total_remisiones): 
                try:
                    tabla_main = session.findById(id_tabla_final)

                    tabla_main.getAbsoluteRow(i).selected = True
                    session.findById("wnd[0]/tbar[1]/btn[5]").press()
                    print(f"✅ Se reproceso remision: {remisiones[i]['remision']}")

                    # Manejo de confirmacion
                    if session.Children.Count > 1:
                        session.findById("wnd[1]/tbar[0]/btn[0]").press() # Enter en popup

                    tabla_main = session.findById(id_tabla_final)
                    tabla_main.getAbsoluteRow(i).selected = False
                except Exception as e:
                    print(f"⚠️ Error al reprocesar {i}: {e}")
                    break
        print(f"✅ Folio de Bascula Creado Exitosamente")
        return folio_txt
    
    def _zsd_buscar_operador(self, session, nombre_operador_kiosco: str, modalidad: str) -> bool:
        """
        Itera sobre el listado del Matchcode (F4) para encontrar al chofer en transaccion de basculas.
        """
        # =================================================================
        # FUNCION AUXILIAR DE LIMPIEZA (Sin 'self' porque está anidada)
        # =================================================================
        def normalizar_texto(texto: str) -> str:
            if not texto: return ""
            t = str(texto).upper()
            t = ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
            t = re.sub(r'[^A-Z\s]', '', t)
            t = re.sub(r'\s+', ' ', t).strip()
            return t
        # =================================================================

        try:
            # ID Retirado según tu regla de negocio
            no_modalidad_retirado = "702551"
            #print(f"Modalidad recibida: {modalidad}")

            encontrado = False
            fila_encontrada = -1

            # Normalizamos el nombre del Kiosko una sola vez (es más rápido)
            nom_k = normalizar_texto(nombre_operador_kiosco)
            #print(f"Nombre Kiosko Normalizado: {nom_k}")

            for i in range(3, 24):
                try:
                    # Obtenemos nombre y numero de la grilla de etiquetas
                    op_nombre_sap = session.findById(f"wnd[1]/usr/lbl[23,{i}]").text.strip()
                    op_numero_sap = session.findById(f"wnd[1]/usr/lbl[12,{i}]").text.strip()
                    
                    nom_s = normalizar_texto(op_nombre_sap)
                    
                    # Log detallado de la comparación
                    #print(f"Comparando Kiosko [{nom_k}] vs SAP [{nom_s}] (Num: {op_numero_sap})")
                    
                    # Validar si coinciden los nombres
                    coincide_nombre = (nom_k in nom_s) or (nom_s in nom_k)
                    
                    if coincide_nombre:
                        # Reglas de negocio de modalidad
                        valido = False
                        
                        if modalidad == "RETIRADO" and op_numero_sap == no_modalidad_retirado:
                            valido = True
                        elif modalidad == "ENTREGADO" and op_numero_sap != no_modalidad_retirado:
                            valido = True
                        elif modalidad == "AUTOFLETE" and op_numero_sap != no_modalidad_retirado:
                             valido = True
                        elif not modalidad:
                            valido = True

                        if valido:
                            fila_encontrada = i
                            encontrado = True
                            print(f"✅ Operador validado y seleccionado en fila {i}.")
                            break
                        else:
                            print(f"⚠️ Nombre coincide, pero modalidad/número no es válido ({op_numero_sap}). Buscando otro...")
                            
                except Exception as e:
                    # Quitamos el pass silencioso para saber si hay un error real en una fila
                    # print(f"Fila {i} vacía o error: {e}") 
                    continue

            # =================================================================
            # ACCIÓN FINAL SI SE ENCONTRÓ
            # =================================================================
            if encontrado:
                # Seleccionar la fila (Focus + F2/Click)
                label_target = f"wnd[1]/usr/lbl[1,{fila_encontrada}]"
                session.findById(label_target).setFocus()
                session.findById("wnd[0]").sendVKey(2) # Seleccionar
                
                # Llenar campo conductor y volver a buscar/confirmar 
                session.findById("wnd[0]/usr/ctxtWA_1105-CONDUC").setFocus()
                session.findById("wnd[0]").sendVKey(4) # F4 otra vez
                
                # Volver a seleccionar en el popup
                session.findById(label_target).setFocus()
                session.findById("wnd[1]/tbar[0]/btn[0]").press() # Check
                
                return True
            else:
                return False

        except Exception as e:
            print(f"❌ Error en _zsd_buscar_operador: {e}")
            return False

    
    # ==============================================================================
    # 4. CREAR TRANSPORTE (VT01N)
    # ==============================================================================
    @tunel_sap("VT01N: Crear Transporte")
    def crear_transporte(self, remisiones: list, centro_expedicion: str, 
                         modalidad: str, operador: str, placas: str, 
                         clase_expedicion_f: str, fecha_checklist: str = "") -> str:
        """
        Crea el número de transporte en la transacción VT01N.
        Retorna: El número de transporte creado (str).
        """
        session = self.obtener_sesion()
        if not session: raise SAPError("Sin sesión SAP.")

        # 1. Preparación de Datos
        # Extraemos solo los números de remisión únicos
        lista_solo_numeros = [rem['remision'] for rem in remisiones]
        remisiones_unicas = list(set(lista_solo_numeros))

        # Mapeo de ZTP_Modalidad
        ztp_modalidad = "ZTP2" # Default
        if modalidad == "RETIRADO":
             ztp_modalidad = "ZTP2"
        elif modalidad == "AUTOFLETE":
            ztp_modalidad = "ZTP1"
        
        # 2. Iniciar Transacción VT01N
        # Reemplazar la entrada manual a VT01N
        self.acceder_a_transaccion(session, "VT01N")

        # 3. Pantalla Inicial
        try:
            session.findById("wnd[0]/usr/ctxtVTTK-TPLST").text = centro_expedicion
            session.findById("wnd[0]/usr/cmbVTTK-SHTYP").key = ztp_modalidad 
            session.findById("wnd[0]").sendVKey(0) # Enter
        except Exception as e:
            raise SAPError(f"Error al iniciar VT01N: {e}")

        # 4. Agregar Remisiones
        session.findById("wnd[0]").sendVKey(7) # F7 - Seleccionar Entregas
        
        # Estrategia robusta (Iterativa UNA POR UNA)
        for remision_id in remisiones_unicas:
            
            # --- PASO 1: BUSCAR EL CENTRO ESPECÍFICO DE ESTA REMISIÓN ---
            # Buscamos el diccionario completo que corresponde a este ID de remisión
            # Usamos next() para encontrar la primera coincidencia en la lista 'remisiones'
            datos_remision = next((item for item in remisiones if item["remision"] == remision_id), None)
            
            # Valor por defecto: el que recibimos como argumento en la función
            centro_a_usar = centro_expedicion 

            # Si encontramos los datos, extraemos el 'cen_exp' del primer material
            if datos_remision and "materiales" in datos_remision:
                mats = datos_remision["materiales"]
                if mats:
                    # Obtenemos el centro del primer material de esa remisión
                    # (Asumiendo que toda la remisión sale del mismo centro)
                    c_temp = mats[0].get("cen_exp", "")
                    if c_temp:
                        centro_a_usar = c_temp

            # print(f"🚛 Agregando Remisión: {remision_id} | Desde Centro: {centro_a_usar}")

            # --- PASO 2: INTERACCIÓN CON SAP ---
            
            # Presionar botón "Entregas" (Ctrl+F5) para abrir el filtro
            session.findById("wnd[0]").sendVKey(29) 
            
            try:
                # Usamos 'centro_a_usar', no el genérico
                session.findById("wnd[1]/usr/ctxtS_VSTEL-LOW").text = centro_a_usar
                
                # Número de Entrega (Remisión actual)
                session.findById("wnd[1]/usr/ctxtS_VBELN-LOW").text = remision_id
                
                # Ejecutar (F8)
                session.findById("wnd[1]").sendVKey(8) 
                
            except Exception as e:
                print(f"⚠️ Error al intentar agregar remisión {remision_id}: {e}")
                # Intentar cerrar el popup si se quedó atorado
                try: session.findById("wnd[1]").sendVKey(12) 
                except: pass

            # Validar si se agregaron entregas (lectura de barra de estado)
            msg = session.findById("wnd[0]/sbar").text
            if "0" in msg:
                print(f"⚠️ SAP indica 0 entregas seleccionadas para {remision_id} en {centro_a_usar}")
                
        # 5. Ir a la pantalla de Datos de Cabecera (Resumen)
        session.findById("wnd[0]").sendVKey(16) # Shift+F4 - Resumen
        
        # Helper internal to close popups
        def cerrar_popup():
             if session.Children.Count > 1:
                 try: session.findById("wnd[1]/tbar[0]/btn[0]").press()
                 except: pass

        # 6. Llenar Datos de Cabecera (Función Auxiliar)
        # This function fills text fields
        self._llenar_datos_transporte(session, modalidad, operador, placas, clase_expedicion_f)

        # 7. Validaciones Finales (Validar campos obligatorios antes de guardar)
        # --- Pestaña: Fechas (TABS_OV_DE) ---
        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP2/tabpTABS_OV_DE").select()
        cerrar_popup()
        
        ahora = datetime.datetime.now()
        if fecha_checklist: # Esto significa: Si la variable NO está vacía
            try:
                # Convertimos el texto "YYYY-MM-DD HH:MM:SS" a un objeto de tiempo real
                ahora = datetime.datetime.strptime(fecha_checklist.strip(), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"⚠️ Aviso: Formato de fecha inválido '{fecha_checklist}'. Usando hora actual.")
        
        # Formateamos al estilo SAP (DD.MM.YYYY y HH:MM)
        fecha_str = ahora.strftime("%d.%m.%Y")
        hora_str = ahora.strftime("%H:%M")
            
        #print(f"Fecha a ingresar: {fecha_str} - Hora a ingresar: {hora_str}" )

        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP2/tabpTABS_OV_DE/ssubG_HEADER_SUBSCREEN2:SAPMV56A:1025/ctxtVTTK-UZDIS").text = hora_str
        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP2/tabpTABS_OV_DE/ssubG_HEADER_SUBSCREEN2:SAPMV56A:1025/ctxtVTTK-DTDIS").text = fecha_str
        
        if centro_expedicion not in ["MX57", "MX47"]:
             session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP2/tabpTABS_OV_DE/ssubG_HEADER_SUBSCREEN2:SAPMV56A:1025/ctxtVTTK-UAREG").text = hora_str
             session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP2/tabpTABS_OV_DE/ssubG_HEADER_SUBSCREEN2:SAPMV56A:1025/ctxtVTTK-DAREG").text = fecha_str

        session.findById("wnd[0]").sendVKey(0) # Validar fechas
        #Aqui sale una ventana emergente que habra que analizar, es diferente a la de pesos
        session.findById("wnd[1]").sendVKey(8) 

        # Pestaña: Gestión (TABS_OV_PR)
        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP1/tabpTABS_OV_PR").select()
        cerrar_popup()
        
        # --- A. Validar Transportista (TDLNR) ---
        transportista_sap = session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP1/tabpTABS_OV_PR/ssubG_HEADER_SUBSCREEN1:SAPMV56A:1021/ctxtVTTK-TDLNR").text
        if not transportista_sap:
             raise SAPError("El campo Transportista (TDLNR) está vacío. Es obligatorio.")
        
        cod_retirado = "702551" 
        if modalidad == "RETIRADO":
            if transportista_sap != cod_retirado:
                 raise SAPError(f"Error Modalidad: Es RETIRADO pero transportista es {transportista_sap} (Se esperaba {cod_retirado}).")
        elif modalidad in ["ENTREGADO", "AUTOFLETE"]:
            if transportista_sap == cod_retirado:
                 raise SAPError(f"Error Modalidad: Es {modalidad} pero transportista es RETIRADO ({cod_retirado}).")

        # --- B. Validar Ruta (ROUTE) ---
        ruta_sap = session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP1/tabpTABS_OV_PR/ssubG_HEADER_SUBSCREEN1:SAPMV56A:1021/ctxtVTTK-ROUTE").text
        if not ruta_sap:
                raise SAPError("El campo Ruta (ROUTE) está vacío. Es obligatorio.")

        # --- C. Validar Clase Expedición (VSART) ---
        vsart_sap = session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP1/tabpTABS_OV_PR/ssubG_HEADER_SUBSCREEN1:SAPMV56A:1021/ctxtVTTK-VSART").text
        if not vsart_sap:
            raise SAPError("El campo Clase de Expedición (VSART) está vacío. Es obligatorio.")
        

        # 8. Guardar
        session.findById("wnd[0]").sendVKey(11) # Ctrl+S
        
        # Manejo de Popups de advertencia al guardar
        try:
             if session.Children.Count > 1:
                 session.findById("wnd[1]/tbar[0]/btn[0]").press()
             if session.Children.Count > 1:
                 session.findById("wnd[1]/tbar[0]/btn[0]").press()
        except:
             pass

        # 9. Obtener Número de Transporte
        mensaje_final = session.findById("wnd[0]/sbar").text
        
        # Extract number
        match = re.search(r'\d+', mensaje_final)
        if match:
             no_transporte = match.group(0)
             print(f"✅ TRANSPORTE CREADO EXITOSAMENTE: {no_transporte}")
             return no_transporte
        else:
             raise SAPError(f"Error al guardar transporte: {mensaje_final}")

    def _llenar_datos_transporte(self, session, modalidad, operador, placas, clase_exp_f):
        """
        Llena los campos detallados en la cabecera del transporte (VT01N).
        """
        def cerrar_popup_si_existe():
            if session.Children.Count > 1:
                try: session.findById("wnd[1]/tbar[0]/btn[0]").press()
                except: pass

        # --- Pestaña: Identificador (TABS_OV_ID) ---
        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP1/tabpTABS_OV_ID").select()
        cerrar_popup_si_existe()
        
        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP1/tabpTABS_OV_ID/ssubG_HEADER_SUBSCREEN1:SAPMV56A:1022/txtVTTK-TPBEZ").text = modalidad
        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP1/tabpTABS_OV_ID/ssubG_HEADER_SUBSCREEN1:SAPMV56A:1022/txtVTTK-TNDR_TRKID").text = placas
        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP1/tabpTABS_OV_ID/ssubG_HEADER_SUBSCREEN1:SAPMV56A:1022/txtVTTK-SIGNI").text = placas
        #print(f"Datos agregados a Identificador: {modalidad} {placas}")

        # --- Pestaña: Datos Adic. (TABS_OV_AI) ---
        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP2/tabpTABS_OV_AI").select()
        cerrar_popup_si_existe()

        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP2/tabpTABS_OV_AI/ssubG_HEADER_SUBSCREEN2:SAPMV56A:1030/ctxtVTTK-ADD03").text = modalidad
        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP2/tabpTABS_OV_AI/ssubG_HEADER_SUBSCREEN2:SAPMV56A:1030/txtVTTK-TEXT2").text = operador
        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP2/tabpTABS_OV_AI/ssubG_HEADER_SUBSCREEN2:SAPMV56A:1030/txtVTTK-TEXT3").text = "01 EN ESPERA"
        #print(f"Datos agregados a Datos Adic: {modalidad} {operador}")

        # --- Pestaña: Gestión (TABS_OV_PR)
        session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP1/tabpTABS_OV_PR").select()
        cerrar_popup_si_existe()
        # Asignar Clase Expedición
        
        try:
            session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP1/tabpTABS_OV_PR/ssubG_HEADER_SUBSCREEN1:SAPMV56A:1021/ctxtVTTK-VSART").text = clase_exp_f
            #print(f"Datos agregados a Gestion: {clase_exp_f}")
        except:
            raise SAPError(f"No se logró ingresar tipo de unidad: {clase_exp_f}")

        #print(F"Datos agregados exitosamente: {modalidad} {operador} {placas} {clase_exp_f}")

    
    # ==============================================================================
    # 5. MODIFICAR TRANSPORTE (VT02N) - DINÁMICO POR DICCIONARIO
    # ==============================================================================
    @tunel_sap("VT02N: Modificar Transporte")
    def modificar_transporte(self, num_transporte: str, data: dict) -> bool:
        """
        Ingresa a la VT02N, modifica los campos recibidos en el diccionario 'data',
        guarda el transporte, evalúa la respuesta de SAP y devuelve True/False.
        Ej. data = {"TEXT3": "02 llamado 29/09/2026 12:15:00"}
        """
        session = self.obtener_sesion()
        if not session:
            raise SAPError("No hay sesión activa en SAP.")

        num_transporte = str(num_transporte).strip()
        if not num_transporte or num_transporte in ["---", "PENDIENTE", "None", ""]:
            raise SAPError(f"El transporte '{num_transporte}' no es válido para VT02N.")

        if not data or not isinstance(data, dict):
            raise SAPError("No se recibieron datos válidos (diccionario vacío) para modificar.")

        def cerrar_popup_si_existe():
            while session.Children.Count > 1:
                try:
                    session.findById("wnd[1]/tbar[0]/btn[0]").press()
                except:
                    try:
                        session.findById("wnd[1]").sendVKey(0)
                    except:
                        break

        try:
            # 1. Entrar a transacción VT02N
            self.acceder_a_transaccion(session, "VT02N")

            # 2. Ingresar el número de transporte en la pantalla inicial y dar Enter
            session.findById("wnd[0]/usr/ctxtVTTK-TKNUM").text = num_transporte
            session.findById("wnd[0]").sendVKey(0)

            # 3. Escuchar a SAP: Validar si el transporte está bloqueado o no existe
            sap_msg = session.findById("wnd[0]/sbar").text
            if sap_msg:
                palabras_bloqueo = ["bloqueado", "actualmente en", "no existe", "archivado", "autorización", "tratamiento"]
                if any(palabra in sap_msg.lower() for palabra in palabras_bloqueo):
                    raise SAPError(f"Bloqueo SAP -> {sap_msg}")

            cerrar_popup_si_existe()

            # 4. Modificar datos según parámetros recibidos en el diccionario 'data'
            # --- C) Pestaña: Datos Adic. (TABS_OV_AI) ---
            mapa_datos_adic = {
                "ADD03": "ctxtVTTK-ADD03",
                "ADD04": "ctxtVTTK-ADD04",
                "TEXT1": "txtVTTK-TEXT1",
                "TEXT2": "txtVTTK-TEXT2",
                "TEXT3": "txtVTTK-TEXT3",
                "TEXT4": "txtVTTK-TEXT4"
            }

            # Verificamos si alguna llave del diccionario pertenece a esta pestaña
            if any(k in data for k in mapa_datos_adic):
                # Pestaña Datos Adicionales ---
                session.findById("wnd[0]/usr/tabsHEADER_TABSTRIP2/tabpTABS_OV_AI").select()
                cerrar_popup_si_existe()

                ruta_adicionales = (
                    "wnd[0]/usr/tabsHEADER_TABSTRIP2/tabpTABS_OV_AI/"
                    "ssubG_HEADER_SUBSCREEN2:SAPMV56A:1030/"
                )

                # Iteramos solo sobre las llaves que sí vinieron en 'data'
                for llave, campo_sap in mapa_datos_adic.items():
                    if llave in data:
                        valor_nuevo = str(data[llave]).strip()
                        session.findById(f"{ruta_adicionales}{campo_sap}").text = valor_nuevo
                        print(f"✏️ [VT02N] Transporte {num_transporte} -> {llave} = '{valor_nuevo}'")

            # 5. Guardar cambios (Ctrl + S / VKey 11)
            session.findById("wnd[0]").sendVKey(11)
            cerrar_popup_si_existe()

            # 6. Evaluar mensaje devuelto en la barra de estado
            msg_bar = session.findById("wnd[0]/sbar").text.strip()
            print(f"📡 [SAP sbar VT02N]: '{msg_bar}'")

            # Validamos tu mensaje particular o los mensajes estándar de éxito en VT02N
            mensajes_exito = [
                "error: al recuperar información", # Mensaje particular de éxito en tu entorno SAP
                "se grabó",
                "se ha grabado",
                "guardado",
                "modificado"
            ]

            if any(exito in msg_bar.lower() for exito in mensajes_exito):
                #self.emitter.keep_alive_signal.emit(f"Transporte {num_transporte} actualizado.", "green")
                return True
            else:
                # Si SAP devuelve otro mensaje inesperado, lo reportamos para escucharlo en el log
                #self.emitter.keep_alive_signal.emit(f"Respuesta inesperada al guardar {num_transporte}: '{msg_bar}'", "red")
                raise SAPError(f"Respuesta inesperada al guardar {num_transporte}: '{msg_bar}'")

        except SAPError as e:
            #self.emitter.keep_alive_signal.emit(f"Error SAP en VT02N: {e}", "red")
            raise e
        
        except Exception as e:
            #self.emitter.keep_alive_signal.emit("Falla técnica en VT02N", "red")
            raise SAPError(f"Error técnico modificando transporte {num_transporte}: {e}")

    # ==============================================================================
    # 6. IMPRIMIR PICKING (VL02N)
    # ==============================================================================
    @tunel_sap("VL02N: Imprimir Picking")
    def imprimir_picking(self, remisiones: list, centro_expedicion: str):
        """
        Entra a la VL02N, busca el mensaje 'Picking Elementia' y lo imprime.
        Maneja duplicados y cantidad de copias según reglas de negocio.
        """
        session = self.obtener_sesion()
        if not session: raise SAPError("Sin sesión SAP.")

        # 1. Limpieza de duplicados (Set)
        lista_solo_numeros = [rem['remision'] for rem in remisiones]
        remisiones_unicas = list(set(lista_solo_numeros))

        for remision in remisiones_unicas:
            try:
                print(f"🖨️ Procesando impresión remisión: {remision}")

                # 2. Navegar a VL02N
                session.findById("wnd[0]/tbar[0]/okcd").text = "/nVL02N"
                session.findById("wnd[0]").sendVKey(0)
                
                # Ingresar Remisión
                session.findById("wnd[0]/usr/ctxtLIKP-VBELN").text = remision
                
                # 3. Ir a Menú: Detalles -> Mensajes de entrega (Cabecera)
                # VBA: session.findById("wnd[0]/mbar/menu[0]/menu[6]").Select
                try:
                    session.findById("wnd[0]/mbar/menu[0]/menu[6]").select()
                except:
                    # A veces si la remisión está bloqueada o no existe, falla aquí
                    print(f"⚠️ No se pudo acceder al menú de mensajes para {remision}. ¿Remisión bloqueada?")
                    continue

                # Validar barra de estado inicial (Por si hay error al entrar)
                msg_status = session.findById("wnd[0]/sbar").text
                if msg_status != "":
                    # A veces salen warnings, pero si es error rojo no dejará avanzar.
                    # El VBA chequeaba si no era vacío. Nosotros imprimimos y seguimos si nos deja.
                    print(f"ℹ️ Aviso SAP al entrar: {msg_status}")

                # 4. Buscar "Picking Elementia" en la tabla
                # Tabla: tblSAPLVMSGTABCONTROL
                encontrado = False
                tbl_mensajes = "wnd[1]/usr/tblSAPLVMSGTABCONTROL"
                
                # Iteramos 0 a 10 como en VBA
                for z in range(11):
                    try:
                        # Columna Texto: txtT685T-VTEXT[1, z]
                        # Nota: El índice de columna [1, z] significa columna 1 visual, fila z.
                        fila_texto = session.findById(f"{tbl_mensajes}/txtT685T-VTEXT[1,{z}]").text
                        
                        if fila_texto == "Picking Elementia":
                            # Seleccionar fila
                            session.findById(tbl_mensajes).getAbsoluteRow(z).selected = True
                            encontrado = True
                            break
                    except:
                        # Fin de la tabla
                        break
                
                if not encontrado:
                    print(f"❌ No se encontró mensaje 'Picking Elementia' para {remision}")
                    session.findById("wnd[1]").sendVKey(12) # Cancelar/Salir del popup
                    continue

                # 5. Configurar Impresora (Botón Medios de Comunicación)
                # VBA: btn[6]
                session.findById("wnd[1]/tbar[0]/btn[6]").press()
                
                # Dispositivo de salida: local
                session.findById("wnd[2]/usr/ctxtNAST-LDEST").text = "local"
                
                # 6. Definir Copias
                # Regla: MX46, MX47, MX57 -> 2 copias, resto 1.
                copias = "1"
                if centro_expedicion in ["MX46", "MX47", "MX57"]:
                    copias = "2"
                
                session.findById("wnd[2]/usr/txtNAST-ANZAL").text = copias
                
                # Regresar (Confirmar datos de impresión) - btn[0]
                session.findById("wnd[2]/tbar[0]/btn[0]").press()
                
                # 7. Ejecutar Acción / Imprimir
                # VBA: btn[86] (Suele ser un botón de "Ejecutar" o "Imprimir" en esa barra)
                session.findById("wnd[1]/tbar[0]/btn[86]").press()
                
                # Confirmar éxito
                msg_final = session.findById("wnd[0]/sbar").text
                if "correctamente" in msg_final or "grabado" in msg_final:
                    print(f"✅ Impresión enviada exitosamente ({copias} copias).")
                else:
                    print(f"⚠️ Resultado impresión: {msg_final}")

            except Exception as e:
                print(f"❌ Error al imprimir remisión {remision}: {e}")

    def obtener_info_material(self, codigo_sap: str) -> dict:
        """
        Recibe un código (ej. '000000000001331169') y devuelve info del catálogo.
        Si no existe, devuelve grupo 'DESCONOCIDO'.
        """
        if not codigo_sap:
            return {"desc_nom_corto": "VACIO", "grupo": "DESCONOCIDO"}
        
        # 1. Limpiar ceros a la izquierda (SAP suele mandar ceros)
        # Convertimos a string y usamos lstrip("0")
        codigo_limpio = str(codigo_sap).strip().lstrip("0")
        
        # 2. Buscar en el diccionario
        info = CATALOGO_MATERIALES.get(codigo_limpio)
        
        if info:
            return info # Retorna {"nombre": "...", "grupo": "ENVASADO"}
        else:
            return {"desc_nom_corto": "NO CATALOGADO", "grupo": "DESCONOCIDO"}

    def validar_clase_expedicion(self, remisiones: list, tipo_unidad_cloudfort: str) -> str:

        """
        1. Valida NO mezclar GRANEL con ENVASADO.
        2. Suma el peso total de todas las remisiones.
        3. Aplica reglas de negocio para determinar F1, F2, F3, F4, F5, F7.
        4. Valida vs CloudFort.
        
        Retorna: La clase de expedición CALCULADA (ej. "F1", "F7").
        """
        grupos_detectados = set()
        peso_total = 0.0
        
        # ---------------------------------------------------------
        # 1. ANÁLISIS DE MATERIALES Y PESO
        # ---------------------------------------------------------
        for rem in remisiones:
            if 'materiales' in rem:
                for mat in rem['materiales']:
                    # Detectar Grupo
                    gpo = mat.get('gpo_material', 'DESCONOCIDO')
                    if gpo in ["GRANEL", "ENVASADO"]:
                        grupos_detectados.add(gpo)
                    
                    # Sumar Peso (Asegurando que sea float)
                    try:
                        peso_mat = float(mat.get('peso_ton', 0))
                        peso_total += peso_mat
                    except:
                        pass # Si hay error en peso, sumamos 0
        

        # ---------------------------------------------------------
        # 2. REGLA DE ORO: NO MEZCLAR
        # ---------------------------------------------------------
        if "GRANEL" in grupos_detectados and "ENVASADO" in grupos_detectados:
            raise SAPError("BLOQUEO DE SEGURIDAD: No se puede mezclar carga GRANEL con ENVASADO en el mismo viaje.")

        # Determinar el Grupo Dominante
        es_granel = "GRANEL" in grupos_detectados
        # Si no hay grupo detectado (ej. solo sacos vacíos), asumimos Envasado para lógica F3/F2
        es_envasado = "ENVASADO" in grupos_detectados or (not es_granel)

        # ---------------------------------------------------------
        # 3. CÁLCULO DE CLASE DE EXPEDICIÓN (Reglas VBA)
        # ---------------------------------------------------------
        clase_calculada = "" # Default

        # --- REGLA 1: MENOR O IGUAL A 20 TON ---
        if peso_total <= 20:
            if es_granel:
                clase_calculada = "F5" # TOLVITA
            else:
                clase_calculada = "F3" # TORTON

        # --- REGLA 2: MAYOR A 38 TON ---
        elif peso_total >= 38:
            if es_granel:
                clase_calculada = "F7" # TOLVA FULL
            else:
                clase_calculada = "F4" # PLANA FULL

        # --- REGLA 3: ENTRE 20 Y 38 (Rango Medio) ---
        else:
            # Por defecto en este rango:
            if es_granel:
                clase_calculada = "F1" # TOLVA SENCILLA
            else:
                clase_calculada = "F2" # PLANA SENCILLA

            # --- EXCEPCIÓN VBA (OVERRIDE 25-27 TON) ---
            # Por el tamaño de las basculas en TULA se generan 2 remisiones de 26 para full
            if 25 <= peso_total <= 27:
                if es_granel:
                    # Si es Granel entre 25-27 cambia a F7 (FULL)
                    clase_calculada = "F7" 
                else:
                    # Envasado se mantiene en F2 (Plana Sencilla)
                    clase_calculada = "F2"

         #print(f"🚚 Transporte Calculado: {clase_calculada}")

        # ---------------------------------------------------------
        # 4. VALIDACIÓN VS CLOUDFORT
        # ---------------------------------------------------------
        # La regla de negocio suele ser: EL PESO MANDA.
        # Si CloudFort dice F1 pero traes 50 toneladas, DEBE ser F7/F4.
        
        tipo_unidad_final = clase_calculada 
        
        if tipo_unidad_cloudfort:
            cf_clean = tipo_unidad_cloudfort[:2].upper()
            
            # Solo validamos congruencia de TIPO (Tolva vs Plana)
            # No validamos capacidad (F1 vs F7) porque eso lo dicta el peso calculado arriba.
            
            if es_granel and not cf_clean.startswith("F1") and not cf_clean.startswith("F5") and not cf_clean.startswith("F7"):
                 print(f"⚠️ Conflicto en tipo de Unidad: CloudFort dice {cf_clean}. Se usará {clase_calculada}.")
            
            elif es_envasado and not cf_clean.startswith("F2") and not cf_clean.startswith("F3") and not cf_clean.startswith("F4"): # F1/F5/F7 son tolvas
                 print(f"⚠️ Conflicto en tipo de Unidad: CloudFort dice {cf_clean}. Se usará {clase_calculada}.")
            
            elif cf_clean != clase_calculada:
                print(f"⚠️ Conflicto en tipo de Unidad: CloudFort dice {cf_clean}, pero por peso ({peso_total} ton) corresponde {clase_calculada}. Se usará {clase_calculada}.")

        return tipo_unidad_final

    # ==============================================================================
    # MOTOR DE DESCARGAS Y ROBOT ORQUESTADOR ZSDMX389
    # ==============================================================================
    @tunel_sap("ZSDMX389: Descarga Reporte")
    def zsdmx389(self, path_descarga: str, nom_archivo: str, extencion: str = "csv",
                 fch_in: str = "01.01.2026", fch_fn: str = "31.12.2026", 
                 org_vta: str = "0152", can_dis: str = "16", 
                 filtro_transporte: str = "", 
                 descargar: bool = True) -> dict: 
        """
        Motor para ejecutar la transacción ZSDMX389.
        filtro_transporte acepta: 'DIF_C' (Excluir C), 'IGUAL_C' (Solo C), Vacio no toma el filtro.
        """
        session = self.obtener_sesion()
        if not session:
            return {"estatus": False, "msg": "No hay sesión abierta en SAP para ejecutar ZSDMX389."}
            
        try:
            # --- 1. NAVEGACIÓN Y PARÁMETROS PRINCIPALES ---
            self.acceder_a_transaccion(session, "ZSDMX389") 
            
            session.findById("wnd[0]/usr/ctxtPA_VKORG").text = org_vta
            
            try:
                session.findById("wnd[0]/usr/ctxtPA_VTWEG").text = can_dis
            except:
                pass

            # opt remisiones 
            session.findById("wnd[0]/usr/radPA_ENTRE").select()
            
            # --- 2. FILTRO: ESTATUS PLANIF. TRANSPORTE (SO_TRSTA) ---
            if filtro_transporte == "DIF_C":
                session.findById("wnd[0]/usr/ctxtSO_TRSTA-LOW").text = ""
                session.findById("wnd[0]/usr/btn%_SO_TRSTA_%_APP_%-VALU_PUSH").press()
                session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,0]").text = "C"
                session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/btnRSCSEL_255-SOP_I[0,0]").setFocus()
                session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/btnRSCSEL_255-SOP_I[0,0]").press()
                session.findById("wnd[2]/usr/cntlOPTION_CONTAINER/shellcont/shell").currentCellRow = 5
                session.findById("wnd[2]/usr/cntlOPTION_CONTAINER/shellcont/shell").selectedRows = "5"
                session.findById("wnd[2]/usr/cntlOPTION_CONTAINER/shellcont/shell").doubleClickCurrentCell()
                session.findById("wnd[1]/tbar[0]/btn[8]").press()
                
            elif filtro_transporte == "IGUAL_C":
                session.findById("wnd[0]/usr/ctxtSO_TRSTA-LOW").text = "C"
                session.findById("wnd[0]/usr/ctxtSO_TRSTA-HIGH").text = ""

            # --- 3. FILTRO: ESTATUS SALIDA DE MERCANCÍA (SO_WBSTK) --- DIF_C
            session.findById("wnd[0]/usr/ctxtSO_WBSTK-LOW").text = ""
            session.findById("wnd[0]/usr/btn%_SO_WBSTK_%_APP_%-VALU_PUSH").press()
            session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,0]").text = "C"
            session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/btnRSCSEL_255-SOP_I[0,0]").setFocus()
            session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/btnRSCSEL_255-SOP_I[0,0]").press()
            session.findById("wnd[2]/usr/cntlOPTION_CONTAINER/shellcont/shell").currentCellRow = 5
            session.findById("wnd[2]/usr/cntlOPTION_CONTAINER/shellcont/shell").selectedRows = "5"
            session.findById("wnd[2]/usr/cntlOPTION_CONTAINER/shellcont/shell").doubleClickCurrentCell()
            session.findById("wnd[1]/tbar[0]/btn[8]").press()
            
            # --- 4. RANGO DE FECHAS Y EJECUCIÓN ---
            session.findById("wnd[0]/usr/ctxtSO_LDDAT-LOW").text = fch_in
            session.findById("wnd[0]/usr/ctxtSO_LDDAT-HIGH").text = fch_fn
            session.findById("wnd[0]").sendVKey(8) 
            
            # --- 5. SELECCIONAR LAYOUT Y EXPORTAR ---
            try:
                session.findById("wnd[0]/tbar[1]/btn[33]").press()
                shell_layout = session.findById("wnd[1]/usr/ssubD0500_SUBSCREEN:SAPLSLVC_DIALOG:0501/cntlG51_CONTAINER/shellcont/shell")
                max_filas = shell_layout.RowCount
                layout_encontrado = False
                
                for i in range(max_filas):
                    nombre_variante = shell_layout.GetCellValue(i, "VARIANT").strip()
                    nombre_texto = shell_layout.GetCellValue(i, "TEXT").strip()
                    
                    if "/$FZ_PLANEAC" in nombre_variante or "/$FZ_PLANEAC" in nombre_texto:
                        shell_layout.currentCellRow = i
                        shell_layout.selectedRows = str(i)
                        shell_layout.clickCurrentCell()
                        layout_encontrado = True
                        break

            except Exception as e:
                print(f"⚠️ Advertencia: Error seleccionando layout dinámicamente. ({e})")
                if session.Children.Count > 1:
                    session.findById("wnd[1]").sendVKey(12) 
                    
            if not layout_encontrado:
                print("⚠️ Layout /$FZ_PLANEAC no encontrado. Se exportará con el layout por defecto.")
                if session.Children.Count > 1:
                    session.findById("wnd[1]").sendVKey(12) 
            
            # --- 6. EXPORTAR ARCHIVO (MODULAR) ---
            if descargar:
                session.findById("wnd[0]/mbar/menu[0]/menu[3]/menu[2]").select()
                if session.Children.Count > 1:
                    return self._exportar_archivo_sap(
                        session=session,
                        path_descarga=path_descarga,
                        nom_archivo=nom_archivo,
                        extension=extencion  # Si corriges el nombre en la firma a 'extension', actualízalo aquí también
                    )
                else:
                    return {
                        "estatus": False,
                        "msg": "No se abrió la ventana de exportación en ZSDMX389."
                    }
            else:
                return {
                    "estatus": True,
                    "msg": "No se solicitó descarga"
                }

        except Exception as e:
            return {
                "estatus": False,
                "msg": f"Falla interna ejecutando ZSDMX389: {e}"
            }

    @tunel_sap("ZSDMX267: Descarga Reporte")
    def zsdmx267(self, path_descarga: str, nom_archivo: str, extension: str = "csv",  
                 fch_in: str = "", fch_fn: str = "", lay_out: str = "",
                 centro_exp: str = "*", descargar: bool = True) -> dict:
        """
        Ejecuta la transacción ZSDMX267, filtra por fechas y centro de expedición,
        asigna el layout indicado y descarga el archivo según la extensión.
        """
        session = self.obtener_sesion()
        if not session:
            return {"estatus": False, "msg": "No hay sesión abierta en SAP para ejecutar ZSDMX267."}

        try:
            # 1. Iniciar Transacción
            self.acceder_a_transaccion(session, "ZSDMX267")

            # 2. Llenar Filtros
           
            session.findById("wnd[0]/usr/ctxtSO_TPLST-LOW").text = centro_exp

            session.findById("wnd[0]/usr/ctxtSO_ERDAT-LOW").text = fch_in
            session.findById("wnd[0]/usr/ctxtSO_ERDAT-HIGH").text = fch_fn
            session.findById("wnd[0]/usr/radP_POSREM").select()

            # 3. Ejecutar Reporte (F8)
            session.findById("wnd[0]").sendVKey(8)

            # 4. Manejo de Popups (ej. Authority check) y validación de datos
            intentos_popup = 0
            while session.Children.Count > 1 and intentos_popup < 10:
                try:
                    msg_titulo = session.findById("wnd[1]").text
                    if "Información" in msg_titulo or "Information" in msg_titulo:
                        session.findById("wnd[1]").sendVKey(0)
                except Exception:
                    pass
                intentos_popup += 1

            mensaje_status = session.findById("wnd[0]/sbar").text.strip().lower()
            if "no existen datos" in mensaje_status or "no data" in mensaje_status:
                return {
                    "estatus": False,
                    "msg": f"La transacción no arrojó resultados: {mensaje_status}"
                }

            # 5. Selección Dinámica de Layout
            if lay_out:
                try:
                    session.findById("wnd[0]").sendVKey(33)  # Abrir selector de disposición
                    shell_layout = session.findById("wnd[1]/usr/cntlGRID/shellcont/shell")
                    max_filas = shell_layout.RowCount
                    layout_encontrado = False

                    # Búsqueda por coincidencia en VARIANT o TEXT
                    for i in range(max_filas):
                        var_val = shell_layout.GetCellValue(i, "VARIANT").strip()
                        txt_val = shell_layout.GetCellValue(i, "TEXT").strip()

                        if lay_out.upper() in var_val.upper() or lay_out.upper() in txt_val.upper():
                            shell_layout.setCurrentCell(i, "TEXT")
                            shell_layout.selectedRows = str(i)
                            shell_layout.doubleClickCurrentCell()
                            layout_encontrado = True
                            break

                    if not layout_encontrado:
                        print(f"⚠️ Layout '{lay_out}' no localizado en el catálogo. Continuando con layout actual.")
                        if session.Children.Count > 1:
                            session.findById("wnd[1]").sendVKey(12)  # Cancelar / Cerrar popup

                except Exception as e_layout:
                    print(f"⚠️ Error al configurar layout: {e_layout}")
                    if session.Children.Count > 1:
                        session.findById("wnd[1]").sendVKey(12)

            #ajuste optimo de columnas para resolver perdida de datos
            session.findById("wnd[0]/mbar/menu[3]/menu[1]/menu[0]").select()
            
            # 6. Descarga delegada al método modular
            if descargar:
                session.findById("wnd[0]/mbar/menu[0]/menu[3]/menu[2]").select()
                if session.Children.Count > 1:
                    return self._exportar_archivo_sap(
                        session=session,
                        path_descarga=path_descarga,
                        nom_archivo=nom_archivo,
                        extension=extension
                    )
                else:
                    return {
                        "estatus": False,
                        "msg": "No se abrió la ventana de exportación en ZSDMX267."
                    }
            else:
                return {"estatus": True, "msg": "Reporte ejecutado sin solicitar descarga."}

        except Exception as e:
            return {
                "estatus": False,
                "msg": f"Falla interna ejecutando ZSDMX267: {e}"
            }

    @tunel_sap("ZSDMX249: Descarga Reporte")
    def zsdmx249(self, path_descarga: str, nom_archivo: str, extension: str = "csv",
                 fch_in_sm_real: str = "", fch_fn_sm_real: str = "",
                 lay_out: str = "/ZQL_REPORT", org_vta: str = "0152",
                 c_exp: str = "*", descargar: bool = True) -> dict:
        """
        Ejecuta la transacción ZSDMX249, ingresa filtros de organización, centro,
        fechas de salida de mercancía y layout en la pantalla inicial, y exporta el archivo.
        """
        session = self.obtener_sesion()
        if not session:
            return {"estatus": False, "msg": "No hay sesión abierta en SAP para ejecutar ZSDMX249."}

        try:
            # 1. Iniciar Transacción
            self.acceder_a_transaccion(session, "ZSDMX249")

            # 2. Llenar Filtros y Layout antes de ejecutar
            session.findById("wnd[0]/usr/radP_AL").select()
            session.findById("wnd[0]/usr/chkP_CBEM").selected = True
            session.findById("wnd[0]/usr/ctxtS_VKORG-LOW").text = org_vta
            session.findById("wnd[0]/usr/ctxtS_VSTEL-LOW").text = c_exp
            session.findById("wnd[0]/usr/ctxtS_FKDAT-LOW").text = fch_in_sm_real
            session.findById("wnd[0]/usr/ctxtS_FKDAT-HIGH").text = fch_fn_sm_real

            if lay_out:
                session.findById("wnd[0]/usr/ctxtP_VARIAN").text = lay_out

            # 3. Ejecutar Reporte (F8)
            session.findById("wnd[0]").sendVKey(8)

            # 4. Manejo de Popups y validación de datos en barra de estado
            intentos_popup = 0
            while session.Children.Count > 1 and intentos_popup < 10:
                try:
                    msg_titulo = session.findById("wnd[1]").text
                    if "Información" in msg_titulo or "Information" in msg_titulo:
                        session.findById("wnd[1]").sendVKey(0)
                    else:
                        break
                except Exception:
                    break
                intentos_popup += 1

            mensaje_status = session.findById("wnd[0]/sbar").text.strip().lower()
            if "no existen datos" in mensaje_status or "no data" in mensaje_status or "sin datos" in mensaje_status:
                return {
                    "estatus": False,
                    "msg": f"La transacción ZSDMX249 no arrojó resultados: {mensaje_status}"
                }

            # 5. Descarga delegada al método modular (_exportar_archivo_sap)
            if descargar:
                session.findById("wnd[0]/mbar/menu[0]/menu[3]/menu[2]").select()
                if session.Children.Count > 1:
                    return self._exportar_archivo_sap(
                        session=session,
                        path_descarga=path_descarga,
                        nom_archivo=nom_archivo,
                        extension=extension
                    )
                else:
                    return {
                        "estatus": False,
                        "msg": "No se abrió la ventana de exportación en ZSDMX249."
                    }
            else:
                return {"estatus": True, "msg": "Reporte ZSDMX249 ejecutado sin solicitar descarga."}

        except Exception as e:
            return {
                "estatus": False,
                "msg": f"Falla interna ejecutando ZSDMX249: {e}"
            }

    @tunel_sap("VT16: Descarga Reporte")
    def vt16(self, path_descarga: str, nom_archivo: str, extension: str = "csv",
             fch_in: str = "", fch_fn: str = "", centro_exp: str = "",
             status_global_in: str = "1", status_global_fn: str = "7",
             lay_out: str = "/HORARIOS_FZ", descargar: bool = True) -> dict:
        """
        Ejecuta la transacción VT16 para ver transportes creados,
        filtra por estatus global, fechas de creación y centro de expedición,
        selecciona el layout indicado y exporta el archivo.
        """
        session = self.obtener_sesion()
        if not session:
            return {"estatus": False, "msg": "No hay sesión abierta en SAP para ejecutar VT16."}

        try:
            # --- 1. NAVEGACIÓN INICIAL ---
            self.acceder_a_transaccion(session, "VT16")

            # Manejo de posible popup inicial
            if session.Children.Count > 1:
                session.findById("wnd[1]").sendVKey(0)

            # --- 2. ESTATUS GLOBAL (REGLA DE NEGOCIO: 0 AL 5) ---
            session.findById("wnd[0]/usr/ctxtK_STTRG-LOW").text = status_global_in
            session.findById("wnd[0]/usr/ctxtK_STTRG-HIGH").text = status_global_fn

            # --- 3. FECHAS Y CENTRO ---
            session.findById("wnd[0]/usr/ctxtK_ERDAT-LOW").text = fch_in
            session.findById("wnd[0]/usr/ctxtK_ERDAT-HIGH").text = fch_fn
            if centro_exp:  # Solo si se manda el centro
                session.findById("wnd[0]/usr/ctxtK_TPLST-LOW").text = centro_exp

            # Ejecutar reporte (F8)
            session.findById("wnd[0]").sendVKey(8)

            # Validar si SAP dice "No existe ningún transporte..."
            if session.Children.Count > 1:
                try:
                    mensaje_popup = session.findById("wnd[1]/usr/txtMESSTXT1").text
                    if "No existe" in mensaje_popup or "ningún" in mensaje_popup:
                        session.findById("wnd[1]").sendVKey(0)  # Cerramos el popup
                        return {
                            "estatus": False,
                            "msg": f"VT16: No se encontraron transportes en este rango ({mensaje_popup.strip()})."
                        }
                except Exception:
                    pass

            mensaje_status = session.findById("wnd[0]/sbar").text.strip().lower()
            if "no existen datos" in mensaje_status or "no data" in mensaje_status or "no existe" in mensaje_status:
                return {
                    "estatus": False,
                    "msg": f"La transacción VT16 no arrojó resultados: {mensaje_status}"
                }

            # --- 4. SELECCIONAR LAYOUT (/HORARIOS_FZ) ---
            if lay_out:
                try:
                    # Seleccionar menú de Layout
                    session.findById("wnd[0]/mbar/menu[3]/menu[0]/menu[1]").select()

                    layout_encontrado = False

                    # Buscar dinámicamente en la lista (Filas 3 a 100)
                    for i in range(3, 100):
                        try:
                            lbl_id = f"wnd[1]/usr/lbl[1,{i}]"
                            nombre_layout = session.findById(lbl_id).text.strip()
                            if nombre_layout == lay_out:
                                session.findById(lbl_id).setFocus()
                                session.findById("wnd[1]").sendVKey(2)  # F2 / Doble clic (Seleccionar)
                                layout_encontrado = True
                                print(f"✅ Layout {lay_out} encontrado y aplicado (Fila {i}).")
                                break
                        except Exception:
                            # Fin de la lista de layouts
                            break

                    if not layout_encontrado:
                        print(f"⚠️ Layout {lay_out} no encontrado en la lista. Se exportará con el layout actual.")
                        if session.Children.Count > 1:
                            session.findById("wnd[1]").sendVKey(12)  # Cerrar la ventana de layouts (Cancelar)

                except Exception as e:
                    print(f"⚠️ Advertencia: Error abriendo menú de layouts. Se usará el actual. ({e})")
                    if session.Children.Count > 1:
                        session.findById("wnd[1]").sendVKey(12)  # Cancelar

            # --- 5. EXPORTAR A EXCEL / CSV ---
            if descargar:
                # Menú: Lista -> Exportar -> Fichero Local (específico de lista clásica en VT16)
                session.findById("wnd[0]/mbar/menu[0]/menu[9]/menu[2]").select()
                if session.Children.Count > 1:
                    return self._exportar_archivo_sap(
                        session=session,
                        path_descarga=path_descarga,
                        nom_archivo=nom_archivo,
                        extension=extension
                    )
                else:
                    return {
                        "estatus": False,
                        "msg": "No se abrió la ventana de exportación en VT16."
                    }
            else:
                return {"estatus": True, "msg": "Reporte VT16 ejecutado sin solicitar descarga."}

        except Exception as e:
            return {
                "estatus": False,
                "msg": f"Falla interna ejecutando VT16: {e}"
            }

    @tunel_sap("FBL4N: Descarga Reporte")
    def fbl4n(self, path_descarga: str, nom_archivo: str, extension: str = "xls",
              fch_in: str = "", fch_fn: str = "",
              cta_mayor: str = "641211091", sociedad: str = "3022",
              lay_out: str = "/ZQL_FLETES", descargar: bool = True) -> dict:
        """
        Ejecuta la transacción FBL4N (Partidas individuales de cuentas de mayor / Acreedores),
        ingresa cuenta mayor, sociedad, rango de fechas de contabilización y layout antes de ejecutar,
        y exporta el archivo mediante _exportar_archivo_sap.
        """
        session = self.obtener_sesion()
        if not session:
            return {"estatus": False, "msg": "No hay sesión abierta en SAP para ejecutar FBL4N."}

        try:
            # --- 1. NAVEGACIÓN INICIAL ---
            self.acceder_a_transaccion(session, "FBL4N")

            # --- 2. LLENAR CAMPOS Y LAYOUT ANTES DE EJECUTAR ---
            session.findById("wnd[0]/usr/radX_AISEL").select()
            session.findById("wnd[0]/usr/ctxtSD_SAKNR-LOW").text = cta_mayor
            session.findById("wnd[0]/usr/ctxtSD_BUKRS-LOW").text = sociedad
            session.findById("wnd[0]/usr/ctxtSO_BUDAT-LOW").text = fch_in
            session.findById("wnd[0]/usr/ctxtSO_BUDAT-HIGH").text = fch_fn
            if lay_out:
                session.findById("wnd[0]/usr/ctxtPA_VARI").text = lay_out

            # --- 3. EJECUTAR REPORTE (F8) ---
            session.findById("wnd[0]").sendVKey(8)

            # Validar si encontró datos en la barra de estado
            mensaje_sap = session.findById("wnd[0]/sbar").text.strip()
            if "se visualizan" not in mensaje_sap.lower():
                return {
                    "estatus": False,
                    "msg": f"La transacción FBL4N no arrojó resultados: {mensaje_sap}"
                }

            # --- 4. EXPORTAR ARCHIVO (MODULAR) ---
            if descargar:
                # Menú Lista -> Exportar -> Hoja de cálculo
                session.findById("wnd[0]/mbar/menu[0]/menu[3]/menu[1]").select()
                if session.Children.Count > 1:
                    return self._exportar_archivo_sap(
                        session=session,
                        path_descarga=path_descarga,
                        nom_archivo=nom_archivo,
                        extension=extension
                    )
                else:
                    return {
                        "estatus": False,
                        "msg": "No se abrió la ventana de exportación en FBL4N."
                    }
            else:
                return {"estatus": True, "msg": "Reporte FBL4N ejecutado sin solicitar descarga."}

        except Exception as e:
            return {
                "estatus": False,
                "msg": f"Falla interna ejecutando FBL4N: {e}"
            }

    def _exportar_archivo_sap(self, session, path_descarga: str, nom_archivo: str, extension: str) -> dict:
        """
        Exporta el reporte activo en SAP adaptando el flujo según la extensión:
        - 'csv' / 'txt': Usa ventana de diálogo estándar SAPLSPO5 (VKey 45 / Fichero Local).
        - 'xlsx' / 'xls': Usa el menú clásico de exportación a hoja de cálculo.
        """
        ext = extension.strip().lower().replace(".", "")
        nombre_completo = f"{nom_archivo}.{ext}" if not nom_archivo.lower().endswith(f".{ext}") else nom_archivo

        # -------------------------------------------------------------
        # CASO 1: CSV / TXT (Fichero local con separadores)
        # -------------------------------------------------------------
        if ext in ["csv", "txt", "xls"]:
            #session.findById("wnd[0]").sendVKey(45)  # Acceso directo a Guardar Fichero Local
            #session.findById("wnd[0]/mbar/menu[0]/menu[3]/menu[2]").select()
            # Seleccionar opción de texto con tabuladores / no convertido
            try:
                # Opción típica: radSPOPLI-SELFLAG[1,0] suele ser 'Texto con tabuladores'
                session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]").select()
                session.findById("wnd[1]/tbar[0]/btn[0]").press()

            except Exception:
                # Si entra directamente al cuadro de diálogo o tiene otra estructura de radio buttons
                if session.Children.Count > 1:
                    session.findById("wnd[1]").sendVKey(0)

        # -------------------------------------------------------------
        # CASO 2: XLSX (Open XLSX)
        # -------------------------------------------------------------
        elif ext in ["xlsx"]:
            # Confirmación de formato si aparece ventana modal intermedia (XML, OpenOffice, MHTML, etc.)
            if session.Children.Count > 1:
                try:
                    session.findById("wnd[1]/usr/radRB_1").select()
                except Exception:
                    pass  # Si no existen esos radio buttons, se acepta la opción default
                
                session.findById("wnd[1]").sendVKey(0)

        else:
            return {
                "estatus": False,
                "msg": f"Extensión '{extension}' no soportada. Usa 'xlsx', 'xls' o 'csv'."
            }

        # -------------------------------------------------------------
        # PANTALLA DE GUARDADO COMÚN (DY_PATH y DY_FILENAME)
        # -------------------------------------------------------------
        session.findById("wnd[1]/usr/ctxtDY_PATH").text = path_descarga
        session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = nombre_completo
        # btn[11] corresponde a 'Reemplazar' / btn[0] 'Generar'
        
        try:
            session.findById("wnd[1]/tbar[0]/btn[11]").press()
        except Exception:
            session.findById("wnd[1]/tbar[0]/btn[0]").press()

        # Validación en la barra de estado
        msg_bar = session.findById("wnd[0]/sbar").text.strip().lower()
        if "bytes transferidos" in msg_bar:
            return {"estatus": True, "msg": f"Descarga exitosa. {msg_bar}"}
        else:
            return {"estatus": False, "msg": f"Respuesta de SAP: {msg_bar}"}
