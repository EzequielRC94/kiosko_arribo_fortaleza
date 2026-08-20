import requests
import json
from datetime import datetime

class CloudFortManager:
    def __init__(self):
        # 1. Base URL general del servicio
        self.url_base = "https://cloudfort.elementia.com/cementosfortaleza/api/"
        
        # 2. Gestión de Tokens (Token por defecto + Diccionario para futuros tokens específicos)
        self.token_default = "6Lkosl00sCAkBBBLdei_J12Y456e4VD6Zgxw5RqR"
        
        # Puedes ir agregando tokens específicos por endpoint aquí cuando se requiera:
        self.tokens_por_endpoint = {
            "getDataArriveStatus": self.token_default,
            "getDataRemision": self.token_default,
            # "nuevoEndpoint": "TOKEN_DIFERENTE_AQUI"
        }

    def _obtener_token(self, endpoint: str) -> str:
        """Devuelve el token específico para un endpoint o el token por defecto."""
        return self.tokens_por_endpoint.get(endpoint, self.token_default)


    def _ejecutar_post(self, endpoint: str, payload_data: dict, timeout: int = 10) -> dict:
        """
        Método centralizado para realizar peticiones POST a las APIs de CloudFort.
        Construye la URL completa e inyecta el token correspondiente.
        """
        url_completa = f"{self.url_base}{endpoint}"
        
        # Inyectamos el token correspondiente si no viene explícito en el payload
        if "token" not in payload_data:
            payload_data["token"] = self._obtener_token(endpoint)

        print(f"📡 Enviando POST a CloudFort [{endpoint}]")

        try:
            response = requests.post(url_completa, json=payload_data, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Respuesta CloudFort [{endpoint}] OK")
                return data
            elif response.status_code == 404:
                raise Exception(f"Recurso no encontrado en CloudFort ({endpoint}).")
            else:
                raise Exception(f"Error HTTP {response.status_code} en {endpoint}: {response.text}")

        except requests.exceptions.Timeout:
            raise Exception(f"Tiempo de espera agotado en API {endpoint}.")
        except requests.exceptions.ConnectionError:
            raise Exception("Error de conexión con CloudFort. Verifique su red.")
        except Exception as e:
            raise Exception(f"Falla al conectar con API ({endpoint}): {e}")

    # =========================================================================
    # ENDPOINTS IMPLEMENTADOS
    # =========================================================================

    def validar_placa(self, placa: str) -> dict:
        """
        Consulta la API de estatus de arribo por Placa.
        Endpoint: getDataArriveStatus
        """
        endpoint = "getDataArriveStatus"
        payload = {
            "placas": placa
        }
        return self._ejecutar_post(endpoint=endpoint, payload_data=payload, timeout=10)

    def obtener_datos_remision(self, remision: str) -> dict:
        """
        Consulta la API de datos de Remisión.
        Endpoint: getDataRemision
        """
        endpoint = "getDataRemision"
        payload = {
            "remision": remision
        }
        return self._ejecutar_post(endpoint=endpoint, payload_data=payload, timeout=4)

    # =========================================================================
    # PLANTILLA PARA NUEVAS APIS EN EL FUTURO
    # =========================================================================
    # def nueva_api_ejemplo(self, parametro: str) -> dict:
    #     endpoint = "nombreNuevoEndpoint"
    #     payload = {
    #         "parametro_campo": parametro
    #     }
    #     return self._ejecutar_post(endpoint=endpoint, payload_data=payload, timeout=5)