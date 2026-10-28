# parquets.py
import os
import glob
from datetime import datetime
import pandas as pd


def actualizar_parquet_zsdmx267() -> dict:
    """
    Lee archivos nuevos/pendientes de ZSDMX267 (.csv),
    aplica limpieza, estandarización de tipos y consolida incrementalmente
    hacia '267.parquet'.
    """
    try:
        # ==========================================
        # 1. CONFIGURACIÓN DE RUTAS
        # ==========================================
        perfil_usuario = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        carpeta_general = os.path.join(perfil_usuario, "Elementia S. A", "kiosko logistica cem - Documentos")
        anno = str(datetime.now().year)

        carpeta_267 = os.path.join(carpeta_general, anno, "zsdmx267")
        archivo_parquet = os.path.join(carpeta_general, "bi", "parquet", "267.parquet")
        archivo_log = os.path.join(carpeta_general, "bi", "memoria_txt", "267.txt")

        os.makedirs(os.path.dirname(archivo_parquet), exist_ok=True)
        os.makedirs(os.path.dirname(archivo_log), exist_ok=True)

        if not os.path.exists(carpeta_267):
            return {"estatus": False, "msg": f"La carpeta de origen no existe: {carpeta_267}"}

        # ==========================================
        # 2. MEMORIA INCREMENTAL
        # ==========================================
        if os.path.exists(archivo_log):
            with open(archivo_log, "r", encoding="utf-8") as f:
                procesados = set(f.read().splitlines())
        else:
            procesados = set()

        # Busca tanto .csv como .xls/.xlsx
        patrones = [os.path.join(carpeta_267, "*.csv"), os.path.join(carpeta_267, "*.xls*")]
        todos_los_archivos = []
        for patron in patrones:
            todos_los_archivos.extend(glob.glob(patron))

        nuevos_archivos = [a for a in todos_los_archivos if os.path.basename(a) not in procesados]

        if not nuevos_archivos:
            print("ℹ️ No hay archivos nuevos para procesar. El Parquet 267 ya está actualizado.")
            return {"estatus": True, "msg": "Sin archivos pendientes.", "nuevos": 0}

        print(f"📦 Se encontraron {len(nuevos_archivos)} archivos nuevos. Iniciando procesamiento...")

        lista_dataframes = []

        # Cargar maestro si existe
        if os.path.exists(archivo_parquet):
            print("🔄 Cargando historial maestro existente...")
            try:
                df_master = pd.read_parquet(archivo_parquet)
                lista_dataframes.append(df_master)
            except Exception as e_pq:
                print(f"⚠️ Error al leer Parquet maestro (se reconstruirá si es necesario): {e_pq}")

        # ==========================================
        # 3. EXTRACCIÓN Y LIMPIEZA
        # ==========================================
        diccionario_nombres = {
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
            "Autor": "transporte_autor"
        }

        archivos_procesados_ok = []

        for archivo in nuevos_archivos:
            nom_base = os.path.basename(archivo)
            print(f"  -> Leyendo: {nom_base}")

            # Lectura flexible según el delimitador generado por SAP
            df_temp = None
            for sep in ['\t', ';', ',']:
                for enc in ['utf-16', 'latin-1', 'utf-8']:
                    try:
                        df_temp = pd.read_csv(
                            archivo,
                            sep=sep,
                            skiprows=3,
                            encoding=enc,
                            dtype=str,
                            quoting=3,
                            on_bad_lines='skip'
                        )
                        # Validar si leyó columnas reales y no una sola cadena larga
                        if len(df_temp.columns) > 5:
                            break
                    except Exception:
                        continue
                if df_temp is not None and len(df_temp.columns) > 5:
                    break

            if df_temp is None or df_temp.empty:
                print(f"⚠️ No se pudo parsear adecuadamente: {nom_base}")
                continue

            # Limpiar espacios invisibles de encabezados
            df_temp.columns = df_temp.columns.str.strip()

            # Reparar columnas duplicadas
            columnas = pd.Series(df_temp.columns)
            for dup in columnas[columnas.duplicated()].unique():
                indices = columnas[columnas == dup].index.tolist()
                for idx_count, idx in enumerate(indices):
                    if idx_count > 0:
                        columnas[idx] = f"{dup}_{idx_count}"
            df_temp.columns = columnas

            # Validar columna ancla
            col_entrega = [c for c in df_temp.columns if "Entrega" in c]
            if not col_entrega:
                print(f"⚠️ Advertencia: No se encontró columna 'Entrega' en {nom_base}. Se omite.")
                continue

            nombre_col_entrega = col_entrega[0]
            df_temp = df_temp.dropna(subset=[nombre_col_entrega])
            df_temp = df_temp[df_temp[nombre_col_entrega].str.strip() != ""]

            # Renombrar al modelo final
            df_temp = df_temp.rename(columns=diccionario_nombres, errors='ignore')
            columnas_finales = list(dict.fromkeys(diccionario_nombres.values()))
            columnas_presentes = [col for col in columnas_finales if col in df_temp.columns]
            df_temp = df_temp[columnas_presentes]

            lista_dataframes.append(df_temp)
            archivos_procesados_ok.append(nom_base)

        if not archivos_procesados_ok:
            return {"estatus": False, "msg": "No se extrajeron registros válidos de los archivos nuevos."}

        # ==========================================
        # 4. CONSOLIDACIÓN Y TIPOS DE DATOS
        # ==========================================
        print("🔗 Consolidando registros...")
        df_final = pd.concat(lista_dataframes, ignore_index=True)

        # Desduplicar si se re-descargaron entregas de días previos
        llaves_dedup = [c for c in ['entrega', 'entrega_pos', 'transporte'] if c in df_final.columns]
        if llaves_dedup:
            df_final = df_final.drop_duplicates(subset=llaves_dedup, keep='last')

        print("⚙️ Tipificando columnas...")

        # Int64
        cols_int = ['destino_km']
        for col in cols_int:
            if col in df_final.columns:
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').round().astype('Int64')

        # Float
        cols_float = ['ctd_facturada', 'tarifa_normal', 'valor_neto', 'peso_bruto', 'peso_neto', 'factura_valor', 'factura_peso']
        for col in cols_float:
            if col in df_final.columns:
                df_final[col] = pd.to_numeric(
                    df_final[col].astype(str).str.replace(',', '').str.strip(),
                    errors='coerce'
                )

        # Date (YYYY-MM-DD)
        cols_date = [
            'fch_creacion_entrega', 'fch_creacion_gasto', '0_fch_creacion_transporte',
            '1_fch_planificacion', '2_fch_bascula_entrada', '3_fch_inicio_carga',
            '4_fch_fin_carga', '5_fch_despacho_exp', '6_fch_inicio_transporte',
            '7_fch_fin_transporte'
        ]
        for col in cols_date:
            if col in df_final.columns:
                df_final[col] = pd.to_datetime(
                    df_final[col].astype(str).str.strip(),
                    dayfirst=True,
                    errors='coerce'
                ).dt.strftime('%Y-%m-%d')

        # Time (HH:MM:SS)
        cols_time = [
            'hora_creacion_entrega', '0_hr_creacion_transporte', '1_hr_planificacion',
            '2_hr_bascula_entrada', '3_hr_inicio_carga', '4_hr_fin_carga',
            '5_hr_despacho_exp', '6_hr_inicio_transporte', '7_hr_fin_transporte'
        ]
        for col in cols_time:
            if col in df_final.columns:
                df_final[col] = pd.to_datetime(
                    df_final[col].astype(str).str.strip(),
                    format='%H:%M:%S',
                    errors='coerce'
                ).dt.strftime('%H:%M:%S')

        # ==========================================
        # 5. GUARDADO FINAL
        # ==========================================
        print(f"💾 Escribiendo Parquet maestro en: {archivo_parquet}...")
        df_final.to_parquet(archivo_parquet, engine='pyarrow', index=False)

        # Actualizar memoria txt
        procesados.update(archivos_procesados_ok)
        with open(archivo_log, 'w', encoding='utf-8') as f:
            for p in sorted(procesados):
                f.write(f"{p}\n")

        print("✅ Parquet 267 actualizado con éxito.")
        return {
            "estatus": True,
            "msg": f"Se procesaron {len(archivos_procesados_ok)} archivos. Total filas: {len(df_final)}.",
            "procesados": len(archivos_procesados_ok)
        }

    except Exception as e:
        print(f"❌ Error durante la generación del Parquet: {e}")
        return {"estatus": False, "msg": str(e)}


if __name__ == "__main__":
    actualizar_parquet_zsdmx267()