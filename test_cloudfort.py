import requests
import json

# --- CONFIGURACIÓN DE LA PRUEBA ---
# URL extraída de tu imagen
URL_API = "http://cloudfort.net/cementosfortaleza/api/getDataArriveStatus"

# Datos proporcionados
TOKEN = "6Lkosl00sCAkBBBLdei_J12Y456e4VD6Zgxw5RqR"
PLACA_PRUEBA = "72BJ7B"

def ejecutar_test():
    print("\n>>> EJECUTANDO TEST DE CONEXIÓN API <<<")
    print(f"\n--- ☁️ INICIANDO PRUEBA CLOUDFORT (Placa: {PLACA_PRUEBA}) ---")
    
    payload = {
        "token": TOKEN,
        "placas": PLACA_PRUEBA
    }
    
    print(f"📡 Enviando petición a: CLOUDFORT")

    try:
        # Petición POST
        response = requests.post(URL_API, json=payload, timeout=15)
        
        print(f"🔔 Código de Estado HTTP: {response.status_code}")

        if response.status_code == 200:
            # Convertimos la respuesta a JSON
            data_json = response.json()
            
            # Formateamos bonito el JSON para verlo bien en consola
            json_bonito = json.dumps(data_json, indent=4, ensure_ascii=False)
            
            print(f"✅ Respuesta CloudFort recibida.")
            
            print("\n" + "="*40)
            print("✅ JSON RECIBIDO DE LA API:")
            print("="*40)
            print(json_bonito)
            print("="*40 + "\n")
            
        elif response.status_code == 404:
            print("❌ Error 404: El servicio no encontró la placa o la ruta.")
            print(f"Respuesta texto: {response.text}")
            
        else:
            print(f"⚠️ Error desconocido ({response.status_code})")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("❌ Error de Conexión: No se pudo contactar con cloudfort.net")
    except Exception as e:
        print(f"❌ Error Crítico: {e}")

if __name__ == "__main__":
    ejecutar_test()