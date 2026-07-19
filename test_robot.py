import sys
import json
from manager_sap import SAPManager, SAPError


# ==============================================================================
# 1. CONFIGURACIÓN GLOBAL DE LA PRUEBA (Edita aquí)
# ==============================================================================
# Estos datos se usarán para AMBAS pruebas (Báscula y Transporte)
DATOS_PRUEBA = {
    "remisiones": [
        {"remision": "7532688810"}, 
        #{"remision": "7531875059"} # Puedes descomentar para probar multiples
    ],
    "centro_exp": "MX16",           # MX57, MX47, MX83...
    "modalidad": "RETIRADO",        # RETIRADO, ENTREGADO, AUTOFLETE
    "operador": "JUAN JOSÉ ÁLVAREZ CABALLERO",
    "placas": "59AC2T",
    "tipo_remision_sap": "ZAM1",    # Para Folio Báscula (ZAM1, TRASPASO, INTERCO)
    "clase_exp_f": "F2"             # Para Transporte (F1, F2...)
}
# ==============================================================================

def probar_folio_bascula(robot):
    """Prueba la creación del Folio de Báscula usando DATOS_PRUEBA."""
    
    # Preparamos string para imprimir
    txt_rems = ", ".join([r["remision"] for r in DATOS_PRUEBA["remisiones"]])
    print(f"\n--- ⚖️ INICIANDO PRUEBA: FOLIO BÁSCULA ({txt_rems}) ---")

    try:
        # Ejecutamos la función del robot
        folio_resultado = robot.crear_folio_bascula(
            remisiones=DATOS_PRUEBA["remisiones"],
            centro_expedicion=DATOS_PRUEBA["centro_exp"], 
            tipo_remision=DATOS_PRUEBA["tipo_remision_sap"], 
            operador=DATOS_PRUEBA["operador"], 
            placas=DATOS_PRUEBA["placas"], 
            modalidad=DATOS_PRUEBA["modalidad"]
        )

        if folio_resultado:
            print(f" ✅ FOLIO CREADO EXITOSAMENTE: {folio_resultado}") 
            return True
        else:
            print(" ⚠️ El robot devolvió vacío (¿Error en folio de bascula?)")
            return False

    except SAPError as e:
        print(f" ⛔ ERROR DE NEGOCIO (Báscula): {e}")
        return False
    except Exception as e:
        print(f" ❌ ERROR CRÍTICO (Báscula): {e}")
        return False

def probar_crear_transporte(robot):
    """Prueba la creación del Transporte usando DATOS_PRUEBA."""
    
    txt_rems = ", ".join([r["remision"] for r in DATOS_PRUEBA["remisiones"]])
    print(f"\n--- 🚚 INICIANDO PRUEBA: TRANSPORTE VT01N ({txt_rems}) ---")

    try:
        no_transporte = robot.crear_transporte(
            remisiones=DATOS_PRUEBA["remisiones"],
            centro_expedicion=DATOS_PRUEBA["centro_exp"],
            modalidad=DATOS_PRUEBA["modalidad"],
            operador=DATOS_PRUEBA["operador"],
            placas=DATOS_PRUEBA["placas"],
            clase_expedicion_f=DATOS_PRUEBA["clase_exp_f"]
        )

        if no_transporte:
            print(f" ✅ TRANSPORTE CREADO EXITOSAMENTE: {no_transporte}") 
            return True
        else:
            print(" ⚠️ El robot terminó sin errores pero no devolvió número.")
            return False

    except SAPError as e:
        print(f" ⛔ ERROR DE NEGOCIO (Transporte): {e}")
        return False
    except Exception as e:
        print(f" ❌ ERROR CRÍTICO (Transporte): {e}")
        return False

