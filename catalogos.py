# catalogos.py
import os

# ==============================================================================
# CATÁLOGO DE PLANTAS Y CENTROS DE EXPEDICIÓN
# Mandante para la app Kiosko/Báscula y para Power Query (zql_bi_catalogo_centros.pq)
# ==============================================================================

CATALOGO_PLANTAS = {
    # --- PLANTAS Y CENTROS ACTIVOS (OPERATIVOS EN KIOSKO / BÁSCULA) ---
    "Planta Tula": {
        "nombre_centro": "Tula",
        "codigos": ["MX47", "MX57"],
        "letra": "T",
        "tipo_centro": "Planta",
        "turnos_operativos": 3,
        "normalidad_operativa": {
            "descripcion": "Lunes 07:00 am - Domingo 07:00 am",
            "dia_inicio": "Lunes",
            "hora_inicio": "07:00",
            "dia_fin": "Domingo",
            "hora_fin": "07:00",
            "dias_operativos": [1, 2, 3, 4, 5, 6],  # Lunes(1) a Sábado(6)
        },
        "pct_retirado": 0.65,
        "activo": True
    },
    "Planta Palmar": {
        "nombre_centro": "Palmar",
        "codigos": ["MX16"],
        "letra": "P",
        "tipo_centro": "Planta",
        "turnos_operativos": 3,
        "normalidad_operativa": {
            "descripcion": "Lunes 07:00 am - Domingo 07:00 am",
            "dia_inicio": "Lunes",
            "hora_inicio": "07:00",
            "dia_fin": "Domingo",
            "hora_fin": "07:00",
            "dias_operativos": [1, 2, 3, 4, 5, 6],  # Lunes(1) a Sábado(6)
        },
        "pct_retirado": 0.60,
        "activo": True
    },
    "Planta Progreso": {
        "nombre_centro": "Progreso",
        "codigos": ["MX76"],
        "letra": "M",
        "tipo_centro": "Planta",
        "turnos_operativos": 2,
        "normalidad_operativa": {
            "descripcion": "Lunes 06:00 am - Sábado 10:00 pm",
            "dia_inicio": "Lunes",
            "hora_inicio": "06:00",
            "dia_fin": "Sábado",
            "hora_fin": "22:00",
            "dias_operativos": [1, 2, 3, 4, 5, 6],  # Lunes(1) a Sábado(6)
        },
        "pct_retirado": 0.50,
        "activo": True
    },
    "Planta Vito": {
        "nombre_centro": "Vito",
        "codigos": ["MX46"],
        "letra": "V",
        "tipo_centro": "Planta",
        "turnos_operativos": 2,
        "normalidad_operativa": {
            "descripcion": "Lunes 07:00 am - Sábado 11:00 pm",
            "dia_inicio": "Lunes",
            "hora_inicio": "07:00",
            "dia_fin": "Sábado",
            "hora_fin": "23:00",
            "dias_operativos": [1, 2, 3, 4, 5, 6],  # Lunes(1) a Sábado(6)
        },
        "pct_retirado": 0.33,
        "activo": True
    },
    "CEDIS GDL": {
        "nombre_centro": "Gdl",
        "codigos": ["MX83"],
        "letra": "G",
        "tipo_centro": "Cedis",
        "turnos_operativos": 2,
        "normalidad_operativa": {
            "descripcion": "Lunes 07:00 am - Sábado 06:00 pm",
            "dia_inicio": "Lunes",
            "hora_inicio": "07:00",
            "dia_fin": "Sábado",
            "hora_fin": "18:00",
            "dias_operativos": [1, 2, 3, 4, 5, 6],  # Lunes(1) a Sábado(6)
        },
        "pct_retirado": 0.50,
        "activo": True
    },

    # --- CENTROS NO ACTIVOS / OTROS CENTROS DE EXPEDICIÓN ---
    "Huehuetoca Diselo": {
        "nombre_centro": "Huehuetoca",
        "codigos": ["MX84"],
        "letra": "",
        "tipo_centro": "Cross Dock",
        "activo": False
    },
    "CEDIS Mazatlan": {
        "nombre_centro": "Mazatlan",
        "codigos": ["MX86"],
        "letra": "",
        "tipo_centro": "Cedis",
        "activo": False
    },
    "CEDIS Merida": {
        "nombre_centro": "Merida",
        "codigos": ["MX87"],
        "letra": "",
        "tipo_centro": "Cedis",
        "activo": False
    },
    "CEDIS Mexicali": {
        "nombre_centro": "Mexicali",
        "codigos": ["MX89"],
        "letra": "",
        "tipo_centro": "Cedis",
        "activo": False
    },
    "Huehuetoca": {
        "nombre_centro": "Huehuetoca",
        "codigos": ["MX90"],
        "letra": "",
        "tipo_centro": "Cross Dock",
        "activo": False
    },
    "Atotonilco": {
        "nombre_centro": "Atotonilco",
        "codigos": ["MX91"],
        "letra": "",
        "tipo_centro": "Cross Dock",
        "activo": False
    },
    "CEDIS Veracruz": {
        "nombre_centro": "Veracruz",
        "codigos": ["MX93"],
        "letra": "",
        "tipo_centro": "Cedis",
        "activo": False
    },
    "Virtual Tuxpan": {
        "nombre_centro": "Virtual Tuxpan",
        "codigos": ["MX41"],
        "letra": "",
        "tipo_centro": None,
        "activo": False
    },
    "CEDIS La Paz": {
        "nombre_centro": "La Paz",
        "codigos": ["MX77"],
        "letra": "",
        "tipo_centro": "Cedis",
        "activo": False
    }
}

