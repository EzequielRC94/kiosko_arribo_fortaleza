# parquets.py
from logging import config
import os
import glob
from datetime import datetime
import pandas as pd


# ==============================================================================
# CONFIGURACIÓN DE ESQUEMAS Y TRANSFORMACIONES POR TRANSACCIÓN
# ==============================================================================

CONFIG_267 = {
    "columna_ancla": "entrega",
    "llaves_dedup": ["entrega", "transporte", "gasto_transporte"],
    "skinprows": 3, # Número de filas a saltar antes de leer encabezados (para zsdmx267)
    # Orden estático de las 19 columnas del layout /0.TRAN_REP en ZSDMX267
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
    "cols_int": [],
    "cols_float": [
        "tarifa_normal", "tarifa_total", "factura_valor"
    ],
    "cols_date": [
        "fch_creacion_gasto"
    ],
    "cols_time": [],
}

CONFIG_249 = {
    "columna_ancla": "entrega", 
    "llaves_dedup": ["entrega", "pedido_pos"], #llave para eliminar duplicados
    #Ezequiel del futuro, falta agregar a la transaccion 249 la columnas:
    #pos_entrega (tenemos la posicion del pedido, peró no de la entrega)
    #puesto_expedicion (modalidad: "entregado/retirado")
    "columnas_fijas": [
        "c_exp",                     # 1. psex / centro expedicion
        "entrega",                   # 2. entrega
        "transporte",                # 3. talón de e / Transporte
        "material_nom",              # 4. denominación / Nombre del material
        "material_cod",              # 5. material / Código de material
        "ton",                       # 6. ctd.entr. / cantidad de entrega (toneladas)
        "gpo_mat",                   # 7. grm2 / Grupo de material 2
        "clte_solicitante",          # 8. solic. / Cliente solicitante            
        "clte_nombre",               # 9. nombre 1 / Nombre del cliente
        "clte_destinatario",         # 10. destinat. / Destinatario
        "clte_nombre_destinatario",  # 11. nombre destinatario / Nombre del destinatario
        "pedido",                    # 12. pedido / Número de pedido
        "pedido_pos",                # 13. pos. / Posición de pedido
        "fch_sm_real",               # 14. fe.sm real / Fecha salida mercancias real
        "ent_crea",                  # 15. creador en / Quien creó la entrega
        "ej_comercial",              # 16. vendedor / Vendedor
        "ej_nombre_completo",        # 17. nombre completo / Nombre completo del vendedor
        "peso_neto",                 # 18. entr peso / Peso neto
        "peso_bruto",                # 19. entr peso.1 / Peso bruto
        "folio_manual",              # 20. folio manu / Folio manual
        "factura",                   # 21. factura / Factura
        "fch_creacion_entrega",      # 22. fe.creació / Fecha de creación de la entrega
        "fch_cita_entrega",          # 23. fe.entrega / Fecha de cita de entrega
    ],

    "cols_int": [],
    "cols_float": ["ton", "peso_neto", "peso_bruto"],
    "cols_date": ["fch_sm_real", "fch_creacion_entrega", "fch_cita_entrega"],
    "cols_time": [],
}

CONFIG_VT16 = {
    "columna_ancla": "transporte",
    "llaves_dedup": ["transporte"],
    "columnas_fijas": [],       # Configurar aquí la lista ordenada de columnas del layout /HORARIOS_FZ
    "cols_int": ["destino_km"],
    "cols_float": [
        "ctd_facturada", "peso_bruto", "peso_neto"
    ],
    "cols_date": [
        "fch_creacion_entrega", "0_fch_creacion_transporte",
        "1_fch_planificacion", "2_fch_bascula_entrada", "3_fch_inicio_carga",
        "4_fch_fin_carga", "5_fch_despacho_exp", "6_fch_inicio_transporte",
        "7_fch_fin_transporte"
    ],
    "cols_time": [
        "hora_creacion_entrega", "0_hr_creacion_transporte", "1_hr_planificacion",
        "2_hr_bascula_entrada", "3_hr_inicio_carga", "4_hr_fin_carga",
        "5_hr_despacho_exp", "6_hr_inicio_transporte", "7_hr_fin_transporte"
    ],
}
CONFIG_vt16 = CONFIG_VT16   



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

    os.makedirs(os.path.dirname(archivo_parquet), exist_ok=True)
    os.makedirs(os.path.dirname(archivo_log), exist_ok=True)

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


