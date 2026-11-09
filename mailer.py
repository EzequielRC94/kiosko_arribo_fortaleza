import win32com.client
from datetime import datetime
from session_data import SessionData

class EmailManager:
    def __init__(self):
        # Configuramos destinatarios fijos
        self.destinatario = "msaavedra@cementosfortaleza.com; desanchezs@cementosfortaleza.com; embarques@elementia.com"
        self.copia = "aramirezc@cementosfortaleza.com"
        self.asunto_base = f"PRUEBAS: arribo en kiosko"

    def enviar_aviso_arribo(self, session: SessionData):
        """
        Genera un correo con tabla HTML desglosando cada material homologado con el nuevo layout.
        """
        try:
            outlook = win32com.client.Dispatch('Outlook.Application')
            mail = outlook.CreateItem(0) # 0 = olMailItem

            mail.To = self.destinatario
            mail.CC = self.copia

            subject_mail = mail.Subject = f"{self.asunto_base} {session.planta_gui_nombre} - {session.ticket_id}"
            if session.origen_datos == "C: Contingencia":
                mail.subject = f"Contingencia: {session.folio_contingencia} {subject_mail}"
            else: 
                mail.subject = subject_mail

             # Recuperamos datos globales seguros
            transporte = getattr(session, "transporte_sap", "PENDIENTE")

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
            <h3>🚀 Aviso de Nuevo Arribo en Kiosko  {session.planta_gui_nombre} {transporte}</h3>
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
                        <td>{mat.get('desc_nom_corto', '')}</td>
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

    def enviar_resumen_fbl4n(
        self,
        mes_en_curso: str,
        df_por_usuario,
        df_por_fecha_usuario,
        df_por_fch_fin_carga=None,) -> dict:
        """
        Arma el correo con el resumen de adicionales generados en el mes en curso
        pertenecientes a viajes de meses pasados (FBL4N).
        """
        self.destinatario = "isantiagom@cementosfortaleza.com"
        self.copia = "aramirezc@cementosfortaleza.com"
        self.asunto_base = f"Resumen adicionales {mes_en_curso}"

        total_general = float(df_por_usuario["importe"].sum()) if not df_por_usuario.empty else 0.0

        # Construcción de filas HTML para Tabla 1: Resumen por usuario
        filas_usuario_html = ""
        for _, row in df_por_usuario.iterrows():
            usr = row.get("usuario_creacion", "SIN_USUARIO")
            imp = float(row.get("importe", 0.0))
            filas_usuario_html += f"""
                <tr>
                    <td>{usr}</td>
                    <td style="text-align: right;">${imp:,.2f}</td>
                </tr>
            """
        filas_usuario_html += f"""
            <tr style="font-weight: bold; background-color: #e6f2f2;">
                <td>TOTAL</td>
                <td style="text-align: right;">${total_general:,.2f}</td>
            </tr>
        """

        # Construcción de filas HTML para Tabla 2: Detalle por fecha y usuario
        filas_detalle_html = ""
        for _, row in df_por_fecha_usuario.iterrows():
            fch = row.get("fch_documento", "")
            usr = row.get("usuario_creacion", "SIN_USUARIO")
            imp = float(row.get("importe", 0.0))
            filas_detalle_html += f"""
                <tr>
                    <td>{fch}</td>
                    <td>{usr}</td>
                    <td style="text-align: right;">${imp:,.2f}</td>
                </tr>
            """
        filas_detalle_html += f"""
            <tr style="font-weight: bold; background-color: #e6f2f2;">
                <td colspan="2">TOTAL</td>
                <td style="text-align: right;">${total_general:,.2f}</td>
            </tr>
        """

        # Construcción de filas HTML para Tabla 3: Resumen por fecha fin de carga y usuario (4_fch_fin_carga, usuario_creacion)
        filas_fin_carga_html = ""
        if df_por_fch_fin_carga is not None and not df_por_fch_fin_carga.empty:
            for _, row in df_por_fch_fin_carga.iterrows():
                fch_carga = row.get("4_fch_fin_carga", "SIN_FECHA")
                usr = row.get("usuario_creacion", "SIN_USUARIO")
                imp = float(row.get("importe", 0.0))
                filas_fin_carga_html += f"""
                    <tr>
                        <td>{fch_carga}</td>
                        <td>{usr}</td>
                        <td style="text-align: right;">${imp:,.2f}</td>
                    </tr>
                """
        filas_fin_carga_html += f"""
            <tr style="font-weight: bold; background-color: #e6f2f2;">
                <td colspan="2">TOTAL</td>
                <td style="text-align: right;">${total_general:,.2f}</td>
            </tr>
        """

        html_body = f"""
        <html>
        <head>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 12px; color: #333333; }}
            table {{ border-collapse: collapse; width: auto; min-width: 380px; margin-bottom: 20px; font-size: 12px; }}
            th, td {{ border: 1px solid #dddddd; text-align: left; padding: 6px 12px; white-space: nowrap; }}
            th {{ background-color: #008080; color: white; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
        </head>
        <body>
            <h3>Resumen de adicionales generados {mes_en_curso}</h3>
            <p>Gastos de fletes creados en el mes corriente pertenecientes a viajes de meses pasados:</p>

            <h4>Tabla por usuario</h4>
            <table>
                <tr>
                    <th>usuario_creacion</th>
                    <th style="text-align: right;">importe</th>
                </tr>
                {filas_usuario_html}
            </table>

            <h4>Detalle por fecha</h4>
            <table>
                <tr>
                    <th>fch_documento</th>
                    <th>usuario_creacion</th>
                    <th style="text-align: right;">importe</th>
                </tr>
                {filas_detalle_html}
            </table>

            <h4>Tabla por fecha fin carga</h4>
            <table>
                <tr>
                    <th>4_fch_fin_carga</th>
                    <th>usuario_creacion</th>
                    <th style="text-align: right;">importe</th>
                </tr>
                {filas_fin_carga_html}
            </table>

            <p><i>Mensaje generado automáticamente por zql_robot de análisis FBL4N.</i></p>
        </body>
        </html>
        """

        try:
            outlook = win32com.client.Dispatch('Outlook.Application')
            mail = outlook.CreateItem(0)  # 0 = olMailItem

            mail.To = self.destinatario
            mail.CC = self.copia
            mail.Subject = self.asunto_base
            mail.HTMLBody = html_body

            mail.Display()  # Abre la ventana del correo en Outlook para verlo antes de enviar
            # mail.Send()  # Comentado para pruebas: no envía el correo automáticamente
            print(f"✅ Correo abierto en Outlook para revisión (Asunto: '{self.asunto_base}', Para: '{self.destinatario}') [# mail.Send() comentado].")
            return {
                "estatus": True,
                "asunto": self.asunto_base,
                "destinatario": self.destinatario,
                "copia": self.copia,
                "msg": "Correo mostrado en ventana de Outlook (envío comentado).",
            }

        except Exception as e:
            print(f"⚠️ Aviso al instanciar Outlook (el resumen y HTML sí se armaron): {e}")
            return {
                "estatus": False,
                "asunto": self.asunto_base,
                "destinatario": self.destinatario,
                "copia": self.copia,
                "error": str(e),
            }

 