# ==============================================================================
# BASE DE DATOS DE MATERIALES (SKUs)
# Mandante para la app Kiosko/Báscula y para Power Query (zql_bi_catalogo_materiales.pq)
# ==============================================================================
CATALOGO_MATERIALES = {
    # --- envasado ---
    "1321185": {"desc_nom_corto": "PATRIA 50",       "grupo": "envasado", "bg": "#00C4DE", "fg": "#000000"},
    "41303":   {"desc_nom_corto": "BCO 50",          "grupo": "envasado", "bg": "#D664FA", "fg": "#000000"},
    "41304":   {"desc_nom_corto": "BCO 25",          "grupo": "envasado", "bg": "#FAB4FA", "fg": "#000000"},
    "41309":   {"desc_nom_corto": "MORTERO UL",      "grupo": "envasado", "bg": "#FFBA82", "fg": "#000000"},
    "41320":   {"desc_nom_corto": "FORTALEZA RS 50", "grupo": "envasado", "bg": "#46C8D7", "fg": "#000000"},
    "41321":   {"desc_nom_corto": "MAGNO RS 50",     "grupo": "envasado", "bg": "#228B22", "fg": "#FFFFFF"},
    "41336":   {"desc_nom_corto": "FORTALEZA 50",    "grupo": "envasado", "bg": "#46C8D7", "fg": "#000000"},
    "41337":   {"desc_nom_corto": "MORTERO FZ 50",   "grupo": "envasado", "bg": "#F79646", "fg": "#000000"},
    "1319772": {"desc_nom_corto": "ESTUCO",          "grupo": "envasado", "bg": "#C8EBC8", "fg": "#000000"},
    "1330688": {"desc_nom_corto": "FORTALEZA RS 25", "grupo": "envasado", "bg": "#A0F0F5", "fg": "#000000"},
    "1330691": {"desc_nom_corto": "MORTERO FZ 25",   "grupo": "envasado", "bg": "#FFD2A0", "fg": "#000000"},
    "1330689": {"desc_nom_corto": "MAGNO RS 25",     "grupo": "envasado", "bg": "#AAE1AA", "fg": "#000000"},
    "1330690": {"desc_nom_corto": "FORTALEZA 25",    "grupo": "envasado", "bg": "#A0F0F5", "fg": "#000000"},
    "1331169": {"desc_nom_corto": "MAGNO 25",        "grupo": "envasado", "bg": "#96EB96", "fg": "#000000"},
    "1331156": {"desc_nom_corto": "MAGNO 50",        "grupo": "envasado", "bg": "#00B050", "fg": "#000000"},
    "1331390": {"desc_nom_corto": "PATRIA 50",       "grupo": "envasado", "bg": "#00C4DE", "fg": "#000000"},
    "1331391": {"desc_nom_corto": "PATRIA 25",       "grupo": "envasado", "bg": "#A0EBFA", "fg": "#000000"},
    "41307":   {"desc_nom_corto": "BCO 25_MZ",       "grupo": "envasado", "bg": "#FAB4FA", "fg": "#000000"},
    "1330641": {"desc_nom_corto": "RS 42.6",         "grupo": "granel",   "bg": "#A24E56", "fg": "#FFFFFF"},

    # --- granel --- (Colores extraídos de tu lógica VBA)
    "974360":  {"desc_nom_corto": "BCO granel",     "grupo": "granel", "bg": "#CA2BFA", "fg": "#FFFFFF"}, # 
    "974527":  {"desc_nom_corto": "granel RS",      "grupo": "granel", "bg": "#A24E56", "fg": "#FFFFFF"}, # Vino tinto
    "974531":  {"desc_nom_corto": "granel",         "grupo": "granel", "bg": "#5E1B21", "fg": "#FFFFFF"}, # Rojo oscuro (Granel L2)
    "981035":  {"desc_nom_corto": "granel MEXALIT", "grupo": "granel", "bg": "#8C4EA2", "fg": "#FFFFFF"}, # Morado oscuro

    # --- BIG BAG ---
    "41335":   {"desc_nom_corto": "BIG BAG",        "grupo": "envasado", "bg": "#00B0F0", "fg": "#000000"}, # Azul cielo intenso
    "1319631": {"desc_nom_corto": "BIG BAG RS",     "grupo": "envasado", "bg": "#00B0F0", "fg": "#000000"},
    
    # --- SACOS / INSUMOS --- (Color Gris Estándar para todos)
    "85901":   {"desc_nom_corto": "SACO BCO25",         "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "85903":   {"desc_nom_corto": "SACO M FZ50",        "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "85904":   {"desc_nom_corto": "SACO BCO50",         "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "85945":   {"desc_nom_corto": "SACO PROPILENO",     "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "85948":   {"desc_nom_corto": "SACO MG",            "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "85950":   {"desc_nom_corto": "SACO RS",            "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "85951":   {"desc_nom_corto": "SACO RS",            "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "87885":   {"desc_nom_corto": "SACO M FZ",          "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "87888":   {"desc_nom_corto": "SACO M UL",          "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "88657":   {"desc_nom_corto": "SACO ESTUCO",        "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "88845":   {"desc_nom_corto": "SACO PATRIA",        "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "89245":   {"desc_nom_corto": "SACO MAGNO LINER",   "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "89247":   {"desc_nom_corto": "SACO RS LINER",      "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "85949":   {"desc_nom_corto": "SACO SUPREMO",       "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "89756":   {"desc_nom_corto": "SACO 30R 25",        "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "89518":   {"desc_nom_corto": "SACO MORTERO FZ 25", "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "89520":   {"desc_nom_corto": "SACO 30R MAGNO 25",  "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "89517":   {"desc_nom_corto": "SACO RS 25",         "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"},
    "89956":   {"desc_nom_corto": "SACO RS MAGNO 25",   "grupo": "saco", "bg": "#D3D3D3", "fg": "#000000"}
}

# ==============================================================================
# CATÁLOGO DE USUARIOS AUTORIZADOS PARA ARRIBO EN BÁSCULA
# ==============================================================================
USUARIOS_AUTORIZADOS_ARRIBO = {
    "jequisl":    "Jose Trinidad Equis Lopez",
    "mcantoc":    "Mario Alejandro Canto Canul",
    "zvilledav":  "Zahira Guadalupe Villeda Vergara",
    "ltorrest":   "Lizeth Torres Tepetate",
    "bjaena":     "Betsabe Montserrath Jaen Arellano",
    "ugonzalezs": "Uriel Arturo Gonzalez Sanchez",
    "lpachecoc":  "Leisdi Alis Pacheco Cruz",
    "dhidalgom":  "Diana Caren Hidalgo Martin",
    "mcruzv":     "Martin Daniel Cruz Vargas",
    "anmoralesg": "Elda Neidy Morales Guerrero",
    "aramirezc":  "Alberto Ezequiel Ramirez Contreras",
    "isantiagom": "Isidro Santiago Mendoza",
    "mcoronadon": "Mario Arturo Coronado Neville"
}

# ==============================================================================
# JERARQUÍA DE PORCENTAJES DE DESPACHO (RETIRADO = 0 / ENTREGADO = 1)
# Prioridad 1: Por Material (en CATALOGO_MATERIALES[cod]["pct_retirado"])
# Prioridad 2: Por Familia ("envasado" / "granel") en CATALOGO_PCT_RETIRADO_FAMILIA
# Prioridad 3: Por Generalidad de Planta en CATALOGO_PLANTAS[planta]["pct_retirado"]
# ==============================================================================
CATALOGO_PCT_RETIRADO_FAMILIA = {
    # Estructura lista para cuando se definan porcentajes por familia (general o por c_exp):
    # "MX47": {"granel": 0.65, "envasado": 0.65},
    # "DEFAULT": {"granel": None, "envasado": None},
}


def obtener_pct_retirado(
    c_exp: str = "",
    mat_codigo: str = "",
    material_familia: str = "",
    planta_nombre: str = "",
) -> float:
    """
    Retorna la proporción (0.0 a 1.0) correspondiente a 'Retirado' (tipo_despacho = 0)
    respetando la jerarquía de negocio:
      1. Por material (CATALOGO_MATERIALES[mat_codigo]['pct_retirado'])
      2. Por familia (CATALOGO_PCT_RETIRADO_FAMILIA)
      3. Por generalidad de planta de despacho (CATALOGO_PLANTAS[planta]['pct_retirado'])
    """
    cod_m = str(mat_codigo or "").strip().lstrip("0")
    ce_u = str(c_exp or "").strip().upper()
    fam_l = str(material_familia or "").strip().lower()
    pl_u = str(planta_nombre or "").strip().upper()

    # 1. Primera mano: Por material
    info_mat = CATALOGO_MATERIALES.get(cod_m, {})
    pct_mat = info_mat.get("pct_retirado")
    if pct_mat is not None:
        return float(pct_mat)

    # 2. Segunda mano: Por familia (específico por centro o DEFAULT)
    if fam_l:
        pct_fam_ce = CATALOGO_PCT_RETIRADO_FAMILIA.get(ce_u, {}).get(fam_l)
        if pct_fam_ce is not None:
            return float(pct_fam_ce)
        pct_fam_def = CATALOGO_PCT_RETIRADO_FAMILIA.get("DEFAULT", {}).get(fam_l)
        if pct_fam_def is not None:
            return float(pct_fam_def)

    # 3. Tercera mano: Por generalidad de planta de despacho
    for nom_planta_gui, info_p in CATALOGO_PLANTAS.items():
        cods_p = [str(c).strip().upper() for c in info_p.get("codigos", [])]
        nom_centro_u = str(info_p.get("nombre_centro", "")).strip().upper()
        if (ce_u and ce_u in cods_p) or (pl_u and (pl_u == nom_centro_u or pl_u == nom_planta_gui.upper())):
            if "pct_retirado" in info_p and info_p["pct_retirado"] is not None:
                return float(info_p["pct_retirado"])

    return 0.50


# ==============================================================================
# CATÁLOGO DE FECHAS Y DÍAS HÁBILES (MANDANTE PARA PYTHON Y POWER QUERY)
# ==============================================================================
FESTIVOS_2026 = [
    "2026-01-01",
    "2026-02-02",
    "2026-03-16",
    "2026-04-02",
    "2026-04-03",
    "2026-04-04",
    "2026-05-01",
    "2026-09-16",
    "2026-11-16",
    "2026-12-12",
    "2026-12-25",
]

_DIAS_CORTOS_ES = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
_DIAS_COMPLETOS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES_PROPER_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def _construir_catalogo_fechas(
    fecha_inicio_str: str = "2026-01-01",
    fecha_fin_str: str = "2026-12-31",
    festivos: list = None,
) -> dict:
    """
    Construye el diccionario maestro CATALOGO_FECHAS día por día con las mismas
    reglas y columnas que zql_bi_catalogo_fechas.pq:
      - Fecha (YYYY-MM-DD)
      - Nombre del día (lun..dom)
      - Semana (ISO / Lunes = día 1)
      - Etiqueta Semana ('Sem 01'..'Sem 53')
      - Nombre del mes ('Enero'..'Diciembre')
      - Mes (1..12)
      - Año (2026)
      - mes_año ('Noviembre_2026')
      - Nombre del día completo ('lunes'..'domingo')
      - Día de la semana (1=Lunes .. 7=Domingo)
      - EsDescanso (1 si es Domingo, 0 en caso contrario)
      - EsFestivo (1 si está en festivos, 0 en caso contrario)
      - EsDiaHabil (1 si EsDescanso == 0 y EsFestivo == 0, 0 en caso contrario)
    """
    from datetime import datetime, timedelta

    set_festivos = set(festivos if festivos is not None else FESTIVOS_2026)
    dt_ini = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
    dt_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()

    catalogo = {}
    actual = dt_ini
    while actual <= dt_fin:
        f_str = actual.strftime("%Y-%m-%d")
        idx_sem = actual.weekday()  # 0 = lunes .. 6 = domingo
        dia_semana_num = idx_sem + 1  # 1 = lunes .. 7 = domingo
        semana_iso = int(actual.isocalendar()[1])
        nom_mes = _MESES_PROPER_ES[actual.month]
        es_descanso = 1 if dia_semana_num == 7 else 0
        es_festivo = 1 if f_str in set_festivos else 0
        es_dia_habil = 1 if (es_descanso == 0 and es_festivo == 0) else 0

        catalogo[f_str] = {
            "Fecha": f_str,
            "Nombre del día": _DIAS_CORTOS_ES[idx_sem],
            "Semana": semana_iso,
            "Etiqueta Semana": f"Sem {semana_iso:02d}",
            "Nombre del mes": nom_mes,
            "Mes": actual.month,
            "Año": actual.year,
            "mes_año": f"{nom_mes}_{actual.year}",
            "Nombre del día completo": _DIAS_COMPLETOS_ES[idx_sem],
            "Día de la semana": dia_semana_num,
            "EsDescanso": es_descanso,
            "EsFestivo": es_festivo,
            "EsDiaHabil": es_dia_habil,
        }
        actual += timedelta(days=1)

    return catalogo


CATALOGO_FECHAS = _construir_catalogo_fechas()


# ==============================================================================
# FUTUROS CATÁLOGOS (Estructuras vacías o ejemplos)
# ==============================================================================
CATALOGO_CLIENTES = {
    # "ID_CLIENTE": {"razon_social": "...", "rfc": "..."}
}

CATALOGO_PRODUCCION = {
    # "L1": "Línea 1 Envasado",
    # "L2": "Línea 2 Envasado"
}


# ==============================================================================
# GENERADORES Y SINCRONIZADORES DE CÓDIGO POWER QUERY (M)
# ==============================================================================

def generar_m_materiales() -> str:
    """Genera el código M para zql_bi_catalogo_materiales.pq basado en CATALOGO_MATERIALES."""
    filas = []
    for cod, info in CATALOGO_MATERIALES.items():
        desc = info.get("desc_nom_corto", "")
        grupo = info.get("grupo", "")
        filas.append(f'        {{"{cod}", "{desc}", "{grupo}"}}')
    
    cuerpo_filas = ",\n".join(filas)
    return (
        "// zql_bi_catalogo_materiales.pq -> catalogo de materiales generado desde catalogos.py\n\n"
        "let\n"
        "    Origen = Table.FromRows({\n"
        f"{cuerpo_filas}\n"
        "    },\n"
        '    {"mat_codigo", "mat_nom_corto", "grupo"}),\n'
        '    #"Tipo cambiado" = Table.TransformColumnTypes(Origen,{\n'
        '        {"mat_codigo", type text},\n'
        '        {"mat_nom_corto", type text},\n'
        '        {"grupo", type text}\n'
        "    })\n"
        "in\n"
        '    #"Tipo cambiado"\n'
    )


def generar_m_centros() -> str:
    """Genera el código M para zql_bi_catalogo_centros.pq basado en CATALOGO_PLANTAS."""
    filas = []
    for nombre, info in CATALOGO_PLANTAS.items():
        nom_centro = info.get("nombre_centro", nombre)
        tipo = info.get("tipo_centro")
        tipo_str = f'"{tipo}"' if tipo else "null"
        act_str = "true" if info.get("activo", False) else "false"
        for cod in info.get("codigos", []):
            filas.append(f'        {{"{cod}", "{nom_centro}", {tipo_str}, {act_str}}}')

    cuerpo_filas = ",\n".join(filas)
    return (
        "// zql_bi_catalogo_centros.pq -> catalogo de centros generado desde catalogos.py\n\n"
        "let\n"
        "    Origen = Table.FromRows({\n"
        f"{cuerpo_filas}\n"
        "    },\n"
        '    {"c_exp", "nombre_centro", "tipo_centro", "activo"}),\n'
        '    #"Tipo cambiado" = Table.TransformColumnTypes(Origen,{\n'
        '        {"c_exp", type text},\n'
        '        {"nombre_centro", type text},\n'
        '        {"tipo_centro", type text},\n'
        '        {"activo", type logical}\n'
        "    })\n"
        "in\n"
        '    #"Tipo cambiado"\n'
    )


def generar_m_fechas() -> str:
    """Genera el código M para zql_bi_catalogo_fechas.pq basado en CATALOGO_FECHAS."""
    fechas_ordenadas = sorted(CATALOGO_FECHAS.keys())
    if fechas_ordenadas:
        y_ini, m_ini, d_ini = [int(x) for x in fechas_ordenadas[0].split("-")]
        y_fin, m_fin, d_fin = [int(x) for x in fechas_ordenadas[-1].split("-")]
    else:
        y_ini, m_ini, d_ini = (2026, 1, 1)
        y_fin, m_fin, d_fin = (2026, 12, 31)

    lineas_festivos = []
    for f_str in fechas_ordenadas:
        info_f = CATALOGO_FECHAS[f_str]
        if int(info_f.get("EsFestivo", 0)) == 1:
            yf, mf, df_d = [int(x) for x in f_str.split("-")]
            lineas_festivos.append(f"        #date({yf}, {mf}, {df_d})")

    cuerpo_festivos = ",\n".join(lineas_festivos)

    return (
        "// zql_bi_catalogo_fechas.pq -> catalogo de fechas generado desde catalogos.py\n"
        "let\n"
        f"    FechaInicio = #date({y_ini}, {m_ini}, {d_ini}),\n"
        f"    FechaFin = #date({y_fin}, {m_fin}, {d_fin}),\n"
        "    Dias = Duration.Days(FechaFin - FechaInicio) + 1,\n"
        "    ListaFechas = List.Dates(FechaInicio, Dias, #duration(1, 0, 0, 0)),\n"
        '    TablaFechas = Table.FromList(ListaFechas, Splitter.SplitByNothing(), {"Fecha"}),\n'
        '    #"Tipo cambiado" = Table.TransformColumnTypes(TablaFechas, {{"Fecha", type date}}),\n'
        '    #"dia corto" = Table.AddColumn(#"Tipo cambiado", "Nombre del día", each Date.ToText([Fecha], "ddd"), type text),\n'
        '    Semana = Table.AddColumn(#"dia corto", "Semana", each Date.WeekOfYear([Fecha], Day.Monday), Int64.Type),\n'
        "    EtiquetaSemana = Table.AddColumn(\n"
        '        Semana, "Etiqueta Semana", each "Sem " & Text.PadStart(Text.From([Semana]), 2, "0"), type text\n'
        "    ),\n"
        '    #"Nombre del mes insertado" = Table.AddColumn(\n'
        '        EtiquetaSemana, "Nombre del mes", each Text.Proper(Date.MonthName([Fecha])), type text\n'
        "    ),\n"
        '    #"Año insertado" = Table.AddColumn(#"Nombre del mes insertado", "Año", each Date.Year([Fecha]), Int64.Type),\n'
        '    #"Columna combinada insertada" = Table.AddColumn(\n'
        '        #"Año insertado", "mes_año", each [Nombre del mes] & "_" & Text.From([Año]), type text\n'
        "    ),\n"
        '    #"Nombre del día insertado" = Table.AddColumn(\n'
        '        #"Columna combinada insertada", "Nombre del día completo", each Date.DayOfWeekName([Fecha]), type text\n'
        "    ),\n"
        '    #"Día de la semana insertado" = Table.AddColumn(\n'
        '        #"Nombre del día insertado", "Día de la semana", each Date.DayOfWeek([Fecha], Day.Monday) + 1, Int64.Type\n'
        "    ),\n"
        "    Festivos = {\n"
        f"{cuerpo_festivos}\n"
        "    },\n"
        "    ConDescanso = Table.AddColumn(\n"
        '        #"Día de la semana insertado",\n'
        '        "EsDescanso",\n'
        "        each if Date.DayOfWeek([Fecha], Day.Sunday) = 0 then 1 else 0,\n"
        "        Int64.Type\n"
        "    ),\n"
        "    ConFestivo = Table.AddColumn(\n"
        '        ConDescanso, "EsFestivo", each if List.Contains(Festivos, [Fecha]) then 1 else 0, Int64.Type\n'
        "    ),\n"
        "    ConDiaHabil = Table.AddColumn(\n"
        '        ConFestivo, "EsDiaHabil", each if [EsDescanso] = 0 and [EsFestivo] = 0 then 1 else 0, Int64.Type\n'
        "    )\n"
        "in\n"
        "    ConDiaHabil\n"
    )


def actualizar_todos_catalogos_pq(directorio_base: str = None) -> dict:
    """
    Actualiza todos los catálogos Power Query a partir de catalogos.py.
    Ejecuta generar_m_materiales(), generar_m_centros() y generar_m_fechas(),
    escribiendo los archivos en directorio_base.
    Si no se especifica directorio_base, se toma la carpeta actual donde reside este archivo.
    """
    if directorio_base is None:
        directorio_base = os.path.dirname(os.path.abspath(__file__))

    catalogos_a_generar = {
        "materiales": ("zql_bi_catalogo_materiales.pq", generar_m_materiales()),
        "centros": ("zql_bi_catalogo_centros.pq", generar_m_centros()),
        "fechas": ("zql_bi_catalogo_fechas.pq", generar_m_fechas()),
    }

    rutas_generadas = {}
    for clave, (nombre_archivo, codigo_m) in catalogos_a_generar.items():
        ruta = os.path.join(directorio_base, nombre_archivo)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(codigo_m)
        rutas_generadas[clave] = ruta

    return rutas_generadas


if __name__ == "__main__":
    print("Sincronizando catalogos Power Query desde catalogos.py...")
    res = actualizar_todos_catalogos_pq()
    print(f"[OK] Materiales actualizados: {res['materiales']}")
    print(f"[OK] Centros actualizados:    {res['centros']}")
    print(f"[OK] Fechas actualizadas:     {res['fechas']}")
