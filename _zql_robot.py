# _zql_robot.py
import os
import json
import time
from datetime import datetime, timedelta
from manager_sap import SAPManager, SAPError
from manager_cloudfort import CloudFortManager
from manager_arribos import ArribosManager
from manager_descargas import DescargasManager
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


def obtener_ruta_base_drive() -> str:
    """Calcula la ruta base operativa del año actual en OneDrive."""
    perfil_usuario = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    anio_actual = datetime.now().strftime("%Y")
    return os.path.join(
        perfil_usuario,
        "Elementia S. A",
        "kiosko logistica cem - Documentos",
        anio_actual
    )


def rutina_diaria(dias_atras: int = 3, ruta_base_drive: str = None):
    """
    Actividad rutinaria diaria:
    Descarga los reportes de SAP actualizando únicamente los últimos 'dias_atras' días (por defecto 3).
    """
    if ruta_base_drive is None:
        ruta_base_drive = obtener_ruta_base_drive()

    manager = DescargasManager()
    hoy = datetime.now()

    # Mes en curso (""). Si hoy está entre los primeros 3 días del mes, también incluye el mes previo
    meses_a_procesar = [""]
    if hoy.day <= dias_atras:
        mes_anterior = (hoy.replace(day=1) - timedelta(days=1)).month
        meses_a_procesar.append(str(mes_anterior))

    print("=" * 70)
    print(" 🚀 INICIANDO DESCARGAS RUTINARIAS SAP (RUTINA DIARIA)")
    print(f" 📁 Ruta Base Drive: {ruta_base_drive}")
    print(f" 📅 Días atrás (249 / 267): {dias_atras} días")
    print(f" 🗓️ Meses a procesar (VT16 / FBL4N): {[m if m else f'{hoy.month} (en curso)' for m in meses_a_procesar]}")
    print("=" * 70)

    # 1. ZSDMX389 (pendientes y en proceso)
    print("\n▶ [1/5] Ejecutando: zsdmx389_robot (tipo_descarga='ambos')...")
    try:
        res_389 = manager.zsdmx389_robot(ruta_base_drive=ruta_base_drive, tipo_descarga="ambos")
        print(f"📋 Resultado zsdmx389_robot:\n{json.dumps(res_389, indent=4, ensure_ascii=False)}")
    except Exception as e_389:
        print(f"❌ Error en zsdmx389_robot: {e_389}")

    # 2. ZSDMX249 (hoy a -3 días, XLS)
    print(f"\n▶ [2/5] Ejecutando: zsdmx249_robot (dias_atras={dias_atras}, extension='xls')...")
    try:
        res_249 = manager.zsdmx249_robot(ruta_base_drive=ruta_base_drive, dias_atras=dias_atras, extension="xls")
        print(f"📋 Resultado zsdmx249_robot:\n{json.dumps(res_249, indent=4, ensure_ascii=False)}")
    except Exception as e_249:
        print(f"❌ Error en zsdmx249_robot: {e_249}")

    # 3. ZSDMX267 (hoy a -3 días, XLS)
    print(f"\n▶ [3/5] Ejecutando: zsdmx267_robot (dias_atras={dias_atras}, extension='xls')...")
    try:
        res_267 = manager.zsdmx267_robot(ruta_base_drive=ruta_base_drive, dias_atras=dias_atras, extension="xls")
        print(f"📋 Resultado zsdmx267_robot:\n{json.dumps(res_267, indent=4, ensure_ascii=False)}")
    except Exception as e_267:
        print(f"❌ Error en zsdmx267_robot: {e_267}")

    # 4. VT16 (mes en curso / últimos días, XLS)
    print(f"\n▶ [4/5] Ejecutando: vt16_robot (extension='xls')...")
    for mes_param in meses_a_procesar:
        etiqueta_mes = f"mes {mes_param}" if mes_param else "mes en curso"
        print(f"  🔹 [VT16] Procesando {etiqueta_mes}...")
        try:
            res_vt16 = manager.vt16_robot(ruta_base_drive=ruta_base_drive, mes=mes_param, extension="xls")
            print(f"  📋 Resultado vt16_robot ({etiqueta_mes}):\n{json.dumps(res_vt16, indent=4, ensure_ascii=False)}")
        except Exception as e_vt16:
            print(f"  ❌ Error en vt16_robot ({etiqueta_mes}): {e_vt16}")

    # 5. FBL4N (mes en curso / últimos días, XLS)
    print(f"\n▶ [5/5] Ejecutando: fbl4n_robot (extension='xls')...")
    for mes_param in meses_a_procesar:
        etiqueta_mes = f"mes {mes_param}" if mes_param else "mes en curso"
        print(f"  🔹 [FBL4N] Procesando {etiqueta_mes}...")
        try:
            res_fbl4n = manager.fbl4n_robot(ruta_base_drive=ruta_base_drive, mes=mes_param, extension="xls")
            print(f"  📋 Resultado fbl4n_robot ({etiqueta_mes}):\n{json.dumps(res_fbl4n, indent=4, ensure_ascii=False)}")
        except Exception as e_fbl4n:
            print(f"  ❌ Error en fbl4n_robot ({etiqueta_mes}): {e_fbl4n}")

    print("\n" + "=" * 70)
    print(" 🏁 RUTINA DE DESCARGAS FINALIZADA")
    print("=" * 70)


if __name__ == "__main__":
    rutina_diaria()


