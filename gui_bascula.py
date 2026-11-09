#gui_bascula.py
import sys
import random
import time
import os
import ctypes

from datetime import datetime, timedelta
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QMessageBox, QCheckBox, QStackedWidget, QDateEdit, QProgressBar,
    QScrollArea, QSizePolicy, QShortcut
)
from PyQt5.QtGui import QFont, QColor, QBrush, QIcon, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QSize, QDate
from manager_arribos import ArribosManager
from prevent_sleep import evitar_bloqueo_windows, restaurar_energia_windows
from manager_sap import SAPManager
from manager_descargas import DescargasManager, configurar_icono_app  
from session_data import SessionData
from catalogos import CATALOGO_PLANTAS, CATALOGO_MATERIALES
from parquets import (
    actualizar_parquet_vt16,
    actualizar_parquet_zsdmx249,
    obtener_df_249,
    obtener_oferta_plantas,
    obtener_rutas_transaccion,
)

# Configuración de las "Pestañas" o Vistas del Carrusel
# Clave: Nombre de la vista
# Valor: Lista de palabras clave para filtrar el material

# ==============================================================================
# WIDGET DASHBOARD MINIMALISTA DE SALIDAS (ZSDMX249 + VT16 + ZSDMX389)
# ==============================================================================
DIAS_SEMANA_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]


def formatear_fecha_larga_es(fecha_dt: datetime) -> str:
    dia_sem = DIAS_SEMANA_ES[fecha_dt.weekday()]
    mes_nom = MESES_ES[fecha_dt.month]
    return f"{dia_sem}, {fecha_dt.day} de {mes_nom} de {fecha_dt.year}"


