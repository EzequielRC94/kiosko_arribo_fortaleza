// zql_bi_catalogo_fechas.pq -> catalogo de fechas
let
    FechaInicio = #date(2026, 1, 1),
    FechaFin = #date(2026, 12, 31),
    Dias = Duration.Days(FechaFin - FechaInicio) + 1,
    ListaFechas = List.Dates(FechaInicio, Dias, #duration(1, 0, 0, 0)),
    TablaFechas = Table.FromList(ListaFechas, Splitter.SplitByNothing(), {"Fecha"}),
    #"Tipo cambiado" = Table.TransformColumnTypes(TablaFechas, {{"Fecha", type date}}),
    #"dia corto" = Table.AddColumn(#"Tipo cambiado", "Nombre del día", each Date.ToText([Fecha], "ddd"), type text),
    Semana = Table.AddColumn(#"dia corto", "Semana", each Date.WeekOfYear([Fecha], Day.Monday), Int64.Type),
    EtiquetaSemana = Table.AddColumn(
        Semana, "Etiqueta Semana", each "Sem " & Text.PadStart(Text.From([Semana]), 2, "0"), type text
    ),
    #"Nombre del mes insertado" = Table.AddColumn(
        EtiquetaSemana, "Nombre del mes", each Text.Proper(Date.MonthName([Fecha])), type text
    ),
    #"Año insertado" = Table.AddColumn(#"Nombre del mes insertado", "Año", each Date.Year([Fecha]), Int64.Type),
    #"Columna combinada insertada" = Table.AddColumn(
        #"Año insertado", "mes_año", each [Nombre del mes] & "_" & Text.From([Año]), type text
    ),
    #"Nombre del día insertado" = Table.AddColumn(
        #"Columna combinada insertada", "Nombre del día completo", each Date.DayOfWeekName([Fecha]), type text
    ),
    #"Día de la semana insertado" = Table.AddColumn(
        #"Nombre del día insertado", "Día de la semana", each Date.DayOfWeek([Fecha], Day.Monday) + 1, Int64.Type
    ),
    Festivos = {
        #date(2026, 1, 1),
        #date(2026, 2, 2),
        #date(2026, 3, 16),
        #date(2026, 4, 2),
        #date(2026, 4, 3),
        #date(2026, 4, 4),
        #date(2026, 5, 1),
        #date(2026, 9, 16),
        #date(2026, 11, 16),
        #date(2026, 12, 12),
        #date(2026, 12, 25)
    },
    ConDescanso = Table.AddColumn(
        #"Día de la semana insertado",
        "EsDescanso",
        each if Date.DayOfWeek([Fecha], Day.Sunday) = 0 then 1 else 0,
        Int64.Type
    ),
    ConFestivo = Table.AddColumn(
        ConDescanso, "EsFestivo", each if List.Contains(Festivos, [Fecha]) then 1 else 0, Int64.Type
    ),
    ConDiaHabil = Table.AddColumn(
        ConFestivo, "EsDiaHabil", each if [EsDescanso] = 0 and [EsFestivo] = 0 then 1 else 0, Int64.Type
    )
in
    ConDiaHabil
