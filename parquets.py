# parquets.py
import sys
import os
import glob
from datetime import datetime
import pandas as pd

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# ==============================================================================
# CONFIGURACIÓN DE ESQUEMAS Y TRANSFORMACIONES POR TRANSACCIÓN
# ==============================================================================

CONFIG_267 = {
    "columna_ancla": "entrega",
    "llaves_dedup": ["entrega", "entrega_pos"], # llave para eliminar duplicados
    "skiprows": 3, # Número de filas a saltar antes de leer encabezados (para zsdmx267)
    # Orden estático de las 20 columnas del layout /$ZQL_ROBOT en ZSDMX267
    "columnas_fijas": [
        "c_exp",               # 1. PtPlaTrnsp / PtoPlanifTransp
        "entrega",             # 2. Entrega
        "entrega_pos",         # 3. Posición de entrega
        "transporte",          # 4. Transporte / Nº de transporte
        "gasto_transporte",    # 5. Nº porte / Gasto de transporte
        "tarifa_normal",       # 6. Tarif norm / Tarifa normal
        "tarifa_total",        # 7. Neto / Valor neto
        "fch_creacion_gasto",  # 8. Fe.liquid. / Fecha creación gasto
        "gasto_estatus",       # 9. Estatus de flete
        "gasto_oc",            # 10. Doc.compr. / Orden de Compra
        "gasto_ceco",          # 11. Ce.coste / Centro de coste
        "gasto_division",      # 12. División
        "destino_poblacion",   # 13. Pob. Dest.
        "destino_region",      # 14. RegionDest / Region Dest.
        "operador_remision",   # 15. Chofer Remisión
        "placas_remision",     # 16. Plac. Rem. / Placas Remisión
        "factura_doc",         # 17. Factura / Doc.facturación
        "factura_valor",       # 18. Neto.1 / Valor Factura / Valor neto.1
        "ruta_id",             # 19. RutaTransp
        "ruta_nombre",         # 20. Nombre de ruta
    ],
    # Respaldo para archivos antiguos de 19 columnas que no tenían 'entrega_pos'
    "columnas_fijas_alt": {
        19: [
            "c_exp", "entrega", "transporte", "gasto_transporte",
            "tarifa_normal", "tarifa_total", "fch_creacion_gasto", "gasto_estatus",
            "gasto_oc", "gasto_ceco", "gasto_division", "destino_poblacion",
            "destino_region", "operador_remision", "placas_remision", "factura_doc",
            "factura_valor", "ruta_id", "ruta_nombre",
        ]
    },
    "cols_int": [],
    "cols_float": [
        "tarifa_normal", "tarifa_total", "factura_valor"
    ],
    "cols_date": [
        "fch_creacion_gasto", "4_fch_fin_carga"
    ],
    "cols_time": [
        "4_hr_fin_carga"
    ],
}

CONFIG_249 = {
    "columna_ancla": "entrega", 
    "llaves_dedup": ["entrega", "pedido_pos"], # llave para eliminar duplicados
    "skiprows": 7, # En ZSDMX249 la fila de encabezados inicia en la fila 7
    "columnas_extra": [
        "material_familia",
        "material_nom_corto",
        "4_fch_fin_carga",
        "4_hr_fin_carga",
        "5_hr_despacho_exp",
        "modalidad",
        "turno_salida",
    ],
    # Columnas ordenadas del layout /$ZQL_ROBOT en ZSDMX249 (23 columnas)
    "columnas_fijas": [
        "c_exp",                     # 1. PsEx / Centro expedición
        "entrega",                   # 2. Entrega
        "transporte",                # 3. Talón de E / Transporte
        "material_cod",              # 4. Material / Código de material
        "material_nom",              # 5. Denominación / Nombre del material
        "ton",                       # 6. Ctd.entr. / Cantidad entrega (ton)
        "gpo_mat",                   # 7. GrM2 / Grupo de material 2 F06 = envasado / F07 = granel  
        "clte_solicitante",          # 8. Solic. / Cliente solicitante            
        "clte_nombre",               # 9. Nombre 1 / Nombre del cliente
        "clte_destinatario",         # 10. Destinat. / Destinatario
        "clte_nombre_destinatario",  # 11. Nombre Destinatario
        "pedido",                    # 12. Pedido
        "pedido_pos",                # 13. Pos. / Posición de pedido
        "fch_sm_real",               # 14. Fe.SM real / Fecha salida mercancía real
        "ent_crea",                  # 15. Creador En / Creador de entrega
        "ej_comercial",              # 16. Vendedor / Ejecutivo comercial
        "ej_nombre_completo",        # 17. Nombre completo del vendedor
        "peso_neto",                 # 18. Entr Peso / Peso neto
        "peso_bruto",                # 19. Entr Peso.1 / Peso bruto
        "folio_manual",              # 20. Folio Manu / Folio manual
        "factura",                   # 21. Factura
        "fch_creacion_entrega",      # 22. Fe.Creació / Fecha creación entrega
        "fch_cita_entrega",          # 23. Fe.entrega / Fecha cita entrega
    ],

    "cols_int": [],
    "cols_float": ["ton", "peso_neto", "peso_bruto"],
    "cols_date": ["fch_sm_real", "fch_creacion_entrega", "fch_cita_entrega", "4_fch_fin_carga"],
    "cols_time": ["4_hr_fin_carga", "5_hr_despacho_exp"],
}

