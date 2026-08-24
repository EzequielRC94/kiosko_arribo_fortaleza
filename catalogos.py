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
    "1321185": {"desc_nom_corto": "PATRIA 50",       "grupo": "ENVASADO", "bg": "#00C4DE", "fg": "#000000"},
    "41303":   {"desc_nom_corto": "BCO 50",          "grupo": "ENVASADO", "bg": "#D664FA", "fg": "#000000"},
    "41304":   {"desc_nom_corto": "BCO 25",          "grupo": "ENVASADO", "bg": "#FAB4FA", "fg": "#000000"},
    "41309":   {"desc_nom_corto": "MORTERO UL",      "grupo": "ENVASADO", "bg": "#FFBA82", "fg": "#000000"},
    "41320":   {"desc_nom_corto": "FORTALEZA RS 50", "grupo": "ENVASADO", "bg": "#46C8D7", "fg": "#000000"},
    "41321":   {"desc_nom_corto": "MAGNO RS 50",     "grupo": "ENVASADO", "bg": "#228B22", "fg": "#FFFFFF"},
    "41336":   {"desc_nom_corto": "FORTALEZA 50",    "grupo": "ENVASADO", "bg": "#46C8D7", "fg": "#000000"},
    "41337":   {"desc_nom_corto": "MORTERO FZ 50",   "grupo": "ENVASADO", "bg": "#F79646", "fg": "#000000"},
    "1319772": {"desc_nom_corto": "ESTUCO",          "grupo": "ENVASADO", "bg": "#C8EBC8", "fg": "#000000"},
    "1330688": {"desc_nom_corto": "FORTALEZA RS 25", "grupo": "ENVASADO", "bg": "#A0F0F5", "fg": "#000000"},
    "1330691": {"desc_nom_corto": "MORTERO FZ 25",   "grupo": "ENVASADO", "bg": "#FFD2A0", "fg": "#000000"},
    "1330689": {"desc_nom_corto": "MAGNO RS 25",     "grupo": "ENVASADO", "bg": "#AAE1AA", "fg": "#000000"},
    "1330690": {"desc_nom_corto": "FORTALEZA 25",    "grupo": "ENVASADO", "bg": "#A0F0F5", "fg": "#000000"},
    "1331169": {"desc_nom_corto": "MAGNO 25",        "grupo": "ENVASADO", "bg": "#96EB96", "fg": "#000000"},
    "1331156": {"desc_nom_corto": "MAGNO 50",        "grupo": "ENVASADO", "bg": "#00B050", "fg": "#000000"},
    "1331390": {"desc_nom_corto": "PATRIA 50",       "grupo": "ENVASADO", "bg": "#00C4DE", "fg": "#000000"},
    "1331391": {"desc_nom_corto": "PATRIA 25",       "grupo": "ENVASADO", "bg": "#A0EBFA", "fg": "#000000"},
    "41307":   {"desc_nom_corto": "BCO 25_MZ",       "grupo": "ENVASADO", "bg": "#FAB4FA", "fg": "#000000"},
    "1330641": {"desc_nom_corto": "RS 42.6",         "grupo": "GRANEL",   "bg": "#A24E56", "fg": "#FFFFFF"},

    # --- GRANEL --- (Colores extraídos de tu lógica VBA)
    "974360":  {"desc_nom_corto": "BCO GRANEL",     "grupo": "GRANEL", "bg": "#CA2BFA", "fg": "#FFFFFF"}, # 
    "974527":  {"desc_nom_corto": "GRANEL RS",      "grupo": "GRANEL", "bg": "#A24E56", "fg": "#FFFFFF"}, # Vino tinto
    "974531":  {"desc_nom_corto": "GRANEL",         "grupo": "GRANEL", "bg": "#5E1B21", "fg": "#FFFFFF"}, # Rojo oscuro (Granel L2)
    "981035":  {"desc_nom_corto": "GRANEL MEXALIT", "grupo": "GRANEL", "bg": "#8C4EA2", "fg": "#FFFFFF"}, # Morado oscuro

    # --- BIG BAG ---
    "41335":   {"desc_nom_corto": "BIG BAG",        "grupo": "ENVASADO", "bg": "#00B0F0", "fg": "#000000"}, # Azul cielo intenso
    "1319631": {"desc_nom_corto": "BIG BAG RS",     "grupo": "ENVASADO", "bg": "#00B0F0", "fg": "#000000"},
    
    # --- SACOS / INSUMOS --- (Color Gris Estándar para todos)
    "85901":   {"desc_nom_corto": "SACO BCO25",         "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "85903":   {"desc_nom_corto": "SACO M FZ50",        "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "85904":   {"desc_nom_corto": "SACO BCO50",         "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "85945":   {"desc_nom_corto": "SACO PROPILENO",     "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "85948":   {"desc_nom_corto": "SACO MG",            "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "85950":   {"desc_nom_corto": "SACO RS",            "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "85951":   {"desc_nom_corto": "SACO RS",            "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "87885":   {"desc_nom_corto": "SACO M FZ",          "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "87888":   {"desc_nom_corto": "SACO M UL",          "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "88657":   {"desc_nom_corto": "SACO ESTUCO",        "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "88845":   {"desc_nom_corto": "SACO PATRIA",        "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "89245":   {"desc_nom_corto": "SACO MAGNO LINER",   "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "89247":   {"desc_nom_corto": "SACO RS LINER",      "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "85949":   {"desc_nom_corto": "SACO SUPREMO",       "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "89756":   {"desc_nom_corto": "SACO 30R 25",        "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "89518":   {"desc_nom_corto": "SACO MORTERO FZ 25", "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "89520":   {"desc_nom_corto": "SACO 30R MAGNO 25",  "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "89517":   {"desc_nom_corto": "SACO RS 25",         "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"},
    "89956":   {"desc_nom_corto": "SACO RS MAGNO 25",   "grupo": "SACO", "bg": "#D3D3D3", "fg": "#000000"}
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