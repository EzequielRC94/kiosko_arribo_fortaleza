import win32com.client
from datetime import datetime
from session_data import SessionData

class EmailManager:
    def __init__(self):
        # Configuramos destinatarios fijos
        self.destinatario = "msaavedra@cementosfortaleza.com; desanchezs@cementosfortaleza.com; embarquestula@elementia.com"
        self.copia = "aramirezc@cementosfortaleza.com"
        self.asunto_base = "PRUEBAS: arribo en kiosko"

    def enviar_aviso_arribo(self, session: SessionData):
        """
        Genera un correo con tabla HTML desglosando cada material homologado con el nuevo layout.
        """
        try:
            outlook = win32com.client.Dispatch('Outlook.Application')
            mail = outlook.CreateItem(0) # 0 = olMailItem

            mail.To = self.destinatario
            mail.CC = self.copia
            mail.Subject = f"{self.asunto_base} - {session.ticket_id}"

            # Construimos el cuerpo en HTML
            # Se agrega 'white-space: nowrap' para evitar que las columnas colapsen y se deformen
            html_body = f"""
            <html>
            <head>
            <style>
                table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 11px; }}
                th, td {{ border: 1px solid #dddddd; text-align: left; padding: 6px; white-space: nowrap; }}
                th {{ background-color: #008080; color: white; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
            </style>
            </head>
            <body>
            <h3>🚀 Aviso de Nuevo Arribo (Kiosko)</h3>
            <p>Se ha registrado un nuevo transporte en el sistema.</p>
            
            <div style="overflow-x:auto;">
            <table>
                <tr>
                    <th>REMISION</th>
                    <th>Pos</th>
                    <th>C_Exp</th>
                    <th>No CLIENTE</th>
                    <th>RAZON SOCIAL</th>
                    <th>POBLACION</th>
                    <th>MODALIDAD</th>
                    <th>Tipo Material</th>
                    <th>TON</th>
                    <th>MATERIAL</th>
                    <th>Cod Material</th>
                    <th>NOMBRE OPERADOR</th>
                    <th>PLACAS</th>
                    <th>TIPO UNIDAD</th>
                    <th>TRANSPORTE</th>
                    <th>FCH CITA</th>
                    <th>FCH ARRIBO</th>
                    <th>FCH ENTRADA</th>
                    <th>FCH SALIDA</th>
                    <th>FCH DOC</th>
                    <th>Gasto Tr</th>
                    <th>Talon enviado?</th>
                    <th>Comentario</th>
                    <th>Pedido</th>
                    <th>destinatario_num</th>
                    <th>folio_contingencia</th>
                </tr>
            """

            # Recuperamos datos globales seguros
            transporte = getattr(session, "transporte_sap", "PENDIENTE")
            fch_arribo = session.inicio_arribo.strftime("%Y-%m-%d %H:%M") if session.inicio_arribo else ""
            fch_cita = getattr(session, "fch_cita_carga", "")
            
            for rem in session.remisiones_agregadas:
                num_rem = rem.get("remision", "")
                
                for mat in rem.get("materiales", []):
                    # Datos específicos de fila mapeados desde SessionData y los diccionarios de materiales
                    fila_html = f"""
                    <tr>
                        <td>{num_rem}</td>
                        <td>{mat.get('posicion', '')}</td>
                        <td>{mat.get('cen_exp', '')}</td>
                        <td>{session.cliente_num}</td>
                        <td>{session.cliente_nombre}</td>
                        <td>{session.poblacion}</td>
                        <td>{session.modalidad}</td>
                        <td>{mat.get('gpo_material', '')}</td>
                        <td>{mat.get('peso_ton', 0)}</td>
                        <td>{mat.get('material_denominacion', '')}</td>
                        <td>{mat.get('material', '')}</td>
                        <td>{session.operador}</td>
                        <td>{session.placa}</td>
                        <td>{session.clase_expedicion}</td>
                        <td>{transporte}</td>
                        <td>{fch_cita}</td>
                        <td>{fch_arribo}</td>
                        <td></td>  <!-- FCH ENTRADA -->
                        <td></td>  <!-- FCH SALIDA -->
                        <td></td>  <!-- FCH DOC -->
                        <td></td>  <!-- Gasto Tr -->
                        <td></td>  <!-- Talon enviado? -->
                        <td></td>  <!-- Comentario -->
                        <td></td>  <!-- Pedido -->
                        <td>{session.destinatario_num}</td>
                        <td>{session.estatus_contingencia}</td>
                    </tr>
                    """
                    html_body += fila_html

            # Cerramos tabla y HTML
            html_body += """
            </table>
            </div>
            <p><i>Este es un mensaje automático del sistema de Kiosko de Auto-Arribo.</i></p>
            </body>
            </html>
            """

            mail.HTMLBody = html_body
            mail.Send()
            print("✅ Correo de aviso enviado correctamente.")

        except Exception as e:
            print(f"⚠️ No se pudo enviar el correo (Outlook): {e}")