CONFIG_VT16 = {
    "columna_ancla": "transporte",
    "llaves_dedup": ["transporte"],
    "skiprows": 2,              # En VT16 los encabezados inician tras saltar la fila de metadatos inicial
    # Columnas ordenadas del layout /$ZQL_ROBOT en VT16 (41 columnas útiles tras descartar vacías)
    "columnas_fijas": [
        "transporte",                  # 1. Transporte
        "status_global",               # 2. G (Estatus global: 1 a 7)
        "c_exp",                       # 3. PTrp (Pto. planificación transporte / Centro exp.)
        "0_fch_creacion_transporte",   # 4. Creado el (Fecha creación transporte)
        "0_hr_creacion_transporte",    # 5. Hora (Hora creación transporte)
        "1_fch_planificacion",         # 6. FinPlanif (Fecha fin planificación)
        "1_hr_planificacion",          # 7. Planif (Hora planificación)
        "2_fch_bascula_entrada",       # 8. FeActReg (Fecha registro en báscula)
        "2_hr_bascula_entrada",        # 9. HoraAcRg (Hora registro en báscula)
        "3_fch_inicio_carga",          # 10. InActCarga (Fecha inicio de carga)
        "3_hr_inicio_carga",           # 11. HrAICg (Hora inicio de carga)
        "4_fch_fin_carga",             # 12. FinActCarg (Fecha fin de carga)
        "4_hr_fin_carga",              # 13. HrAFCg (Hora fin de carga)
        "5_fch_despacho_exp",          # 14. FeActDpExp (Fecha despacho expedición)
        "5_hr_despacho_exp",           # 15. HrADpExp (Hora despacho expedición)
        "6_fch_inicio_transporte",     # 16. InActTrans (Fecha inicio de transporte)
        "6_hr_inicio_transporte",      # 17. HrAITr (Hora inicio de transporte)
        "7_fch_fin_transporte",        # 18. FinActTran (Fecha fin de transporte)
        "7_hr_fin_transporte",         # 19. HrAFTr (Hora fin de transporte)
        "clase_expedicion",            # 20. Ex (Clase de expedición: F1, F2, F7...)
        "clase_exp_denom",             # 21. Denom.cl.exped. (Tolva Neumática, Trailer Plataforma...)
        "transp_num_proveedor",        # 22. AgServTran (Número de transportista / proveedor)
        "transp_nombre",               # 23. Nom.AS (Nombre transportista / CLIENTE RECOGE...)
        "id_track",                    # 24. IDTrackTransp (Identificador de tracking / Placas)
        "signatura",                   # 25. Signatura (Placas del transporte)
        "identif_ext_1",               # 26. Identif.ext.1
        "identif_ext_2",               # 27. Identif.ext.2
        "texto_adic_1",                # 28. Texto adic.1
        "texto_adic_2",                # 29. Texto adic.2 (Nombre del chofer / operador)
        "texto_adic_3",                # 30. Texto adic.3
        "texto_adic_4",                # 31. Texto adic.4
        "modalidad",                   # 32. Suplem.3 (RETIRADO / ENTREGADO)
        "suplem_4",                    # 33. Suplem.4
        "clase_transporte",            # 34. ClTr (Clase de transporte: ZTP1, ZTP2...)
        "clase_transp_desc",           # 35. Cl.transp. (Descripción clase transporte)
        "tmp_tot",                     # 36. TmpTot (Tiempo total)
        "est_gasto",                   # 37. CP / estatus_gasto
        "status_global_desc",          # 38. Den.stat.glob. (Descripción estatus: Fin de transporte...)
        "transporte_autor",            # 39. Autor (Usuario que creó el transporte en SAP)
        "ruta_id",                     # 40. Ruta (Código de ruta SAP)
        "km",                          # 41. Distancia (Kilometraje)
    ],
    "cols_int": [
        "km"
    ],
    "cols_float": [],
    "cols_date": [
        "0_fch_creacion_transporte", "1_fch_planificacion", "2_fch_bascula_entrada",
        "3_fch_inicio_carga", "4_fch_fin_carga", "5_fch_despacho_exp",
        "6_fch_inicio_transporte", "7_fch_fin_transporte"
    ],
    "cols_time": [
        "0_hr_creacion_transporte", "1_hr_planificacion", "2_hr_bascula_entrada",
        "3_hr_inicio_carga", "4_hr_fin_carga", "5_hr_despacho_exp",
        "6_hr_inicio_transporte", "7_hr_fin_transporte"
    ],
} 

CONFIG_FBL4N = {
    "columna_ancla": "documento",
    "llaves_dedup": ["documento"],
    "skiprows": 5,          # Fila encbezados en FBL4N inicia tras saltar 5 filas de metadatos
    "cols_drop": ["St", "fch_pago"],  # Columnas a descartar antes de guardar en parquet
    "columnas_extra": ["4_fch_fin_carga"],  # Columna enriquecida mediante relación con vt16.parquet
    "columnas_fijas": [
        "St",               # 1. Estatus -> NO considerar (eliminar de parquet)
        "documento",        # 2. Documento
        "c_exp",            # 3. Centro
        "fch_documento",    # 4. Fecha documento
        "fch_registro",     # 5. Fecha registro
        "clase_documento",  # 6. Clase documento
        "libro_mayor",      # 7. Libro mayor
        "ceco",             # 8. Centro de costo
        "oc",               # 9. Orden de compra
        "transporte",       # 10. Referencia -> transporte
        "importe",          # 11. Importe
        "moneda",           # 12. Moneda
        "acreedor",         # 13. Acreedor
        "usuario_creacion", # 14. Usuario creación
        "fch_pago",         # 15. Fecha pago -> NO considerar (eliminar de parquet)
    ],

    "cols_int": [],
    "cols_float": ["importe"],
    "cols_date": ["fch_documento", "fch_registro", "4_fch_fin_carga"],
    "cols_time": [],
}

# ==============================================================================
# FUNCIONES AUXILIARES REUTILIZABLES (MOTOR DE PARQUETS)
# ==============================================================================

def obtener_rutas_transaccion(transaccion: str) -> dict:
    """
    Construye dinámicamente las rutas de origen, parquet y memoria_txt
    a partir del número o nombre de transacción (ej. '249', '267', '389' o 'zsdmx249').
    """
    cod_tx = str(transaccion).lower().replace("zsdmx", "").strip()

    perfil_usuario = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    carpeta_general = os.path.join(perfil_usuario, "Elementia S. A", "kiosko logistica cem - Documentos")
    anno = str(datetime.now().year)

    # Identificar la carpeta de origen (soporta 'zsdmx267', 'vt16', 'fbl4n', etc.)
    candidatos_carpeta = [
        os.path.join(carpeta_general, anno, f"zsdmx{cod_tx}"),
        os.path.join(carpeta_general, anno, str(transaccion).lower()),
        os.path.join(carpeta_general, anno, cod_tx),
    ]
    carpeta_origen = candidatos_carpeta[0]
    for c in candidatos_carpeta:
        if os.path.exists(c):
            carpeta_origen = c
            break

    archivo_parquet = os.path.join(carpeta_general, "bi", "parquet", f"{cod_tx}.parquet")
    archivo_log = os.path.join(carpeta_general, "bi", "memoria_txt", f"{cod_tx}.txt")

    try:
        os.makedirs(os.path.dirname(archivo_parquet), exist_ok=True)
        os.makedirs(os.path.dirname(archivo_log), exist_ok=True)
    except Exception:
        pass

    return {
        "cod_tx": cod_tx,
        "carpeta_general": carpeta_general,
        "carpeta_origen": carpeta_origen,
        "archivo_parquet": archivo_parquet,
        "archivo_log": archivo_log,
    }


def _cargar_memoria_modificacion(archivo_log: str) -> dict:
    """
    Lee el archivo de memoria (formato: 'nombre_archivo|YYYY-MM-DD HH:MM:SS').
    Soporta retrocompatibilidad si una línea solo tenía el nombre del archivo.
    """
    memoria = {}
    if os.path.exists(archivo_log):
        with open(archivo_log, "r", encoding="utf-8") as f:
            for linea in f.read().splitlines():
                linea = linea.strip()
                if not linea:
                    continue
                if "|" in linea:
                    nom, fch_mod = linea.split("|", 1)
                    memoria[nom.strip()] = fch_mod.strip()
                else:
                    memoria[linea] = "SIN_FECHA"
    return memoria


