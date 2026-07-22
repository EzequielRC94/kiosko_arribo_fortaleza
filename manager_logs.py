# manager_logs.py
import os
import pandas as pd
from datetime import datetime
from session_data import SessionData

class LogManager:
    def __init__(self):
        self.ruta_base = ""

    def set_planta(self, planta_nombre: str):
        """
        Configura la ruta de logs dinámicamente, incluyendo el mes en español.
        Ej: ...\kiosko\2026\logs\07_julio
        """
        user_profile = os.path.expanduser("~")
        
        carpetas_plantas = {
            "Planta Tula": "Cementos Tula Embarques - Documentos",
            "Planta Palmar": "Cementos Palmar Embarques - Documentos",
            "Planta Vito": "Cementos Vito Embarques - Documentos",
            "Planta Progreso": "Cementos Progreso Embarques - Documentos",
            "CEDIS GDL": "CEDIS GDL Embarques - Documentos"
        }
        
        carpeta_planta = carpetas_plantas.get(planta_nombre, "Documentos Kiosko")
        
        now = datetime.now()
        anio_actual = now.strftime("%Y")
        
        # Diccionario para formatear el mes "07_julio"
        meses_es = {
            1: '01_enero', 2: '02_febrero', 3: '03_marzo', 4: '04_abril',
            5: '05_mayo', 6: '06_junio', 7: '07_julio', 8: '08_agosto',
            9: '09_septiembre', 10: '10_octubre', 11: '11_noviembre', 12: '12_diciembre'
        }
        mes_str = meses_es.get(now.month, f"{now.month:02d}_mes")

        self.ruta_base = os.path.join(
            user_profile, 
            "Elementia S. A", 
            carpeta_planta, 
            "kiosko", 
            anio_actual, 
            "logs", 
            mes_str
        )

        if not os.path.exists(self.ruta_base):
            try:
                os.makedirs(self.ruta_base, exist_ok=True)
                print(f"📁 Carpeta de logs creada: {self.ruta_base}")
            except Exception as e:
                pass
                
    def _obtener_ruta_archivo_hoy(self) -> str:
        """Devuelve la ruta completa del Excel de hoy."""
        hoy_str = datetime.now().strftime("%Y%m%d")
        nombre_archivo = f"logs_{hoy_str}.xlsx"
        # Unimos la ruta de la carpeta base (que ya tiene el mes) con el archivo
        return os.path.join(self.ruta_base, nombre_archivo)

    def generar_siguiente_id_movimiento(self) -> str:
        """
        Genera ID único: YYYYMMDD_001 revisando el Excel en la carpeta de logs.
        """
        hoy_str = datetime.now().strftime("%Y%m%d")
        ruta_completa = self._obtener_ruta_archivo_hoy()
        consecutivo = 1

        # Verificamos si ya existe el archivo EN LA RUTA ESPECÍFICA
        if os.path.exists(ruta_completa):
            try:
                df = pd.read_excel(ruta_completa, engine='openpyxl')
                consecutivo = len(df) + 1
                #print(f"Len: {len(df)}")
                #print(f"ruta: {ruta_completa}")

            except Exception as e:
                print(f"Advertencia: No se pudo leer Excel ({e}). Iniciando en 1.")
                consecutivo = 1
        
        nuevo_id = f"{hoy_str}_{consecutivo:03d}"
        return nuevo_id

    def guardar_evento(self, session: SessionData):
        """Guarda la fila en el Excel."""
        
        ruta_completa = self._obtener_ruta_archivo_hoy()
        
        # ... (Preparación de datos igual que antes) ...
        remisiones_str = [""] * 6
        for i, rem in enumerate(session.remisiones_agregadas):
            if i < 6:
                remisiones_str[i] = rem.get("remision", "")

        id_mov = session.id_movimiento if session.id_movimiento else "SIN_ID"
        historial_texto = " ; ".join(session.historial_acciones)

        datos_fila = {
            "id_movimiento": id_mov,
            "fch_inicio_arribo": session.inicio_arribo.strftime("%Y-%m-%d %H:%M:%S"),
            "ticket_cloudfort": session.ticket_id,
            "fch_checklist": session.fecha_checklist,
            "fch_fin_arribo": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if session.fin_arribo else "",
            "operador": session.operador,
            "placa": session.placa,
            "transporte": session.transporte_sap if hasattr(session, 'transporte_sap') else "",
            "remision 1": remisiones_str[0],
            "ultimo_paso": session.estatus_arribo_ultimo_paso,
            "mgj_ult_paso": session.estatus_arribo_mensaje,
            "historial_completo": historial_texto
        }

        df_nuevo = pd.DataFrame([datos_fila])

        try:
            if not os.path.exists(ruta_completa):
                # Caso 1: Archivo nuevo -> Escribimos directo
                df_nuevo.to_excel(ruta_completa, index=False, engine='openpyxl')
            else:
                # Caso 2: Archivo existe -> Anexamos
                # Primero leemos para saber cuántas filas hay (sin dañar el writer)
                try:
                    df_existente = pd.read_excel(ruta_completa, engine='openpyxl')
                    # La fila de inicio es: filas existentes + 1 (por el encabezado)
                    start_row = len(df_existente) + 1
                except:
                    start_row = 1 # Si falla leer, asumimos que escribimos al principio (riesgoso pero funcional)

                # Usamos el modo 'overlay' que escribe ENCIMA de la hoja existente sin borrarla
                with pd.ExcelWriter(ruta_completa, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                    df_nuevo.to_excel(writer, index=False, header=False, startrow=start_row)
            
            print(f"✅ LOG GUARDADO CORRECTAMENTE: {ruta_completa}")
            
        except Exception as e:
            print(f"❌ ERROR CRÍTICO AL GUARDAR LOG: {e}")
            # Fallback de emergencia: Si el append falla, intentamos leer todo y reescribir (más lento pero seguro)
            try:
                if os.path.exists(ruta_completa):
                    df_old = pd.read_excel(ruta_completa, engine='openpyxl')
                    df_total = pd.concat([df_old, df_nuevo], ignore_index=True)
                    df_total.to_excel(ruta_completa, index=False, engine='openpyxl')
            except:
                pass