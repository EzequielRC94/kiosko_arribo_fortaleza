# test_descargas.py
import os
from manager_sap import SAPManager

def ejecutar_prueba_robot():
    print("🚀 Iniciando prueba aislada del Robot ZSDMX389...")
    
    # 1. Definir una ruta de prueba temporal
    # Usamos una carpeta "Prueba_Kiosko" para no mezclar datos con tu operación real
    user_profile = os.path.expanduser("~")
    ruta_prueba = os.path.join(user_profile, "Descargas")
    
    print(f"📂 Ruta base configurada para la prueba: {ruta_prueba}")
    
    # 2. Instanciar el manager de SAP
    sap = SAPManager()
    
    # 3. Validar conexión antes de arrancar
    if not sap.validar_conexion():
        print("❌ No se detectó una sesión activa de SAP.")
        print("💡 Acción: Por favor, abre SAP GUI, inicia sesión y vuelve a correr este test.")
        return
        
    print("✅ Conexión con SAP detectada. Ejecutando descargas...\n")
    
    # 4. Ejecutar el robot y capturar el "acuse de recibo" (El diccionario)
    try:
        # Llamamos a la función que acabamos de refactorizar
        rutas_generadas = sap.zsdmx389_robot(ruta_base_drive=ruta_prueba)
        
        # 5. Imprimir los resultados del diccionario
        print("\n🎉 ¡EJECUCIÓN EXITOSA! Acuse de recibo del robot:")
        print("-" * 60)
        print(f"📄 Archivo Pendientes : {rutas_generadas.get('pendientes', 'No generado')}")
        print(f"📄 Archivo En Proceso : {rutas_generadas.get('en_proceso', 'No generado')}")
        print("-" * 60)
        
        # 6. Validación física: Comprobar que SAP realmente escribió los archivos en el disco
        print("\n🔍 Verificación física en disco duro:")
        for clave, ruta in rutas_generadas.items():
            if os.path.exists(ruta):
                tamano_kb = os.path.getsize(ruta) / 1024
                print(f"  ✔️ El archivo '{clave}' EXISTE. Tamaño: {tamano_kb:.2f} KB")
            else:
                print(f"  ⚠️ El archivo '{clave}' NO se encontró en la ruta esperada.")
                
    except Exception as e:
        print(f"\n❌ Ocurrió un error durante la ejecución del robot: {e}")
        print("💡 Recuerda: Detectar esto ahora es una victoria. Revisa el mensaje para ajustar el código.")

if __name__ == "__main__":
    ejecutar_prueba_robot()