def _guardar_memoria_modificacion(archivo_log: str, memoria: dict):
    """Guarda el diccionario de archivos procesados y su fecha de modificación."""
    with open(archivo_log, "w", encoding="utf-8") as f:
        for nom in sorted(memoria.keys()):
            f.write(f"{nom}|{memoria[nom]}\n")


def _filtrar_columna_ancla(df: pd.DataFrame, col_ancla: str) -> pd.DataFrame:
    """
    Filtra rigurosamente filas donde la columna ancla sea nula, vacía, 'nan', 'none' o 'null'.
    Evita que Power BI rechace relaciones 1 a varios por valores en blanco.
    """
    if not col_ancla or df is None or df.empty:
        return df

    # Buscar coincidencia exacta insensible a mayúsculas
    col_target = None
    for c in df.columns:
        if str(c).strip().lower() == col_ancla.strip().lower():
            col_target = c
            break
    if not col_target:
        for c in df.columns:
            if col_ancla.strip().lower() in str(c).strip().lower():
                col_target = c
                break

    if not col_target or col_target not in df.columns:
        return df

    # 1. Eliminar NaN / Nulls nativos de pandas
    df = df.dropna(subset=[col_target])
    # 2. Eliminar cadenas vacías, espacios, 'nan', 'none', 'null' o 'undefined'
    val_limpio = df[col_target].astype(str).str.strip().str.lower()
    df = df[~val_limpio.isin(["", "nan", "none", "null", "undefined"])].copy()
    return df


def _leer_archivo_sap_flexible(archivo: str, config: dict = None) -> pd.DataFrame | None:
    """
    Lee un archivo descargado de SAP (.csv, .txt, .xls) probando distintos
    delimitadores y codificaciones, limpiando encabezados antes de numerar
    columnas duplicadas para evitar variaciones entre '.1' y '_1'.
    """
    filas_a_saltar = config.get("skiprows", 3) if config else 3
    df_raw = None
    for sep in ["\t", ";", ","]:
        for enc in ["utf-16", "latin-1", "utf-8"]:
            try:
                df_raw = pd.read_csv(
                    archivo,
                    sep=sep,
                    skiprows=filas_a_saltar,
                    header=None, # No extraemos headers directamente con pandas
                    encoding=enc,
                    dtype=str,
                    quoting=3,
                    on_bad_lines="skip",
                )
                if len(df_raw.columns) > 3 and len(df_raw) > 1:
                    break
            except Exception:
                continue
        if df_raw is not None and len(df_raw.columns) > 3 and len(df_raw) > 1:
            break

    if df_raw is None or df_raw.empty or len(df_raw) < 2:
        return None

    # Extraer la fila de encabezados (fila 0) y limpiar espacios ANTES de deduplicar nombres
    encabezados_raw = df_raw.iloc[0].fillna("").astype(str).str.strip()
    indices_validos = [
        i for i, col in enumerate(encabezados_raw)
        if col and not col.startswith("Unnamed")
    ]
    if not indices_validos:
        return None

    df_temp = df_raw.iloc[1:, indices_validos].copy()
    columnas = pd.Series([encabezados_raw.iloc[i] for i in indices_validos], dtype=str)

    # Numerar columnas duplicadas siempre de forma estática y uniforme con '.1', '.2', etc.
    for dup in columnas[columnas.duplicated()].unique():
        indices = columnas[columnas == dup].index.tolist()
        for idx_count, idx in enumerate(indices):
            if idx_count > 0:
                columnas.iloc[idx] = f"{dup}.{idx_count}"

    df_temp.columns = columnas
    df_temp = df_temp.dropna(how="all").reset_index(drop=True)
    return df_temp


def _normalizar_serie_transporte(serie: pd.Series) -> pd.Series:
    """
    Estandariza los números de transporte para cruces fiables entre tablas:
    - Retira espacios y sufijos decimales (ej. '.0').
    - Quita ceros no significativos a la izquierda ('0010456' -> '10456').
    - Conserva '0' si el valor original era numérico cero.
    """
    s = serie.fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    s_lstrip = s.str.lstrip("0")
    return s_lstrip.mask((s_lstrip == "") & (s != ""), "0")