def _leer_archivo_sap_flexible(archivo: str) -> pd.DataFrame | None:
    """
    Lee un archivo descargado de SAP (.csv, .txt, .xls) probando distintos
    delimitadores y codificaciones, limpiando encabezados antes de numerar
    columnas duplicadas para evitar variaciones entre '.1' y '_1'.
    """
    _skinprows = config.get("skiprows", 3) if config else 3
    df_raw = None
    for sep in ["\t", ";", ","]:
        for enc in ["utf-16", "latin-1", "utf-8"]:
            try:
                df_raw = pd.read_csv(
                    archivo,
                    sep=sep,
                    skiprows=_skinprows,
                    header=None, #No extraemos headers
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
            df_temp = _leer_archivo_sap_flexible(ruta_arch)

            if df_temp is None or df_temp.empty:
                print(f"⚠️ No se pudo parsear adecuadamente: {nom_base}")
                continue

            print(f"  -> Columnas en {nom_base} ({len(df_temp.columns)}): {list(df_temp.columns)}")

            # 1. Asignar nombres configurados en orden posicional (sin diccionarios)
            if columnas_fijas:
                if len(df_temp.columns) == len(columnas_fijas):
                    df_temp.columns = list(columnas_fijas)
                else:
                    print(
                        f"⚠️ Advertencia en {nom_base}: tiene {len(df_temp.columns)} columnas, "
                        f"pero 'columnas_fijas' define {len(columnas_fijas)}. "
                        f"Se conservan nombres originales."
                    )

            # 2. Filtrado por columna ancla o primera columna para omitir subtotales/filas vacías
            if columna_ancla:
                cols_ancla = [c for c in df_temp.columns if columna_ancla.lower() in c.lower()]
                if not cols_ancla:
                    print(f"⚠️ Advertencia: No se encontró columna ancla '{columna_ancla}' en {nom_base}. Se omite.")
                    continue
                col_ref = cols_ancla[0]
                df_temp = df_temp.dropna(subset=[col_ref])
                df_temp = df_temp[df_temp[col_ref].astype(str).str.strip() != ""]
            else:
                primera_col = df_temp.columns[0]
                df_temp = df_temp.dropna(subset=[primera_col])
                df_temp = df_temp[df_temp[primera_col].astype(str).str.strip() != ""]

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
                if columnas_fijas:
                    cols_permitidas = [c for c in list(columnas_fijas) + ["_archivo_origen"] if c in df_master.columns]
                    df_master = df_master[cols_permitidas]
                lista_dataframes.append(df_master)
            except Exception as e_pq:
                print(f"⚠️ Error al leer Parquet maestro (se reconstruirá): {e_pq}")

        lista_dataframes.extend(nuevos_dfs)

        # ==========================================
        # 4. CONSOLIDACIÓN Y TIPIFICACIÓN
        # ==========================================
        print("🔗 Consolidando registros...")
        df_final = pd.concat(lista_dataframes, ignore_index=True)

        if llaves_dedup:
            llaves_presentes = [c for c in llaves_dedup if c in df_final.columns]
            if llaves_presentes:
                df_final = df_final.drop_duplicates(subset=llaves_presentes, keep="last")

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
                    df_final[col].astype(str).str.strip(),
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
    """
    return actualizar_parquet_transaccion("249", config=CONFIG_249)


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


if __name__ == "__main__":
    actualizar_parquet_zsdmx249()
    #actualizar_parquet_zsdmx267()
    #actualizar_parquet_vt16()
