# manager_cloudfort.py
import requests
import json
from datetime import datetime

class CloudFortManager:
    def __init__(self):
        # URL de la api
        self.url = "http://cloudfort.net/cementosfortaleza/api/getDataArriveStatus" 
        
        # Token fijo
        self.token = "6Lkosl00sCAkBBBLdei_J12Y456e4VD6Zgxw5RqR"

    def validar_placa(self, placa: str) -> dict:

        """
        Consulta la API de CloudFort enviando Token y Placa.
        Retorna el diccionario con la respuesta si es exitoso (Código 200).
        """
        
        # Estructura exacta: {"token": "...", "placas": "..."}
        payload = {
            "token": self.token,
            "placas": placa
        }

        print(f"📡 Enviando POST a CloudFort: {placa}")

        try:
            # Enviamos la petición POST
            # timeout=10 evita que el programa se congele si no hay internet
            response = requests.post(self.url, json=payload, timeout=10)
            
            # Verificamos respuesta HTTP
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Respuesta CloudFort: {json.dumps(data, indent=2)}")
                return data
            elif response.status_code == 404:
                raise Exception("Placa no encontrada en CloudFort.")
            else:
                raise Exception(f"Error HTTP {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            raise Exception("Tiempo de espera agotado (CloudFort no responde).")
        except requests.exceptions.ConnectionError:
            raise Exception("Error de conexión. Verifique su internet.")
        except Exception as e:
            raise Exception(f"Falla al conectar API: {e}")
        
    def obtener_datos_remision(self, remision: str) -> dict:
        """
        DRAFT: Consulta la nueva API de CloudFort para traer datos de la remisión.
        """
        # URL ficticia para el endpoint en construcción
        url_remision = "http://cloudfort.net/cementosfortaleza/api/getDataRemision" 
        
        payload = {
            "token": self.token,
            "remision": remision
        }

        print(f"📡 Enviando POST a CloudFort (Remisión): {remision}")

        try:
            # Usamos un timeout corto (ej. 4 segundos). 
            # Si en 4 segs no responde, mejor lanzamos el Robot.
            response = requests.post(url_remision, json=payload, timeout=4)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Respuesta CloudFort Remisión OK.")
                
                # IMPORTANTE: Aquí deberás formatear o "mapear" el JSON (data) 
                # para que retorne EXACTAMENTE la misma estructura de diccionario 
                # que devuelve tu sap_manager.extraer_datos_remision()
                # Ej: {"remision": ..., "cliente": ..., "materiales": [...]}
                
                return data
            elif response.status_code == 404:
                raise Exception("Rem no encontrada en CF.")
            else:
                raise Exception(f"Error HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            raise Exception("Timeout: La API tardó demasiado.")
        except requests.exceptions.ConnectionError:
            raise Exception("Error de conexión con la API.")
        except Exception as e:
            raise Exception(f"Falla en API Remisión: {e}")