def relacionar_fbl4n_con_vt16(df_fbl4n: pd.DataFrame = None) -> pd.DataFrame | dict:
    """
    Relaciona la información de FBL4N con 'vt16.parquet' mediante la columna 'transporte'
    y consulta a VT16 por la columna '4_fch_fin_carga'.

    - Si se le proporciona un DataFrame 'df_fbl4n', realiza el cruce en memoria y lo retorna.
    - Si 'df_fbl4n' es None, lee 'fbl4n.parquet', efectúa el cruce con 'vt16.parquet',
      guarda el parquet maestro actualizado y retorna un diccionario con el resultado.
    """
    rutas_vt16 = obtener_rutas_transaccion("vt16")
    archivo_vt16 = rutas_vt16["archivo_parquet"]

    # 1. Validar existencia del parquet de VT16
    if not os.path.exists(archivo_vt16):
        print(f"  [FBL4N <-> VT16] 'vt16.parquet' no existe aun ({archivo_vt16}). Se omite cruce de '4_fch_fin_carga'.")
        if df_fbl4n is not None:
            if "4_fch_fin_carga" not in df_fbl4n.columns:
                df_fbl4n["4_fch_fin_carga"] = None
            return df_fbl4n
        return {"estatus": True, "msg": "vt16.parquet no existe aun; fbl4n sin cambios.", "cruzados": 0}

    # 2. Cargar vt16.parquet
    try:
        df_vt16 = pd.read_parquet(archivo_vt16, engine="fastparquet")
    except Exception:
        df_vt16 = pd.read_parquet(archivo_vt16)

    if "transporte" not in df_vt16.columns or "4_fch_fin_carga" not in df_vt16.columns:
        print("  [FBL4N <-> VT16] 'vt16.parquet' no contiene las columnas esperadas ('transporte', '4_fch_fin_carga').")
        if df_fbl4n is not None:
            if "4_fch_fin_carga" not in df_fbl4n.columns:
                df_fbl4n["4_fch_fin_carga"] = None
            return df_fbl4n
        return {"estatus": False, "msg": "Columnas faltantes en vt16.parquet.", "cruzados": 0}

    # 3. Preparar mapa de 'transporte' -> '4_fch_fin_carga' desde VT16
    df_vt16_sub = df_vt16.dropna(subset=["transporte"]).copy()
    df_vt16_sub["_t_norm"] = _normalizar_serie_transporte(df_vt16_sub["transporte"])
    df_vt16_sub = df_vt16_sub[df_vt16_sub["_t_norm"] != ""]
    # Priorizar registros que tengan fecha valida no nula
    df_vt16_sub = df_vt16_sub.sort_values(by="4_fch_fin_carga", na_position="first").drop_duplicates(
        subset=["_t_norm"], keep="last"
    )
    mapa_fin_carga = dict(zip(df_vt16_sub["_t_norm"], df_vt16_sub["4_fch_fin_carga"]))

    guardar_en_disco = False
    rutas_fbl4n = obtener_rutas_transaccion("fbl4n")
    archivo_fbl4n = rutas_fbl4n["archivo_parquet"]

    if df_fbl4n is None:
        if not os.path.exists(archivo_fbl4n):
            return {"estatus": False, "msg": f"No se encontro 'fbl4n.parquet' en: {archivo_fbl4n}", "cruzados": 0}
        try:
            df_fbl4n = pd.read_parquet(archivo_fbl4n, engine="fastparquet")
        except Exception:
            df_fbl4n = pd.read_parquet(archivo_fbl4n)
        guardar_en_disco = True

    # Retrocompatibilidad si el DataFrame aun tenia 'referencia'
    if "referencia" in df_fbl4n.columns and "transporte" not in df_fbl4n.columns:
        df_fbl4n.rename(columns={"referencia": "transporte"}, inplace=True)

    if "transporte" not in df_fbl4n.columns:
        print("  [FBL4N <-> VT16] 'fbl4n' no contiene la columna 'transporte' para relacionar.")
        if guardar_en_disco:
            return {"estatus": False, "msg": "Columna 'transporte' ausente en fbl4n.", "cruzados": 0}
        return df_fbl4n

    print("  -> [FBL4N <-> VT16] Consultando en vt16.parquet por '4_fch_fin_carga' mediante columna 'transporte'...")
    claves_fbl4n = _normalizar_serie_transporte(df_fbl4n["transporte"])
    fechas_vt16 = claves_fbl4n.map(mapa_fin_carga)

    if "4_fch_fin_carga" in df_fbl4n.columns:
        df_fbl4n["4_fch_fin_carga"] = fechas_vt16.combine_first(df_fbl4n["4_fch_fin_carga"])
    else:
        df_fbl4n["4_fch_fin_carga"] = fechas_vt16

    df_fbl4n["4_fch_fin_carga"] = pd.to_datetime(
        df_fbl4n["4_fch_fin_carga"],
        format="mixed",
        dayfirst=True,
        errors="coerce",
    ).dt.strftime("%Y-%m-%d")

    total_cruzados = int(df_fbl4n["4_fch_fin_carga"].notna().sum())
    print(f"  OK [FBL4N <-> VT16] Cruce completado: {total_cruzados} registros con '4_fch_fin_carga' asignada.")

    if guardar_en_disco:
        print(f"  -> Guardando 'fbl4n.parquet' con fecha fin de carga actualizada...")
        df_fbl4n.to_parquet(archivo_fbl4n, engine="fastparquet", index=False)
        return {
            "estatus": True,
            "msg": f"Cruce exitoso con VT16: {total_cruzados} registros con '4_fch_fin_carga'.",
            "cruzados": total_cruzados,
        }

    return df_fbl4n


CONFIG_FBL4N["fn_post_carga"] = relacionar_fbl4n_con_vt16


def _calcular_turno_desde_hora(serie_hora: pd.Series) -> pd.Series:
    """
    Clasifica una serie de horas ('HH:MM:SS') en los 3 turnos operativos:
      - 1er Turno: 00:00 a 06:59
      - 2do Turno: 07:00 a 14:59
      - 3er Turno: 15:00 a 23:59
    """
    horas_dt = pd.to_datetime(
        serie_hora.fillna("").astype(str).str.strip(),
        format="%H:%M:%S",
        errors="coerce",
    )
    hr = horas_dt.dt.hour
    resultado = pd.Series("sin turno", index=serie_hora.index, dtype="object")
    resultado = resultado.mask((hr >= 0) & (hr <= 6), "1er Turno")
    resultado = resultado.mask((hr >= 7) & (hr <= 14), "2do Turno")
    resultado = resultado.mask((hr >= 15) & (hr <= 23), "3er Turno")
    return resultado