def probar_cloudfort(placa_a_probar):
    """
    Prueba aislada de conexión con CloudFort para ver el JSON real.
    """
    print(f"\n--- ☁️ INICIANDO PRUEBA CLOUDFORT (Placa: {placa_a_probar}) ---")
    
    try:
        # 1. Instanciamos el manager
        # (Asegúrate de haber creado el archivo cloudfort_manager.py con el código anterior)
        from manager_cloudfort import CloudFortManager
        cf_manager = CloudFortManager()
        
        # 2. Hacemos la consulta
        print("📡 Enviando petición...")
        respuesta_json = cf_manager.validar_placa(placa_a_probar)
        
        # 3. Imprimimos el JSON bonito en consola
        print("\n" + "="*40)
        print(" ✅ JSON RECIBIDO DE LA API:")
        print("="*40)
        print(json.dumps(respuesta_json, indent=4)) # indent=4 hace que se vea ordenado
        print("="*40 + "\n")
        
        return True

    except Exception as e:
        print("\n" + "x"*40)
        print(f" ❌ ERROR AL CONSULTAR CLOUDFORT:")
        print(f" {e}")
        print("x"*40 + "\n")
        return False

def probar_zsdmx389(robot):
    """Prueba la descarga del archivo de contingencia ZSDMX389."""
    
    print("\n--- 📥 INICIANDO PRUEBA: DESCARGA ZSDMX389 (CONTINGENCIA) ---")

    try:
        # Llamamos a la función orquestadora que creamos en manager_sap.py
        # Esta ya calcula la ruta (OneDrive/Documentos) y las fechas automáticamente.
        ruta_guardada = robot.descargar_contingencia_zsdmx389()

        if ruta_guardada:
            print(f" ✅ DESCARGA EXITOSA.")
            print(f" 📁 Archivo guardado en: {ruta_guardada}") 
            return True
        else:
            print(" ⚠️ El robot terminó sin errores pero no devolvió la ruta del archivo.")
            return False

    except Exception as e:
        print(f" ❌ ERROR CRÍTICO (ZSDMX389): {e}")
        return False

def probar_vt16(robot, centro_exp_test="MX47"):
    """Prueba la descarga operativa de la VT16."""
    
    print(f"\n--- 📊 INICIANDO PRUEBA: DESCARGA VT16 (Centro: {centro_exp_test}) ---")

    try:
        # Llamamos al orquestador que ya tiene la lógica de fechas de hoy y estatus 0-5
        ruta_guardada = robot.descargar_operacion_vt16(centro_exp=centro_exp_test)

        if ruta_guardada:
            print(f" ✅ DESCARGA VT16 EXITOSA.")
            print(f" 📁 Archivo guardado en: {ruta_guardada}") 
            return True
        else:
            print(" ⚠️ La VT16 terminó sin errores críticos, pero no generó archivo (¿Quizás no hay transportes hoy para ese centro?).")
            return False

    except Exception as e:
        print(f" ❌ ERROR CRÍTICO (VT16): {e}")
        return False

# ==============================================================================
# BLOQUE PARA PRUEBA DE PLACAS CON CLOUDFORT
# ==============================================================================
"""
if __name__ == "__main__":
    # --- CONFIGURACIÓN DE LA PRUEBA ---
    PLACA_TEST = "793EV4" # <--- ¡Pon aquí la placa que quieres probar!
    # ----------------------------------

    print(">>> EJECUTANDO TEST DE CONEXIÓN API <<<")
    
    probar_cloudfort(PLACA_TEST)    

"""

# ==============================================================================
# BLOQUE PRINCIPAL DE EJECUCIÓN
# ==============================================================================

if __name__ == "__main__":
    print(">>> INICIANDO SECUENCIA DE PRUEBAS ROBOT SAP <<<")
    
    try:
        # 1. Instanciamos el robot UNA sola vez para compartir la sesión
        mi_robot = SAPManager()
        
        # --- PRUEBA ZSDMX389 (CONTINGENCIA) ---
        exito_descarga = probar_zsdmx389(mi_robot)
        
        # --- PRUEBA BÁSCULA Y TRANSPORTE (Comentadas temporalmente) ---
        """
        exito_folio = probar_folio_bascula(mi_robot) 
        
        if exito_folio:
            print("\n... Procediendo a crear transporte ...")
            probar_crear_transporte(mi_robot)
        else:
            print("\n⚠️ Saltando prueba de transporte porque falló el folio de báscula.")
        """
            
    except Exception as e:
        print(f"Error general al iniciar SAPManager: {e}")