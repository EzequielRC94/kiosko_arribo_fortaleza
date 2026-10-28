import os
import time
from datetime import datetime
from manager_sap import SAPManager

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
    def __init__(self):
        # Instanciar aquí ahorra memoria, ya que se crea una sola vez por sesión
        # y SAPManager es muy ligero hasta que invoca obtener_sesion()
        self.sap_manager = SAPManager()

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
                    respuesta_sap = self.sap_manager.zsdmx389_descargar_archivos(
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
                    
                    respuesta_sap = self.sap_manager.zsdmx389_descargar_archivos(
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