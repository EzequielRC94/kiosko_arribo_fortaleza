// zql_bi_catalogo_centros.pq -> catalogo de centros generado desde catalogos.py

let
    Origen = Table.FromRows({
        {"MX47", "Tula", "Planta", true},
        {"MX57", "Tula", "Planta", true},
        {"MX16", "Palmar", "Planta", true},
        {"MX76", "Progreso", "Planta", true},
        {"MX46", "Vito", "Planta", true},
        {"MX83", "Gdl", "Cedis", true},
        {"MX84", "Huehuetoca", "Cross Dock", false},
        {"MX86", "Mazatlan", "Cedis", false},
        {"MX87", "Merida", "Cedis", false},
        {"MX89", "Mexicali", "Cedis", false},
        {"MX90", "Huehuetoca", "Cross Dock", false},
        {"MX91", "Atotonilco", "Cross Dock", false},
        {"MX93", "Veracruz", "Cedis", false},
        {"MX41", "Virtual Tuxpan", null, false},
        {"MX77", "La Paz", "Cedis", false}
    },
    {"c_exp", "nombre_centro", "tipo_centro", "activo"}),
    #"Tipo cambiado" = Table.TransformColumnTypes(Origen,{
        {"c_exp", type text},
        {"nombre_centro", type text},
        {"tipo_centro", type text},
        {"activo", type logical}
    })
in
    #"Tipo cambiado"
