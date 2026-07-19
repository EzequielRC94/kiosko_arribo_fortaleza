import os
import shutil

# --- CONFIGURACIÓN ---
# Se utiliza 'r' antes de la cadena para que lea correctamente las barras invertidas en Windows
ruta_base = r"C:\Users\aramirezc\OneDrive - Elementia S. A\Documentos\data"

def reestructurar_carpetas(base_dir):
    if not os.path.exists(base_dir):
        print(f"La ruta base '{base_dir}' no existe. Verifica la ruta.")
        return

    print("Iniciando la reestructuración de archivos...")

    # 1. Recorrer la estructura actual (data > mes > transaccion > archivos)
    for mes in os.listdir(base_dir):
        ruta_mes = os.path.join(base_dir, mes)

        # Verificar que sea una carpeta de mes (ej. 01_enero)
        if os.path.isdir(ruta_mes) and any(
            mes.startswith(f"{i:02d}_") for i in range(1, 13)
        ):

            for transaccion in os.listdir(ruta_mes):
                ruta_transaccion_vieja = os.path.join(ruta_mes, transaccion)

                if os.path.isdir(ruta_transaccion_vieja):
                    # Nueva ruta de destino (data > transaccion > mes)
                    ruta_transaccion_nueva = os.path.join(
                        base_dir, transaccion, mes
                    )

                    # Crear la nueva estructura si no existe
                    os.makedirs(ruta_transaccion_nueva, exist_ok=True)

                    # Mover los archivos a la nueva ubicación
                    for archivo in os.listdir(ruta_transaccion_vieja):
                        origen_archivo = os.path.join(
                            ruta_transaccion_vieja, archivo
                        )
                        destino_archivo = os.path.join(
                            ruta_transaccion_nueva, archivo
                        )

                        if os.path.isfile(origen_archivo):
                            try:
                                shutil.move(origen_archivo, destino_archivo)
                                print(f"Movido: {archivo} -> {transaccion}/{mes}/")
                            except Exception as e:
                                print(f"Error al mover {archivo}: {e}")

    # 2. LIMPIEZA: Eliminar carpetas de meses que quedaron vacías
    print("\nLimpiando carpetas vacías...")
    for mes in os.listdir(base_dir):
        ruta_mes = os.path.join(base_dir, mes)
        
        if os.path.isdir(ruta_mes) and any(
            mes.startswith(f"{i:02d}_") for i in range(1, 13)
        ):
            # Eliminar las subcarpetas de transacciones vacías
            for transaccion in os.listdir(ruta_mes):
                ruta_trans_vieja = os.path.join(ruta_mes, transaccion)
                if (
                    os.path.isdir(ruta_trans_vieja)
                    and not os.listdir(ruta_trans_vieja)
                ):
                    os.rmdir(ruta_trans_vieja)

            # Eliminar la carpeta del mes si ya no tiene nada adentro
            if not os.listdir(ruta_mes):
                os.rmdir(ruta_mes)
                print(f"Carpeta original eliminada: {mes}/")

    print("\n¡Proceso de reestructuración finalizado! Listo para Power BI.")


if __name__ == "__main__":
    reestructurar_carpetas(ruta_base)