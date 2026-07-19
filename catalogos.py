# catalogos.py

# ==============================================================================
# CATÁLOGO DE PLANTAS Y CENTROS DE EXPEDICIÓN
# ==============================================================================
CATALOGO_PLANTAS = {
    "Planta Tula":      ["MX47", "MX57"],
    "Planta Palmar":    ["MX16"],
    "Planta Progreso":  ["MX76"],
    "Planta Vito":      ["MX46"],
    "CEDIS GDL":        ["MX83"]
}

# ==============================================================================
# BASE DE DATOS DE MATERIALES (SKUs)
# ==============================================================================
CATALOGO_MATERIALES = {
    # --- ENVASADO ---
    "1321185": {"desc_nom_corto": "PATRIA 50",      "grupo": "ENVASADO"},
    "41303":   {"desc_nom_corto": "BCO 50",         "grupo": "ENVASADO"},
    "41304":   {"desc_nom_corto": "BCO 25",         "grupo": "ENVASADO"},
    "41309":   {"desc_nom_corto": "MORTERO UL",     "grupo": "ENVASADO"},
    "41320":   {"desc_nom_corto": "CPC 30 RS 50",   "grupo": "ENVASADO"},
    "41321":   {"desc_nom_corto": "MAGNO RS 50",    "grupo": "ENVASADO"},
    "41336":   {"desc_nom_corto": "CPC30 RS 50",    "grupo": "ENVASADO"},
    "41337":   {"desc_nom_corto": "MORTERO FZ 50",  "grupo": "ENVASADO"},
    "1319772": {"desc_nom_corto": "ESTUCO",         "grupo": "ENVASADO"},
    "1330688": {"desc_nom_corto": "CPC 30 RS 25",   "grupo": "ENVASADO"},
    "1330691": {"desc_nom_corto": "MORTERO FZ 25",  "grupo": "ENVASADO"},
    "1330689": {"desc_nom_corto": "MAGNO RS 25",    "grupo": "ENVASADO"},
    "1330690": {"desc_nom_corto": "CPC 30 R 25",    "grupo": "ENVASADO"},
    "1331169": {"desc_nom_corto": "MAGNO 25",       "grupo": "ENVASADO"},
    "1331156": {"desc_nom_corto": "MAGNO 50",       "grupo": "ENVASADO"},
    "1331390": {"desc_nom_corto": "PATRIA 50",      "grupo": "ENVASADO"},
    "1331391": {"desc_nom_corto": "PATRIA 25",      "grupo": "ENVASADO"},
    "41307":   {"desc_nom_corto": "BCO 25_MZ",      "grupo": "ENVASADO"},
    "1330641": {"desc_nom_corto": "RS 42.6",        "grupo": "ENVASADO"},

    # --- GRANEL ---
    "974360":  {"desc_nom_corto": "BCO GRANEL",     "grupo": "GRANEL"},
    "974527":  {"desc_nom_corto": "GRANEL RS",      "grupo": "GRANEL"},
    "974531":  {"desc_nom_corto": "GRANEL",         "grupo": "GRANEL"},
    "981035":  {"desc_nom_corto": "GRANEL MEXALIT", "grupo": "GRANEL"},

    # --- BIG BAG ---
    "41335":   {"desc_nom_corto": "BIG BAG",        "grupo": "ENVASADO"},
    "1319631": {"desc_nom_corto": "BIG BAG RS",     "grupo": "ENVASADO"},
    
    # --- SACOS / INSUMOS ---
    "85901":   {"desc_nom_corto": "SACO BCO25",         "grupo": "SACO"},
    "85903":   {"desc_nom_corto": "SACO M FZ50",        "grupo": "SACO"},
    "85904":   {"desc_nom_corto": "SACO BCO50",         "grupo": "SACO"},
    "85945":   {"desc_nom_corto": "SACO PROPILENO",     "grupo": "SACO"},
    "85948":   {"desc_nom_corto": "SACO MG",            "grupo": "SACO"},
    "85950":   {"desc_nom_corto": "SACO RS",            "grupo": "SACO"},
    "85951":   {"desc_nom_corto": "SACO RS",            "grupo": "SACO"},
    "87885":   {"desc_nom_corto": "SACO M FZ",          "grupo": "SACO"},
    "87888":   {"desc_nom_corto": "SACO M UL",          "grupo": "SACO"},
    "88657":   {"desc_nom_corto": "SACO ESTUCO",        "grupo": "SACO"},
    "88845":   {"desc_nom_corto": "SACO PATRIA",        "grupo": "SACO"},
    "89245":   {"desc_nom_corto": "SACO MAGNO LINER",   "grupo": "SACO"},
    "89247":   {"desc_nom_corto": "SACO RS LINER",      "grupo": "SACO"},
    "85949":   {"desc_nom_corto": "SACO SUPREMO",       "grupo": "SACO"},
    "89756":   {"desc_nom_corto": "SACO 30R 25",        "grupo": "SACO"},
    "89518":   {"desc_nom_corto": "SACO MORTERO FZ 25", "grupo": "SACO"},
    "89520":   {"desc_nom_corto": "SACO 30R MAGNO 25",  "grupo": "SACO"},
    "89517":   {"desc_nom_corto": "SACO RS 25",         "grupo": "SACO"},
    "89956":   {"desc_nom_corto": "SACO RS MAGNO 25",   "grupo": "SACO"}
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