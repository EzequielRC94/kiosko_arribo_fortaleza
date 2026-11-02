# test_robot.py
from _zql_robot import obtener_ruta_base_drive
from manager_descargas import DescargasManager


def _probar_descargas_manager(dias_atras: int = 120, ruta_base_drive: str = None, forzar: bool = True):
    """
    Descarga los archivos de la transacción ZSDMX267 para los últimos 'dias_atras' días.
    - forzar=True: vuelve a descargar y sobreescribir aunque ya existan en disco.
    """
    if ruta_base_drive is None:
        ruta_base_drive = obtener_ruta_base_drive()

    print(f"🚀 Iniciando descarga de ZSDMX267 para los últimos {dias_atras} días...")
    print(f"📁 Ruta destino: {ruta_base_drive}")

    manager_descargas = DescargasManager()
    resultado = manager_descargas.zsdmx267_robot(
        ruta_base_drive=ruta_base_drive,
        dias_atras=dias_atras,
        extension="xls",
        forzar=forzar
    )
    return resultado


if __name__ == "__main__":
    _probar_descargas_manager(dias_atras=120, forzar=True)

