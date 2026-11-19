# catalogos.py
# Almacén central de catálogos estáticos (sin lógica de análisis ni creación de archivos).

# ==============================================================================
# CATÁLOGO DE PLANTAS Y CENTROS DE EXPEDICIÓN
# Mandante para la app Kiosko/Báscula y para catalogo_centros.parquet
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
        "activo": True,
        "capacidades_lineas": [
            {
                "id_linea": "TULA_GRA_L1",
                "nombre": "Granel Línea 1 (MX47)",
                "gpo": "granel",
                "ce": "MX47",
                "capacidad_total": 3,
                "max_fulles": 1,
                "peso_full": 2,
            },
            {
                "id_linea": "TULA_GRA_L2",
                "nombre": "Granel Línea 2 (MX57)",
                "gpo": "granel",
                "ce": "MX57",
                "capacidad_total": 6,
                "max_fulles": 2,
                "peso_full": 2,
            },
            {
                "id_linea": "TULA_ENV_L1",
                "nombre": "Envasado Línea 1 (MX47)",
                "gpo": "envasado",
                "ce": "MX47",
                "capacidad_total": 4,
                "max_fulles": 3,
                "peso_full": 1,
            },
            {
                "id_linea": "TULA_ENV_L2",
                "nombre": "Envasado Línea 2 (MX57)",
                "gpo": "envasado",
                "ce": "MX57",
                "capacidad_total": 4,
                "max_fulles": 3,
                "peso_full": 1,
            },
        ],
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
        "activo": True,
        "capacidades_lineas": [
            {
                "id_linea": "PALMAR_GRA",
                "nombre": "Granel",
                "gpo": "granel",
                "ce": "MX16",
                "capacidad_total": 6,
                "max_fulles": 3,
                "peso_full": 2,
            },
            {
                "id_linea": "PALMAR_ENV",
                "nombre": "Envasado",
                "gpo": "envasado",
                "ce": "MX16",
                "capacidad_total": 6,
                "max_fulles": 4,
                "peso_full": 1,
            },
        ],
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
        "activo": True,
        "capacidades_lineas": [
            {
                "id_linea": "PROGRESO_GRA",
                "nombre": "Granel",
                "gpo": "granel",
                "ce": "MX76",
                "capacidad_total": 6,
                "max_fulles": 3,
                "peso_full": 2,
            },
            {
                "id_linea": "PROGRESO_ENV",
                "nombre": "Envasado",
                "gpo": "envasado",
                "ce": "MX76",
                "capacidad_total": 4,
                "max_fulles": 2,
                "peso_full": 2,
            },
        ],
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
        "activo": True,
        "capacidades_lineas": [
            {
                "id_linea": "VITO_GRA_L1",
                "nombre": "Granel Línea 1",
                "gpo": "granel",
                "ce": "MX46",
                "capacidad_total": 2,
                "max_fulles": 1,
                "peso_full": 2,
            },
            {
                "id_linea": "VITO_GRA_L2",
                "nombre": "Granel Línea 2",
                "gpo": "granel",
                "ce": "MX46",
                "capacidad_total": 1,
                "max_fulles": 0,
                "peso_full": 2,
            },
            {
                "id_linea": "VITO_ENV",
                "nombre": "Envasado",
                "gpo": "envasado",
                "ce": "MX46",
                "capacidad_total": 2,
                "max_fulles": 1,
                "peso_full": 2,
            },
        ],
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
        "activo": True,
        "capacidades_lineas": [
            {
                "id_linea": "PROGRESO_GRA",
                "nombre": "Granel",
                "gpo": "granel",
                "ce": "MX76",
                "capacidad_total": 6,
                "max_fulles": 3,
                "peso_full": 2,
            },
            {
                "id_linea": "PROGRESO_ENV",
                "nombre": "Envasado",
                "gpo": "envasado",
                "ce": "MX76",
                "capacidad_total": 4,
                "max_fulles": 2,
                "peso_full": 2,
            },
        ],
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
# Mandante para la app Kiosko/Báscula y para catalogo_materiales.parquet
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
    "974360":  {"desc_nom_corto": "BCO GRANEL",     "grupo": "granel", "bg": "#CA2BFA", "fg": "#FFFFFF"}, # 
    "974527":  {"desc_nom_corto": "GRANEL RS",      "grupo": "granel", "bg": "#A24E56", "fg": "#FFFFFF"}, # Vino tinto
    "974531":  {"desc_nom_corto": "GRANEL",         "grupo": "granel", "bg": "#5E1B21", "fg": "#FFFFFF"}, # Rojo oscuro (Granel L2)
    "981035":  {"desc_nom_corto": "GRANEL MEXALIT", "grupo": "granel", "bg": "#8C4EA2", "fg": "#FFFFFF"}, # Morado oscuro

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
# CATÁLOGO DE ESTATUS OPERATIVOS DE BÁSCULA
# ==============================================================================
CATALOGO_ESTATUS_BASCULA = {
    "estatus_1": {
        "texto": "01 en espera",
        "bg": "#E8F5E9",
        "fg": "#1B5E20",
    },

    "estatus_1_2": {
        "texto": "01 llamado",
        "bg": "#DAF8DD",
        "fg": "#1B5E20",
        },

    "estatus_2": {
        "texto": "02 ingresando...",
        "bg": "#C8EBC8",
        "fg": "#000000",
    },
    "estatus_3": {
        "texto": "03 cargando...",
        "bg": "#81C784",
        "fg": "#000000",
    },
    "estatus_4": {
        "texto": "04 cargado",
        "bg": "#2E7D32",
        "fg": "#FFFFFF",
    },
    "estatus_5": {
        "texto": "05 despachado",
        "bg": "#1B5E20",
        "fg": "#FFFFFF",
    },
}