def enriquecer_249(df_249: pd.DataFrame = None) -> pd.DataFrame | dict:
    """
    Paso 0 y Cruce de 249.parquet:
    1. Genera 'material_familia': cruza 'material_cod' con CATALOGO_MATERIALES['grupo']
       y usa 'gpo_mat' (F06 = envasado, F07 = granel) como respaldo si no está en el catálogo.
    2. Genera 'material_nom_corto': cruza 'material_cod' con CATALOGO_MATERIALES['desc_nom_corto']
       y usa 'material_nom' como respaldo.
    3. Cruza con 'vt16.parquet' mediante 'transporte' para traer:
       '4_fch_fin_carga', '4_hr_fin_carga', '5_hr_despacho_exp', 'modalidad' y calcular 'turno_salida'.
    """
    from catalogos import CATALOGO_MATERIALES

    guardar_en_disco = False
    rutas_249 = obtener_rutas_transaccion("249")
    archivo_249 = rutas_249["archivo_parquet"]

    if df_249 is None:
        if not os.path.exists(archivo_249):
            return {"estatus": False, "msg": f"No se encontró '249.parquet' en: {archivo_249}", "cruzados": 0}
        try:
            df_249 = pd.read_parquet(archivo_249, engine="fastparquet")
        except Exception:
            df_249 = pd.read_parquet(archivo_249)
        guardar_en_disco = True

    if df_249.empty:
        if guardar_en_disco:
            return {"estatus": True, "msg": "249.parquet vacío.", "cruzados": 0}
        return df_249

    # ------------------------------------------------------------------
    # A. PASO 0: COLUMNA 'material_familia' Y 'material_nom_corto'
    # ------------------------------------------------------------------
    mapa_grupo = {
        str(k).strip().lstrip("0"): str(v.get("grupo", "")).strip().lower()
        for k, v in CATALOGO_MATERIALES.items()
    }
    mapa_nom_corto = {
        str(k).strip().lstrip("0"): str(v.get("desc_nom_corto", "")).strip()
        for k, v in CATALOGO_MATERIALES.items()
    }

    cod_norm = (
        _normalizar_serie_transporte(df_249["material_cod"])
        if "material_cod" in df_249.columns
        else pd.Series("", index=df_249.index)
    )
    fam_cat = cod_norm.map(mapa_grupo)

    gpo_raw = (
        df_249["gpo_mat"].fillna("").astype(str).str.strip().str.upper()
        if "gpo_mat" in df_249.columns
        else pd.Series("", index=df_249.index)
    )
    fam_respaldo = gpo_raw.map({"F06": "envasado", "F07": "granel"}).fillna("otro")

    df_249["material_familia"] = fam_cat.where(fam_cat.notna() & (fam_cat != ""), fam_respaldo).str.lower()

    nom_cat = cod_norm.map(mapa_nom_corto)
    nom_respaldo = (
        df_249["material_nom"].fillna("").astype(str).str.strip()
        if "material_nom" in df_249.columns
        else pd.Series("", index=df_249.index)
    )
    df_249["material_nom_corto"] = nom_cat.where(nom_cat.notna() & (nom_cat != ""), nom_respaldo)

    # ------------------------------------------------------------------
    # B. CRUCE CON 'vt16.parquet' MEDIANTE 'transporte' (HORA / TURNO / MODALIDAD)
    # ------------------------------------------------------------------
    rutas_vt16 = obtener_rutas_transaccion("vt16")
    archivo_vt16 = rutas_vt16["archivo_parquet"]
    total_cruzados = 0

    if os.path.exists(archivo_vt16) and "transporte" in df_249.columns:
        try:
            df_vt16 = pd.read_parquet(archivo_vt16, engine="fastparquet")
        except Exception:
            try:
                df_vt16 = pd.read_parquet(archivo_vt16)
            except Exception:
                df_vt16 = pd.DataFrame()

        if not df_vt16.empty and "transporte" in df_vt16.columns:
            df_vt16_sub = df_vt16.dropna(subset=["transporte"]).copy()
            df_vt16_sub["_t_norm"] = _normalizar_serie_transporte(df_vt16_sub["transporte"])
            df_vt16_sub = df_vt16_sub[df_vt16_sub["_t_norm"] != ""]
            if "4_fch_fin_carga" in df_vt16_sub.columns:
                df_vt16_sub = df_vt16_sub.sort_values(by="4_fch_fin_carga", na_position="first")
            df_vt16_sub = df_vt16_sub.drop_duplicates(subset=["_t_norm"], keep="last")

            claves_249 = _normalizar_serie_transporte(df_249["transporte"])

            for col_vt in ["4_fch_fin_carga", "4_hr_fin_carga", "5_hr_despacho_exp", "modalidad"]:
                if col_vt in df_vt16_sub.columns:
                    mapa_col = dict(zip(df_vt16_sub["_t_norm"], df_vt16_sub[col_vt]))
                    valores_vt = claves_249.map(mapa_col)
                    if col_vt in df_249.columns:
                        df_249[col_vt] = valores_vt.combine_first(df_249[col_vt])
                    else:
                        df_249[col_vt] = valores_vt
                elif col_vt not in df_249.columns:
                    df_249[col_vt] = None

            # Determinar hora efectiva de salida: prioriza 5_hr_despacho_exp y respalda con 4_hr_fin_carga
            hr_despacho = df_249["5_hr_despacho_exp"] if "5_hr_despacho_exp" in df_249.columns else pd.Series(None, index=df_249.index)
            hr_fin_carga = df_249["4_hr_fin_carga"] if "4_hr_fin_carga" in df_249.columns else pd.Series(None, index=df_249.index)
            hr_efectiva = hr_despacho.where(hr_despacho.notna() & (hr_despacho.astype(str).str.strip() != ""), hr_fin_carga)

            df_249["turno_salida"] = _calcular_turno_desde_hora(hr_efectiva)
            total_cruzados = int((df_249["turno_salida"] != "sin turno").sum())
        else:
            for col_vt in ["4_fch_fin_carga", "4_hr_fin_carga", "5_hr_despacho_exp", "modalidad"]:
                if col_vt not in df_249.columns:
                    df_249[col_vt] = None
            if "turno_salida" not in df_249.columns:
                df_249["turno_salida"] = "sin turno"
    else:
        for col_vt in ["4_fch_fin_carga", "4_hr_fin_carga", "5_hr_despacho_exp", "modalidad"]:
            if col_vt not in df_249.columns:
                df_249[col_vt] = None
        if "turno_salida" not in df_249.columns:
            df_249["turno_salida"] = "sin turno"

    if guardar_en_disco:
        df_249.to_parquet(archivo_249, engine="fastparquet", index=False)
        return {
            "estatus": True,
            "msg": f"249.parquet enriquecido ('material_familia' y cruce VT16: {total_cruzados} con turno).",
            "cruzados": total_cruzados,
        }

    return df_249


CONFIG_249["fn_post_carga"] = enriquecer_249


