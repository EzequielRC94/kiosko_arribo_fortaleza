import os
import glob
import pandas as pd

def analizar_archivo_sap():
    print(">>> 🚀 INICIANDO MODO RAYOS X PARA SAP/PANDAS <<<\n")

    # --- 1. BUSCAR EL ARCHIVO ---
    user_profile = os.path.expanduser("~")
    ruta_carpeta = os.path.join(user_profile, "Elementia S. A", "autoarribo", "zsdmx389")
    
    if not os.path.exists(ruta_carpeta):
        ruta_carpeta = os.path.join(user_profile, "Documentos", "autoarribo", "zsdmx389")

    archivos = glob.glob(os.path.join(ruta_carpeta, "ZSDMX389_*.csv"))
    if not archivos:
        print("❌ No se encontraron archivos de contingencia.")
        return

    archivo_reciente = max(archivos, key=os.path.getmtime)
    print(f"📁 Analizando: {os.path.basename(archivo_reciente)}\n")

    # --- 2. LECTURA CRUDA (PYTHON PURO) ---
    print("="*60)
    print(" 🕵️‍♂️ PASO 1: LECTURA EN CRUDO (Viendo caracteres ocultos)")
    print("="*60)
    try:
        with open(archivo_reciente, 'r', encoding='latin1') as f:
            for i in range(10): # Leemos solo las primeras 10 líneas
                linea = f.readline()
                if not linea: break
                
                # repr() es la magia aquí: nos muestra exactamente cómo viene el texto 
                # (ej. si hay tabuladores dirá \t)
                print(f"Línea {i}: {repr(linea)}")
    except Exception as e:
        print(f"Error en lectura cruda: {e}")

    print("\n" + "="*60)
    print(" 🐼 PASO 2: LECTURA CON PANDAS (Cómo lo ve la librería)")
    print("="*60)
    
    # --- 3. LECTURA CON PANDAS ---
    try:
        # header=None fuerza a Pandas a leer TODO, desde la línea 0, sin asumir títulos
        df = pd.read_csv(archivo_reciente, sep='\t', header=None, encoding='latin1', dtype=str)
        
        # Iteramos las primeras 10 filas de Pandas
        for index, row in df.head(10).iterrows():
            print(f"--- Fila de Pandas {index} ---")
            
            # Convertimos la fila a una lista y limpiamos un poco para que sea fácil de leer en consola
            valores = [str(val).strip() for val in row.values]
            print(valores)
            
    except Exception as e:
        print(f"Error en lectura Pandas: {e}")

if __name__ == "__main__":
    analizar_archivo_sap()