# manager_arribos.py
import os
import pandas as pd
from datetime import datetime
from session_data import SessionData

class ArribosManager:
    """
    Gestiona el archivo 'arribos.xlsx' (Base de Datos Operativa).
    Registra los camiones EN PROCESO desglosados por material/posición.
    """

    def __init__(self):
        self.nombre_archivo = "arribos.xlsx"
        self.ruta_base = ""
        self.ruta_completa = ""
        # Quitamos la inicialización aquí, ahora dependerá de set_planta()

    def configurar_ruta(self, ruta_base_drive: str):
        """
        Configura la ruta real operativa basándose en la variable global del Kiosko.
        Agrega automáticamente la subcarpeta 'arribos'.
        """
        # 1. Usamos la ruta dinámica heredada de SessionData
        self.ruta_base = os.path.join(ruta_base_drive, "arribos")
        
        # 2. Construimos la ruta exacta al Excel
        self.ruta_completa = os.path.join(self.ruta_base, self.nombre_archivo)

        # 3. Crear directorios y el archivo si no existen
        if not os.path.exists(self.ruta_base):
            try:
                os.makedirs(self.ruta_base, exist_ok=True)
                print(f"📁 Carpeta de arribos creada: {self.ruta_base}")
            except Exception as e:
                print(f"⚠️ Error creando carpeta arribos: {e}")
                
        self._inicializar_archivo()

    def _inicializar_archivo(self):
        """Crea el Excel con las columnas solicitadas si no existe."""
        if not os.path.exists(self.ruta_completa):
            columnas = [
                "ticket",                  # A. ID Turno (CloudFort)
                "estatus_operacion",       # B. 01 EN ESPERA, 02 DOCUMENTADO, 03 LLAMADO, 04 CARGANDO
                "fecha_arribo",            # C. Momento del registro en DB

                "cliente_num",             # D. ID Cliente (Pendiente de extracción SAP)
                "destinatario_num",        # E. ID Destinatario (Pendiente de extracción SAP)
                "cliente_nombre",          # F. Nombre Cliente
                "destinatario_nombre",     # G. Nombre Destinatario (Pendiente de extracción SAP)

                "poblacion",               # H. Población
                "modalidad",               # I. Entregado // Retirado // Autoflete
                "clase_entrega",           # J. ZAM1, ZCCD, etc.
                "remision",                # K. Número de entrega
                "pos",                     # L. Posición (10, 20...)
                "c_exp",                   # M. Centro Expedición
                "gpo_material",            # N. GRANEL / ENVASADO
                "ton",                     # O. Peso en toneladas
                "material_cod",            # P. Código de Material
                "material_nombre",         # Q. Nombre de Material

                "operador",                # R. Nombre de operador
                "placas",                  # S. Placas de la unidad
                "clase_expedicion",        # T. F1, F2, F3, F4, F5, F7
                "transporte",              # U. Número de transporte (48...)

                "origen_datos",            # V. "A: Web Service", "B: Robot SAP", "C: Contingencia"
                "estatus_contingencia",    # W. "N/A", "PENDIENTE", "CERRADO"

                "fch_cita_carga",          # X. Formato SAP: 03.07.2026 08:00
                "fch_checklist",           # Y. Timestamp: 2026-07-03 06:13:43
                "fch_inicio_arribo",       # Z. Inicio Arribo
                "fch_fin_arribo",          # AA. Fin Arribo

                "fch_bascula_entrada",     # AB. Registro de báscula entrada
                "fch_inicio_carga",        # AC. Inicio de carga
                "fch_fin_carga",           # AD. Fin de carga
                "fch_bascula_salida",      # AE. Despacho / Salida
                "gasto_transporte",        # AF. Gasto de transporte
                "gasto_enviado"            # AG. Indicador de envío a SAP
            ]
            try:
                df = pd.DataFrame(columns=columnas)
                df.to_excel(self.ruta_completa, index=False, engine='openpyxl')
                print(f"✅ Base de datos Arribos inicializada en: {self.ruta_completa}")
            except Exception as e:
                print(f"❌ Error inicializando arribos.xlsx: {e}")

    def registrar_nuevo_arribo(self, session_data: SessionData):
        """
        Maquina de escribir
        Guarda UNA FILA POR MATERIAL con el mapeo exacto solicitado.
        """

        filas_a_insertar = []
        
        # Recuperamos datos de sesión de forma segura
        transporte_real = getattr(session_data, "transporte_sap", "")

        # Formateamos fechas de sesión si existen
        inicio_arr_str = session_data.inicio_arribo.strftime("%Y-%m-%d %H:%M:%S") if session_data.inicio_arribo else ""
        fin_arr_str = session_data.fin_arribo.strftime("%Y-%m-%d %H:%M:%S") if session_data.fin_arribo else ""

        # Recorremos cada remisión
        for remision in session_data.remisiones_agregadas:
            num_remision = remision.get("remision", "")
            clase_ent = remision.get("clase_entrega", "") # Recuperamos la clase de entrega específica
            
            # Recorremos cada material (posición) dentro de la remisión
            materiales = remision.get("materiales", [])
            for mat in materiales:
                
                fila = {
                    "ticket":                  session_data.ticket_id,                  # ID Turno (CloudFort)
                    "estatus_operacion":       "01 EN ESPERA",                          # 01 EN ESPERA, 02 DOCUMENTADO, 03 LLAMADO, 04 CARGANDO
                    "fecha_arribo":            inicio_arr_str,                          # Momento del registro en DB

                    "cliente_num":             session_data.cliente_num,                # ID Cliente (Pendiente de extracción SAP)
                    "destinatario_num":        session_data.destinatario_num,           # ID Destinatario (Pendiente de extracción SAP)
                    "cliente_nombre":          session_data.cliente_nombre,             # Nombre Cliente
                    "destinatario_nombre":     session_data.destinatario_nombre,        # Nombre Destinatario (Pendiente de extracción SAP)

                    "poblacion":               session_data.poblacion,                  #
                    "modalidad":               session_data.modalidad,                  # Entregado // Retirado // Autoflete
                    "clase_entrega":           clase_ent,                               # ZAM1, ZCCD, etc.
                    "remision":                num_remision,                            # Número de entrega
                    "pos":                     mat.get("posicion", ""),                 # Posición (10, 20...)
                    "c_exp":                   mat.get("cen_exp", ""),                  # Centro Expedición
                    "gpo_material":            mat.get("gpo_material", "Desc"),         # GRANEL / ENVASADO
                    "ton":                     mat.get("peso_ton", 0.0),                # Peso en toneladas
                    "material_cod":            mat.get("material", ""),                 # Código de Material
                    "material_nombre":         mat.get("material_denominacion", ""),    # Nombre de Material

                    "operador":                session_data.operador,                   # Nombre de operador
                    "placas":                  session_data.placa,                      # Placas de la unidad
                    "clase_expedicion":        session_data.clase_expedicion,           # F1, F2, F3, F4, F5, F7
                    "transporte":              transporte_real,                         # Número de transporte (48...)

                    "origen_datos":            session_data.origen_datos,               # "A: Web Service", "B: Robot SAP", "C: Contingencia"
                    "folio_contingencia":      session_data.folio_contingencia,         # "Folio asignado a contingencias"
                    "estatus_contingencia":    session_data.estatus_contingencia,       # "N/A", "PENDIENTE", "CERRADO"

                    # Fechas
                    "fch_cita_carga":          session_data.fch_cita_carga,             # Formato SAP: 03.07.2026 08:00
                    "fch_checklist":           session_data.fecha_checklist,            # Timestamp: 2026-07-03 06:13:43
                    "fch_inicio_arribo":       inicio_arr_str,                          # Inicio Arribo
                    "fch_fin_arribo":          fin_arr_str,                             # Fin Arribo

                    # Campos para procesos posteriores
                    "fch_bascula_entrada":     "",                                      # Registro de báscula entrada
                    "fch_inicio_carga":        "",                                      # Inicio de carga
                    "fch_fin_carga":           "",                                      # Fin de carga
                    "fch_bascula_salida":      "",                                      # Despacho / Salida
                    "gasto_transporte":        "",                                      # Gasto de transporte
                    "gasto_enviado":           ""                                       # Indicador de envío a SAP
                }
                filas_a_insertar.append(fila)

        if not filas_a_insertar:
            return

        # Guardado (Append)
        try:
            nuevo_df = pd.DataFrame(filas_a_insertar)
            
            if os.path.exists(self.ruta_completa):
                # Leemos para append
                with pd.ExcelWriter(self.ruta_completa, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                    # Determinamos fila de inicio
                    try:
                        df_existente = pd.read_excel(self.ruta_completa, engine='openpyxl')
                        start_row = len(df_existente) + 1
                    except:
                        start_row = 1
                    # Escribimos sin encabezados
                    nuevo_df.to_excel(writer, index=False, header=False, startrow=start_row)
            else:
                # Si no existe (raro porque se inicializa), creamos de cero
                nuevo_df.to_excel(self.ruta_completa, index=False, engine='openpyxl')
            
            print(f"✅ Arribo registrado en Xlsx Operativo ({len(filas_a_insertar)} posiciones).")

        except PermissionError:
            print("❌ ERROR: El archivo 'arribos.xlsx' está abierto. No se pudo registrar.")
        except Exception as e:
            print(f"❌ Error guardando en arribos.xlsx: {e}")