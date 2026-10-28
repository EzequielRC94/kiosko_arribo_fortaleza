# _zql_robot.py
import os
import time
from datetime import datetime, timedelta
from manager_sap import SAPManager, SAPError
from manager_cloudfort import CloudFortManager
from manager_arribos import ArribosManager
from session_data import SessionData


def obtener_datos_remision(
    remision: str,
    session_data: SessionData = None,
    cloudfort_manager: CloudFortManager = None,
    sap_manager: SAPManager = None,
    arribos_manager: ArribosManager = None,
    ruta_base_drive: str = None,
    on_status=None
) -> dict:
    """
    Máquina extractora de información (Plan A -> Plan B -> Plan C).
    únicamente busca la remisión y devuelve los datos encontrados o indica que no encontró nada.

    Retorna un diccionario con la estructura:
    {
        "estatus": bool,          # True si encontró datos_sap, False si no encontró nada
        "datos": dict | None,     # Diccionario con la información de la remisión (datos_sap) o None
        "origen": str,            # "A: Web Service", "B: Robot SAP", "C: Contingencia" o ""
        "error_sap": str          # Mensaje si SAP lanzó un SAPError directo; vacío ("") en caso contrario
    }
    """
    remision = str(remision).strip()

    # Inicialización bajo demanda para permitir llamadas desde cualquier clase o función
    if cloudfort_manager is None:
        cloudfort_manager = CloudFortManager()
    if sap_manager is None:
        sap_manager = SAPManager()
    if arribos_manager is None:
        arribos_manager = ArribosManager()

    if ruta_base_drive is None:
        if session_data and getattr(session_data, "ruta_base_drive", None):
            ruta_base_drive = session_data.ruta_base_drive
        else:
            perfil_usuario = os.environ.get("USERPROFILE", os.path.expanduser("~"))
            anno = datetime.now().strftime("%Y")
            ruta_base_drive = os.path.join(
                perfil_usuario,
                "Elementia S. A",
                "kiosko logistica cem - Documentos",
                anno
            )

    def _notificar_status(msg: str):
        if callable(on_status):
            on_status(msg)

    # =================================================================
    # FUNCIONES INTERNAS (PLANES DE EXTRACCIÓN)
    # =================================================================
    def _metodo_a_ws(rem: str) -> dict:
        return cloudfort_manager.obtener_datos_remision(rem)

    def _metodo_b_robot(rem: str) -> dict:
        return sap_manager.extraer_datos_remision(rem)

    def _metodo_c_excel(rem: str) -> dict:
        return arribos_manager.leer_zsdmx389_local(
            ruta_base_drive=ruta_base_drive,
            rem=rem,
            tipo_archivo="pendientes"
        )

    # =================================================================
    # EXTRACCIÓN DE DATOS (PLAN A -> PLAN B -> PLAN C)
    # =================================================================
    datos_sap = None
    origen_datos = ""

    # --- PLAN A: API WEB CLOUDFORT ---
    try:
        _notificar_status("Plan A: Consultando API CloudFort...")
        datos_sap = _metodo_a_ws(remision)
        origen_datos = "A: Web Service"
    except Exception as e_api:
        if session_data is not None:
            session_data.registrar_paso("[API CF] Falla", str(e_api))

        # --- PLAN B: ROBOT SAP ---
        if datos_sap is None:
            try:
                _notificar_status("Plan B: Desplegando Robot SAP...")
                if session_data is not None:
                    session_data.registrar_paso("[SAP] Inicio Robot", "Buscando en SAP")
                datos_sap = _metodo_b_robot(remision)
                origen_datos = "B: Robot SAP"

            except SAPError as e_sap:
                # Si SAP devuelve un error directo de documento, entregamos el aviso a quien llamó
                return {
                    "estatus": False,
                    "datos": None,
                    "origen": "B: Robot SAP",
                    "error_sap": str(e_sap)
                }

            except Exception as e_robot:
                # FALLA TÉCNICA (SAP Cerrado, Sin internet, Error de código)
                if session_data is not None:
                    session_data.registrar_paso("[SAP] Falla Técnica", str(e_robot))

                # --- PLAN C: EXCEL CONTINGENCIA ---
                if datos_sap is None:
                    try:
                        _notificar_status("Plan C: Buscando en Archivo Local Excel...")
                        if session_data is not None:
                            session_data.registrar_paso("[EXCEL] Inicio", "Buscando en zsdmx389")
                        datos_sap = _metodo_c_excel(remision)
                        origen_datos = "C: Contingencia"

                    except Exception as e_excel:
                        if session_data is not None:
                            session_data.registrar_paso("[EXCEL] Falla", str(e_excel))

    # =================================================================
    # ENTREGA DE INFORMACIÓN
    # =================================================================
    return {
        "estatus": datos_sap is not None,
        "datos": datos_sap,
        "origen": origen_datos,
        "error_sap": ""
    }


