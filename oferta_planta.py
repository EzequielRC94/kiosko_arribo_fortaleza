# oferta_planta.py
import os
from datetime import datetime
import pandas as pd

from catalogos import (
    CATALOGO_PLANTAS,
    CATALOGO_MATERIALES,
    CATALOGO_FECHAS,
    obtener_pct_retirado,
)
from parquets import obtener_oferta_plantas, obtener_rutas_transaccion


def _obtener_dias_operativos_centro(c_exp: str, planta_nom: str = "") -> list:
    """
    Obtiene la lista de días operativos de la semana (1=Lunes .. 7=Domingo)
    según la llave 'normalidad_operativa' en CATALOGO_PLANTAS.
    """
    ce_u = str(c_exp or "").strip().upper()
    pl_u = str(planta_nom or "").strip().upper()

    for nom_planta_gui, info_p in CATALOGO_PLANTAS.items():
        cods_p = [str(c).strip().upper() for c in info_p.get("codigos", [])]
        nom_centro_u = str(info_p.get("nombre_centro", "")).strip().upper()
        if (ce_u and ce_u in cods_p) or (pl_u and (pl_u == nom_centro_u or pl_u == nom_planta_gui.upper())):
            norm_op = info_p.get("normalidad_operativa", {})
            dias_op = norm_op.get("dias_operativos")
            if dias_op:
                return list(dias_op)
    return [1, 2, 3, 4, 5, 6]