def actualizar_parquet_transaccion(transaccion: str, config: dict = None) -> dict:
    """
    Motor genérico para actualizar el Parquet de cualquier transacción SAP ('249', '267', '389', etc.).
    - Valida la fecha de última modificación de cada archivo en la carpeta de la transacción.
    - Si la fecha de modificación no ha cambiado, NO vuelve a cargar el archivo.
    - Si el archivo es nuevo o fue actualizado, reemplaza sus datos previos en el Parquet maestro.
    """
    try:
        rutas = obtener_rutas_transaccion(transaccion)
        cod_tx = rutas["cod_tx"]
        carpeta_origen = rutas["carpeta_origen"]
        archivo_parquet = rutas["archivo_parquet"]
        archivo_log = rutas["archivo_log"]

        if not os.path.exists(carpeta_origen):
            return {"estatus": False, "msg": f"La carpeta de origen no existe: {carpeta_origen}"}

        # ==========================================
        # 1. MEMORIA POR FECHA DE MODIFICACIÓN
        # ==========================================
        memoria = _cargar_memoria_modificacion(archivo_log)

        patrones = [
            os.path.join(carpeta_origen, "*.csv"),
            os.path.join(carpeta_origen, "*.txt"),
            os.path.join(carpeta_origen, "*.xls"),
        ]
        todos_los_archivos = []
        for patron in patrones:
            todos_los_archivos.extend(glob.glob(patron))

        archivos_a_procesar = []
        for archivo in sorted(set(todos_los_archivos)):
            nom_base = os.path.basename(archivo)
            mtime_str = datetime.fromtimestamp(os.path.getmtime(archivo)).strftime("%Y-%m-%d %H:%M:%S")

            # Solo procesamos si el archivo no está en memoria o si su fecha de modificación cambió
            if memoria.get(nom_base) != mtime_str:
                archivos_a_procesar.append((archivo, nom_base, mtime_str))

        if not archivos_a_procesar:
            print(f"ℹ️ No hay archivos nuevos ni modificados. El Parquet {cod_tx} ya está actualizado.")
            return {"estatus": True, "msg": "Sin archivos pendientes por actualizar.", "procesados": 0}

        print(f"📦 [Parquet {cod_tx}] Se detectaron {len(archivos_a_procesar)} archivo(s) nuevo(s) o modificado(s)...")

        # ==========================================
        # 2. LECTURA Y LIMPIEZA DE ARCHIVOS NUEVOS/MODIFICADOS
        # ==========================================
        config = config or {}
        columnas_fijas = config.get("columnas_fijas")
        columna_ancla = config.get("columna_ancla")
        llaves_dedup = config.get("llaves_dedup", [])

        nuevos_dfs = []
        nombres_actualizados = {}

        for ruta_arch, nom_base, mtime_str in archivos_a_procesar:
            print(f"  -> Leyendo: {nom_base} (Modificado: {mtime_str})")
            df_temp = _leer_archivo_sap_flexible(ruta_arch, config=config)

            if df_temp is None or df_temp.empty:
                print(f"⚠️ No se pudo parsear adecuadamente: {nom_base}")
                continue

            # print(f"  -> Columnas en {nom_base} ({len(df_temp.columns)}): {list(df_temp.columns)}")

            # 1. Asignar nombres configurados en orden posicional (sin diccionarios)
            if columnas_fijas:
                if len(df_temp.columns) == len(columnas_fijas):
                    df_temp.columns = list(columnas_fijas)
                elif "columnas_fijas_alt" in config and len(df_temp.columns) in config["columnas_fijas_alt"]:
                    alt_cols = config["columnas_fijas_alt"][len(df_temp.columns)]
                    df_temp.columns = list(alt_cols)
                    # Completar columnas faltantes con None para mantener homogeneidad
                    for col_faltante in columnas_fijas:
                        if col_faltante not in df_temp.columns:
                            df_temp[col_faltante] = None
                else:
                    print(
                        f"⚠️ Advertencia en {nom_base}: tiene {len(df_temp.columns)} columnas, "
                        f"pero 'columnas_fijas' define {len(columnas_fijas)}. "
                        f"Se conservan nombres originales."
                    )

            # Retrocompatibilidad: estandarizar columna 'referencia' a 'transporte'
            if "referencia" in df_temp.columns and "transporte" not in df_temp.columns:
                df_temp.rename(columns={"referencia": "transporte"}, inplace=True)

            # 2. Filtrado estricto por columna ancla o primera columna para omitir subtotales/filas vacías
            if columna_ancla:
                df_temp = _filtrar_columna_ancla(df_temp, columna_ancla)
                if df_temp.empty:
                    print(f"⚠️ {nom_base}: sin registros válidos en columna ancla '{columna_ancla}'. Se omite.")
                    continue
            else:
                primera_col = df_temp.columns[0]
                df_temp = df_temp.dropna(subset=[primera_col])
                val_p = df_temp[primera_col].astype(str).str.strip().str.lower()
                df_temp = df_temp[~val_p.isin(["", "nan", "none", "null"])].copy()

            # Guardamos trazabilidad del archivo origen para poder reemplazarlo limpiamente si se re-descarga
            df_temp["_archivo_origen"] = nom_base

            nuevos_dfs.append(df_temp)
            nombres_actualizados[nom_base] = mtime_str

        if not nuevos_dfs:
            return {"estatus": False, "msg": f"No se extrajeron registros válidos para la transacción {cod_tx}."}

        # ==========================================
        # 3. CARGA DE HISTORIAL MAESTRO Y REEMPLAZO DE ARCHIVOS MODIFICADOS
        # ==========================================
        lista_dataframes = []
        if os.path.exists(archivo_parquet):
            print(f"🔄 Cargando Parquet maestro existente ({cod_tx}.parquet)...")
            try:
                df_master = pd.read_parquet(archivo_parquet, engine="fastparquet")
                if "_archivo_origen" in df_master.columns:
                    # Quitamos del maestro los registros viejos de los archivos que acabamos de volver a leer
                    df_master = df_master[~df_master["_archivo_origen"].isin(nombres_actualizados.keys())]
                # Retrocompatibilidad: estandarizar columna 'referencia' a 'transporte'
                if "referencia" in df_master.columns and "transporte" not in df_master.columns:
                    df_master.rename(columns={"referencia": "transporte"}, inplace=True)
                if columnas_fijas:
                    cols_extra = config.get("columnas_extra", [])
                    cols_permitidas = [
                        c for c in list(columnas_fijas) + list(cols_extra) + ["_archivo_origen"]
                        if c in df_master.columns
                    ]
                    df_master = df_master[cols_permitidas]
                if columna_ancla:
                    df_master = _filtrar_columna_ancla(df_master, columna_ancla)
                lista_dataframes.append(df_master)
            except Exception as e_pq:
                print(f"⚠️ Error al leer Parquet maestro (se reconstruirá): {e_pq}")

        lista_dataframes.extend(nuevos_dfs)

        # ==========================================
        # 4. CONSOLIDACIÓN Y TIPIFICACIÓN
        # ==========================================
        print("🔗 Consolidando registros...")
        df_final = pd.concat(lista_dataframes, ignore_index=True)

        # Asegurar únicamente las columnas esperadas (descartando cualquier columna huérfana de parquets viejos)
        if columnas_fijas:
            cols_extra = config.get("columnas_extra", [])
            cols_finales = [
                c for c in list(columnas_fijas) + list(cols_extra) + ["_archivo_origen"]
                if c in df_final.columns
            ]
            df_final = df_final[cols_finales]

        # Eliminar columnas explícitamente descartadas (ej. en FBL4N 'St', 'fch_pago')
        for c_drop in config.get("cols_drop", []):
            if c_drop in df_final.columns:
                df_final = df_final.drop(columns=[c_drop])

        # Filtrado de garantía de la columna ancla en df_final (elimina cualquier blanco/nulo restante)
        if columna_ancla:
            filas_antes = len(df_final)
            df_final = _filtrar_columna_ancla(df_final, columna_ancla)
            filas_despues = len(df_final)
            if filas_antes != filas_despues:
                print(f"🧹 Se purgaron {filas_antes - filas_despues} fila(s) con '{columna_ancla}' vacía o nula.")

        if llaves_dedup:
            llaves_presentes = [c for c in llaves_dedup if c in df_final.columns]
            if llaves_presentes:
                df_final = df_final.drop_duplicates(subset=llaves_presentes, keep="last")

        # Hook de post-procesamiento tras cargar y consolidar archivos (ej. relacionar FBL4N con VT16)
        fn_post = config.get("fn_post_carga")
        if callable(fn_post):
            df_final = fn_post(df_final)

        # Int64
        for col in config.get("cols_int", []):
            if col in df_final.columns:
                df_final[col] = pd.to_numeric(df_final[col], errors="coerce").round().astype("Int64")

        # Float
        for col in config.get("cols_float", []):
            if col in df_final.columns:
                df_final[col] = pd.to_numeric(
                    df_final[col].astype(str).str.replace(",", "").str.strip(),
                    errors="coerce",
                )

        # Date (YYYY-MM-DD)
        for col in config.get("cols_date", []):
            if col in df_final.columns:
                df_final[col] = pd.to_datetime(
                    df_final[col],
                    format="mixed",
                    dayfirst=True,
                    errors="coerce",
                ).dt.strftime("%Y-%m-%d")

        # Time (HH:MM:SS)
        for col in config.get("cols_time", []):
            if col in df_final.columns:
                df_final[col] = pd.to_datetime(
                    df_final[col].astype(str).str.strip(),
                    format="%H:%M:%S",
                    errors="coerce",
                ).dt.strftime("%H:%M:%S")

        # ==========================================
        # 5. GUARDADO FINAL Y ACTUALIZACIÓN DE MEMORIA
        # ==========================================
        print(f"💾 Escribiendo Parquet maestro en: {archivo_parquet}...")
        df_final.to_parquet(archivo_parquet, engine="fastparquet", index=False)

        memoria.update(nombres_actualizados)
        _guardar_memoria_modificacion(archivo_log, memoria)

        print(f"✅ Parquet {cod_tx} actualizado con éxito ({len(nombres_actualizados)} archivo(s), {len(df_final)} filas totales).")
        return {
            "estatus": True,
            "msg": f"Se procesaron {len(nombres_actualizados)} archivo(s). Total filas: {len(df_final)}.",
            "procesados": len(nombres_actualizados),
        }

    except Exception as e:
        print(f"❌ Error durante la generación del Parquet ({transaccion}): {e}")
        return {"estatus": False, "msg": str(e)}