def main_descarga_zsdmx267_diaria():
    """
    Robot para la descarga diaria/histórica de la transacción ZSDMX267 en formato CSV.
    Itera día por día en reversa desde fecha_fin hasta fecha_inicio.
    """
    # 1. Instancia del gestor SAP
    sap_manager = SAPManager()
    session = sap_manager.obtener_sesion()
    
    if not session:
        print("❌ Error: SAP no está conectado o no hay sesiones abiertas.")
        return False

    # 2. Configuración de parámetros y filtros
    centro_exp = "MX*"
    lay_out = "/0.TRAN_REP"
    extension = "xls"
    
    # 3. Rango de fechas dinámico (hace 3 días hasta hoy)
    hoy = datetime.now()
    fecha_fin_dt = hoy
    fecha_inicio_dt = hoy - timedelta(days=3)
    
    # 4. Configuración de ruta de descarga (crea directorios si no existen)
    perfil_usuario = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    anno = hoy.strftime("%Y")
    
    path_descarga = os.path.join(
        perfil_usuario,
        "Elementia S. A",
        "kiosko logistica cem - Documentos",
        anno,
        "zsdmx267"
    )
    
    os.makedirs(path_descarga, exist_ok=True)

    print("=" * 65)
    print(" INICIANDO ROBOT DE DESCARGA ZSDMX267 (CSV)")
    print(f" • Centro:    {centro_exp}")
    print(f" • Layout:    {lay_out}")
    print(f" • Rango:     {fecha_inicio_dt.strftime('%d.%m.%Y')} al {fecha_fin_dt.strftime('%d.%m.%Y')}")
    print(f" • Directorio: {path_descarga}")
    print("=" * 65)

    # 5. Bucle día por día hacia atrás
    dias_totales = (fecha_fin_dt.date() - fecha_inicio_dt.date()).days
    hubo_fallas = False

    for i in range(dias_totales + 1):
        fecha_loop = fecha_fin_dt - timedelta(days=i)
        
        # Formato de entrada para SAP (DD.MM.YYYY)
        fch_sap = fecha_loop.strftime("%d.%m.%Y")
        
        # Nombre base del archivo (sin extensión, ya que _exportar_archivo_sap la concatena)
        nom_archivo = f"zsdmx267_{fecha_loop.strftime('%Y%m%d')}"

        print(f"\n⏳ Procesando {fch_sap} ({centro_exp})...")

        # 6. Ejecución de la descarga aislada por día
        resultado = sap_manager.zsdmx267_descargar_archivos(
            path_descarga=path_descarga,
            nom_archivo=nom_archivo,
            extension=extension,
            fch_in=fch_sap,
            fch_fn=fch_sap,
            lay_out=lay_out,
            centro_exp=centro_exp,
            descargar=True
        )

        if resultado.get("estatus"):
            print(f"  ✅ {resultado.get('msg')}")
        else:
            print(f"  ⚠️ Falla o sin datos para {fch_sap}: {resultado.get('msg')}")
            hubo_fallas = True

        # Breve pausa para liberar la UI entre transacciones consecutivas
        time.sleep(1)

    # 7. Resumen de ejecución
   
    if not hubo_fallas:
        print(f"✅ Proceso Terminado: Todas las descargas concluyeron con éxito.")
    else:
        print(f"⚠️ Proceso Terminado: Algunas fechas presentaron advertencias o no arrojaron datos.")
    # print(f"📁 Destino: {path_descarga}")
  

    return not hubo_fallas


if __name__ == "__main__":
    main_descarga_zsdmx267_diaria()
