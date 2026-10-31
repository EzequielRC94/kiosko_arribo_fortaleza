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
    print("\n▶ [1/5] Ejecutando: zsdmx389_robot (tipo_descarga='ambos')...")
    try:
        res_389 = manager.zsdmx389_robot(ruta_base_drive=ruta_base_drive, tipo_descarga="ambos")
        print(f"📋 Resultado zsdmx389_robot:\n{json.dumps(res_389, indent=4, ensure_ascii=False)}")
    except Exception as e_389:
        print(f"❌ Error en zsdmx389_robot: {e_389}")

    # 2. Probar zsdmx249_robot (hoy a -3 días, CSV)
    print("\n▶ [2/5] Ejecutando: zsdmx249_robot (dias_atras=3, extension='csv')...")
    try:
        res_249 = manager.zsdmx249_robot(ruta_base_drive=ruta_base_drive, dias_atras=3, extension="csv")
        print(f"📋 Resultado zsdmx249_robot:\n{json.dumps(res_249, indent=4, ensure_ascii=False)}")
    except Exception as e_249:
        print(f"❌ Error en zsdmx249_robot: {e_249}")

    # 3. Probar zsdmx267_robot (hoy a -3 días, XLS)
    print("\n▶ [3/5] Ejecutando: zsdmx267_robot (dias_atras=3, extension='xls')...")
    try:
        res_267 = manager.zsdmx267_robot(ruta_base_drive=ruta_base_drive, dias_atras=3, extension="xls")
        print(f"📋 Resultado zsdmx267_robot:\n{json.dumps(res_267, indent=4, ensure_ascii=False)}")
    except Exception as e_267:
        print(f"❌ Error en zsdmx267_robot: {e_267}")

    # 4. Probar vt16_robot (mes en curso, CSV)
    print("\n▶ [4/5] Ejecutando: vt16_robot (mes en curso, extension='csv')...")
    try:
        res_vt16 = manager.vt16_robot(ruta_base_drive=ruta_base_drive, extension="csv")
        print(f"📋 Resultado vt16_robot:\n{json.dumps(res_vt16, indent=4, ensure_ascii=False)}")
    except Exception as e_vt16:
        print(f"❌ Error en vt16_robot: {e_vt16}")

    # 5. Probar fbl4n_robot (mes en curso, XLS)
    print("\n▶ [5/5] Ejecutando: fbl4n_robot (mes en curso, extension='xls')...")
    try:
        res_fbl4n = manager.fbl4n_robot(ruta_base_drive=ruta_base_drive, extension="xls")
        print(f"📋 Resultado fbl4n_robot:\n{json.dumps(res_fbl4n, indent=4, ensure_ascii=False)}")
    except Exception as e_fbl4n:
        print(f"❌ Error en fbl4n_robot: {e_fbl4n}")

    print("\n" + "=" * 70)
    print(" 🏁 PRUEBA FINALIZADA")
    print("=" * 70)


if __name__ == "__main__":
    probar_descargas_manager()
