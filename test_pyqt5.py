import os
import win32com.client as win32

# Definimos la ruta de la carpeta (usamos r"" para que lea correctamente las barras invertidas)
carpeta = r"C:\Users\aramirezc\Elementia S. A\Cementos Tula Embarques - Documentos\Arribo\2026\09 SEPTIEMBRE"

def actualizar_reportes():
    # Iniciamos la aplicación de Excel en segundo plano
    excel = win32.Dispatch("Excel.Application")
    excel.Visible = False # Cambia a True si quieres ver cómo lo hace
    excel.DisplayAlerts = False # Evita ventanas emergentes de "Guardar cambios"
    
    # Constante de VBA para xlDown
    xlDown = -4121 

    try:
        # Iteramos por todos los archivos en la carpeta
        for archivo in os.listdir(carpeta):
            if archivo.endswith(".xlsm") and not archivo.startswith("~$"):
                ruta_completa = os.path.join(carpeta, archivo)
                print(f"Procesando: {archivo}")
                
                # Abrimos el libro
                wb = excel.Workbooks.Open(ruta_completa)
                
                try:
                    ws = wb.Sheets("Reporte_Tula")
                    
                    # Evaluamos si E26 es MORTERO FZ 50
                    if ws.Range("E26").Value == "MORTERO FZ 50":
                        
                        # Range("E26:O26").Select / Selection.Insert Shift:=xlDown
                        ws.Range("E26:O26").Insert(Shift=xlDown)
                        
                        # Escribimos el nuevo valor en E26
                        ws.Range("E26").Value = "MORTERO FZ 25"
                        
                        # Insertamos las fórmulas. 
                        # Usamos .FormulaLocal porque tus fórmulas están en español.
                        # Nota: Corregí el I20 de tu instrucción a I26 para mantener la congruencia de la fila.
                        ws.Range("F26").FormulaLocal = '=SUMAR.SI.CONJUNTO(Tabla_Arribo[TON], Tabla_Arribo[MATERIAL], E26, Tabla_Arribo[FCH SALIDA], ">="&fch_archivo, Tabla_Arribo[FCH SALIDA], "<"&fch_archivo+1)'
                        ws.Range("G26").FormulaLocal = '=BUSCARX(E26,torre_control[Material],torre_control[Ton Objetivo x día],"")'
                        ws.Range("H26").FormulaLocal = '=SI.ERROR(F26/G26,"")'
                        ws.Range("I26").FormulaLocal = '=SUMAR.SI.CONJUNTO(Tabla_Arribo[TON],Tabla_Arribo[MATERIAL],Reporte_Tula!E26)-F26'
                        
                        # Guardamos los cambios
                        wb.Save()
                        print(" -> Modificado y guardado con éxito.")
                    else:
                        print(" -> No requiere modificación (E26 no es MORTERO FZ 50).")
                        
                except Exception as e:
                    print(f" -> Error en la hoja Reporte_Tula: {e}")
                
                finally:
                    # Cerramos el libro
                    wb.Close()
                    
    finally:
        # Cerramos Excel y liberamos memoria (Crucial para no dejar procesos fantasmas)
        excel.Quit()
        print("Proceso finalizado.")

if __name__ == "__main__":
    actualizar_reportes()