class DashboardSalidasWidget(QWidget):
    """
    Dashboard minimalista en PyQt5 para visualizar en tiempo real las salidas
    de la planta desde 249.parquet (cruzado con VT16 y pendientes Por Cargar de ZSDMX389).
    """
    def __init__(self, parent_window: "VentanaBasculaMain"):
        super().__init__(parent_window)
        self.parent_win = parent_window
        self.nombre_planta = parent_window.nombre_planta
        self.codigos_sap = list(parent_window.codigos_sap or [])
        self._init_ui()

    def _crear_card(self, bg: str = "#FFFFFF", border: str = "#E2E8F0") -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border: 1px solid {border}; border-radius: 10px; }}"
            f"QLabel {{ border: none; background: transparent; }}"
        )
        return card

    def _crear_tabla_compacta(self, headers: list, filas: int) -> QTableWidget:
        tbl = QTableWidget(filas, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setShowGrid(False)
        tbl.setAlternatingRowColors(False)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col_i in range(1, len(headers)):
            tbl.horizontalHeader().setSectionResizeMode(col_i, QHeaderView.ResizeMode.ResizeToContents)
        tbl.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                font-family: 'Segoe UI', Arial;
                font-size: 12px;
                color: #1E293B;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #475569;
                font-weight: bold;
                font-size: 11px;
                border: none;
                border-bottom: 1px solid #CBD5E1;
                padding: 4px 6px;
            }
            QTableWidget::item {
                padding: 2px 6px;
                border-bottom: 1px solid #F1F5F9;
            }
        """)
        return tbl

    def _init_ui(self):
        self.setStyleSheet("background-color: #F1F5F9;")
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(6, 4, 6, 6)
        root_layout.setSpacing(8)

        # ------------------------------------------------------------------
        # 1. BARRA SUPERIOR MINIMALISTA DEL DASHBOARD (FILTRO FECHA + ESTADO)
        # ------------------------------------------------------------------
        header_card = self._crear_card("#FFFFFF", "#CBD5E1")
        header_card.setFixedHeight(54)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(14, 6, 14, 6)
        header_layout.setSpacing(12)

        nombre_corto =CATALOGO_PLANTAS.get(self.nombre_planta, {}).get("nombre_centro", self.nombre_planta)
        cods_txt = ", ".join(self.codigos_sap) if self.codigos_sap else "Todos"
        self.lbl_titulo_planta = QLabel(f"Salidas {nombre_corto}  ({cods_txt})")
        self.lbl_titulo_planta.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.lbl_titulo_planta.setStyleSheet("color: #0F172A;")

        self.lbl_fecha_larga = QLabel("")
        self.lbl_fecha_larga.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_fecha_larga.setStyleSheet(
            "color: #0F766E; background-color: #CCFBF1; padding: 4px 10px; border-radius: 6px;"
        )

        # Controles de Fecha
        btn_style = """
            QPushButton {
                background-color: #F8FAFC; color: #334155; border: 1px solid #CBD5E1;
                border-radius: 6px; padding: 4px 10px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """
        self.btn_ayer = QPushButton("◀ Ayer")
        self.btn_ayer.setStyleSheet(btn_style)
        self.btn_ayer.clicked.connect(self._ir_ayer)

        self.btn_hoy = QPushButton("Hoy")
        self.btn_hoy.setStyleSheet(btn_style)
        self.btn_hoy.clicked.connect(self._ir_hoy)

        self.date_picker = QDateEdit(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("yyyy-MM-dd")
        self.date_picker.setFixedWidth(115)
        self.date_picker.setStyleSheet("""
            QDateEdit {
                background-color: #FFFFFF; color: #0F172A; border: 1px solid #94A3B8;
                border-radius: 6px; padding: 4px 8px; font-weight: bold; font-size: 12px;
            }
        """)
        self.date_picker.dateChanged.connect(self._on_date_changed)

        self.lbl_ultima_act = QLabel("Última Actualización: --/--/---- --:--:--")
        self.lbl_ultima_act.setFont(QFont("Segoe UI", 10))
        self.lbl_ultima_act.setStyleSheet("color: #64748B;")

        self.btn_sync_sap = QPushButton("🔄 Actualizar SAP (249/VT16/389)")
        self.btn_sync_sap.setStyleSheet("""
            QPushButton {
                background-color: #0F766E; color: white; border: none;
                border-radius: 6px; padding: 6px 12px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #115E59; }
        """)
        self.btn_sync_sap.clicked.connect(self.parent_win._ejecutar_robot_zsdmx_bascula)

        header_layout.addWidget(self.lbl_titulo_planta)
        header_layout.addWidget(self.lbl_fecha_larga)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_ultima_act)
        header_layout.addWidget(self.btn_ayer)
        header_layout.addWidget(self.btn_hoy)
        header_layout.addWidget(self.date_picker)
        header_layout.addWidget(self.btn_sync_sap)

        root_layout.addWidget(header_card)

        # ------------------------------------------------------------------
        # 2. CUERPO PRINCIPAL EN 3 COLUMNAS PROPORCIONALES (ESTILO DASHBOARD)
        # ------------------------------------------------------------------
        body_layout = QHBoxLayout()
        body_layout.setSpacing(8)

        # ==================================================================
        # COLUMNA IZQUIERDA (stretch=2): KPIs GLOBALES, ARRIBOS Y MODALIDAD
        # ==================================================================
        col_izq = QVBoxLayout()
        col_izq.setSpacing(8)

        # Card A: KPI Principal Total Cargado vs Oferta Planta
        card_kpi_carga = self._crear_card("#FFFFFF", "#CBD5E1")
        lay_kpi_carga = QVBoxLayout(card_kpi_carga)
        lay_kpi_carga.setContentsMargins(12, 10, 12, 10)
        lay_kpi_carga.setSpacing(4)

        lbl_hdr_carga = QLabel("RESUMEN DE SALIDAS VS OFERTA PLANTA")
        lbl_hdr_carga.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_hdr_carga.setStyleSheet("color: #64748B; letter-spacing: 0.5px;")
        lay_kpi_carga.addWidget(lbl_hdr_carga)

        fila_big = QHBoxLayout()
        self.lbl_total_cargado = QLabel("0.00 ton")
        self.lbl_total_cargado.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.lbl_total_cargado.setStyleSheet("color: #0F766E;")

        self.lbl_cump_badge = QLabel("0.0%")
        self.lbl_cump_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cump_badge.setFixedWidth(75)
        self.lbl_cump_badge.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_cump_badge.setStyleSheet(
            "background-color: #DCFCE7; color: #166534; border-radius: 6px; padding: 4px;"
        )
        fila_big.addWidget(self.lbl_total_cargado)
        fila_big.addStretch()
        fila_big.addWidget(self.lbl_cump_badge)
        lay_kpi_carga.addLayout(fila_big)

        self.bar_cumplimiento = QProgressBar()
        self.bar_cumplimiento.setRange(0, 100)
        self.bar_cumplimiento.setValue(0)
        self.bar_cumplimiento.setTextVisible(False)
        self.bar_cumplimiento.setFixedHeight(8)
        self.bar_cumplimiento.setStyleSheet("""
            QProgressBar { background-color: #E2E8F0; border-radius: 4px; border: none; }
            QProgressBar::chunk { background-color: #0D9488; border-radius: 4px; }
        """)
        lay_kpi_carga.addWidget(self.bar_cumplimiento)

        grid_meta = QGridLayout()
        grid_meta.setVerticalSpacing(4)
        grid_meta.setHorizontalSpacing(8)
        self.lbl_oferta_planta = self._agregar_par_metrica(grid_meta, 0, "Oferta Planta:", "0.00", "#1E293B", bold=True)
        self.lbl_tendencia_dia = self._agregar_par_metrica(grid_meta, 1, "Tendencia Cierre:", "0.00", "#B91C1C", bold=True)
        self.lbl_turnos_op = self._agregar_par_metrica(grid_meta, 2, "Turnos Operativos:", "3", "#475569", bold=False)
        lay_kpi_carga.addLayout(grid_meta)

        col_izq.addWidget(card_kpi_carga)

        # Card B: Estado de Arribos y Patio (ZSDMX389 + 249)
        card_arribos = self._crear_card("#FFFFFF", "#CBD5E1")
        lay_arribos = QVBoxLayout(card_arribos)
        lay_arribos.setContentsMargins(12, 10, 12, 10)
        lay_arribos.setSpacing(4)

        lbl_hdr_arr = QLabel("BALANCE DE ARRIBOS Y PATIO (EN PROCESO)")
        lbl_hdr_arr.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_hdr_arr.setStyleSheet("color: #64748B;")
        lay_arribos.addWidget(lbl_hdr_arr)

        grid_arr = QGridLayout()
        grid_arr.setVerticalSpacing(4)
        self.lbl_arribo_mas_1d = self._agregar_par_metrica(grid_arr, 0, "Arribo con más de 1 día:", "0.00", "#64748B")
        self.lbl_arribo_hoy = self._agregar_par_metrica(grid_arr, 1, "Arribo de hoy:", "0.00", "#64748B")
        self.lbl_total_arribado = self._agregar_par_metrica(grid_arr, 2, "Total Arribado:", "0.00", "#0F172A", bold=True)
        self.lbl_total_por_cargar = self._agregar_par_metrica(grid_arr, 3, "Total Por Cargar (Patio):", "0.00", "#DC2626", bold=True)
        lay_arribos.addLayout(grid_arr)

        col_izq.addWidget(card_arribos)

        # Card C: Salidas Por Modalidad & Mix Prod Entregado
        card_mod = self._crear_card("#FFFFFF", "#CBD5E1")
        lay_mod = QVBoxLayout(card_mod)
        lay_mod.setContentsMargins(12, 10, 12, 10)
        lay_mod.setSpacing(6)

        lbl_hdr_mod = QLabel("SALIDAS POR MODALIDAD")
        lbl_hdr_mod.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_hdr_mod.setStyleSheet(
            "background-color: #334E68; color: white; padding: 4px 8px; border-radius: 4px;"
        )
        lay_mod.addWidget(lbl_hdr_mod)

        grid_mod = QGridLayout()
        grid_mod.setVerticalSpacing(4)
        self.lbl_mod_ent_txt, self.lbl_mod_ent_val = self._agregar_par_dinamico(grid_mod, 0, "Entregado (0%)", "0")
        self.lbl_mod_ret_txt, self.lbl_mod_ret_val = self._agregar_par_dinamico(grid_mod, 1, "Retirado (0%)", "0")
        self.lbl_mod_aut_txt, self.lbl_mod_aut_val = self._agregar_par_dinamico(grid_mod, 2, "Autoflete (0%)", "0")
        lay_mod.addLayout(grid_mod)

        lbl_hdr_mix_ent = QLabel("SALIDAS MIX PROD. ENTREGADO")
        lbl_hdr_mix_ent.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_hdr_mix_ent.setStyleSheet(
            "background-color: #D9E2EC; color: #102A43; padding: 4px 8px; border-radius: 4px;"
        )
        lay_mod.addWidget(lbl_hdr_mix_ent)

        grid_mix_ent = QGridLayout()
        grid_mix_ent.setVerticalSpacing(4)
        self.lbl_ent_gra_txt, self.lbl_ent_gra_val = self._agregar_par_dinamico(grid_mix_ent, 0, "granel (0%)", "0")
        self.lbl_ent_env_txt, self.lbl_ent_env_val = self._agregar_par_dinamico(grid_mix_ent, 1, "envasado (0%)", "0")
        lay_mod.addLayout(grid_mix_ent)
        lay_mod.addStretch()

        col_izq.addWidget(card_mod, stretch=1)
        body_layout.addLayout(col_izq, stretch=2)

        # ==================================================================
        # COLUMNA CENTRAL Y DERECHA (stretch=6): MIX + TURNOS + PRODUCTOS
        # ==================================================================
        col_der = QVBoxLayout()
        col_der.setSpacing(8)

        # --- MITAD SUPERIOR: MIX PLANTA/CENTROS (IZQ) Y TURNOS (DER) ---
        top_tables_layout = QHBoxLayout()
        top_tables_layout.setSpacing(8)

        # Sub-columna: Mix Productos Planta + Centros (MX57, MX47, etc.)
        col_mix_centros = QVBoxLayout()
        col_mix_centros.setSpacing(6)

        self.tbl_mix_planta = self._crear_bloque_mix(
            col_mix_centros,
            titulo="Salidas Mix Productos Planta",
            bg_header="#336B78",
            fg_header="#FFFFFF",
        )

        self.tablas_centros = {}
        # Solo desglosar por centro si la planta tiene más de un centro de expedición (ej. Planta Tula: MX47 y MX57)
        if len(self.codigos_sap) > 1:
            colores_centros = [
                ("#CBE4EA", "#102A43"),
                ("#D8E8EE", "#102A43"),
                ("#E2E8F0", "#1E293B"),
            ]
            for idx_c, cod_ce in enumerate(self.codigos_sap):
                bg_c, fg_c = colores_centros[idx_c % len(colores_centros)]
                self.tablas_centros[cod_ce] = self._crear_bloque_mix(
                    col_mix_centros,
                    titulo=f"Salidas Mix Productos {cod_ce}",
                    bg_header=bg_c,
                    fg_header=fg_c,
                )
        else:
            col_mix_centros.addStretch()

        top_tables_layout.addLayout(col_mix_centros, stretch=1)

        # Sub-columna: Salidas por Turno (1er, 2do, 3er Turno)
        col_turnos = QVBoxLayout()
        col_turnos.setSpacing(6)

        self.tbl_turno_1 = self._crear_bloque_mix(
            col_turnos,
            titulo="Salidas Mix Productos 1er Turno (00:00 - 06:59)",
            bg_header="#FDE8D7",
            fg_header="#431407",
        )
        self.tbl_turno_2 = self._crear_bloque_mix(
            col_turnos,
            titulo="Salidas Mix Productos 2do Turno (07:00 - 14:59)",
            bg_header="#E2E0EC",
            fg_header="#1E1B4B",
        )
        self.tbl_turno_3 = self._crear_bloque_mix(
            col_turnos,
            titulo="Salidas Mix Productos 3er Turno (15:00 - 23:59)",
            bg_header="#F8D8F6",
            fg_header="#4A044E",
        )

        top_tables_layout.addLayout(col_turnos, stretch=1)
        col_der.addLayout(top_tables_layout, stretch=5)

        # --- MITAD INFERIOR: SALIDA POR PRODUCTO (envasado Y granel/BIG BAG) ---
        bot_tables_layout = QHBoxLayout()
        bot_tables_layout.setSpacing(8)

        self.tbl_prod_env = self._crear_bloque_productos(
            bot_tables_layout,
            titulo="Salida Por Producto — envasado",
        )
        self.tbl_prod_gra = self._crear_bloque_productos(
            bot_tables_layout,
            titulo="Salida Por Producto — granel y Big Bag",
        )

        col_der.addLayout(bot_tables_layout, stretch=6)
        body_layout.addLayout(col_der, stretch=6)

        root_layout.addLayout(body_layout, stretch=1)

    def _agregar_par_metrica(self, grid: QGridLayout, fila: int, etiqueta: str, valor_ini: str, color_val: str, bold: bool = False) -> QLabel:
        lbl_k = QLabel(etiqueta)
        lbl_k.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold if bold else QFont.Weight.Normal))
        lbl_k.setStyleSheet("color: #475569;")

        lbl_v = QLabel(valor_ini)
        lbl_v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_v.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold if bold else QFont.Weight.Normal))
        lbl_v.setStyleSheet(f"color: {color_val};")

        grid.addWidget(lbl_k, fila, 0)
        grid.addWidget(lbl_v, fila, 1)
        return lbl_v

    def _agregar_par_dinamico(self, grid: QGridLayout, fila: int, etiqueta: str, valor_ini: str):
        lbl_k = QLabel(etiqueta)
        lbl_k.setFont(QFont("Segoe UI", 10))
        lbl_k.setStyleSheet("color: #334155;")

        lbl_v = QLabel(valor_ini)
        lbl_v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_v.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_v.setStyleSheet("color: #0F172A;")

        grid.addWidget(lbl_k, fila, 0)
        grid.addWidget(lbl_v, fila, 1)
        return lbl_k, lbl_v

    def _crear_bloque_mix(self, parent_layout: QVBoxLayout, titulo: str, bg_header: str, fg_header: str) -> QTableWidget:
        card = self._crear_card("#FFFFFF", "#CBD5E1")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(2)

        lbl = QLabel(titulo)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl.setStyleSheet(
            f"background-color: {bg_header}; color: {fg_header}; padding: 4px; border-radius: 4px;"
        )
        lay.addWidget(lbl)

        tbl = self._crear_tabla_compacta(["Gpo Mat", "Salidas", "Objetivo", "Cump", "Tend"], 3)
        tbl.setFixedHeight(104)
        lay.addWidget(tbl)
        parent_layout.addWidget(card)
        return tbl

    def _crear_bloque_productos(self, parent_layout: QHBoxLayout, titulo: str) -> QTableWidget:
        card = self._crear_card("#FFFFFF", "#CBD5E1")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(4)

        lbl = QLabel(titulo)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl.setStyleSheet(
            "background-color: #336B78; color: #FFFFFF; padding: 5px; border-radius: 4px;"
        )
        lay.addWidget(lbl)

        tbl = self._crear_tabla_compacta(["Producto", "Cargado", "Obj", "% Cump", "Por Cargar"], 0)
        lay.addWidget(tbl)
        parent_layout.addWidget(card, stretch=1)
        return tbl

    def _ir_ayer(self):
        ayer = QDate.currentDate().addDays(-1)
        self.date_picker.setDate(ayer)

    def _ir_hoy(self):
        hoy = QDate.currentDate()
        self.date_picker.setDate(hoy)

    def _on_date_changed(self, qdate: QDate):
        fecha_str = qdate.toString("yyyy-MM-dd")
        self.parent_win.cargar_df_249(fecha_str=fecha_str)

    def obtener_fecha_seleccionada_str(self) -> str:
        return self.date_picker.date().toString("yyyy-MM-dd")

    def _poblar_tabla_mix(self, tbl: QTableWidget, sal_gra: float, obj_gra: float, sal_env: float, obj_env: float, factor_tend: float):
        filas_datos = [
            ("granel", sal_gra, obj_gra, False),
            ("envasado", sal_env, obj_env, False),
            ("Total", sal_gra + sal_env, obj_gra + obj_env, True),
        ]
        for r_idx, (etiqueta, sal, obj, es_total) in enumerate(filas_datos):
            cump = (sal / obj * 100.0) if obj > 0 else 0.0
            tend = sal * factor_tend
            textos = [
                etiqueta,
                f"{sal:,.0f}",
                f"{obj:,.0f}" if obj > 0 else "-",
                f"{cump:.0f}%" if obj > 0 else "-",
                f"{tend:,.0f}",
            ]
            for c_idx, txt in enumerate(textos):
                item = QTableWidgetItem(txt)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    if c_idx == 0
                    else Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if es_total:
                    f = QFont("Segoe UI", 10, QFont.Weight.Bold)
                    item.setFont(f)
                    item.setBackground(QColor("#F8FAFC"))
                tbl.setItem(r_idx, c_idx, item)
            tbl.setRowHeight(r_idx, 24)

    def _poblar_tabla_productos(self, tbl: QTableWidget, lista_filas: list):
        tbl.setRowCount(len(lista_filas))
        for r_idx, fila in enumerate(lista_filas):
            prod = fila["producto"]
            cargado = fila["cargado"]
            obj = fila["obj"]
            por_cargar = fila["por_cargar"]
            es_total = fila.get("es_total", False)

            cump = (cargado / obj * 100.0) if obj > 0 else None
            cump_str = f"{cump:.0f}%" if cump is not None else ""
            obj_str = f"{obj:,.0f}" if obj > 0 else ""

            vals = [
                prod,
                f"{cargado:,.0f}",
                obj_str,
                cump_str,
                f"{por_cargar:,.0f}",
            ]
            for c_idx, txt in enumerate(vals):
                item = QTableWidgetItem(txt)
                if c_idx == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                elif c_idx == 3:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                if es_total:
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                    item.setBackground(QColor("#F1F5F9"))
                else:
                    if c_idx == 0:
                        item.setBackground(QColor("#F8FAFC"))
                        item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

                # Color condicional en columna % Cump (c_idx == 3)
                if c_idx == 3 and cump is not None:
                    item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                    if cump >= 80:
                        item.setBackground(QColor("#86EFAC"))
                        item.setForeground(QColor("#14532D"))
                    elif cump >= 55:
                        item.setBackground(QColor("#FDE68A"))
                        item.setForeground(QColor("#713F12"))
                    else:
                        item.setBackground(QColor("#FECACA"))
                        item.setForeground(QColor("#7F1D1D"))

                # Color rojo en columna Por Cargar (c_idx == 4)
                if c_idx == 4:
                    item.setForeground(QColor("#B91C1C"))
                    item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

                tbl.setItem(r_idx, c_idx, item)
            tbl.setRowHeight(r_idx, 23)

    def renderizar_metricas(self, m: dict):
        """Actualiza todos los componentes visuales del Dashboard con el diccionario calculado."""
        fecha_dt = m["fecha_dt"]
        self.lbl_fecha_larga.setText(formatear_fecha_larga_es(fecha_dt))
        self.lbl_ultima_act.setText(f"Última Actualización: {m['ultima_actualizacion']}")

        # 1. KPIs Globales
        tot_cargado = m["total_cargado"]
        oferta = m["oferta_planta"]
        cump_global = (tot_cargado / oferta * 100.0) if oferta > 0 else 0.0
        tend_global = m["tendencia_global"]

        self.lbl_total_cargado.setText(f"{tot_cargado:,.1f} ton")
        self.lbl_cump_badge.setText(f"{cump_global:.1f}%")
        self.bar_cumplimiento.setValue(min(100, max(0, int(round(cump_global)))))

        sem_of = m.get("semana_oferta")
        suf_sem = f" (Sem {sem_of})" if sem_of is not None else ""
        self.lbl_oferta_planta.setText(f"{oferta:,.1f} ton{suf_sem}")
        flecha = "↗" if tend_global >= oferta else "↘"
        color_tend = "#15803D" if tend_global >= oferta else "#DC2626"
        self.lbl_tendencia_dia.setText(f"{flecha} {tend_global:,.1f} ton")
        self.lbl_tendencia_dia.setStyleSheet(f"color: {color_tend}; font-weight: bold;")
        self.lbl_turnos_op.setText(f"{m['turnos_operativos']:.0f}")

        # 2. Arribos y Patio
        self.lbl_arribo_mas_1d.setText(f"{m['arribo_mas_1d']:,.1f}")
        self.lbl_arribo_hoy.setText(f"{m['arribo_hoy']:,.1f}")
        self.lbl_total_arribado.setText(f"{m['total_arribado']:,.1f}")
        self.lbl_total_por_cargar.setText(f"{m['total_por_cargar']:,.1f}")

        # 3. Modalidad y Mix Entregado
        mod = m["modalidad"]
        tot_mod = max(tot_cargado, 0.001)
        self.lbl_mod_ent_txt.setText(f"Entregado ({mod['ENTREGADO'] / tot_mod * 100:.0f}%)")
        self.lbl_mod_ent_val.setText(f"{mod['ENTREGADO']:,.0f}")
        self.lbl_mod_ret_txt.setText(f"Retirado ({mod['RETIRADO'] / tot_mod * 100:.0f}%)")
        self.lbl_mod_ret_val.setText(f"{mod['RETIRADO']:,.0f}")
        self.lbl_mod_aut_txt.setText(f"Autoflete ({mod['AUTOFLETE'] / tot_mod * 100:.0f}%)")
        self.lbl_mod_aut_val.setText(f"{mod['AUTOFLETE']:,.0f}")

        mix_ent = m["mix_entregado"]
        tot_ent = max(mix_ent["granel"] + mix_ent["envasado"], 0.001)
        self.lbl_ent_gra_txt.setText(f"granel ({mix_ent['granel'] / tot_ent * 100:.0f}%)")
        self.lbl_ent_gra_val.setText(f"{mix_ent['granel']:,.0f}")
        self.lbl_ent_env_txt.setText(f"envasado ({mix_ent['envasado'] / tot_ent * 100:.0f}%)")
        self.lbl_ent_env_val.setText(f"{mix_ent['envasado']:,.0f}")

        # 4. Tablas Mix Planta y Centros
        factor_tend = m["factor_tendencia"]
        mix_p = m["mix_planta"]
        self._poblar_tabla_mix(
            self.tbl_mix_planta,
            sal_gra=mix_p["granel"]["salidas"],
            obj_gra=mix_p["granel"]["objetivo"],
            sal_env=mix_p["envasado"]["salidas"],
            obj_env=mix_p["envasado"]["objetivo"],
            factor_tend=factor_tend,
        )

        for cod_ce, tbl_ce in self.tablas_centros.items():
            datos_ce = m["por_centro"].get(cod_ce, {
                "granel": {"salidas": 0.0, "objetivo": 0.0},
                "envasado": {"salidas": 0.0, "objetivo": 0.0},
            })
            self._poblar_tabla_mix(
                tbl_ce,
                sal_gra=datos_ce["granel"]["salidas"],
                obj_gra=datos_ce["granel"]["objetivo"],
                sal_env=datos_ce["envasado"]["salidas"],
                obj_env=datos_ce["envasado"]["objetivo"],
                factor_tend=factor_tend,
            )

        # 5. Tablas por Turno
        turnos_map = [
            ("1er Turno", self.tbl_turno_1),
            ("2do Turno", self.tbl_turno_2),
            ("3er Turno", self.tbl_turno_3),
        ]
        for nom_t, tbl_t in turnos_map:
            dt_t = m["por_turno"].get(nom_t, {
                "granel": {"salidas": 0.0, "objetivo": 0.0},
                "envasado": {"salidas": 0.0, "objetivo": 0.0},
                "factor_tend": 1.0,
            })
            self._poblar_tabla_mix(
                tbl_t,
                sal_gra=dt_t["granel"]["salidas"],
                obj_gra=dt_t["granel"]["objetivo"],
                sal_env=dt_t["envasado"]["salidas"],
                obj_env=dt_t["envasado"]["objetivo"],
                factor_tend=dt_t.get("factor_tend", 1.0),
            )

        # 6. Tablas de Productos
        self._poblar_tabla_productos(self.tbl_prod_env, m["filas_productos_envasado"])
        self._poblar_tabla_productos(self.tbl_prod_gra, m["filas_productos_granel"])


# ==============================================================================
# VENTANA PRINCIPAL DE OPERACIÓN
# ==============================================================================
class VentanaBasculaMain(QMainWindow):
    def __init__(self, session_data: SessionData):
        super().__init__()
        self.sap_manager = SAPManager()
        self.manager_descargas = DescargasManager(sap_manager=self.sap_manager)

        self.session_data = session_data
        self.nombre_planta = session_data.planta_gui_nombre # <--
        self.codigos_sap = session_data.planta_gui_codigos # <--
        self.intervalo_robot_minutos = 10


        # --- CONFIGURACIÓN DINÁMICA DE VISTAS ---
        if "Tula" in self.nombre_planta:
            self.vistas_config = [
                {"nombre": "granel - LÍNEA 1 (MX47)",   "gpo": "granel",   "ce": "MX47", "filtro_mat": ""},
                {"nombre": "granel - LÍNEA 2 (MX57)",   "gpo": "granel",   "ce": "MX57", "filtro_mat": ""},
                {"nombre": "envasado - LÍNEA 2 (MX57) FORTALEZA", "gpo": "envasado", "ce": "MX57", "filtro_mat": "FORTALEZA"},
                {"nombre": "envasado - LÍNEA 2 (MX57) MORTEROS",  "gpo": "envasado", "ce": "MX57", "filtro_mat": "MORTERO"},
                {"nombre": "envasado - LÍNEA 2 (MX57) BIG BAG",   "gpo": "envasado", "ce": "MX57", "filtro_mat": "BIG BAG"},
                {"nombre": "envasado - LÍNEA 1 (MX47) MAGNOS",    "gpo": "envasado", "ce": "MX47", "filtro_mat": "MAGNO"},
                {"nombre": "envasado - LÍNEA 1 (MX47) BLANCOS",   "gpo": "envasado", "ce": "MX47", "filtro_mat": "BCO"},
                {"nombre": "DASHBOARD SALIDAS (249)",             "gpo": "DASHBOARD","ce": "",     "filtro_mat": ""},
            ]
        else:
            self.vistas_config = [
                {"nombre": "granel",                  "gpo": "granel",    "ce": "", "filtro_mat": ""},
                {"nombre": "envasado",                "gpo": "envasado",  "ce": "", "filtro_mat": ""},
                {"nombre": "DASHBOARD SALIDAS (249)", "gpo": "DASHBOARD", "ce": "", "filtro_mat": ""},
            ]

        
        # Estado
        self.indice_vista_actual = 0
        self.datos_totales = [] # Aquí vivirá la "Base de Datos" temporal (ZSDMX389)
        self.df_249 = pd.DataFrame() # DataFrame filtrado de salidas reales (249.parquet)
        self._auto_fecha_249_aplicada = False
        self._cache_oferta_parquet = {"ruta": None, "mtime": None, "df": None}
        
        # UI Config
        self.setWindowTitle(f"Control de Báscula - {session_data.planta_gui_nombre}")
        # self.showMaximized() QUITAMOS de aquí (lo haremos al final cuando ya esté todo construido)
        self.setMinimumSize(1024, 700) # Un tamaño base seguro por si el usuario restaura la ventana
        self.setStyleSheet("background-color: #FFFFFF;")

        # Atajo de teclado F5 para cambiar vista
        self.shortcut_f5 = QShortcut(QKeySequence("F5"), self)
        self.shortcut_f5.activated.connect(self.cambiar_vista)

        # ====================================================================
        # CONFIGURACIÓN HOMOLOGADA DEL ÍCONO (TÍTULO Y BARRA DE TAREAS)
        configurar_icono_app(self, app_id="kiosko.bascula.produccion.1.0")

        # Layout Principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # ---------------------------------------------------------
        # 1/3 SUPERIOR: PANEL DE CONTROL Y KPI
        # ---------------------------------------------------------
        self.frame_top = QFrame()
        self.frame_top.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #aaa;")
        self.frame_top.setFixedHeight(280) # Aproximadamente 1/3 de pantalla FHD
        top_layout = QHBoxLayout(self.frame_top)
        
        # A. Info de Vista Actual (Izquierda)
        layout_info = QVBoxLayout()
        self.lbl_vista_titulo = QLabel("CARGANDO...")
        self.lbl_vista_titulo.setFont(QFont("Arial Black", 26, QFont.Weight.Bold))
        self.lbl_vista_titulo.setStyleSheet("color: #008080;")
        
        self.lbl_kpi_unidades = QLabel("Unidades Pendientes: 0")
        self.lbl_kpi_unidades.setFont(QFont("Arial", 16))
        
        self.lbl_kpi_toneladas = QLabel("Toneladas Pendientes: 0.00 ton")
        self.lbl_kpi_toneladas.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.lbl_kpi_toneladas.setStyleSheet("color: #D35400;") # Color óxido para resaltar
        
        layout_info.addWidget(self.lbl_vista_titulo)
        layout_info.addWidget(self.lbl_kpi_unidades)
        layout_info.addWidget(self.lbl_kpi_toneladas)
        layout_info.addStretch()
        
        # B. Botones de Acción (Derecha)
        layout_botones = QVBoxLayout()
        layout_botones.setSpacing(8)

        fila_botones_nav = QHBoxLayout()
        fila_botones_nav.setSpacing(8)

        # Botón Cambiar Vista
        self.btn_cambiar_vista = QPushButton("🔄 CAMBIAR VISTA (F5)")
        self.btn_cambiar_vista.setFixedHeight(65)
        self.btn_cambiar_vista.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.btn_cambiar_vista.setStyleSheet("""
            QPushButton { background-color: #2C3E50; color: white; border-radius: 10px; }
            QPushButton:hover { background-color: #34495E; }
        """)
        self.btn_cambiar_vista.clicked.connect(self.cambiar_vista)

        # Botón Acceso Directo al Dashboard Salidas 249
        self.btn_ir_dashboard = QPushButton("📊 DASHBOARD SALIDAS")
        self.btn_ir_dashboard.setFixedHeight(65)
        self.btn_ir_dashboard.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.btn_ir_dashboard.setStyleSheet("""
            QPushButton { background-color: #0F766E; color: white; border-radius: 10px; }
            QPushButton:hover { background-color: #115E59; }
        """)
        self.btn_ir_dashboard.clicked.connect(self.alternar_vista_dashboard)

        fila_botones_nav.addWidget(self.btn_cambiar_vista)
        fila_botones_nav.addWidget(self.btn_ir_dashboard)

        # Botón Nuevo Arribo (Pocket gui_arribo)
        self.btn_arribar_nvo = QPushButton("➕ NUEVO ARRIBO")
        self.btn_arribar_nvo.setFixedHeight(65)
        self.btn_arribar_nvo.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self.btn_arribar_nvo.setStyleSheet("""
            QPushButton { background-color: #008080; color: white; border-radius: 10px; border: 2px solid #006666; }
            QPushButton:hover { background-color: #006666; }
            QPushButton:pressed { background-color: #004d4d; }
            QPushButton:disabled { background-color: #BDC3C7; color: #7F8C8D; border: 2px solid #A6ACAF; }
        """)
        self.btn_arribar_nvo.clicked.connect(self.accion_nuevo_arribo)

        # Validación de permisos por usuario de Windows (environ)
        from catalogos import USUARIOS_AUTORIZADOS_ARRIBO
        usuario_windows = (os.environ.get("USERNAME") or os.environ.get("USER") or "").strip().lower()
        if usuario_windows in USUARIOS_AUTORIZADOS_ARRIBO:
            self.btn_arribar_nvo.setEnabled(True)
            self.btn_arribar_nvo.setToolTip(f"Autorizado: {USUARIOS_AUTORIZADOS_ARRIBO[usuario_windows]} ({usuario_windows})")
        else:
            self.btn_arribar_nvo.setEnabled(False)
            self.btn_arribar_nvo.setToolTip(f"No disponible para el usuario actual ({usuario_windows})")

        # Botón LLAMAR
        self.btn_llamar = QPushButton("📢 LLAMAR SELECCIONADOS")
        self.btn_llamar.setFixedHeight(80)
        self.btn_llamar.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.btn_llamar.setStyleSheet("""
            QPushButton { background-color: #27AE60; color: white; border-radius: 10px; border: 2px solid #1E8449; }
            QPushButton:hover { background-color: #2ECC71; }
            QPushButton:pressed { background-color: #1E8449; }
        """)
        self.btn_llamar.clicked.connect(self.accion_llamar_operadores)

        layout_botones.addLayout(fila_botones_nav)
        layout_botones.addWidget(self.btn_arribar_nvo)
        layout_botones.addWidget(self.btn_llamar)
        
        top_layout.addLayout(layout_info, stretch=2)
        top_layout.addLayout(layout_botones, stretch=1)

        # ---------------------------------------------------------
        # 2/3 INFERIOR: CONTENEDOR APILADO (TABLA OPERADORES / DASHBOARD 249)
        # ---------------------------------------------------------
        self.tabla = QTableWidget()
        # Definimos las 12 columnas definitivas desde el inicio (Índices 0 al 11)
        columnas = ["Sel", "Estatus", "Turno", "Remision", "Transporte", "Material", "Ton", "Mod", "Placas", "Operador", "Destinatario", "Espera"]
        self.tabla.setColumnCount(len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        
        # Ajustamos al contenido las columnas de datos cortos
        columnas_autoajuste = [0, 1, 2, 3, 4, 6, 7, 8, 9, 11]
        for col in columnas_autoajuste:
            self.tabla.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
            
        # Dejamos que Material (5) y Destinatario (10) se estiren dinámicamente para llenar el monitor sin cortar la GUI
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeMode.Stretch)
        
        self.tabla.setStyleSheet("""
            QTableWidget { background-color: white; font-size: 14px; gridline-color: #ccc; }
            QHeaderView::section { background-color: #333; color: white; font-weight: bold; padding: 5px; }
            QCheckBox::indicator { width: 30px; height: 30px; }
        """)

        self.dashboard_widget = DashboardSalidasWidget(self)

        self.stack_central = QStackedWidget()
        self.stack_central.addWidget(self.tabla)            # Índice 0: Tabla Operativa Báscula
        self.stack_central.addWidget(self.dashboard_widget) # Índice 1: Dashboard Minimalista 249
        
        # Agregamos widgets al layout principal
        self.main_layout.addWidget(self.frame_top)
        self.main_layout.addWidget(self.stack_central, stretch=1)

        # ---------------------------------------------------------
        # INICIALIZACIÓN
        # ---------------------------------------------------------
        # Extraes de la sesión
        self.ruta_base_drive = self.session_data.ruta_base_drive

        # 2. Instanciar el manager de arribos
        self.arribos_manager = ArribosManager()

        # 3. Sincronización ligera inicial de parquets (vt16, 249 y oferta_planta)
        try:
            actualizar_parquet_vt16()
            actualizar_parquet_zsdmx249()
            obtener_oferta_plantas(ruta_base_drive=self.ruta_base_drive, limite_minutos=999)
        except Exception as e_pq_ini:
            print(f"⚠️ Aviso al sincronizar parquets en arranque: {e_pq_ini}")

        self.cargar_datos_reales()
        self.actualizar_interfaz_vista()

         # 💻 KEEP-ALIVE WINDOWS: Evitamos que la gui entre en reposo
        evitar_bloqueo_windows()
        self.sap_manager.iniciar_keep_alive(intervalo_minutos=13)
        # No es necesario el keep alive, si estamos descargando el archivo cada 10 minutos
        
        # 4. Timer 
        # --- TEMPORIZADOR PARA ROBOT DESCARGA ZSDMX389, ZSDMX249 Y VT16 ---
        self.timer_robot_sap = QTimer(self)
        tiempo_robot_ms = self.intervalo_robot_minutos * 60 * 1000
        print(f"🤖 [SAP] Robot ZSDMX389 + ZSDMX249 + VT16 iniciado. Intervalo: {self.intervalo_robot_minutos} min")
        self.timer_robot_sap.start(tiempo_robot_ms)
        self.timer_robot_sap.timeout.connect(self._ejecutar_robot_zsdmx_bascula)
    
    def mostrar_mensaje_estado(self, msg: str, es_correcto: bool):
        """
        'aplicar_color_estado'.
        Muestra texto en la barra inferior (statusBar) con fondo y letra condicional.
        """
        if es_correcto:
            # Estado Válido / Éxito (Fondo Verde Claro, Texto Verde Oscuro)
            estilo = """
                QStatusBar { 
                    background-color: rgb(198, 239, 206); 
                    color: rgb(0, 97, 0); 
                    font-weight: bold; 
                }
            """
        else:
            # Estado Inválido / Error (Fondo Rosa, Texto Rojo Oscuro)
            estilo = """
                QStatusBar { 
                    background-color: rgb(255, 199, 206); 
                    color: rgb(156, 0, 6); 
                    font-weight: bold; 
                }
            """
        
        # Aplicamos el color y mandamos el texto a la pantalla
        self.statusBar().setStyleSheet(estilo)
        self.statusBar().showMessage(msg, 10000) # El 10000 indica que el mensaje se borrará solo a los 10 segundos
    # ==========================================================================
    # LÓGICA DE VISTAS
    # ==========================================================================
    
    def cambiar_vista(self):
        """Cicla entre las vistas configuradas en VISTAS_CONFIG."""
        self.indice_vista_actual = (self.indice_vista_actual + 1) % len(self.vistas_config)
        self.actualizar_interfaz_vista()

    def alternar_vista_dashboard(self):
        """Salta directamente a la vista Dashboard Salidas (249) o regresa a la primera vista operativa."""
        idx_dash = next(
            (i for i, v in enumerate(self.vistas_config) if v.get("gpo") == "DASHBOARD"),
            None,
        )
        if idx_dash is None:
            return
        if self.indice_vista_actual == idx_dash:
            self.indice_vista_actual = 0
        else:
            self.indice_vista_actual = idx_dash
        self.actualizar_interfaz_vista()

    def accion_nuevo_arribo(self):
        """
        Abre gui_arribo.py en modo satélite/pocket reutilizando los datos de planta
        de la sesión actual de Báscula. Al concluir el arribo, cierra la ventana
        y ejecuta cargar_datos_reales() para reflejar el camión en la tabla.
        """
        from gui_arribo import AppWindow

        # Creamos una sesión limpia para el arribo pero heredando la planta y ruta activas en Báscula
        session_arribo = SessionData()
        session_arribo.planta_gui_nombre = self.session_data.planta_gui_nombre
        session_arribo.planta_gui_codigos = list(self.session_data.planta_gui_codigos)
        session_arribo.planta_gui_letra = getattr(self.session_data, "planta_gui_letra", "X")
        session_arribo.ruta_base_drive = self.session_data.ruta_base_drive

        self.ventana_arribo_pocket = AppWindow(session_config=session_arribo, modo_bascula=True)
        self.ventana_arribo_pocket.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.ventana_arribo_pocket.arribo_completado_signal.connect(self.cargar_datos_reales)
        self.ventana_arribo_pocket.show()

    def actualizar_interfaz_vista(self):
        """Filtra los datos globales y repuebla la tabla o muestra el Dashboard minimalista según la vista actual."""
        config_actual = self.vistas_config[self.indice_vista_actual]
        nombre_vista = config_actual["nombre"]
        filtro_gpo = config_actual["gpo"]
        filtro_ce = config_actual["ce"]
        filtro_mat = config_actual.get("filtro_mat", "")

        self.lbl_vista_titulo.setText(f"VISTA: {nombre_vista}")

        # --- MODO DASHBOARD SALIDAS (249) ---
        if filtro_gpo == "DASHBOARD":
            self.stack_central.setCurrentIndex(1)
            self.btn_llamar.setVisible(False)
            self.lbl_kpi_unidades.setVisible(False)
            self.lbl_kpi_toneladas.setVisible(False)
            self.frame_top.setFixedHeight(155)
            self.btn_ir_dashboard.setText("🚛 VOLVER A TABLERO")
            self.cargar_df_249()
            return

        # --- MODO TABLERO OPERATIVO DE BÁSCULA ---
        self.stack_central.setCurrentIndex(0)
        self.btn_llamar.setVisible(True)
        self.lbl_kpi_unidades.setVisible(True)
        self.lbl_kpi_toneladas.setVisible(True)
        self.frame_top.setFixedHeight(280)
        self.btn_ir_dashboard.setText("📊 DASHBOARD SALIDAS")
        
        # Filtrado
        items_filtrados = []
        suma_toneladas = 0.0
        
        for x_remision in self.datos_totales:
            estatus = x_remision.get("estatus", "")
            
            # 1. Filtro de Estatus (Solo ESPERA o LLAMADO)
            if estatus not in ["ESPERA", "LLAMADO"]:
                continue

            # 2. Filtro por Grupo de Material (envasado o granel)
            if x_remision.get("gpo_material") != filtro_gpo:
                continue

            # 3. Filtro por Centro de Expedición (Solo aplica si la vista tiene un "ce" específico como Tula)
            if filtro_ce != "" and x_remision.get("c_exp") != filtro_ce:
                continue

            # 4. Filtro por Familia de Material (Solo si la vista lo requiere)
            if filtro_mat != "" and filtro_mat not in str(x_remision.get("material", "")): 
                continue

            # Si pasa todos los filtros, lo agregamos a la tabla
            items_filtrados.append(x_remision)
            if estatus in ["ESPERA", "LLAMADO"]:
                suma_toneladas += float(x_remision.get("toneladas", 0.0))

        # Actualizar KPIs
        pendientes = len([x for x in items_filtrados if x.get("estatus") == "ESPERA"])
        self.lbl_kpi_unidades.setText(f"Unidades Pendientes: {pendientes}")
        self.lbl_kpi_toneladas.setText(f"Toneladas Pendientes: {suma_toneladas:.2f} TON")

        # ordenar array
        items_filtrados.sort(key=lambda x: str(x.get("transporte", "")))

        # Poblar Tabla
        self._llenar_tabla(items_filtrados)

    def _llenar_tabla(self, lista_camiones):
        self.tabla.setRowCount(0)
        
        # 1. Asegurar que las columnas del encabezado sean las nuevas (puedes poner esto en tu __init__ también)
        #columnas = ["Sel", "Estatus", "Turno", "Remision", "Transporte", "Material", "Ton", "Mod", "Placas", "Operador", "Destinatario", "Espera"]
        #self.tabla.setColumnCount(len(columnas))
        #self.tabla.setHorizontalHeaderLabels(columnas)
        
        for i, datos in enumerate(lista_camiones):
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            
            # Columna 0: Checkbox
            chk_widget = QWidget()
            chk = QCheckBox()
            chk.setStyleSheet("margin-left: 10px;")
            if datos["estatus"] == "ESPERA":
                chk.setChecked(False)
            else:
                chk.setDisabled(True) 
            
            # Usamos la remisión como el ID infalible para no depender del transporte vacío
            chk.setProperty("id_identificador", datos["remision"])
            
            layout_chk = QHBoxLayout(chk_widget)
            layout_chk.addWidget(chk)
            layout_chk.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_chk.setContentsMargins(0,0,0,0)
            self.tabla.setCellWidget(row, 0, chk_widget)

            try:
                # OJO: Ajusta "%d.%m.%Y %H:%M:%S" al formato exacto que te da SAP en el CSV
                fch_obj = datetime.strptime(datos["fch_planif"], "%d.%m.%Y %H:%M:%S")
                delta = datetime.now() - fch_obj
                
                dias = delta.days
                horas = delta.seconds // 3600
                minutos = (delta.seconds % 3600) // 60
                
                if dias > 0:
                    tiempo_espera = f"{dias}d {horas}h"
                else:
                    tiempo_espera = f"{horas}h {minutos}m"
            except:
                tiempo_espera = "---" # Por si SAP manda un formato raro o vacío

            modalidad = str(datos.get("modalidad", ""))[:3].upper()

            # 2. Ensamblar la fila en el orden EXACTO de tus columnas (Índices 1 al 10)
            vals = [
                datos["estatus"],           # Columna 1: Estatus
                datos["turno"],             # Columna 2: Turno
                datos["remision"],          # Columna 3: Remision
                datos["transporte"],        # Columna 4: Transporte
                datos["material"],          # Columna 5: Material
                f"{datos['toneladas']:.2f}",# Columna 6: Ton
                modalidad,                  # Columna 7: Modalidad
                datos["placas"],            # Columna 8: Placas
                datos["operador"],          # Columna 9: Operador
                datos["destinatario_nom"],  # Columna 10: Destinatario
                tiempo_espera               # Columna 11: Espera
            ]

            for col_idx, valor in enumerate(vals, start=1):
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if datos["estatus"] == "LLAMADO":
                    item.setBackground(QColor("#D5F5E3")) 
                    item.setForeground(QColor("#145A32"))

                # --- FORMATO CONDICIONAL PARA MODALIDAD ---
                elif col_idx == 7: 
                    if valor == "ENT":
                        item.setBackground(QColor("#FFCBCE")) # Rosa/Rojo de tu VBA
                        item.setForeground(QColor("#943126")) # Texto rojo oscuro
                    elif valor == "AUT":
                        item.setBackground(QColor("#C6F3CE")) # Verde de tu VBA
                        item.setForeground(QColor("#1E8449")) # Texto verde oscuro
                    elif valor == "RET":
                        item.setBackground(QColor("#FFEB9C")) # Amarillo de tu VBA
                        item.setForeground(QColor("#7D6608")) # Texto café/dorado
                elif col_idx == 5: # <-- Asegúrate de que 5 sea tu columna de Material
                    from catalogos import CATALOGO_MATERIALES
                    
                    # Buscamos qué material del catálogo está contenido en el texto de la celda
                    for data in CATALOGO_MATERIALES.values():
                        if str(data["desc_nom_corto"]).upper() in str(valor).upper():
                            # Si lo encuentra, aplica los colores configurados y rompe el ciclo
                            if "bg" in data:
                                item.setBackground(QColor(data["bg"]))
                            if "fg" in data:
                                item.setForeground(QColor(data["fg"]))
                            break
            
                self.tabla.setItem(row, col_idx, item)
        print(f"✅ [{time.strftime('%H:%M:%S')}] Tabla Actualizada")

    def accion_llamar_operadores(self):
            """
            Orquesta el llamado de operadores:
            1. Obtiene las remisiones seleccionadas y sus transportes asociados.
            2. Arma el diccionario data = {"TEXT3": "02 llamado DD/MM/YYYY HH:MM:SS"}.
            3. Ejecuta modificar_transporte en SAP (VT02N) en Modo Túnel y actualiza la tabla si devuelve True.
            """
            remisiones_seleccionadas = []
            
            # 1. Escanear Tabla buscando checkboxes marcados
            filas = self.tabla.rowCount()
            for r in range(filas):
                widget_chk = self.tabla.cellWidget(r, 0)
                if widget_chk:
                    chk = widget_chk.findChild(QCheckBox)
                    if chk and chk.isChecked():
                        rem_id = str(chk.property("id_identificador")).strip()
                        remisiones_seleccionadas.append(rem_id)

            if not remisiones_seleccionadas:
                QMessageBox.warning(self, "Atención", "Seleccione al menos un operador de la lista para llamar.")
                return

            # 2. Agrupar remisiones por Número de Transporte (Evita entrar 2 veces a VT02N en un Full)
            # Estructura: { "4800123456": ["7530000001", "7530000002"] }
            mapa_transportes = {}
            sin_transporte = []

            for x_rem in self.datos_totales:
                rem_actual = str(x_rem.get("remision", "")).strip()
                if rem_actual in remisiones_seleccionadas:
                    num_trans = str(x_rem.get("transporte", "")).strip()
                    if num_trans and num_trans not in ["---", "PENDIENTE", "None", ""]:
                        if num_trans not in mapa_transportes:
                            mapa_transportes[num_trans] = []
                        mapa_transportes[num_trans].append(rem_actual)
                    else:
                        sin_transporte.append(rem_actual)

            if sin_transporte:
                QMessageBox.warning(
                    self, "Transporte Faltante",
                    f"Las siguientes remisiones aún no tienen número de transporte válido:\n{', '.join(sin_transporte)}"
                )
                if not mapa_transportes:
                    return

            # 3. Confirmación del usuario en Báscula
            confirm = QMessageBox.question(
                self, "Confirmar Llamado",
                f"¿Desea llamar a {len(mapa_transportes)} unidad(es) ({len(remisiones_seleccionadas)} remisiones) a Báscula?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm != QMessageBox.Yes:
                return

            # 4. Armar el diccionario con la estampa de tiempo al momento
            ahora_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            texto_llamado = f"02 llamado {ahora_str}"
            
            data_cambios = {
                "TEXT3": texto_llamado
            }

            # 5. Iterar sobre cada transporte único y mandarlo a SAP VT02N dentro del Modo Túnel
            transportes_exitosos = []
            errores_sap = []

            # Importamos SAPError por si hay bloqueo en SAP
            from manager_sap import SAPError

            with self.sap_manager.tunel(f"Báscula: Llamar {len(mapa_transportes)} Transporte(s) en VT02N"):
                for num_transporte, lista_rems in mapa_transportes.items():
                    try:
                        QApplication.processEvents() # Mantiene viva la ventana de Qt5 mientras trabaja SAP
                        exito = self.sap_manager.modificar_transporte(num_transporte, data_cambios)
                        
                        if exito:
                            transportes_exitosos.append(num_transporte)
                            # Actualizamos en memoria todas las remisiones asociadas a este transporte
                            for x_remision in self.datos_totales:
                                if str(x_remision.get("transporte", "")).strip() == num_transporte:
                                    x_remision["estatus"] = "LLAMADO"
                                    
                    except SAPError as e_sap:
                        print(f"❌ Error SAP al llamar transporte {num_transporte}: {e_sap}")
                        errores_sap.append(f"• {e_sap}")
                    except Exception as e_gen:
                        print(f"❌ Error inesperado con transporte {num_transporte}: {e_gen}")
                        errores_sap.append(f"Transporte {num_transporte}: {e_gen}")

            # 6. Refrescar interfaz y dar retroalimentación al usuario
            self.actualizar_interfaz_vista()

            if transportes_exitosos and not errores_sap:
                QMessageBox.information(
                    self, "Éxito", 
                    f"Se actualizaron correctamente {len(transportes_exitosos)} transporte(s) en SAP con:\n'{texto_llamado}'"
                )
            elif transportes_exitosos and errores_sap:
                detalle_err = "\n".join(errores_sap)
                QMessageBox.warning(
                    self, "Llamado Parcial",
                    f"Se llamaron {len(transportes_exitosos)} transporte(s), pero hubo errores en otros:\n\n{detalle_err}"
                )
            else:
                detalle_err = "\n".join(errores_sap)
                QMessageBox.critical(
                    self, "Error en SAP",
                    f"No se pudo modificar ningún transporte en VT02N:\n\n{detalle_err}"
                )
                
    # ==========================================================================
    # CARGA DE DATOS REALES Y SINCRONIZACIÓN DE PARQUETS (249, VT16, OFERTA)
    # ==========================================================================
    def _ejecutar_robot_zsdmx_bascula(self):
        """
        Orquestación periódica del Robot de Báscula (cada 10 min):
        - Descarga las remisiones EN PROCESO (ZSDMX389).
        - Descarga los últimos 2 días (ayer y hoy) de ZSDMX249 (límite 10 min).
        - Descarga VT16 del mes en curso (límite 10 min).
        - Actualiza vt16.parquet y consolida/enriquece 249.parquet (horas, turnos y modalidades).
        - Actualiza oferta_planta.parquet (1 vez al día).
        - Recarga datos en vivo para el tablero de báscula y el Dashboard 249.
        - Se ejecuta en Modo Túnel / Fila Virtual para no colisionar con llamados VT02N ni nuevos arribos.
        """
        import time

        def _tarea_descarga_bascula():
            if not self.sap_manager.validar_conexion():
                return
            print(f"⏳ [{time.strftime('%H:%M:%S')}] [ROBOT BÁSCULA] Iniciando actualización (ZSDMX389 + ZSDMX249 + VT16)...")
            try:
                # 1. Descarga ZSDMX389 (En Proceso)
                res_389 = self.manager_descargas.zsdmx389_robot(
                    self.ruta_base_drive,
                    tipo_descarga="en_proceso",
                )

                # 2. Descarga ZSDMX249 (ayer y hoy -> dias_atras=1, validando antigüedad > 10 min)
                res_249 = self.manager_descargas.zsdmx249_robot(
                    self.ruta_base_drive,
                    dias_atras=1,
                    extension="xls",
                    limite_minutos=self.intervalo_robot_minutos,
                )

                # 3. Descarga VT16 (mes en curso, validando antigüedad > 10 min)
                res_vt16 = self.manager_descargas.vt16_robot(
                    self.ruta_base_drive,
                    extension="xls",
                    limite_minutos=self.intervalo_robot_minutos,
                )

                # 4. Actualizar vt16.parquet primero para que el cruce de 249.parquet tome los datos en vivo
                res_pq_vt16 = actualizar_parquet_vt16()

                # 5. Actualizar 249.parquet (consolida nuevos/modificados y enriquece con VT16)
                res_pq_249 = actualizar_parquet_zsdmx249()

                # 6. Actualizar oferta_planta.parquet (validando limite_minutos=999 -> solo 1 vez por día)
                obtener_oferta_plantas(ruta_base_drive=self.ruta_base_drive, limite_minutos=999)

                ok_389 = res_389.get("estatus", False)
                ok_249 = res_249.get("estatus", False)
                ok_vt16 = res_vt16.get("estatus", False)

                # Recargar datos de la vista activa y del Dashboard 249
                self.cargar_datos_reales()

                if ok_389 and ok_249 and ok_vt16:
                    msg_exito = f"SAP Sincronizado | 389 OK | 249 OK | VT16 OK"
                    self.mostrar_mensaje_estado(msg=msg_exito, es_correcto=True)
                else:
                    errores = []
                    if not ok_389:
                        errores.append(f"389: {res_389.get('msg', 'Error')}")
                    if not ok_249:
                        errores.append(f"249: {res_249.get('msg', 'Error')}")
                    if not ok_vt16:
                        errores.append(f"VT16: {res_vt16.get('msg', 'Error')}")
                    msg_error = " | ".join(errores)
                    print(f"⚠️ [{time.strftime('%H:%M:%S')}] Aviso en robot SAP: {msg_error}")
                    self.mostrar_mensaje_estado(msg=msg_error, es_correcto=False)

            except Exception as e:
                print(f"⚠️ [{time.strftime('%H:%M:%S')}] Error crítico en ejecución de báscula: {e}")

        self.sap_manager.ejecutar_o_encolar(
            "Robot Báscula: ZSDMX389 + ZSDMX249 + VT16",
            _tarea_descarga_bascula
        )

    def cargar_datos_reales(self):
        """Extrae la data en vivo del Excel ZSDMX389 (En Proceso) y actualiza df_249."""
        try:
            # Pasamos rem=None para que traiga la lista completa y tipo_archivo="en_proceso"
            nuevos_datos = self.arribos_manager.leer_zsdmx389_local(
                ruta_base_drive=self.ruta_base_drive, 
                rem=None, 
                tipo_archivo="en_proceso",
                codigos_planta=self.session_data.planta_gui_codigos
            )
            
            # TRUCO: Conservar el estatus visual "LLAMADO"
            transportes_llamados = [x_remision["remision"] for x_remision in self.datos_totales if x_remision.get("estatus") == "LLAMADO"]

            for nuevo_cam in nuevos_datos:
                if nuevo_cam["remision"] in transportes_llamados:
                    nuevo_cam["estatus"] = "LLAMADO"

            self.datos_totales = nuevos_datos
            self.cargar_df_249()
            self.actualizar_interfaz_vista()
            
        except Exception as e:
            print(f"⚠️ Aviso: No se pudo refrescar el tablero de báscula: {e}")

    def cargar_df_249(self, fecha_str: str = None):
        """
        Lee '249.parquet', filtra por los códigos de centro de la planta activa
        (self.session_data.planta_gui_codigos) y por la fecha seleccionada,
        guarda el resultado en self.df_249 y actualiza el Dashboard minimalista.
        """
        try:
            if not fecha_str:
                fecha_str = self.dashboard_widget.obtener_fecha_seleccionada_str()

            df_planta_actual = obtener_df_249(
                codigos_planta=self.session_data.planta_gui_codigos,
                fecha_sm=fecha_str,
            )

            # Si en el arranque inicial hoy aún no tiene registros en 249.parquet,
            # seleccionamos automáticamente la fecha más reciente con salidas de la planta
            if df_planta_actual.empty and not self._auto_fecha_249_aplicada:
                self._auto_fecha_249_aplicada = True
                df_hist = obtener_df_249(
                    codigos_planta=self.session_data.planta_gui_codigos,
                    fecha_sm=None,
                )
                if not df_hist.empty and "fch_sm_real" in df_hist.columns:
                    fechas_validas = sorted(
                        [f for f in df_hist["fch_sm_real"].dropna().astype(str).unique() if f and f != "NaT"]
                    )
                    if fechas_validas:
                        ultima_fch = fechas_validas[-1]
                        qdate_ult = QDate.fromString(ultima_fch, "yyyy-MM-dd")
                        if qdate_ult.isValid():
                            self.dashboard_widget.date_picker.blockSignals(True)
                            self.dashboard_widget.date_picker.setDate(qdate_ult)
                            self.dashboard_widget.date_picker.blockSignals(False)
                            fecha_str = ultima_fch
                            df_planta_actual = df_hist[df_hist["fch_sm_real"] == fecha_str].copy()
            else:
                self._auto_fecha_249_aplicada = True

            self.df_249 = df_planta_actual
            metricas = self.calcular_metricas_dashboard_249(fecha_str=fecha_str)
            self.dashboard_widget.renderizar_metricas(metricas)

        except Exception as e:
            print(f"⚠️ Error al cargar/calcular df_249 para el Dashboard: {e}")

    def calcular_oferta_planta_desde_parquet(self, fecha_dt: datetime) -> dict:
        """
        Flujo homologado data -> parquet -> gui:
        1. Asegura que 'oferta_planta.parquet' esté vigente (1 vez al día con limite_minutos=999).
        2. Carga 'oferta_planta.parquet' con caché basado en fecha de modificación (mtime).
        3. Calcula la oferta de planta por semana, por planta, por código y el tonelaje POR DÍA,
           incluyendo mix_planta, por_centro, por_turno (oferta / turnos_operativos) y por producto.
        """
        if fecha_dt is None:
            fecha_dt = datetime.now()

        # Verificar/generar parquet de oferta (solo se regenera si no existe o pasaron > 999 min)
        obtener_oferta_plantas(ruta_base_drive=self.ruta_base_drive, limite_minutos=999)

        info_planta_cat = CATALOGO_PLANTAS.get(self.nombre_planta or "", {})
        turnos_operativos = int(info_planta_cat.get("turnos_operativos", 3) or 3)
        nombre_centro_cat = str(info_planta_cat.get("nombre_centro", "")).strip().upper()
        cods_upper = [str(c).strip().upper() for c in (self.codigos_sap or []) if str(c).strip()]

        turnos_nombres = ["1er Turno", "2do Turno", "3er Turno"]
        resultado_base = {
            "semana_oferta": None,
            "oferta_planta": 0.0,
            "turnos_operativos": turnos_operativos,
            "mix_planta": {"granel": 0.0, "envasado": 0.0},
            "por_centro": {c: {"granel": 0.0, "envasado": 0.0} for c in cods_upper},
            "por_turno": {t: {"granel": 0.0, "envasado": 0.0} for t in turnos_nombres},
            "productos_envasado": {},
            "productos_granel_bigbag": {},
        }

        rutas_oferta = obtener_rutas_transaccion("oferta_planta")
        archivo_parquet = rutas_oferta["archivo_parquet"]
        if not os.path.exists(archivo_parquet):
            return resultado_base

        # Cargar con caché basado en fecha de modificación para no releer el disco innecesariamente, en este caso el parquet creado
        try:
            mtime_actual = os.path.getmtime(archivo_parquet)
            if (
                self._cache_oferta_parquet["df"] is not None
                and self._cache_oferta_parquet["ruta"] == archivo_parquet
                and self._cache_oferta_parquet["mtime"] == mtime_actual
            ):
                df = self._cache_oferta_parquet["df"].copy()
            else:
                try:
                    df = pd.read_parquet(archivo_parquet, engine="fastparquet")
                except Exception:
                    df = pd.read_parquet(archivo_parquet)
                self._cache_oferta_parquet["ruta"] = archivo_parquet
                self._cache_oferta_parquet["mtime"] = mtime_actual
                self._cache_oferta_parquet["df"] = df.copy()
        except Exception as e:
            print(f"⚠️ [oferta_planta.parquet] Error leyendo '{archivo_parquet}': {e}")
            return resultado_base

        if df is None or df.empty:
            return resultado_base

        # 1. Filtrar por planta (por c_exp en codigos de la planta activa o respaldo por nombre_centro)
        ce_col = df["c_exp"].fillna("").astype(str).str.strip().str.upper()
        if cods_upper:
            df_planta = df[ce_col.isin(cods_upper)].copy()
            if df_planta.empty and nombre_centro_cat and "nombre_centro" in df.columns:
                nc_col = df["nombre_centro"].fillna("").astype(str).str.strip().str.upper()
                df_planta = df[nc_col == nombre_centro_cat].copy()
        elif nombre_centro_cat and "nombre_centro" in df.columns:
            nc_col = df["nombre_centro"].fillna("").astype(str).str.strip().str.upper()
            df_planta = df[nc_col == nombre_centro_cat].copy()
        else:
            df_planta = df.copy()

        if df_planta.empty:
            return resultado_base

        # Si el parquet trae turnos_operativos enriquecidos desde CATALOGO_PLANTAS, usarlos
        if "turnos_operativos" in df_planta.columns:
            turnos_vals = pd.to_numeric(df_planta["turnos_operativos"], errors="coerce").dropna()
            if not turnos_vals.empty:
                turnos_operativos = int(turnos_vals.iloc[0])

        # 2. Determinar la semana vigente (última semana declarada <= semana de fecha_dt, válida para semanas subsecuentes)
        semana_fecha = int(fecha_dt.isocalendar()[1])
        semanas_disp = sorted(pd.to_numeric(df_planta["semana"], errors="coerce").dropna().astype(int).unique())
        if not semanas_disp:
            return resultado_base
        semanas_candidatas = [s for s in semanas_disp if s <= semana_fecha]
        semana_vigente = int(semanas_candidatas[-1]) if semanas_candidatas else int(semanas_disp[-1])

        df_vigente = df_planta[pd.to_numeric(df_planta["semana"], errors="coerce") == semana_vigente].copy()
        if df_vigente.empty:
            return resultado_base

        fam_series = df_vigente["material_familia"].fillna("").astype(str).str.strip().str.lower()
        ton_series = pd.to_numeric(df_vigente["ton_of"], errors="coerce").fillna(0.0)
        ce_vig_series = df_vigente["c_exp"].fillna("").astype(str).str.strip().str.upper()

        # 3. Calcular Mix Planta y Oferta Total Planta (tonelaje POR DÍA)
        tot_granel = float(ton_series[fam_series == "granel"].sum())
        tot_envasado = float(ton_series[fam_series == "envasado"].sum())
        oferta_total = tot_granel + tot_envasado

        # 4. Calcular Objetivos por Centro de Expedición (c_exp)
        por_centro = {}
        centros_a_evaluar = cods_upper if cods_upper else sorted(ce_vig_series.unique())
        for cod_ce in centros_a_evaluar:
            g_ce = float(ton_series[(ce_vig_series == cod_ce) & (fam_series == "granel")].sum())
            e_ce = float(ton_series[(ce_vig_series == cod_ce) & (fam_series == "envasado")].sum())
            por_centro[cod_ce] = {"granel": g_ce, "envasado": e_ce}

        # 5. Calcular Objetivos por Turno (oferta_planta / turnos_operativos)
        div_turnos = float(max(1, turnos_operativos))
        obj_gra_turno = round(tot_granel / div_turnos, 2)
        obj_env_turno = round(tot_envasado / div_turnos, 2)

        por_turno = {}
        for idx_t, nom_t in enumerate(turnos_nombres, start=1):
            if idx_t <= turnos_operativos:
                por_turno[nom_t] = {"granel": obj_gra_turno, "envasado": obj_env_turno}
            else:
                por_turno[nom_t] = {"granel": 0.0, "envasado": 0.0}

        # 6. Calcular Objetivos por Producto (Envasado vs Granel + Big Bag)
        productos_envasado = {}
        productos_granel_bigbag = {}

        df_vigente["_nom_corto_u"] = df_vigente["mat_nom_corto"].fillna("").astype(str).str.strip().str.upper()
        df_vigente["_fam_l"] = fam_series
        df_vigente["_ton_v"] = ton_series

        df_agrup_prod = (
            df_vigente.groupby(["_nom_corto_u", "_fam_l"], as_index=False, sort=False)["_ton_v"]
            .sum()
        )
        for _, r_prod in df_agrup_prod.iterrows():
            nom_p = str(r_prod["_nom_corto_u"]).strip().upper()
            fam_p = str(r_prod["_fam_l"]).strip().lower()
            ton_p = float(r_prod["_ton_v"])

            if fam_p == "granel" or "BIG BAG" in nom_p:
                productos_granel_bigbag[nom_p] = productos_granel_bigbag.get(nom_p, 0.0) + ton_p
            elif fam_p == "envasado":
                productos_envasado[nom_p] = productos_envasado.get(nom_p, 0.0) + ton_p

        return {
            "semana_oferta": semana_vigente,
            "oferta_planta": oferta_total,
            "turnos_operativos": turnos_operativos,
            "mix_planta": {"granel": tot_granel, "envasado": tot_envasado},
            "por_centro": por_centro,
            "por_turno": por_turno,
            "productos_envasado": productos_envasado,
            "productos_granel_bigbag": productos_granel_bigbag,
        }

    def calcular_metricas_dashboard_249(self, fecha_str: str) -> dict:
        """
        Calcula con condicionales todas las salidas de la fecha para la planta activa:
          - Cuánto de envasado y cuánto de granel (Total planta y por Centro de Expedición).
          - Cuánto ha salido por Turno (1er, 2do y 3er Turno).
          - Cuánto ha salido por Modalidad (Entregado, Retirado, Autoflete) y Mix Entregado. 
          - Cuánto ha salido por Material/Producto y cuánto queda Por Cargar (desde ZSDMX389).
        """
        try:
            fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
        except Exception:
            fecha_dt = datetime.now()

        cfg_obj = self.calcular_oferta_planta_desde_parquet(fecha_dt=fecha_dt)
        semana_oferta = cfg_obj.get("semana_oferta")
        oferta_planta = float(cfg_obj.get("oferta_planta", 0.0))
        turnos_op = float(cfg_obj.get("turnos_operativos", 3.0))
        obj_mix_planta = cfg_obj.get("mix_planta", {"granel": 0.0, "envasado": 0.0})
        obj_por_centro = cfg_obj.get("por_centro", {})
        obj_por_turno = cfg_obj.get("por_turno", {})
        obj_prod_env = cfg_obj.get("productos_envasado", {})
        obj_prod_gra = cfg_obj.get("productos_granel_bigbag", {})

        df = self.df_249 if self.df_249 is not None else pd.DataFrame()

        # Factor de tendencia: si es hoy, proyecta sobre las horas transcurridas; si es día cerrado, factor = 1.0
        ahora = datetime.now()
        if fecha_dt.date() == ahora.date():
            horas_transcurridas = max(1.0, ahora.hour + (ahora.minute / 60.0))
            factor_tendencia = 24.0 / horas_transcurridas
        else:
            factor_tendencia = 1.0

        # ------------------------------------------------------------------
        # 1. CONDICIONALES: SALIDAS POR FAMILIA (envasado / granel) Y CENTRO
        # ------------------------------------------------------------------
        if not df.empty:
            fam_series = df["material_familia"].fillna("").astype(str).str.strip().str.lower()
            ce_series = df["c_exp"].fillna("").astype(str).str.strip().str.upper()
            ton_series = pd.to_numeric(df["ton"], errors="coerce").fillna(0.0)

            sal_granel_planta = float(ton_series[fam_series == "granel"].sum())
            sal_envasado_planta = float(ton_series[fam_series == "envasado"].sum())
        else:
            fam_series = pd.Series(dtype=str)
            ce_series = pd.Series(dtype=str)
            ton_series = pd.Series(dtype=float)
            sal_granel_planta = 0.0
            sal_envasado_planta = 0.0

        total_cargado = sal_granel_planta + sal_envasado_planta
        tendencia_global = total_cargado * factor_tendencia

        mix_planta = {
            "granel": {
                "salidas": sal_granel_planta,
                "objetivo": float(obj_mix_planta.get("granel", 0.0)),
            },
            "envasado": {
                "salidas": sal_envasado_planta,
                "objetivo": float(obj_mix_planta.get("envasado", 0.0)),
            },
        }

        # Caso por centro solo debe activarse si la planta tiene más de un centro (ej. Planta Tula con MX47 y MX57)
        por_centro = {}
        if len(self.codigos_sap) > 1:
            for cod_ce in self.codigos_sap:
                cod_u = str(cod_ce).strip().upper()
                if not df.empty:
                    s_gra_ce = float(ton_series[(ce_series == cod_u) & (fam_series == "granel")].sum())
                    s_env_ce = float(ton_series[(ce_series == cod_u) & (fam_series == "envasado")].sum())
                else:
                    s_gra_ce = 0.0
                    s_env_ce = 0.0
                obj_ce = obj_por_centro.get(cod_u, {"granel": 0.0, "envasado": 0.0})
                por_centro[cod_u] = {
                    "granel": {"salidas": s_gra_ce, "objetivo": float(obj_ce.get("granel", 0.0))},
                    "envasado": {"salidas": s_env_ce, "objetivo": float(obj_ce.get("envasado", 0.0))},
                }

        # ------------------------------------------------------------------
        # 2. CONDICIONALES: SALIDAS POR TURNO (1er, 2do, 3er Turno)
        # ------------------------------------------------------------------
        por_turno = {}
        turno_series = (
            df["turno_salida"].fillna("SIN TURNO").astype(str)
            if not df.empty and "turno_salida" in df.columns
            else pd.Series(dtype=str)
        )

        # Si hay registros del día que aún no tienen cruce de hora en VT16 ("SIN TURNO"),
        # turno en curso para que el total de turnos cuadre con las salidas reales
        for nom_t, rango_hr in [("1er Turno", (0, 7)), ("2do Turno", (7, 15)), ("3er Turno", (15, 24))]:
            if not df.empty:
                s_gra_t = float(ton_series[(turno_series == nom_t) & (fam_series == "granel")].sum())
                s_env_t = float(ton_series[(turno_series == nom_t) & (fam_series == "envasado")].sum())
            else:
                s_gra_t = 0.0
                s_env_t = 0.0

            obj_t = obj_por_turno.get(nom_t, {"granel": 0.0, "envasado": 0.0})

            # Factor tendencia del turno (si es hoy y el turno sigue en curso, proyecta hasta fin del turno)
            hr_ini, hr_fin = rango_hr
            dur_turno = float(hr_fin - hr_ini)
            if fecha_dt.date() == ahora.date() and hr_ini <= ahora.hour < hr_fin:
                hrs_en_turno = max(0.5, (ahora.hour - hr_ini) + (ahora.minute / 60.0))
                f_tend_t = dur_turno / hrs_en_turno
            else:
                f_tend_t = 1.0

            por_turno[nom_t] = {
                "granel": {"salidas": s_gra_t, "objetivo": float(obj_t.get("granel", 0.0))},
                "envasado": {"salidas": s_env_t, "objetivo": float(obj_t.get("envasado", 0.0))},
                "factor_tend": f_tend_t,
            }

        # ------------------------------------------------------------------
        # 3. CONDICIONALES: SALIDAS POR MODALIDAD Y MIX ENTREGADO
        # ------------------------------------------------------------------
        modalidad_tot = {"ENTREGADO": 0.0, "RETIRADO": 0.0, "AUTOFLETE": 0.0}
        mix_entregado = {"granel": 0.0, "envasado": 0.0}

        if not df.empty:
            mod_raw = (
                df["modalidad"].fillna("").astype(str).str.strip().str.upper()
                if "modalidad" in df.columns
                else pd.Series("", index=df.index)
            )
            mask_ent = mod_raw.str.startswith("ENT")
            mask_ret = mod_raw.str.startswith("RET")
            mask_aut = mod_raw.str.startswith("AUT")

            modalidad_tot["ENTREGADO"] = float(ton_series[mask_ent].sum())
            modalidad_tot["RETIRADO"] = float(ton_series[mask_ret].sum())
            modalidad_tot["AUTOFLETE"] = float(ton_series[mask_aut].sum())

            mix_entregado["granel"] = float(ton_series[mask_ent & (fam_series == "granel")].sum())
            mix_entregado["envasado"] = float(ton_series[mask_ent & (fam_series == "envasado")].sum())

        # ------------------------------------------------------------------
        # 4. ARRIBOS Y PENDIENTES "POR CARGAR" DESDE ZSDMX389 (self.datos_totales)
        # ------------------------------------------------------------------
        arribo_hoy = 0.0
        arribo_mas_1d = 0.0
        por_cargar_por_prod = {}

        for cam in self.datos_totales:
            if cam.get("estatus") not in ["ESPERA", "LLAMADO"]:
                continue
            ton_cam = float(cam.get("toneladas", 0.0))
            fch_p_str = str(cam.get("fch_planif", "")).strip()
            es_antiguo = False
            if fch_p_str:
                try:
                    dt_p = datetime.strptime(fch_p_str, "%d.%m.%Y %H:%M:%S")
                    if dt_p.date() < ahora.date():
                        es_antiguo = True
                except Exception:
                    pass
            if es_antiguo:
                arribo_mas_1d += ton_cam
            else:
                arribo_hoy += ton_cam

            mat_cam = str(cam.get("material", "")).strip().upper()
            por_cargar_por_prod[mat_cam] = por_cargar_por_prod.get(mat_cam, 0.0) + ton_cam

        total_por_cargar = arribo_hoy + arribo_mas_1d
        total_arribado = total_cargado + total_por_cargar

        # ------------------------------------------------------------------
        # 5. CONDICIONALES: SALIDA POR PRODUCTO (envasado Y granel / BIG BAG)
        # ------------------------------------------------------------------
        nom_corto_series = (
            df["material_nom_corto"].fillna("").astype(str).str.strip().str.upper()
            if not df.empty and "material_nom_corto" in df.columns
            else pd.Series(dtype=str)
        )

        def _armar_filas_tabla_producto(dic_objetivos: dict, filtro_fam_extra: str = None) -> list:
            filas = []
            tot_carg = 0.0
            tot_obj = 0.0
            tot_pend = 0.0
            productos_vistos = set()

            for nom_prod, obj_val in dic_objetivos.items():
                nom_u = nom_prod.strip().upper()
                productos_vistos.add(nom_u)
                carg = float(ton_series[nom_corto_series == nom_u].sum()) if not df.empty else 0.0
                pend = sum(
                    v for k, v in por_cargar_por_prod.items()
                    if nom_u == k or (nom_u in k.split(" / "))
                )
                tot_carg += carg
                tot_obj += float(obj_val)
                tot_pend += pend
                filas.append({
                    "producto": nom_prod,
                    "cargado": carg,
                    "obj": float(obj_val),
                    "por_cargar": pend,
                    "es_total": False,
                })

            # Incluir cualquier otro producto que haya tenido salida real en df_249 y no estuviera en la plantilla fija
            if not df.empty and filtro_fam_extra:
                if filtro_fam_extra == "ENVASADO_SIN_BIGBAG":
                    mask_extra = (fam_series == "envasado") & (~nom_corto_series.str.contains("BIG BAG"))
                else:
                    mask_extra = (fam_series == "granel") | (nom_corto_series.str.contains("BIG BAG"))

                for nom_real in sorted(nom_corto_series[mask_extra].unique()):
                    if not nom_real or nom_real in productos_vistos:
                        continue
                    carg_r = float(ton_series[nom_corto_series == nom_real].sum())
                    if carg_r <= 0:
                        continue
                    pend_r = sum(
                        v for k, v in por_cargar_por_prod.items()
                        if nom_real == k or (nom_real in k.split(" / "))
                    )
                    tot_carg += carg_r
                    tot_pend += pend_r
                    filas.append({
                        "producto": nom_real,
                        "cargado": carg_r,
                        "obj": 0.0,
                        "por_cargar": pend_r,
                        "es_total": False,
                    })

            filas.append({
                "producto": "Total",
                "cargado": tot_carg,
                "obj": tot_obj,
                "por_cargar": tot_pend,
                "es_total": True,
            })
            return filas

        filas_env = _armar_filas_tabla_producto(obj_prod_env, filtro_fam_extra="ENVASADO_SIN_BIGBAG")
        filas_gra = _armar_filas_tabla_producto(obj_prod_gra, filtro_fam_extra="GRANEL_Y_BIGBAG")

        # Obtener estampa de tiempo de última actualización de 249.parquet
        rutas_249 = obtener_rutas_transaccion("249")
        arch_249 = rutas_249["archivo_parquet"]
        if os.path.exists(arch_249):
            ult_act_str = datetime.fromtimestamp(os.path.getmtime(arch_249)).strftime("%d/%m/%Y %H:%M:%S")
        else:
            ult_act_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        return {
            "fecha_dt": fecha_dt,
            "ultima_actualizacion": ult_act_str,
            "semana_oferta": semana_oferta,
            "total_cargado": total_cargado,
            "oferta_planta": oferta_planta,
            "tendencia_global": tendencia_global,
            "turnos_operativos": turnos_op,
            "factor_tendencia": factor_tendencia,
            "arribo_mas_1d": arribo_mas_1d,
            "arribo_hoy": arribo_hoy,
            "total_arribado": total_arribado,
            "total_por_cargar": total_por_cargar,
            "modalidad": modalidad_tot,
            "mix_entregado": mix_entregado,
            "mix_planta": mix_planta,
            "por_centro": por_centro,
            "por_turno": por_turno,
            "filas_productos_envasado": filas_env,
            "filas_productos_granel": filas_gra,
        }


if __name__ == "__main__":
    app = QApplication(sys.argv)
    configurar_icono_app(app_id="kiosko.bascula.produccion.1.0")

    font = QFont("Arial", 12)
    app.setFont(font)
    
    # Usar el selector unificado
    from gui_selector_planta import obtener_configuracion_inicial
    session_config = obtener_configuracion_inicial()
    
    if session_config:
        ventana = VentanaBasculaMain(session_config)
        print(f"🏢 Kiosko iniciado en {ventana.session_data.planta_gui_nombre} {ventana.session_data.planta_gui_codigos}")
        ventana.showMaximized()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