def generar_excel_oferta_mensual(
    anio: int = 2026,
    mes: int = 11,
    ruta_base_drive: str = None,
    ruta_salida_xlsx: str = None,
    vkorg: str = "0152",
    bukrs: int = 3022,
    usar_semana_vigente_si_falta: bool = True,
) -> dict:
    """
    Genera el archivo .xlsx mensual de oferta desglosada por día hábil y tipo de despacho.

    Columnas de salida:
      BUKRS | VKORG | WERKS | MATNR | fecha | tipo_despacho | volumen
      Columnas auxiliares para análisis:
      des_tipo_despacho | mat_familia | mat_nom_corto

    Reglas:
      - BUKRS: siempre 3022
      - VKORG: siempre 0152 (152)
      - WERKS: c_exp
      - MATNR: mat_codigo_norm (código de material)
      - fecha: fecha de despacho (YYYY-MM-DD) de CATALOGO_FECHAS con EsDiaHabil == 1
               respetando además la normalidad_operativa de CATALOGO_PLANTAS.
      - tipo_despacho: 0 = Retirado, 1 = Entregado
      - volumen: toneladas a despachar repartidas según obtener_pct_retirado
                 (1° por material, 2° por familia, 3° por planta:
                  Tula 65%, Palmar 60%, Progreso 50%, Vito 33%).
      - des_tipo_despacho: 'retirado' o 'entregado'
      - mat_familia: familia del producto ('envasado' / 'granel') desde oferta_planta.parquet
      - mat_nom_corto: descripción corta del producto desde oferta_planta.parquet
    """
    # 1. Asegurar que oferta_planta.parquet esté creado y actualizado (1 vez al día -> 999 min)
    res_pq = obtener_oferta_plantas(ruta_base_drive=ruta_base_drive, limite_minutos=999)
    rutas_oferta = obtener_rutas_transaccion("oferta_planta")
    archivo_parquet = rutas_oferta["archivo_parquet"]

    if not os.path.exists(archivo_parquet):
        return {
            "estatus": False,
            "msg": f"No se encontró 'oferta_planta.parquet' en: {archivo_parquet} ({res_pq.get('msg', '')})",
            "ruta_xlsx": None,
            "filas": 0,
        }

    # 2. Leer oferta_planta.parquet
    try:
        df_oferta = pd.read_parquet(archivo_parquet, engine="fastparquet")
    except Exception:
        df_oferta = pd.read_parquet(archivo_parquet)

    if df_oferta is None or df_oferta.empty:
        return {
            "estatus": False,
            "msg": "El archivo 'oferta_planta.parquet' está vacío.",
            "ruta_xlsx": None,
            "filas": 0,
        }

    # Normalización preventiva de columnas clave en df_oferta
    df_oferta["semana"] = pd.to_numeric(df_oferta["semana"], errors="coerce").fillna(0).astype(int)
    df_oferta["c_exp"] = df_oferta["c_exp"].fillna("").astype(str).str.strip().str.upper()
    if "mat_codigo_norm" not in df_oferta.columns:
        df_oferta["mat_codigo_norm"] = (
            df_oferta["mat_codigo"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.lstrip("0")
        )
    df_oferta["ton_of"] = pd.to_numeric(df_oferta["ton_of"], errors="coerce").fillna(0.0)

    # 3. Filtrar las fechas del mes y año solicitados desde CATALOGO_FECHAS donde EsDiaHabil == 1
    fechas_habiles_mes = [
        info_f
        for f_key, info_f in sorted(CATALOGO_FECHAS.items())
        if int(info_f.get("Año", 0)) == int(anio)
        and int(info_f.get("Mes", 0)) == int(mes)
        and int(info_f.get("EsDiaHabil", 0)) == 1
    ]

    if not fechas_habiles_mes:
        return {
            "estatus": False,
            "msg": f"No se encontraron días hábiles en CATALOGO_FECHAS para {anio}-{mes:02d}.",
            "ruta_xlsx": None,
            "filas": 0,
        }

    # 4. Super ciclo for: por cada día hábil del mes, duplicar cada línea de oferta_planta
    #    correspondiente a la semana del día y desglosar en tipo_despacho 0 (Retirado) y 1 (Entregado)
    registros_salida = []
    centros_disponibles = sorted(df_oferta["c_exp"].unique())

    for info_dia in fechas_habiles_mes:
        fecha_str = info_dia["Fecha"]              # YYYY-MM-DD
        semana_iso = int(info_dia["Semana"])       # Ej. 45, 46, 47, 48, 49 en Nov 2026
        dia_semana_num = int(info_dia["Día de la semana"])  # 1=Lunes .. 7=Domingo

        for ce in centros_disponibles:
            df_ce = df_oferta[df_oferta["c_exp"] == ce]
            if df_ce.empty:
                continue

            planta_nom = str(df_ce["planta"].iloc[0]) if "planta" in df_ce.columns else ""
            dias_op_planta = _obtener_dias_operativos_centro(ce, planta_nom)
            if dia_semana_num not in dias_op_planta:
                continue

            # Buscar coincidencia exacta de semana
            df_sem = df_ce[df_ce["semana"] == semana_iso]

            # Si la semana específica aún no está declarada en oferta_planta, tomar la última semana vigente <= semana_iso
            if df_sem.empty and usar_semana_vigente_si_falta:
                semanas_ce = sorted(df_ce["semana"].unique())
                candidatas = [s for s in semanas_ce if s <= semana_iso]
                semana_efectiva = candidatas[-1] if candidatas else semanas_ce[-1]
                df_sem = df_ce[df_ce["semana"] == semana_efectiva]

            if df_sem.empty:
                continue

            for _, row_of in df_sem.iterrows():
                werks = str(row_of["c_exp"]).strip().upper()
                matnr = str(row_of["mat_codigo_norm"]).strip()
                ton_diaria = float(row_of["ton_of"])
                familia = str(row_of.get("material_familia", "")).strip().lower()
                nom_corto = str(row_of.get("mat_nom_corto", "")).strip()
                planta_r = str(row_of.get("planta", "")).strip()

                # Porcentaje Retirado (jerarquía: 1. Material -> 2. Familia -> 3. Planta)
                pct_ret = obtener_pct_retirado(
                    c_exp=werks,
                    mat_codigo=matnr,
                    material_familia=familia,
                    planta_nombre=planta_r,
                )
                pct_ent = 1.0 - pct_ret

                vol_retirado = round(ton_diaria * pct_ret, 2)
                vol_entregado = round(ton_diaria * pct_ent, 2)

                # Fila 1: tipo_despacho = 0 (Retirado)
                registros_salida.append({
                    "BUKRS": bukrs,
                    "VKORG": vkorg,
                    "WERKS": werks,
                    "MATNR": matnr,
                    "fecha": fecha_str,
                    "tipo_despacho": 0,
                    "volumen": vol_retirado,
                    "des_tipo_despacho": "retirado",
                    "mat_familia": familia,
                    "mat_nom_corto": nom_corto,
                })

                # Fila 2: tipo_despacho = 1 (Entregado)
                registros_salida.append({
                    "BUKRS": bukrs,
                    "VKORG": vkorg,
                    "WERKS": werks,
                    "MATNR": matnr,
                    "fecha": fecha_str,
                    "tipo_despacho": 1,
                    "volumen": vol_entregado,
                    "des_tipo_despacho": "entregado",
                    "mat_familia": familia,
                    "mat_nom_corto": nom_corto,
                })

    columnas_finales = [
        "BUKRS",
        "VKORG",
        "WERKS",
        "MATNR",
        "fecha",
        "tipo_despacho",
        "volumen",
        "des_tipo_despacho",
        "mat_familia",
        "mat_nom_corto",
    ]
    df_resultado = pd.DataFrame(
        registros_salida,
        columns=columnas_finales,
    )

    # 5. Determinar ruta de guardado del archivo .xlsx
    if not ruta_salida_xlsx:
        if not ruta_base_drive:
            ruta_base_drive = os.path.join(rutas_oferta["carpeta_general"], str(anio))
        carpeta_oferta = os.path.join(ruta_base_drive, "oferta_plantas")
        try:
            os.makedirs(carpeta_oferta, exist_ok=True)
            ruta_salida_xlsx = os.path.join(
                carpeta_oferta, f"layout_oferta_despacho_{anio}_{mes:02d}.xlsx"
            )
        except Exception:
            ruta_salida_xlsx = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                f"layout_oferta_despacho_{anio}_{mes:02d}.xlsx",
            )

    try:
        df_resultado.to_excel(ruta_salida_xlsx, index=False, engine="openpyxl")
    except PermissionError:
        ruta_salida_xlsx = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"layout_oferta_despacho_{anio}_{mes:02d}.xlsx",
        )
        df_resultado.to_excel(ruta_salida_xlsx, index=False, engine="openpyxl")

    print(
        f"✅ [oferta_planta] Excel generado exitosamente ({len(df_resultado)} filas) en:\n"
        f"   {ruta_salida_xlsx}"
    )
    return {
        "estatus": True,
        "msg": f"Archivo generado con {len(df_resultado)} registros.",
        "ruta_xlsx": ruta_salida_xlsx,
        "filas": len(df_resultado),
        "df": df_resultado,
    }


if __name__ == "__main__":
    res = generar_excel_oferta_mensual(anio=2026, mes=11)
    print(res["msg"])