# ==============================================================================
# FUNCIONES DE ENTRADA POR TRANSACCIÓN
# ==============================================================================


def actualizar_parquet_zsdmx249() -> dict:
    """
    Lee todos los archivos de la carpeta zsdmx249, valida su fecha de actualización
    y consolida incrementalmente en '249.parquet'.
    Garantiza que la columna 'material_familia' y el cruce con VT16 estén sincronizados.
    """
    res = actualizar_parquet_transaccion("249", config=CONFIG_249)
    if not res.get("estatus", False):
        return res

    # Si no hubo archivos nuevos pero el parquet maestro ya existe, asegurar enriquecimiento
    if res.get("procesados", 0) == 0:
        res_enr = enriquecer_249()
        if isinstance(res_enr, dict) and res_enr.get("estatus"):
            res["msg"] += f" | {res_enr.get('msg', '')}"

    return res


def obtener_df_249(codigos_planta: list = None, fecha_sm: str = None) -> pd.DataFrame:
    """
    Lee '249.parquet', asegura las columnas enriquecidas ('material_familia', 'material_nom_corto',
    'turno_salida', 'modalidad') y filtra opcionalmente por los códigos de centro de la planta
    y por la fecha de salida de mercancía ('YYYY-MM-DD').
    """
    rutas_249 = obtener_rutas_transaccion("249")
    archivo_249 = rutas_249["archivo_parquet"]

    if not os.path.exists(archivo_249):
        return pd.DataFrame()

    try:
        df = pd.read_parquet(archivo_249, engine="fastparquet")
    except Exception:
        try:
            df = pd.read_parquet(archivo_249)
        except Exception as e:
            print(f"⚠️ Error leyendo 249.parquet: {e}")
            return pd.DataFrame()

    if df.empty:
        return df

    # Garantizar en memoria el enriquecimiento con catálogo y VT16 si faltara alguna columna
    cols_requeridas = {"material_familia", "material_nom_corto", "turno_salida", "modalidad"}
    if not cols_requeridas.issubset(set(df.columns)):
        df = enriquecer_249(df)

    df["ton"] = pd.to_numeric(df.get("ton", 0.0), errors="coerce").fillna(0.0)
    df["c_exp"] = df.get("c_exp", "").fillna("").astype(str).str.strip().str.upper()

    if codigos_planta:
        cods_upper = [str(c).strip().upper() for c in codigos_planta if str(c).strip()]
        if cods_upper:
            df = df[df["c_exp"].isin(cods_upper)].copy()

    if fecha_sm and "fch_sm_real" in df.columns:
        df = df[df["fch_sm_real"].fillna("").astype(str).str.strip() == str(fecha_sm).strip()].copy()

    return df.reset_index(drop=True)


