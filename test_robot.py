# test_robot.py
import os
import json
from datetime import datetime
from manager_descargas import DescargasManager


def obtener_ruta_base_drive() -> str:
    """Calcula la ruta base operativa del año actual."""
    perfil_usuario = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    anio_actual = datetime.now().strftime("%Y")
    return os.path.join(
        perfil_usuario,
        "Elementia S. A",
        "kiosko logistica cem - Documentos",
        anio_actual
    )


def probar_descargas_manager():
    """
    Instancia DescargasManager y ejecuta todas sus funciones de descarga
    para validar su funcionamiento.
    """
    ruta_base_drive = obtener_ruta_base_drive()
    manager = DescargasManager()

    print("=" * 70)
    print(" 🧪 INICIANDO PRUEBA DE DESCARGAS MANAGER")
    print(f" 📁 Ruta Base Drive: {ruta_base_drive}")
    print("=" * 70)

    # 1. Probar zsdmx389_robot (pendientes y en_proceso)
    print("\n▶ [1/2] Ejecutando: zsdmx389_robot (tipo_descarga='ambos')...")
    try:
        res_389 = manager.zsdmx389_robot(ruta_base_drive=ruta_base_drive, tipo_descarga="ambos")
        print(f"📋 Resultado zsdmx389_robot:\n{json.dumps(res_389, indent=4, ensure_ascii=False)}")
    except Exception as e_389:
        print(f"❌ Error en zsdmx389_robot: {e_389}")

    # 2. Probar zsdmx249_robot (hoy a -3 días)
    print("\n▶ [2/2] Ejecutando: zsdmx249_robot (dias_atras=3)...")
    try:
        res_249 = manager.zsdmx249_robot(ruta_base_drive=ruta_base_drive, dias_atras=3, extension="csv")
        print(f"📋 Resultado zsdmx249_robot:\n{json.dumps(res_249, indent=4, ensure_ascii=False)}")
    except Exception as e_249:
        print(f"❌ Error en zsdmx249_robot: {e_249}")

    print("\n" + "=" * 70)
    print(" 🏁 PRUEBA FINALIZADA")
    print("=" * 70)


if __name__ == "__main__":
    probar_descargas_manager()

