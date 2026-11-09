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


# ==============================================================================
# SINCRONIZACIÓN DE CATÁLOGOS POWER QUERY (MANDANTE: catalogos.py)
# ==============================================================================

def actualizar_catalogos_powerquery(directorio_base: str = None) -> bool:
    """
    Actualiza todos los catálogos Power Query (materiales y centros) desde catalogos.py.
    """
    try:
        from catalogos import actualizar_todos_catalogos_pq
        res = actualizar_todos_catalogos_pq(directorio_base)
        for clave, ruta in res.items():
            print(f"[OK] Catalogo de {clave} PQ sincronizado con exito: {ruta}")
        return True
    except Exception as e:
        print(f"[ERROR] Al sincronizar catalogos PQ: {e}")
        return False


def actualizar_catalogo_materiales(directorio_base: str = None) -> bool:
    """Alias para mantener compatibilidad."""
    return actualizar_catalogos_powerquery(directorio_base)


def actualizar_catalogo_centros(directorio_base: str = None) -> bool:
    """Alias para mantener compatibilidad."""
    return actualizar_catalogos_powerquery(directorio_base)


def rutina_diaria(dias_atras: int = 4, ruta_base_drive: str = None):
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
    print(" INICIANDO DESCARGAS RUTINARIAS SAP (RUTINA DIARIA)")
    print(f" Ruta Base Drive: {ruta_base_drive}")
    print(f" Dias atras (249 / 267): {dias_atras} dias")
    print(f" Meses a procesar (VT16 / FBL4N): {[m if m else f'{hoy.month} (en curso)' for m in meses_a_procesar]}")
    print("=" * 70)

    # 0. Sincronización de catálogos Power Query (Materiales y Centros)
    print("\n▶ [0/5] Sincronizando catalogos Power Query desde catalogos.py...")
    try:
        actualizar_catalogos_powerquery()
    except Exception as e_cat:
        print(f"[AVISO] Error actualizando catalogos Power Query: {e_cat}")

    # 1. ZSDMX389 (pendientes y en proceso)
    print("\n▶ [1/5] Ejecutando: zsdmx389_robot (tipo_descarga='ambos')...")
    try:
        res_389 = manager.zsdmx389_robot(ruta_base_drive=ruta_base_drive, tipo_descarga="ambos")
        print(f"Resultado zsdmx389_robot:\n{json.dumps(res_389, indent=4, ensure_ascii=False)}")
    except Exception as e_389:
        print(f"[ERROR] En zsdmx389_robot: {e_389}")

    # 2. ZSDMX249 (hoy a -3 días, XLS)
    print(f"\n▶ [2/5] Ejecutando: zsdmx249_robot (dias_atras={dias_atras}, extension='xls')...")
    try:
        res_249 = manager.zsdmx249_robot(ruta_base_drive=ruta_base_drive, dias_atras=dias_atras, extension="xls")
        print(f"Resultado zsdmx249_robot:\n{json.dumps(res_249, indent=4, ensure_ascii=False)}")
    except Exception as e_249:
        print(f"[ERROR] En zsdmx249_robot: {e_249}")

    # 3. ZSDMX267 (hoy a -3 días, XLS)
    print(f"\n▶ [3/5] Ejecutando: zsdmx267_robot (dias_atras={dias_atras}, extension='xls')...")
    try:
        res_267 = manager.zsdmx267_robot(ruta_base_drive=ruta_base_drive, dias_atras=dias_atras, 
                                         extension="xls", forzar=True)
        print(f"Resultado zsdmx267_robot:\n{json.dumps(res_267, indent=4, ensure_ascii=False)}")
    except Exception as e_267:
        print(f"[ERROR] En zsdmx267_robot: {e_267}")

    # 4. VT16 (mes en curso / últimos días, XLS)
    print(f"\n▶ [4/5] Ejecutando: vt16_robot (extension='xls')...")
    for mes_param in meses_a_procesar:
        etiqueta_mes = f"mes {mes_param}" if mes_param else "mes en curso"
        print(f"  [VT16] Procesando {etiqueta_mes}...")
        try:
            res_vt16 = manager.vt16_robot(ruta_base_drive=ruta_base_drive, mes=mes_param, extension="xls")
            print(f"  Resultado vt16_robot ({etiqueta_mes}):\n{json.dumps(res_vt16, indent=4, ensure_ascii=False)}")
        except Exception as e_vt16:
            print(f"  [ERROR] En vt16_robot ({etiqueta_mes}): {e_vt16}")

    # 5. FBL4N (mes en curso / últimos días, XLS)
    print(f"\n▶ [5/5] Ejecutando: fbl4n_robot (extension='xls')...")
    for mes_param in meses_a_procesar:
        etiqueta_mes = f"mes {mes_param}" if mes_param else "mes en curso"
        print(f"  [FBL4N] Procesando {etiqueta_mes}...")
        try:
            res_fbl4n = manager.fbl4n_robot(ruta_base_drive=ruta_base_drive, mes=mes_param, extension="xls")
            print(f"  Resultado fbl4n_robot ({etiqueta_mes}):\n{json.dumps(res_fbl4n, indent=4, ensure_ascii=False)}")
        except Exception as e_fbl4n:
            print(f"  [ERROR] En fbl4n_robot ({etiqueta_mes}): {e_fbl4n}")

    # 5.1. FBL4N (Analizar adicionales del mes en curso y enviar correo)
    print(f"\n▶ [5.1] Analizando adicionales FBL4N del mes en curso y preparando correo...")
    try:
        res_analisis = analizar_fbl4n(mes_en_curso="", ruta_parquet=None)
        print(f"Resultado analizar_fbl4n:\n{json.dumps(res_analisis, indent=4, ensure_ascii=False)}")
    except Exception as e_analisis:
        print(f"[ERROR] En analizar_fbl4n: {e_analisis}")

    print("\n" + "=" * 70)
    print(" RUTINA DE DESCARGAS FINALIZADA")
    print("=" * 70)


