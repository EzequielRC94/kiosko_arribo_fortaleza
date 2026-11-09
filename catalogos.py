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
        "activo": True
    },
    "Planta Palmar": {
        "nombre_centro": "Palmar",
        "codigos": ["MX16"],
        "letra": "P",
        "tipo_centro": "Planta",
        "turnos_operativos": 3,
        "activo": True
    },
    "Planta Progreso": {
        "nombre_centro": "Progreso",
        "codigos": ["MX76"],
        "letra": "M",
        "tipo_centro": "Planta",
        "turnos_operativos": 2,
        "activo": True
    },
    "Planta Vito": {
        "nombre_centro": "Vito",
        "codigos": ["MX46"],
        "letra": "V",
        "tipo_centro": "Planta",
        "turnos_operativos": 2,
        "activo": True
    },
    "CEDIS GDL": {
        "nombre_centro": "Gdl",
        "codigos": ["MX83"],
        "letra": "G",
        "tipo_centro": "Cedis",
        "turnos_operativos": 2,
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


def actualizar_todos_catalogos_pq(directorio_base: str = None) -> dict:
    """
    Actualiza todos los catálogos Power Query a partir de catalogos.py.
    Ejecuta generar_m_materiales() y generar_m_centros(), escribiendo los archivos en directorio_base.
    Si no se especifica directorio_base, se toma la carpeta actual donde reside este archivo.
    """
    if directorio_base is None:
        directorio_base = os.path.dirname(os.path.abspath(__file__))

    catalogos_a_generar = {
        "materiales": ("zql_bi_catalogo_materiales.pq", generar_m_materiales()),
        "centros": ("zql_bi_catalogo_centros.pq", generar_m_centros())
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