def obtener_oferta_plantas(ruta_base_drive: str = None, limite_minutos: int = 999) -> dict:
    """
    Genera y actualiza 'oferta_planta.parquet' siguiendo el flujo data -> parquet -> gui:
    1. Valida mediante _requiere_descarga(archivo_parquet, limite_minutos=999) si el parquet
       necesita actualizarse (una vez por día).
    2. Si requiere actualización, lee '{ruta_base_drive}\\oferta_plantas\\oferta_plantas.xlsx'
       (hoja 'oferta_plantas').
    3. Ejecuta las tareas de limpieza de datos (semana, planta, c_exp, mat_codigo_norm,
       mat_nombre_norm, ton_of).
    4. Cruza información con CATALOGO_PLANTAS (turnos_operativos, nombre_centro, codigos)
       y CATALOGO_MATERIALES (material_familia, mat_nom_corto).
    5. Guarda la tabla limpia y enriquecida en 'oferta_planta.parquet' (sin cálculos de agregación).
    """
    from catalogos import CATALOGO_PLANTAS, CATALOGO_MATERIALES
    from manager_descargas import _requiere_descarga

    rutas_oferta = obtener_rutas_transaccion("oferta_planta")
    archivo_parquet = rutas_oferta["archivo_parquet"]

    if not ruta_base_drive:
        anno = str(datetime.now().year)
        ruta_base_drive = os.path.join(rutas_oferta["carpeta_general"], anno)

    ruta_excel = os.path.join(ruta_base_drive, "oferta_plantas", "oferta_plantas.xlsx")

    # 1. Analizar si realmente requiere actualizar el parquet (por defecto limite_minutos=999 -> 1 vez al día)
    if not _requiere_descarga(archivo_parquet, limite_minutos=limite_minutos):
        return {
            "estatus": True,
            "msg": "oferta_planta.parquet vigente (actualizado hoy).",
            "archivo_parquet": archivo_parquet,
            "actualizado": False,
        }

    if not os.path.exists(ruta_excel):
        msg_err = f"No se encontró el archivo origen en: {ruta_excel}"
        print(f"⚠️ [oferta_planta.parquet] {msg_err}")
        return {
            "estatus": os.path.exists(archivo_parquet),
            "msg": msg_err,
            "archivo_parquet": archivo_parquet,
            "actualizado": False,
        }

    # 2. Lectura del Excel origen
    try:
        try:
            df_raw = pd.read_excel(ruta_excel, sheet_name="oferta_plantas", engine="openpyxl")
        except Exception:
            df_raw = pd.read_excel(ruta_excel, sheet_name=0, engine="openpyxl")
    except Exception as e:
        msg_err = f"Error leyendo '{ruta_excel}': {e}"
        print(f"⚠️ [oferta_planta.parquet] {msg_err}")
        return {
            "estatus": os.path.exists(archivo_parquet),
            "msg": msg_err,
            "archivo_parquet": archivo_parquet,
            "actualizado": False,
        }

    if df_raw is None or df_raw.empty:
        return {
            "estatus": False,
            "msg": "El archivo oferta_plantas.xlsx está vacío.",
            "archivo_parquet": archivo_parquet,
            "actualizado": False,
        }

    # 3. Tareas de limpieza de datos
    df = df_raw.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    cols_esperadas = {"semana", "planta", "c_exp", "mat_codigo", "mat_nombre", "ton_of"}
    if not cols_esperadas.issubset(set(df.columns)):
        msg_err = f"Columnas inesperadas en oferta_plantas.xlsx: {list(df.columns)}"
        print(f"⚠️ [oferta_planta.parquet] {msg_err}")
        return {
            "estatus": False,
            "msg": msg_err,
            "archivo_parquet": archivo_parquet,
            "actualizado": False,
        }

    df["semana"] = pd.to_numeric(df["semana"], errors="coerce")
    df = df.dropna(subset=["semana"]).copy()
    df["semana"] = df["semana"].astype(int)

    df["planta"] = df["planta"].fillna("").astype(str).str.strip()
    df["c_exp"] = df["c_exp"].fillna("").astype(str).str.strip().str.upper()

    df["mat_codigo_norm"] = (
        df["mat_codigo"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.lstrip("0")
    )
    df["mat_nombre_norm"] = df["mat_nombre"].fillna("").astype(str).str.strip()

    ton_limpio = (
        df["ton_of"]
        .fillna("0")
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.strip()
    )
    ton_limpio = ton_limpio.replace({"-": "0", "": "0", "nan": "0", "None": "0"})
    df["ton_of"] = pd.to_numeric(ton_limpio, errors="coerce").fillna(0.0)

    # 4. Cruce de información con CATALOGO_PLANTAS (turnos_operativos, nombre_centro, codigos)
    mapa_ce_info = {}
    mapa_centro_info = {}
    for nom_planta_gui, info_p in CATALOGO_PLANTAS.items():
        cods_list = [str(c).strip().upper() for c in info_p.get("codigos", []) if str(c).strip()]
        cods_str = ",".join(cods_list)
        nom_centro = str(info_p.get("nombre_centro", "")).strip()
        turnos_op = int(info_p.get("turnos_operativos", 3) or 3)
        registro_info = {
            "planta_gui_nombre": nom_planta_gui,
            "nombre_centro": nom_centro,
            "turnos_operativos": turnos_op,
            "codigos": cods_str,
        }
        for c_code in cods_list:
            mapa_ce_info[c_code] = registro_info
        if nom_centro:
            mapa_centro_info[nom_centro.upper()] = registro_info

    nombres_centro_col = []
    turnos_op_col = []
    codigos_col = []
    planta_gui_col = []

    for _, row in df.iterrows():
        ce_val = row["c_exp"]
        pl_val = row["planta"].upper()
        info_match = mapa_ce_info.get(ce_val) or mapa_centro_info.get(pl_val) or {}
        nombres_centro_col.append(info_match.get("nombre_centro", row["planta"]))
        turnos_op_col.append(int(info_match.get("turnos_operativos", 3)))
        codigos_col.append(info_match.get("codigos", ce_val))
        planta_gui_col.append(info_match.get("planta_gui_nombre", ""))

    df["nombre_centro"] = nombres_centro_col
    df["turnos_operativos"] = pd.Series(turnos_op_col, index=df.index, dtype="int64")
    df["codigos"] = codigos_col
    df["planta_gui_nombre"] = planta_gui_col

    # 5. Cruce con CATALOGO_MATERIALES para material_familia y mat_nom_corto
    mapa_grupo_cat = {
        str(k).strip().lstrip("0"): str(v.get("grupo", "")).strip().lower()
        for k, v in CATALOGO_MATERIALES.items()
    }
    mapa_nom_cat = {
        str(k).strip().lstrip("0"): str(v.get("desc_nom_corto", "")).strip()
        for k, v in CATALOGO_MATERIALES.items()
    }

    familias_col = []
    nom_corto_col = []
    for _, row in df.iterrows():
        cod_m = row["mat_codigo_norm"]
        nom_m_upper = row["mat_nombre_norm"].upper()

        fam = mapa_grupo_cat.get(cod_m, "")
        if not fam:
            fam = "granel" if "GRANEL" in nom_m_upper else "envasado"
        familias_col.append(fam.lower())

        nom_c = mapa_nom_cat.get(cod_m, "")
        if not nom_c:
            nom_c = row["mat_nombre_norm"] or cod_m
        nom_corto_col.append(nom_c)

    df["material_familia"] = familias_col
    df["mat_nom_corto"] = nom_corto_col

    # 6. Guardar en oferta_planta.parquet
    try:
        df.to_parquet(archivo_parquet, engine="fastparquet", index=False)
        print(f"✅ [oferta_planta.parquet] Actualizado correctamente ({len(df)} registros) en: {archivo_parquet}")
        return {
            "estatus": True,
            "msg": f"oferta_planta.parquet actualizado ({len(df)} filas).",
            "archivo_parquet": archivo_parquet,
            "actualizado": True,
        }
    except Exception as e:
        msg_err = f"Error guardando oferta_planta.parquet: {e}"
        print(f"❌ [oferta_planta.parquet] {msg_err}")
        return {
            "estatus": False,
            "msg": msg_err,
            "archivo_parquet": archivo_parquet,
            "actualizado": False,
        }


def actualizar_parquet_zsdmx267() -> dict:
    """
    Lee todos los archivos de la carpeta zsdmx267, valida su fecha de actualización
    y consolida incrementalmente en '267.parquet'.
    """
    return actualizar_parquet_transaccion("267", config=CONFIG_267)


def actualizar_parquet_vt16() -> dict:
    """
    Lee todos los archivos de la carpeta vt16, valida su fecha de actualización
    y consolida incrementalmente en 'vt16.parquet'.
    """
    return actualizar_parquet_transaccion("vt16", config=CONFIG_VT16)


def actualizar_parquet_fbl4n() -> dict:
    """
    Lee todos los archivos de la carpeta fbl4n, valida su fecha de actualización
    y consolida incrementalmente en 'fbl4n.parquet'.
    Cuando termina de cargar los archivos, realiza una llamada a 'vt16.parquet',
    relaciona la columna 'transporte' y consulta a VT16 por '4_fch_fin_carga'.
    """
    res = actualizar_parquet_transaccion("fbl4n", config=CONFIG_FBL4N)
    if not res.get("estatus", False):
        return res

    # Si no hubo archivos nuevos por procesar en fbl4n pero el parquet maestro ya existe,
    # ejecutamos la llamada a vt16.parquet para mantener sincronizada '4_fch_fin_carga'
    if res.get("procesados", 0) == 0:
        res_cruce = relacionar_fbl4n_con_vt16()
        if res_cruce.get("estatus") and res_cruce.get("cruzados", 0) > 0:
            res["msg"] += f" | Sincronizado con VT16: {res_cruce['cruzados']} registros con '4_fch_fin_carga'."

    return res


if __name__ == "__main__":
    actualizar_parquet_zsdmx249()
    actualizar_parquet_zsdmx267()
    actualizar_parquet_vt16()
    actualizar_parquet_fbl4n()
    print("Prueba final. Todos los Parquets se han actualizado correctamente.")
