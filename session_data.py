# session_data.py
import datetime
from typing import List, Dict, Any

class SessionData:
    def __init__(self):
        # --- DATOS OPERATIVOS ---

        #Datos de la remision
        self.remisiones_agregadas: List[Dict[str, Any]] = []
        self.transporte_sap: str = ""
        self.clase_entrega: str = ""
        self.clase_expedicion_sap: str = ""
        self.fch_cita_carga: str = ""

        #Datos del operador
        self.operador: str = ""
        self.placa: str = ""
        self.clase_expedicion: str = "" 
        self.proveedor: str = ""

        #Datos del cliente
        self.cliente_nombre: str = ""
        self.destinatario_nombre: str = ""
        self.cliente_num: str = ""
        self.destinatario_num: str = ""
        self.poblacion: str = ""
        self.ruta: str = ""
        self.modalidad: str = ""
        
        
        #Datos de cloudofort
        self.tipo_unidad_cloudfort: str = "" #Tipo de unidad cloudfort
        self.fecha_checklist: str = ""    # La hora exacta que devolvió CloudFort

        #Datos kiosko
        self.origen_datos: str = ""             # "A: Web Service", "B: Robot SAP", "C: Contingencia"
        self.id_movimiento: str = ""            #Id de movmiento se genera al dar "nuevo arribo"
        self.ticket_id: str = ""                # Se genera con la hora del Checklist
        self.inicio_arribo = datetime.datetime.now() # Hora en que pulsó "Nuevo Arribo"
        self.fin_arribo = None                  # Se llena al Finalizar o Cancelar
        self.estatus_arribo_mensaje: str = ""   # "Exito", "Cancelado por usuario", "Error SAP..."
        self.planta_gui_nombre: str = ""
        self.planta_gui_codigos: list = []
        self.ruta_base_drive: str

        self.folio_contingencia: str = ""     # Folio de contingencia incremental
        self.estatus_contingencia: str = ""     # "N/A", "PENDIENTE", "CERRADO"

        # Variables de compatibilidad (para mostrar Log resumen)
        self.estatus_arribo_ultimo_paso: str = "Inicio"  # Rastro del operador (V0, V1, V2...)
        self.historial_acciones: list = [] # Lista de movimiento

    def reset_session(self):
        """Reinicia todo para el siguiente camión."""

        # --- DATOS OPERATIVOS ---

        # Datos de la remisión
        self.remisiones_agregadas = []
        self.transporte_sap = ""
        self.clase_entrega = ""
        self.clase_expedicion_sap = ""
        self.fch_cita_carga = ""

        # Datos del operador
        self.operador = ""
        self.placa = ""
        self.clase_expedicion = ""
        self.proveedor = ""

        # Datos del cliente
        self.cliente_nombre = ""
        self.destinatario_nombre = ""
        self.cliente_num = ""
        self.destinatario_num = ""
        self.poblacion = ""
        self.ruta = ""
        self.modalidad = ""

        # Datos CloudFort
        self.tipo_unidad_cloudfort = ""
        self.fecha_checklist = ""

        # Datos Kiosko
        self.origen_datos = ""
        self.id_movimiento = ""
        self.ticket_id = ""
        self.inicio_arribo = datetime.datetime.now()
        self.fin_arribo = None
        self.estatus_arribo_mensaje = ""

        self.folio_contingencia = ""
        self.estatus_contingencia = ""

        # Variables de compatibilidad (para mostrar Log resumen)
        self.estatus_arribo_ultimo_paso = "Inicio"
        self.historial_acciones = []

    def agregar_remision(self, datos_sap: dict):
        # --- Guardar registro completo ---
        self.remisiones_agregadas.append(datos_sap)

        # --- Datos del operador ---
        self.operador = datos_sap.get("operador", self.operador)
        self.placa = datos_sap.get("placa", self.placa)

        # --- Datos del cliente ---
        self.cliente_num = datos_sap.get("cliente_num", self.cliente_num)
        self.cliente_nombre = datos_sap.get("cliente", self.cliente_nombre)

        self.destinatario_num = datos_sap.get("destinatario_num", self.destinatario_num)
        self.destinatario_nombre = datos_sap.get(
            "destinatario_nombre",
            self.destinatario_nombre
        )

        self.poblacion = datos_sap.get("poblacion", self.poblacion)
        self.ruta = datos_sap.get("ruta", self.ruta)
        self.modalidad = datos_sap.get("modalidad", self.modalidad)

        # --- Datos de remisión ---
        self.transporte_sap = datos_sap.get("transporte", self.transporte_sap)
        self.clase_entrega = datos_sap.get("clase_entrega", self.clase_entrega)
        self.clase_expedicion_sap = datos_sap.get("clase_expedicion", self.clase_expedicion_sap)
        self.fch_cita_carga = datos_sap.get("fch_cita_carga", self.fch_cita_carga)

        # --- Tipo unidad CloudFort ---
        self.tipo_unidad_cloudfort = datos_sap.get(
            "clase_expedicion",
            self.tipo_unidad_cloudfort
        )

        # --- Regla de negocio proveedor ---
        if self.modalidad == "RETIRADO":
            self.proveedor = "702551"
        else:
            self.proveedor = ""

    def obtener_peso_total(self) -> float:
        # ... (Igual que antes) ...
        total = 0.0
        for remision in self.remisiones_agregadas:
            materiales = remision.get("materiales", [])
            total += sum(mat.get("peso_ton", 0.0) for mat in materiales)
        return total

    def registrar_paso(self, accion: str, _estatus_arribo_msg: str):
        """Guarda una acción con su hora exacta y detalle en la lista."""
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        
        # ¡Corregido! Ahora guardamos la Acción Y el Mensaje
        evento = f"[{hora}] {accion} | {_estatus_arribo_msg}" 
        
        self.historial_acciones.append(evento)
        self.estatus_arribo_ultimo_paso = accion
        self.estatus_arribo_mensaje = _estatus_arribo_msg
        print(f"Log: {evento}") # Para verlo bonito en consola