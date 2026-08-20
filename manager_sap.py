#manager_sap.py
import win32com.client
import sys
import unicodedata
import time, datetime
import threading
import pythoncom
import re
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal
from catalogos import CATALOGO_MATERIALES

class SignalEmitter (QObject):
    keep_alive_signal = pyqtSignal(str, str)

class SAPError(Exception):
    """Excepción personalizada para errores de negocio en SAP."""
    pass

class SAPManager:
    """
    Clase para gestionar la conexión con SAP GUI y mantener la sesión viva.
    """
    def __init__(self):
        # Bandera para controlar la detención del hilo Keep-Alive
        self.stop_thread = False
        # Referencia al hilo de Keep-Alive
        self.keep_alive_thread = None
        # Referencia a la sesión (no se almacena persistentemente, solo se usa temporalmente)
        self.session = None
        # Inicializar el emisor de señales
        self.emitter = SignalEmitter() 

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
            
            # Tiempo cumplido: Mandar ping a SAP
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
                        "gpo_material": info_material.get("grupo")
                    })
        
                except Exception as e_row:
                    print(f"❌ Error leyendo fila {i}: {e_row}")
                    # Importante: No hacemos break aquí para intentar leer la siguiente fila si es posible,
                    # o si es un error fatal, el break de arriba ya actuó.
                    break

            self.emitter.keep_alive_signal.emit("Información obtenida correctamente", "green")
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
                # AQUI ESTÁ LA CLAVE: Usamos 'centro_a_usar', no el genérico
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
    # 5. IMPRIMIR PICKING (VL02N)
    # ==============================================================================
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
    def zsdmx389_descargar_archivos(self, path_descarga: str, nom_archivo: str, fch_in: str, fch_fn: str, 
                                  org_vta: str = "0152", can_dis: str = "16", 
                                  filtro_transporte: str = "", 
                                  descargar: bool = True):
        """
        Motor genérico para ejecutar la transacción ZSDMX389.
        filtro_transporte acepta: 'DIF_C' (Excluir C), 'IGUAL_C' (Solo C), Vacio no toma el filtro.
        """
        session = self.obtener_sesion()
        if not session:
            raise Exception("No hay sesión abierta en SAP para ejecutar ZSDMX389.")
            
        try:
            # --- 1. NAVEGACIÓN Y PARÁMETROS PRINCIPALES ---
            self.acceder_a_transaccion(session, "ZSDMX389") 
            
            session.findById("wnd[0]/usr/ctxtPA_VKORG").text = org_vta
            
            try:
                session.findById("wnd[0]/usr/ctxtPA_VTWEG").text = can_dis
            except:
                pass
                
            session.findById("wnd[0]/usr/radPA_ENTRE").select()
            
            # --- 2. FILTRO: ESTATUS PLANIF. TRANSPORTE (SO_TRSTA) ---
            # Si el filtro llega vacio entonces no hace nada
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

            # --- 3. FILTRO: ESTATUS SALIDA DE MERCANCÍA (SO_WBSTK) ---
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
                        #print(f"✅ Layout /$FZ_PLANEAC encontrado y aplicado (Fila {i}).")
                        break

            except Exception as e:
                print(f"⚠️ Advertencia: Error seleccionando layout dinámicamente. ({e})")
                if session.Children.Count > 1:
                    session.findById("wnd[1]").sendVKey(12) 
                    
            if not layout_encontrado:
                print("⚠️ Layout /$FZ_PLANEAC no encontrado. Se exportará con el layout por defecto.")
                if session.Children.Count > 1:
                    session.findById("wnd[1]").sendVKey(12) 
            
            # --- 6. EXPORTAR A CSV ---
            if descargar:
                session.findById("wnd[0]").sendVKey(45) 
                session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]").select()
                session.findById("wnd[1]/tbar[0]/btn[0]").press() 
                
                session.findById("wnd[1]/usr/ctxtDY_PATH").text = path_descarga
                session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = nom_archivo
                session.findById("wnd[1]/tbar[0]/btn[11]").press() 
                
        except Exception as e:
            print(f"❌ Error interno ejecutando ZSDMX389: {e}")
            raise Exception(f"Falla en ejecución ZSDMX389: {e}")

    def zsdmx389_robot(self, ruta_base_drive: str, tipo_descarga: str = "ambos") -> dict:
        """
        Robot Orquestador que recibe la ruta dinámica, crea las subcarpetas 
        (pendientes / en_proceso) y lanza las descargas selectivas.
        tipo_descarga acepta: 'pendientes', 'en_proceso', o 'ambos'.
        """
        import os
        from datetime import datetime
        
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
        
        # --- 2. RANGO DE FECHAS ---
        anio_actual = datetime.now().year
        fch_in = f"01.01.{anio_actual}"
        fch_fn = f"31.12.{anio_actual}"
        
        self.emitter.keep_alive_signal.emit(f"Descargando reportes ZSDMX389 ({tipo_descarga})...", "blue")
        rutas_generadas = {}
        
        try:
            # --- 3A. DESCARGAR PENDIENTES ---
            if tipo_descarga in ["pendientes", "ambos"]:
                self.zsdmx389_descargar_archivos(
                    path_descarga=ruta_pendientes, 
                    nom_archivo=nom_pendientes, 
                    fch_in=fch_in, 
                    fch_fn=fch_fn, 
                    filtro_transporte="" # Vacío: Trae todo lo pendiente con o sin transporte
                )
                rutas_generadas['pendientes'] = os.path.join(ruta_pendientes, nom_pendientes)
            
            # --- 3B. DESCARGAR EN PROCESO ---
            if tipo_descarga in ["en_proceso", "ambos"]:
                self.zsdmx389_descargar_archivos(
                    path_descarga=ruta_en_proceso, 
                    nom_archivo=nom_en_proceso, 
                    fch_in=fch_in, 
                    fch_fn=fch_fn, 
                    filtro_transporte="IGUAL_C" # Solo C: Trae solo lo que está en proceso
                )
                rutas_generadas['en_proceso'] = os.path.join(ruta_en_proceso, nom_en_proceso)
            
            self.emitter.keep_alive_signal.emit(f"Archivos ZSDMX389 ({tipo_descarga}) actualizados", "green")
            import time
            # print(f"✅ [{time.strftime('%H:%M:%S')}] Contingencia ZSDMX389 actualizada correctamente en: {ruta_zsdmx}")
            return rutas_generadas
            
        except Exception as e:
            self.emitter.keep_alive_signal.emit("Error actualizando ZSDMX389", "red")
            raise Exception(f"Falla descargando reportes ZSDMX389: {e}")

    def vt16(self, centro_exp: str, fch_in: str, fch_fn: str, path_descarga: str, nom_archivo: str, status_global_in: str, status_global_fn: str, descargar: bool = True) -> bool:
        """
        Ejecuta la transacción VT16 para ver transportes creados.
        Filtra estatus global de transporte del 0 al 5.
        """
        session = self.obtener_sesion()
        if not session:
            raise Exception("No hay sesión abierta en SAP para ejecutar VT16.")
            
        try:
            # --- 1. NAVEGACIÓN INICIAL ---
            session.findById("wnd[0]/tbar[0]/okcd").text = "/nVT16"
            session.findById("wnd[0]").sendVKey(0)
            
            # Manejo de posible popup inicial
            if session.Children.Count > 1:
                session.findById("wnd[1]").sendVKey(0)

            # --- 2. ESTATUS GLOBAL (REGLA DE NEGOCIO: 0 AL 5) ---
            session.findById("wnd[0]/usr/ctxtK_STTRG-LOW").text = status_global_in
            session.findById("wnd[0]/usr/ctxtK_STTRG-HIGH").text = status_global_fn

            # --- 3. FECHAS Y CENTRO ---
            session.findById("wnd[0]/usr/ctxtK_ERDAT-LOW").text = fch_in
            session.findById("wnd[0]/usr/ctxtK_ERDAT-HIGH").text = fch_fn
            if centro_exp: # Solo si se manda el centro
                session.findById("wnd[0]/usr/ctxtK_TPLST-LOW").text = centro_exp

            # Ejecutar reporte (F8)
            session.findById("wnd[0]").sendVKey(8)
            
            # Validar si SAP dice "No existe ningún transporte..."
            if session.Children.Count > 1:
                try:
                    mensaje_popup = session.findById("wnd[1]/usr/txtMESSTXT1").text
                    if "No existe" in mensaje_popup or "ningún" in mensaje_popup:
                        session.findById("wnd[1]").sendVKey(0) # Cerramos el popup
                        print("ℹ️ VT16: No se encontraron transportes en este rango.")
                        return False
                except:
                    pass

            # --- 4. SELECCIONAR LAYOUT (/HORARIOS_FZ) ---
            try:
                # Seleccionar menú de Layout
                session.findById("wnd[0]/mbar/menu[3]/menu[0]/menu[1]").select()
                
                layout_encontrado = False
                
                # Buscar dinámicamente en la lista (Filas 1 a 100)
                for i in range(3, 100):
                    try:
                        # Construimos el ID de la etiqueta dinámicamente
                        lbl_id = f"wnd[1]/usr/lbl[1,{i}]"
                        
                        # Extraemos el texto
                        nombre_layout = session.findById(lbl_id).text.strip()
                        # print(f"Layout analizado(Fila {i}) {nombre_layout}")
                        # Comparamos
                        if nombre_layout == "/HORARIOS_FZ":
                            session.findById(lbl_id).setFocus()
                            session.findById("wnd[1]").sendVKey(2) # F2 / Doble clic (Seleccionar)
                            layout_encontrado = True
                            print(f"✅ Layout /HORARIOS_FZ encontrado y aplicado (Fila {i}).")
                            break
                            
                    except:
                        # Si llegamos a un índice 'i' que no existe, SAP lanza error.
                        # Significa que ya revisamos toda la lista, así que rompemos el ciclo.
                        break
                
                # Si recorrió toda la lista y no lo encontró
                if not layout_encontrado:
                    print("⚠️ Layout /HORARIOS_FZ no encontrado en la lista. Se exportará con el layout actual.")
                    session.findById("wnd[1]").sendVKey(12) # Cerrar la ventana de layouts (Cancelar)

            except Exception as e:
                print(f"⚠️ Advertencia: Error abriendo menú de layouts. Se usará el actual. ({e})")
                if session.Children.Count > 1:
                    session.findById("wnd[1]").sendVKey(12) # Cancelar
            
            # --- 5. EXPORTAR A EXCEL / CSV ---
            if descargar:
                # Menú: Lista -> Exportar -> Fichero Local
                session.findById("wnd[0]/mbar/menu[0]/menu[9]/menu[2]").select()
                
                # Seleccionar formato (Spreadsheet / Excel)
                session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]").select()
                session.findById("wnd[1]/tbar[0]/btn[0]").press()
                
                # Rutas y guardado
                session.findById("wnd[1]/usr/ctxtDY_PATH").text = path_descarga
                session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = nom_archivo
                session.findById("wnd[1]/tbar[0]/btn[11]").press() # Guardar/Reemplazar
                
                # Validar mensajes finales de error ("sy")
                if session.Children.Count > 1:
                    try:
                        mensaje_popup = session.findById("wnd[1]/usr/txtMESSTXT1").text
                        if "sy" in mensaje_popup.lower():
                            session.findById("wnd[1]").sendVKey(0)
                            return False
                    except:
                        pass

            return True

        except Exception as e:
            print(f"❌ Error técnico ejecutando VT16: {e}")
            return False

    def descargar_operacion_vt16(self, centro_exp: str = "") -> str:
        """
        Orquestador que prepara las variables para descargar la VT16.
        Se ejecuta idealmente cada ciertos minutos para alimentar el tablero de báscula.
        """
        import os
        from datetime import datetime
        
        # --- 1. RUTAS Y NOMBRES ---
        user_profile = os.path.expanduser("~")
        ruta_base = os.path.join(user_profile, "Elementia S. A", "autoarribo", "vt16")
        
        if not os.path.exists(os.path.dirname(os.path.dirname(ruta_base))):
            ruta_base = os.path.join(user_profile, "Documentos", "autoarribo", "vt16")
            
        if not os.path.exists(ruta_base):
            os.makedirs(ruta_base)
            
        # Archivo diario que se sobrescribe: Ej. VT16_20260623.csv
        fecha_str = datetime.now().strftime("%Y%m%d")
        nombre_archivo = f"VT16_{fecha_str}.csv" 
        
        # --- 2. FECHAS (Día en curso) ---
        # A diferencia de ZSDMX389 que baja todo el año, VT16 suele ser del día
        # o un rango corto para no saturar la descarga. Usaremos el día de hoy.
        fch_hoy = datetime.now().strftime("%d.%m.%Y")
        
        self.emitter.keep_alive_signal.emit("Descargando archivo operativo VT16...", "blue")
        
        # --- 3. EJECUTAR DESCARGA ---
        exito = self.vt16(
            centro_exp=centro_exp, 
            fch_in=fch_hoy, 
            fch_fn=fch_hoy, 
            path_descarga=ruta_base, 
            nom_archivo=nombre_archivo, 
            status_global_in = "0",
            status_global_fn = "5",
            descargar=True
        )
        
        if exito:
            ruta_completa = os.path.join(ruta_base, nombre_archivo)
            print(f"✅ Archivo VT16 guardado en: {ruta_completa}")
            self.emitter.keep_alive_signal.emit("VT16 actualizada", "green")
            return ruta_completa
        else:
            self.emitter.keep_alive_signal.emit("Error/Sin datos actualizando VT16", "orange")
            return ""
        
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