def analizar_fbl4n(mes_en_curso: str = None, ruta_parquet: str = None) -> dict:
    """
    Lee el archivo fbl4n.parquet, filtra los gastos de fletes creados en el mes corriente
    pero pertenecientes a viajes de meses pasados:
      - fch_documento == mes_en_curso
      - 4_fch_fin_carga != mes_en_curso
    Arma el resumen por usuario y el detalle por fecha y usuario, y prepara el correo
    mediante EmailManager (mailer.py).
    """
    import pandas as pd
    from parquets import obtener_rutas_transaccion, actualizar_parquet_vt16, actualizar_parquet_fbl4n
    from mailer import EmailManager

    hoy = datetime.now()
    if not mes_en_curso:
        mes_en_curso = hoy.strftime("%Y-%m")
    else:
        mes_en_curso = str(mes_en_curso).strip()
        if mes_en_curso.isdigit() and 1 <= int(mes_en_curso) <= 12:
            mes_en_curso = f"{hoy.year}-{int(mes_en_curso):02d}"

    if not ruta_parquet:
        # Asegurar que vt16.parquet y fbl4n.parquet estén actualizados con las últimas descargas
        actualizar_parquet_vt16()
        actualizar_parquet_fbl4n()
        rutas = obtener_rutas_transaccion("fbl4n")
        ruta_parquet = rutas["archivo_parquet"]

    if not os.path.exists(ruta_parquet):
        msg_err = f"No se encontró el archivo fbl4n.parquet en: {ruta_parquet}"
        print(f"⚠️ [analizar_fbl4n] {msg_err}")
        return {"estatus": False, "msg": msg_err}

    try:
        df = pd.read_parquet(ruta_parquet, engine="fastparquet")
    except Exception:
        df = pd.read_parquet(ruta_parquet)

    if df.empty:
        msg_vacio = "El archivo fbl4n.parquet está vacío."
        print(f"ℹ️ [analizar_fbl4n] {msg_vacio}")
        return {"estatus": False, "msg": msg_vacio}

    # Asegurar tipo numérico en importe y limpiar usuario_creacion
    df["importe"] = pd.to_numeric(df["importe"], errors="coerce").fillna(0.0)
    df["usuario_creacion"] = df["usuario_creacion"].fillna("SIN_USUARIO").astype(str).str.strip()

    # Extraer año-mes (YYYY-MM) de fch_documento y 4_fch_fin_carga
    fch_doc_ym = pd.to_datetime(
        df["fch_documento"], format="mixed", dayfirst=True, errors="coerce"
    ).dt.strftime("%Y-%m")

    if "4_fch_fin_carga" in df.columns:
        fch_carga_ym = pd.to_datetime(
            df["4_fch_fin_carga"], format="mixed", dayfirst=True, errors="coerce"
        ).dt.strftime("%Y-%m")
    else:
        fch_carga_ym = pd.Series([None] * len(df), index=df.index)

    # Filtrar: fch_documento == mes_en_curso y 4_fch_fin_carga != mes_en_curso
    mask = (fch_doc_ym == mes_en_curso) & (fch_carga_ym.fillna("") != mes_en_curso)
    df_adicionales = df[mask].copy()

    if "4_fch_fin_carga" in df_adicionales.columns:
        df_adicionales["4_fch_fin_carga"] = (
            df_adicionales["4_fch_fin_carga"]
            .fillna("SIN_FECHA")
            .astype(str)
            .str.strip()
            .replace({"": "SIN_FECHA", "nan": "SIN_FECHA", "None": "SIN_FECHA", "NaT": "SIN_FECHA"})
        )
    else:
        df_adicionales["4_fch_fin_carga"] = "SIN_FECHA"

    # 1. Tabla por usuario: usuario_creacion -> sumatoria(importe)
    df_por_usuario = (
        df_adicionales.groupby("usuario_creacion", as_index=False)["importe"]
        .sum()
        .sort_values(by="importe", ascending=False)
        .reset_index(drop=True)
    )

    # 2. Tabla por fecha y usuario: fch_documento -> usuario_creacion -> sumatoria(importe)
    df_por_fecha_usuario = (
        df_adicionales.groupby(["fch_documento", "usuario_creacion"], as_index=False)["importe"]
        .sum()
        .sort_values(by=["fch_documento", "importe"], ascending=[True, False])
        .reset_index(drop=True)
    )

    # 3. Tabla por fecha fin carga y usuario: 4_fch_fin_carga -> usuario_creacion -> sumatoria(importe)
    df_por_fch_fin_carga = (
        df_adicionales.groupby(["4_fch_fin_carga", "usuario_creacion"], as_index=False)["importe"]
        .sum()
        .sort_values(by=["4_fch_fin_carga", "importe"], ascending=[True, False])
        .reset_index(drop=True)
    )

    total_importe = float(df_por_usuario["importe"].sum()) if not df_por_usuario.empty else 0.0

    # Construir vista previa en texto
    lineas_resumen = [
        "=" * 65,
        f"Resumen de adicionales generados {mes_en_curso},",
        "=" * 65,
        "\n(Tabla por usuario)",
        "usuario_creacion -> (sumatoria) importe",
        "-" * 45,
    ]
    if df_por_usuario.empty:
        lineas_resumen.append("  (Sin registros para este periodo)")
    else:
        for _, row in df_por_usuario.iterrows():
            lineas_resumen.append(f"  {row['usuario_creacion']:<20} -> ${row['importe']:>14,.2f}")
        lineas_resumen.append("-" * 45)
        lineas_resumen.append(f"  {'TOTAL':<20} -> ${total_importe:>14,.2f}")

    lineas_resumen.extend([
        "\n(Tabla por fecha y usuario)",
        "Detalle por fecha,",
        "fch_documento -> usuario_creacion -> (sumatoria) importe",
        "-" * 60,
    ])
    if df_por_fecha_usuario.empty:
        lineas_resumen.append("  (Sin registros para este periodo)")
    else:
        for _, row in df_por_fecha_usuario.iterrows():
            lineas_resumen.append(
                f"  {str(row['fch_documento']):<12} -> {row['usuario_creacion']:<20} -> ${row['importe']:>14,.2f}"
            )
        lineas_resumen.append("-" * 60)
        lineas_resumen.append(f"  {'TOTAL':<36} -> ${total_importe:>14,.2f}")

    lineas_resumen.extend([
        "\n(Tabla por fecha fin carga)",
        "4_fch_fin_carga -> usuario_creacion -> (sumatoria) importe",
        "-" * 60,
    ])
    if df_por_fch_fin_carga.empty:
        lineas_resumen.append("  (Sin registros para este periodo)")
    else:
        for _, row in df_por_fch_fin_carga.iterrows():
            lineas_resumen.append(
                f"  {str(row['4_fch_fin_carga']):<12} -> {row['usuario_creacion']:<20} -> ${row['importe']:>14,.2f}"
            )
        lineas_resumen.append("-" * 60)
        lineas_resumen.append(f"  {'TOTAL':<36} -> ${total_importe:>14,.2f}")
    lineas_resumen.append("=" * 65)

    texto_resumen = "\n".join(lineas_resumen)
    print(texto_resumen)

    # Preparar correo mediante EmailManager (con mail.Send() comentado)
    email_mgr = EmailManager()
    res_correo = email_mgr.enviar_resumen_fbl4n(
        mes_en_curso=mes_en_curso,
        df_por_usuario=df_por_usuario,
        df_por_fecha_usuario=df_por_fecha_usuario,
        df_por_fch_fin_carga=df_por_fch_fin_carga,
    )

    return {
        "estatus": True,
        "mes_en_curso": mes_en_curso,
        "total_registros": int(len(df_adicionales)),
        "total_importe": round(total_importe, 2),
        "tabla_por_usuario": df_por_usuario.to_dict(orient="records"),
        "tabla_por_fecha_usuario": df_por_fecha_usuario.to_dict(orient="records"),
        "tabla_por_fch_fin_carga": df_por_fch_fin_carga.to_dict(orient="records"),
        "correo": res_correo,
    }


if __name__ == "__main__":
    rutina_diaria()
    