MAPA_AUX_EG_ESTATUS = {
    0: CATALOGO_ESTATUS_BASCULA["estatus_1"]["texto"],
    1: CATALOGO_ESTATUS_BASCULA["estatus_1"]["texto"],
    2: CATALOGO_ESTATUS_BASCULA["estatus_2"]["texto"],
    3: CATALOGO_ESTATUS_BASCULA["estatus_3"]["texto"],
    4: CATALOGO_ESTATUS_BASCULA["estatus_4"]["texto"],
    5: CATALOGO_ESTATUS_BASCULA["estatus_5"]["texto"],
}

# ==============================================================================
# CATÁLOGO DE UNIDADES (CLASE DE EXPEDICIÓN)
# ==============================================================================
CATALOGO_UNIDADES = {
    "F1": {"unidad_nom": "tolva sencilla",      "tipo_unidad": "sencilla"},
    "F2": {"unidad_nom": "plataforma sencilla", "tipo_unidad": "sencilla"},
    "F3": {"unidad_nom": "torton",              "tipo_unidad": "sencilla"},
    "F4": {"unidad_nom": "plataforma full",     "tipo_unidad": "full"},
    "F5": {"unidad_nom": "tolvita",             "tipo_unidad": "sencilla"},
    "F7": {"unidad_nom": "tolva full",          "tipo_unidad": "full"},
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
# CATÁLOGO DE FECHAS Y DÍAS HÁBILES (MANDANTE PARA PYTHON Y catalogo_fechas.parquet)
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
    Construye el diccionario maestro CATALOGO_FECHAS día por día para
    Python y catalogo_fechas.parquet:
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
# CATÁLOGO DE LÍNEAS DE TRANSPORTE (MANDANTE PARA catalogo_lineas_transporte.parquet)
# ==============================================================================
CATALOGO_LINEAS_TRANSPORTE = {
    "708348":  {"razon_social": "ALEJANDRA JASMIN HERNANDEZ VAZQUEZ", "nom_corto": "Alejandra Jasmin", "clase_transportista": "transportista", "activo": False},
    "706556":  {"razon_social": "ALFONSO ORTIZ RAMIREZ", "nom_corto": "Alfonso Ortiz", "clase_transportista": "transportista", "activo": True},
    "707607":  {"razon_social": "ANGEL CHAVEZ LEON", "nom_corto": "Angel Chavez", "clase_transportista": "transportista", "activo": False},
    "705801":  {"razon_social": "ARTURO VASQUEZ CASTILLO", "nom_corto": "Arturo Vaques", "clase_transportista": "transportista", "activo": False},
    "708541":  {"razon_social": "BLOCK TABICON Y AGREGADOS SA DE CV", "nom_corto": "Block Tabicon", "clase_transportista": "transportista", "activo": False},
    "707652":  {"razon_social": "CESAR PELAEZ ROJAS", "nom_corto": "Cesar Pelaez", "clase_transportista": "transportista", "activo": False},
    "708455":  {"razon_social": "CLA KAR COMPAÑIA DEL SURESTE SA DE", "nom_corto": "Cla Kar", "clase_transportista": "transportista", "activo": False},
    "707765":  {"razon_social": "COMERCIALIZADORA EE SERRANO S.A DE C.V", "nom_corto": "EE Serrano", "clase_transportista": "transportista", "activo": False},
    "1626602": {"razon_social": "CORPORATIVO TAEMSI", "nom_corto": "Taemsi", "clase_transportista": "transportista", "activo": False},
    "708401":  {"razon_social": "EVERARDO OLVERA AVILA", "nom_corto": "Everardo Olvera", "clase_transportista": "transportista", "activo": False},
    "707673":  {"razon_social": "FERNANDO ORTA ACOSTA", "nom_corto": "Fernando Orta", "clase_transportista": "transportista", "activo": False},
    "700001":  {"razon_social": "FERROMEX SA DE CV", "nom_corto": "Ferromex", "clase_transportista": "Ferroviario", "activo": False},
    "705561":  {"razon_social": "FERROSUR SA DE CV", "nom_corto": "Ferrosur", "clase_transportista": "Ferroviario", "activo": False},
    "708493":  {"razon_social": "FLETERA ITZAE S DE RL DE CV", "nom_corto": "Itzae", "clase_transportista": "transportista", "activo": False},
    "707837":  {"razon_social": "GERARDO PEREZ HERNANDEZ", "nom_corto": "Gerardo Perez", "clase_transportista": "transportista", "activo": False},
    "708457":  {"razon_social": "GRUPO CITRAB", "nom_corto": "Citrab", "clase_transportista": "transportista", "activo": False},
    "706968":  {"razon_social": "JESUS HERNANDEZ TORRES", "nom_corto": "Jesus Hernandez", "clase_transportista": "transportista", "activo": False},
    "707699":  {"razon_social": "JOAQUIN YAÑEZ LEON", "nom_corto": "Joaquin Yañez", "clase_transportista": "transportista", "activo": False},
    "708406":  {"razon_social": "JORGE ALFREDO VILLEDA HERNANDEZ", "nom_corto": "Jorge Alfredo", "clase_transportista": "transportista", "activo": False},
    "708512":  {"razon_social": "JORGE EMMANUEL VILLEDA SALDAÑA", "nom_corto": "Emmanuel Villeda", "clase_transportista": "transportista", "activo": False},
    "705651":  {"razon_social": "JOSE SALOMON VILLEGAS VELAZQUEZ", "nom_corto": "Jose Salomon", "clase_transportista": "transportista", "activo": False},
    "708428":  {"razon_social": "LEOPOLDO BALBOA ALONSO", "nom_corto": "Leopoldo Balboa", "clase_transportista": "transportista", "activo": False},
    "707771":  {"razon_social": "LEOPOLDO MARTIN VAZQUEZ OROPEZA", "nom_corto": "Vazoro", "clase_transportista": "transportista", "activo": False},
    "708213":  {"razon_social": "LUGO MENDEZ ROGER ALBERTO", "nom_corto": "Lugo Mendez", "clase_transportista": "transportista", "activo": False},
    "707835":  {"razon_social": "M & N INDUSTRIAL SOLUTIONS S.A DE C.V", "nom_corto": "M & N", "clase_transportista": "transportista", "activo": False},
    "708231":  {"razon_social": "MADERA DOMINGUEZ VICTOR DE ATOCHA", "nom_corto": "Madera Dominguez", "clase_transportista": "transportista", "activo": False},
    "708489":  {"razon_social": "MARCO ANTONIO VILLALOBOS ARROYO", "nom_corto": "Marco Villalobos", "clase_transportista": "transportista", "activo": False},
    "708542":  {"razon_social": "MAURICIO RAFAEL LEPE VALDEZ", "nom_corto": "Lepe", "clase_transportista": "transportista", "activo": False},
    "707396":  {"razon_social": "MAURICIO YAÑEZ BAUTISTA", "nom_corto": "Mauricio Yañez", "clase_transportista": "transportista", "activo": False},
    "708310":  {"razon_social": "MAURILIO VEGA ESTRADA", "nom_corto": "Maurilio Bega", "clase_transportista": "transportista", "activo": False},
    "706463":  {"razon_social": "OLP CONSTRUCCIONES", "nom_corto": "OLP Cons", "clase_transportista": "transportista", "activo": False},
    "705947":  {"razon_social": "OSCAR SILVA MORA", "nom_corto": "Oscar Silva", "clase_transportista": "transportista", "activo": False},
    "1626586": {"razon_social": "ROBLES FARIAS ADLAI FRANCISCO", "nom_corto": "Adlai Francisco", "clase_transportista": "transportista", "activo": False},
    "707015":  {"razon_social": "SANDRA AZPEITIA GARCIA", "nom_corto": "Sandra Azpeitia", "clase_transportista": "transportista", "activo": False},
    "705800":  {"razon_social": "SERVICIOS LOGISTICOS SULTANES S.A D", "nom_corto": "Los Sultanes", "clase_transportista": "transportista", "activo": False},
    "15733":   {"razon_social": "TRANSPORTACIÓN TERRESTRE ESPECIALIZADA S.A. DE C.V.", "nom_corto": "Transp Especializada", "clase_transportista": "transportista", "activo": False},
    "708080":  {"razon_social": "TRANSPORTADORA GEOS S.A DE C.V.", "nom_corto": "Geos", "clase_transportista": "transportista", "activo": False},
    "1629958": {"razon_social": "TRANSPORTE INGENIERIA Y SERVICIOS T", "nom_corto": "Transp Ingenieia", "clase_transportista": "transportista", "activo": False},
    "708329":  {"razon_social": "TRANSPORTES JORMAC SA DE CV", "nom_corto": "Jormac", "clase_transportista": "transportista", "activo": False},
    "704663":  {"razon_social": "TRANSPORTES PITIC  S.A. DE    C.V.", "nom_corto": "Pitic", "clase_transportista": "autoflete", "activo": False},
    "1628015": {"razon_social": "TRANSPORTES TRIPLE P SAS DE CV", "nom_corto": "Triple P", "clase_transportista": "transportista", "activo": False},
    "708403":  {"razon_social": "TRANSPORTES Y MAQUINARIA SAN FRANCISCO", "nom_corto": "San Francisco", "clase_transportista": "transportista", "activo": False},
    "706150":  {"razon_social": "TRANSPORTISTAS UNIDOS DEL REFUGIO S.A. DE C.V.", "nom_corto": "Tursa", "clase_transportista": "transportista", "activo": False},
    "706296":  {"razon_social": "TRELSA SA DE CV", "nom_corto": "Trelsa", "clase_transportista": "transportista", "activo": False},
    "1900330": {"razon_social": "UNILAND TRADING B.V.", "nom_corto": "Uniland T", "clase_transportista": "transportista", "activo": False},
    "707025":  {"razon_social": "VENY EDGAR GARCIA MARTINEZ", "nom_corto": "Veny Garcia", "clase_transportista": "transportista", "activo": False},
    "708523":  {"razon_social": "VIANEY MENDOZA GALVEZ", "nom_corto": "Vianey Mendoza", "clase_transportista": "transportista", "activo": False},
    "705717":  {"razon_social": "ADOCRETOS DE PUEBLA SA DE CV", "nom_corto": "Adocretos", "clase_transportista": "autoflete", "activo": True},
    "706638":  {"razon_social": "ALVARO ADAN CRUZ LOPEZ", "nom_corto": "Alvaro Adan", "clase_transportista": "transportista", "activo": True},
    "707825":  {"razon_social": "ANA GABRIELA CRUZ FLORES", "nom_corto": "Ana Gabriela", "clase_transportista": "transportista", "activo": True},
    "708496":  {"razon_social": "ANAYELY MARLEN CHOREÑO TESILLO", "nom_corto": "LMR Anayely", "clase_transportista": "transportista", "activo": True},
    "708498":  {"razon_social": "AUTOTRANSPORTES ESPECIALIZADOS ALFA", "nom_corto": "Alfa", "clase_transportista": "transportista", "activo": True},
    "834838":  {"razon_social": "CEMENTOS DEL BAJIO S.A. DE C.V.", "nom_corto": "Cementos del Bajio", "clase_transportista": "transportista", "activo": True},
    "707046":  {"razon_social": "CENTRO DE DISTRIBUCION FORTALEZA MO", "nom_corto": "Dist Foraleza Morelia", "clase_transportista": "transportista", "activo": True},
    "708421":  {"razon_social": "DAFNE GARRIDO RESENDIZ", "nom_corto": "Dafne Garrido", "clase_transportista": "transportista", "activo": True},
    "708192":  {"razon_social": "DIANA VANESSA RAMÍREZ SOTO", "nom_corto": "Diana Vanessa", "clase_transportista": "transportista", "activo": True},
    "705910":  {"razon_social": "EDGAR MONROY FRIAS", "nom_corto": "Edgar Monroy", "clase_transportista": "transportista", "activo": True},
    "707215":  {"razon_social": "FELIPE ALMAZAN HERNANDEZ", "nom_corto": "Felipe Almazan", "clase_transportista": "transportista", "activo": True},
    "708263":  {"razon_social": "FLETES HESA, S. A. DE C. V.", "nom_corto": "Fletes Hesa", "clase_transportista": "transportista", "activo": True},
    "705845":  {"razon_social": "FLETES PREHI, S. DE R.L. DE C.V.", "nom_corto": "Prehi", "clase_transportista": "transportista", "activo": True},
    "823476":  {"razon_social": "FRANCISCO AGUILAR BARRON", "nom_corto": "Fco Aguilar", "clase_transportista": "transportista", "activo": True},
    "708529":  {"razon_social": "FRANCISCO JAVIER MONTEJO RAMIREZ", "nom_corto": "Fco Javier Montejo", "clase_transportista": "transportista", "activo": True},
    "706330":  {"razon_social": "GABRIELA SANCHEZ MENDOZA", "nom_corto": "Gabriela Sanchez", "clase_transportista": "sindicato", "activo": True},
    "707431":  {"razon_social": "GENOVEVA AIDE EUROZA LUGO", "nom_corto": "Genoveva Aide", "clase_transportista": "sindicato", "activo": True},
    "708418":  {"razon_social": "GEOMEM CONSTRUCCIONES", "nom_corto": "Geomem", "clase_transportista": "transportista", "activo": True},
    "706920":  {"razon_social": "GLORIA MONROY HERNANDEZ", "nom_corto": "Gloria Monroy", "clase_transportista": "transportista", "activo": True},
    "1629842": {"razon_social": "GRUPO TRANSMENAGUI SA DE CV", "nom_corto": "Transmenagui", "clase_transportista": "transportista", "activo": True},
    "706856":  {"razon_social": "GUSTAVO RAMIREZ LEON", "nom_corto": "Gustavo Ramirez", "clase_transportista": "transportista", "activo": True},
    "707355":  {"razon_social": "GUSTAVO VELAZQUEZ MELCHOR", "nom_corto": "Gustavo Velazquez", "clase_transportista": "transportista", "activo": True},
    "708463":  {"razon_social": "ISMAEL VELAZQUEZ SANCHEZ", "nom_corto": "Ismael Velazquez", "clase_transportista": "transportista", "activo": True},
    "708398":  {"razon_social": "IVONNE NAVARRETE CRUZ", "nom_corto": "Ivonne Navarrete", "clase_transportista": "transportista", "activo": True},
    "707757":  {"razon_social": "JESUS ALDHEIR SANCHEZ PELAEZ", "nom_corto": "Jesus Aldheir", "clase_transportista": "transportista", "activo": True},
    "707409":  {"razon_social": "JOSE LUIS CRUZ HERNANDEZ", "nom_corto": "Jose Luis Cruz", "clase_transportista": "transportista", "activo": True},
    "707861":  {"razon_social": "JOSUE GABRIEL ALMAZAN ALVARES", "nom_corto": "Josue Almazan", "clase_transportista": "transportista", "activo": True},
    "707656":  {"razon_social": "JUAN CARLOS GARDUNO CRUZ", "nom_corto": "J Carlos Garduño", "clase_transportista": "transportista", "activo": True},
    "708405":  {"razon_social": "KIAV ELECTROCONSTRUCCIONES", "nom_corto": "Kiav", "clase_transportista": "transportista", "activo": False},
    "708425":  {"razon_social": "LI TRANSPORTES SA DE CV", "nom_corto": "Li Transportes", "clase_transportista": "transportista", "activo": True},
    "708091":  {"razon_social": "LOGISTICA EN TRANSPORTE NACIONAL E INTERNACIÓN K + K", "nom_corto": "K + K", "clase_transportista": "sindicato", "activo": True},
    "707895":  {"razon_social": "LOGISTICA ESPECIALIZADA EN PRODUCTO ENVASADO Y GRANEL S DE RL DE CV", "nom_corto": "Logistica Sindicato", "clase_transportista": "sindicato", "activo": True},
    "708446":  {"razon_social": "LOGISTICA OPERACIONES A GRANEL", "nom_corto": "Ops a Granel", "clase_transportista": "transportista", "activo": True},
    "707422":  {"razon_social": "LORENA MENDOZA SANCHEZ", "nom_corto": "Lorena Mendoza", "clase_transportista": "transportista", "activo": True},
    "840041":  {"razon_social": "LORENZO ANTONIO ALMAZAN GONZALEZ", "nom_corto": "Lorenzo Danton", "clase_transportista": "transportista", "activo": True},
    "707800":  {"razon_social": "LUIS FELIPE ALVAREZ", "nom_corto": "Luis Felipe TAM", "clase_transportista": "transportista", "activo": True},
    "708409":  {"razon_social": "MARIA DEL CARMEN ZAMORA RAMIREZ", "nom_corto": "Maria Del Carmen", "clase_transportista": "transportista", "activo": True},
    "706855":  {"razon_social": "MARTIN HERRERA MORENO", "nom_corto": "Martin Herrera", "clase_transportista": "transportista", "activo": True},
    "707681":  {"razon_social": "MIRIAM CAMACHO MOCTEZUMA", "nom_corto": "Miriam Camacho", "clase_transportista": "transportista", "activo": True},
    "708221":  {"razon_social": "MISAEL NATERAS MARTINEZ", "nom_corto": "Misael Nateras", "clase_transportista": "transportista", "activo": True},
    "707286":  {"razon_social": "OMAR ANDRES NAVARRETE CRUZ", "nom_corto": "Omar Navarrete", "clase_transportista": "transportista", "activo": True},
    "707480":  {"razon_social": "PABLO AVILA DIMAS", "nom_corto": "Pablo Avila", "clase_transportista": "transportista", "activo": True},
    "1628471": {"razon_social": "PR CONSTRUCCION Y LOGISTICA", "nom_corto": "PR Logistica", "clase_transportista": "transportista", "activo": True},
    "708115":  {"razon_social": "RAUL GOMEZ HERNANDEZ", "nom_corto": "Raul Gomez", "clase_transportista": "transportista", "activo": True},
    "702551":  {"razon_social": "RETIRADO", "nom_corto": "RETIRADO", "clase_transportista": "transportista", "activo": True},
    "706600":  {"razon_social": "ROGELIO LOPEZ MORENO", "nom_corto": "Rogelio Lopez", "clase_transportista": "transportista", "activo": True},
    "706290":  {"razon_social": "ROGELIO NAVARRETE LOPEZ", "nom_corto": "Rogelio Navarrete", "clase_transportista": "transportista", "activo": True},
    "707375":  {"razon_social": "ROSA ISELA ESPERILLA CRUZ", "nom_corto": "Rosa Isela", "clase_transportista": "transportista", "activo": True},
    "707095":  {"razon_social": "SERGIO ALMAZAN SANCHEZ", "nom_corto": "Sergio Almazan", "clase_transportista": "transportista", "activo": True},
    "1629400": {"razon_social": "SOCIEDAD COOPERATIVA DE PRODUCCION Y PRESTACION DE SERVICIOS CUAUHT", "nom_corto": "Cuauhtemoc", "clase_transportista": "transportista", "activo": True},
    "1628181": {"razon_social": "THS TRANSPORT S.A. DE C.V.", "nom_corto": "THS", "clase_transportista": "transportista", "activo": True},
    "706603":  {"razon_social": "TRACTOCARGA SAN ANGEL S.A. DE C.V.", "nom_corto": "San Angel", "clase_transportista": "transportista", "activo": True},
    "705905":  {"razon_social": "TRANSITIA SC DEL RL DE CV", "nom_corto": "Transitia", "clase_transportista": "transportista", "activo": True},
    "822591":  {"razon_social": "TRANSPORTACION CARRETERA, S.A. DE C.V.", "nom_corto": "Tracsa", "clase_transportista": "transportista", "activo": True},
    "708241":  {"razon_social": "TRANSPORTES ABC DEL CARIBE SA DE CV", "nom_corto": "ABC Del Caribe", "clase_transportista": "transportista", "activo": True},
    "706631":  {"razon_social": "TRANSPORTES DE CARGA EDOS S.A DE C.V", "nom_corto": "Edos", "clase_transportista": "sindicato", "activo": True},
    "708531":  {"razon_social": "TRANSPORTES DEL BAJIO LOPEZ", "nom_corto": "Bajio Lopez", "clase_transportista": "transportista", "activo": True},
    "708202":  {"razon_social": "TRANSPORTES QUERETANOS SA DE CV", "nom_corto": "Queretanos", "clase_transportista": "autoflete", "activo": True},
    "707386":  {"razon_social": "URIEL MONROY GARCIA", "nom_corto": "Uriel Monroy", "clase_transportista": "transportista", "activo": True},
    "708456":  {"razon_social": "URIEL PAREDES PEREZ", "nom_corto": "Uriel Paredes", "clase_transportista": "transportista", "activo": True},
}

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
