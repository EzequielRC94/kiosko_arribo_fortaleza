# parquets.py
import os
import glob
from datetime import datetime
import pandas as pd


# ==============================================================================
# CONFIGURACIÓN DE ESQUEMAS Y TRANSFORMACIONES POR TRANSACCIÓN
# ==============================================================================

CONFIG_267 = {
    "columna_ancla": "Entrega",
    "llaves_dedup": ["entrega", "entrega_pos", "transporte"],
    "diccionario_nombres": {
        # --- IDENTIFICADORES Y RUTAS ---
        "PtPlaTrnsp": "c_exp",
        "PtoPlanifTransp": "c_exp",
        "Entrega": "entrega",
        "Transporte": "transporte",
        "Nº de transporte": "transporte",
        "Gasto de transporte": "gasto_transporte",
        "RutaTransp": "ruta_id",
        "Nombre de ruta": "ruta_nombre",
        "Pob. Dest.": "destino_poblacion",
        "RegionDest": "destino_region",
        "Region Dest.": "destino_region",
        "Tarif norm": "tarifa_normal",
        "Tarifa normal": "tarifa_normal",
        "Valor neto": "valor_neto",
        "Distancia": "destino_km",
        "Kilometraje": "destino_km",

        # --- TRANSPORTISTAS ---
        "Cant.Fact.": "ctd_facturada",
        "Cantidad Facturada": "ctd_facturada",
        "AgServTran": "transp_num_proveedor",
        "Agente servicios": "transp_num_proveedor",
        "Nombre transportista": "transp_nombre",
        "Cl.exped.": "clase_expedicion",
        "Clase expedición": "clase_expedicion",
        "Denomin.": "clase_exp_denominacion",
        "NoPlat": "signatura",
        "Signatura": "signatura",
        "IDTrackTransp": "id_track",
        "Plac. Rem.": "placas_remision",
        "Placas Remisión": "placas_remision",
        "Texto adic.2": "operador_transporte",
        "Chofer Remisión": "operador_remision",

        # --- CLIENTES Y MATERIALES ---
        "Nombre.1": "cliente_nombre",
        "Nombre.2": "destinatario_nombre",
        "Solic.": "cliente_numero",
        "Solicitante": "cliente_numero",
        "Destinat.": "destinatario_numero",
        "Material": "material_numero",
        "Denominación": "material_denominacion",
        "Peso neto": "peso_neto",
        "Neto_1": "peso_neto",
        "Peso total": "peso_bruto",
        "Peso bruto": "peso_bruto",

        # --- PEDIDOS Y ENTREGAS ---
        "Doc.modelo": "pedido",
        "F. Manual": "folio_manual",
        "Folio Manual": "folio_manual",
        "PosEnt": "entrega_pos",
        "Creado el": "fch_creacion_entrega",
        "Fecha CreRem": "fch_creacion_entrega",
        "Hora": "hora_creacion_entrega",
        "Hora CreRem": "hora_creacion_entrega",

        # --- GASTOS Y FINANZAS ---
        "Fecha creación gasto": "fch_creacion_gasto",
        "Estatus de flete": "gasto_estatus",
        "Orden de Compra": "gasto_oc",
        "Ce.coste": "gasto_ceco",
        "Centro de coste": "gasto_ceco",
        "División": "gasto_division",
        "División Descripción": "gasto_division_nombre",
        "Doc.facturación": "factura_doc",
        "Valor Factura": "factura_valor",
        "Neto.1": "factura_valor",
        "Peso Factura": "factura_peso",
        "Neto.2": "factura_peso",

        # --- FECHAS LOGÍSTICAS ---
        "FechaCrea": "0_fch_creacion_transporte",
        "FinPlanif": "1_fch_planificacion",
        "Fin planificación": "1_fch_planificacion",
        "FeActReg": "2_fch_bascula_entrada",
        "Fe.actual registro": "2_fch_bascula_entrada",
        "InActCarga": "3_fch_inicio_carga",
        "Inicio actual carga": "3_fch_inicio_carga",
        "FinActCarg": "4_fch_fin_carga",
        "Fin actual carga": "4_fch_fin_carga",
        "FeActDpExp": "5_fch_despacho_exp",
        "Fe.act.desp.exped.": "5_fch_despacho_exp",
        "InActTrans": "6_fch_inicio_transporte",
        "Inic.actual transp.": "6_fch_inicio_transporte",
        "FinActTran": "7_fch_fin_transporte",
        "Fin act.transporte": "7_fch_fin_transporte",

        # --- HORAS LOGÍSTICAS ---
        "Hora.1": "0_hr_creacion_transporte",
        "Hora CreTrp": "0_hr_creacion_transporte",
        "FinPlanif.1": "1_hr_planificacion",
        "Hora final planif.": "1_hr_planificacion",
        "HoraActReg": "2_hr_bascula_entrada",
        "Hora actual registro": "2_hr_bascula_entrada",
        "HrActInCga": "3_hr_inicio_carga",
        "Hora act.inic.carga": "3_hr_inicio_carga",
        "HrAcFinCga": "4_hr_fin_carga",
        "Hora act.fin carga": "4_hr_fin_carga",
        "HoraActDeE": "5_hr_despacho_exp",
        "Hora act.desp.exp.": "5_hr_despacho_exp",
        "HrAcInTran": "6_hr_inicio_transporte",
        "Hora act.in.transp.": "6_hr_inicio_transporte",
        "HrAcFiTrsp": "7_hr_fin_transporte",
        "Hora act.fin transp.": "7_hr_fin_transporte",

        # --- TRANSPORTE EXTRA ---
        "Cl.transp.": "clase_transporte",
        "Clase de transporte": "clase_transporte",
        "Descripción": "clase_transp_desc",
        "Denominac": "modalidad",
        "Autor": "transporte_autor",
    },
    "cols_int": ["destino_km"],
    "cols_float": [
        "ctd_facturada", "tarifa_normal", "valor_neto",
        "peso_bruto", "peso_neto", "factura_valor", "factura_peso"
    ],
    "cols_date": [
        "fch_creacion_entrega", "fch_creacion_gasto", "0_fch_creacion_transporte",
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

CONFIG_249 = {
    "columna_ancla": None,      # Acepta cualquier columna válida del reporte ZSDMX249
    "llaves_dedup": [],         # Reemplaza por archivo actualizado (_archivo_origen)
    "diccionario_nombres": None, # Conserva todas las columnas del layout /ZQL_REPORT
    "cols_int": [],
    "cols_float": [],
    "cols_date": [],
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
    nombre_carpeta_sap = f"zsdmx{cod_tx}"

    perfil_usuario = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    carpeta_general = os.path.join(perfil_usuario, "Elementia S. A", "kiosko logistica cem - Documentos")
    anno = str(datetime.now().year)

    carpeta_origen = os.path.join(carpeta_general, anno, nombre_carpeta_sap)
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
    delimitadores y codificaciones, limpiando encabezados y columnas duplicadas.
    """
    df_temp = None
    for sep in ["\t", ";", ","]:
        for enc in ["utf-16", "latin-1", "utf-8"]:
            try:
                df_temp = pd.read_csv(
                    archivo,
                    sep=sep,
                    skiprows=3,
                    encoding=enc,
                    dtype=str,
                    quoting=3,
                    on_bad_lines="skip",
                )
                if len(df_temp.columns) > 3:
                    break
            except Exception:
                continue
        if df_temp is not None and len(df_temp.columns) > 3:
            break

    if df_temp is None or df_temp.empty:
        return None

    # Limpiar espacios invisibles de encabezados y descartar columnas totalmente vacías ("Unnamed")
    df_temp.columns = df_temp.columns.str.strip()
    cols_validas = [c for c in df_temp.columns if c and not c.startswith("Unnamed")]
    df_temp = df_temp[cols_validas]

    # Reparar nombres de columnas duplicadas
    columnas = pd.Series(df_temp.columns)
    for dup in columnas[columnas.duplicated()].unique():
        indices = columnas[columnas == dup].index.tolist()
        for idx_count, idx in enumerate(indices):
            if idx_count > 0:
                columnas[idx] = f"{dup}_{idx_count}"
    df_temp.columns = columnas

    # Eliminar filas que sean líneas separadoras de SAP (ej. '---' o vacías)
    df_temp = df_temp.dropna(how="all")
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
            os.path.join(carpeta_origen, "*.xls*"),
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
        diccionario_nombres = config.get("diccionario_nombres")
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

            # Validar columna ancla si está configurada (ej. 'Entrega')
            if columna_ancla:
                cols_ancla = [c for c in df_temp.columns if columna_ancla.lower() in c.lower()]
                if not cols_ancla:
                    print(f"⚠️ Advertencia: No se encontró columna '{columna_ancla}' en {nom_base}. Se omite.")
                    continue
                col_ref = cols_ancla[0]
                df_temp = df_temp.dropna(subset=[col_ref])
                df_temp = df_temp[df_temp[col_ref].astype(str).str.strip() != ""]
            else:
                # Si no hay columna ancla fija, tomamos la primera columna como referencia para filtrar filas vacías/subtotales
                primera_col = df_temp.columns[0]
                df_temp = df_temp.dropna(subset=[primera_col])
                df_temp = df_temp[df_temp[primera_col].astype(str).str.strip() != ""]

            # Si hay mapeo de nombres de columnas, renombramos y filtramos
            if diccionario_nombres:
                df_temp = df_temp.rename(columns=diccionario_nombres, errors="ignore")
                columnas_finales = list(dict.fromkeys(diccionario_nombres.values()))
                columnas_presentes = [col for col in columnas_finales if col in df_temp.columns]
                df_temp = df_temp[columnas_presentes]

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
                df_master = pd.read_parquet(archivo_parquet)
                if "_archivo_origen" in df_master.columns:
                    # Quitamos del maestro los registros viejos de los archivos que acabamos de volver a leer
                    df_master = df_master[~df_master["_archivo_origen"].isin(nombres_actualizados.keys())]
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
        df_final.to_parquet(archivo_parquet, engine="pyarrow", index=False)

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


if __name__ == "__main__":
    actualizar_parquet_zsdmx249()
    # actualizar_parquet_zsdmx267()
