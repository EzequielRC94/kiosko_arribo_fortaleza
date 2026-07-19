# manager_logs.py
import os
import pandas as pd
from datetime import datetime
from session_data import SessionData

class LogManager:
    r"""
    Encargado de escribir los registros en Excel en la ruta
    1. Ruta en Carpeta Copartida de One Drive
    2. Ruta en PC local One Drive
    ruta = C:\Users\TU_USUARIO\Documents\autoarribo\logs
    """

    def __init__(self):
        # Obtenemos la carpeta del usuario (C:\Users\Operador)
        user_profile = os.path.expanduser("~")
        
        
        # Opción A: Si usas OneDrive Empresarial (SharePoint Sincronizado)
        self.ruta_base = os.path.join(user_profile, "Elementia S. A", "autoarribo", "logs")

        # Fallback de seguridad: Si no encuentra OneDrive, usa Documentos
        if not os.path.exists(os.path.dirname(self.ruta_base)):
             print("⚠️ No encontré OneDrive, guardando en Documentos locales.")
             self.ruta_base = os.path.join(user_profile, "Documentos", "autoarribo", "logs")

        # Creamos la carpeta final si no existe
        if not os.path.exists(self.ruta_base):
            try:
                os.makedirs(self.ruta_base)
            except:
                pass

    def _obtener_ruta_archivo_hoy(self) -> str:
        """Devuelve la ruta completa del Excel de hoy."""
        hoy_str = datetime.now().strftime("%Y%m%d")
        nombre_archivo = f"logs_{hoy_str}.xlsx"
        # Unimos la ruta de la carpeta con el nombre del archivo
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
            "ID Movimiento": id_mov,
            "Inicio Arribo": session.inicio_arribo.strftime("%Y-%m-%d %H:%M:%S"),
            "Ticket CloudFort": session.ticket_id,
            "Fecha Checklist": session.fecha_checklist,
            "Fin Arribo": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if session.fin_arribo else "",
            "Operador": session.operador,
            "Placa": session.placa,
            "Transporte": session.transporte_sap if hasattr(session, 'transporte_sap') else "",
            "Remision 1": remisiones_str[0],
            "Ultimo Paso": session.estatus_arribo_ultimo_paso,
            "Mensaje Resultado": session.estatus_arribo_mensaje,
            "Historial Completo": historial_texto
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