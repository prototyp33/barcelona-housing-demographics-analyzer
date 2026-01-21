"""
Market Cockpit View - Dashboard principal según Wireframe 1.

Incluye:
- KPIs críticos (Precio vs Índice, Presión Turística, Crimen, Ruido)
- Mapa coroplético + Top 5 barrios vulnerables
- Métricas secundarias (Tendencia, Regulación, Asequibilidad)
- Acciones rápidas
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app.components import card_standard, render_empty_state
from src.app.data_loader import (
    load_critical_kpis,
    load_top_vulnerable_barrios,
    load_regulation_summary,
    load_affordability_summary,
    load_price_trends,
    load_available_years,
)
from src.app.utils import format_smart_currency, get_noise_level_color, PROFESSIONAL_COLORS
from src.app.styles import render_responsive_kpi_grid, KPIMetric

logger = logging.getLogger(__name__)


def _format_trend_icon(trend_value: Optional[float]) -> tuple[str, str]:
    """
    Formatea icono de tendencia basado en valor.
    
    Args:
        trend_value: Valor de cambio (positivo = aumento, negativo = disminución).
    
    Returns:
        Tupla con (icono, color).
    """
    if trend_value is None:
        return "→", "normal"
    elif trend_value > 2.0:
        return "↗↗", "normal"  # Crecimiento fuerte
    elif trend_value > 0:
        return "↗", "normal"  # Crecimiento
    elif trend_value < -2.0:
        return "↘↘", "inverse"  # Decrecimiento fuerte
    elif trend_value < 0:
        return "↘", "inverse"  # Decrecimiento
    else:
        return "→", "off"  # Estable


def render_critical_kpis(year: Optional[int] = None, barrio_id: Optional[int] = None) -> None:
    """
    Renderiza los 4 KPIs críticos del Market Cockpit alineados con el reporte profesional.
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

    kpis = load_critical_kpis(year, barrio_id=barrio_id)
    
    # Precio vs Índice
    precio_data = kpis.get("precio_vs_indice", {})
    precio_value = precio_data.get("value")
    precio_trend = precio_data.get("trend")
    precio_icon, precio_color = _format_trend_icon(precio_trend)
    
    # Presión Turística
    turismo_data = kpis.get("presion_turistica", {})
    turismo_value = turismo_data.get("value")
    turismo_trend = turismo_data.get("trend")
    turismo_icon, turismo_color = _format_trend_icon(turismo_trend)
    
    # Criminalidad
    crimen_data = kpis.get("criminalidad", {})
    crimen_value = crimen_data.get("value")
    crimen_trend = crimen_data.get("trend")
    crimen_icon, crimen_color = _format_trend_icon(-crimen_trend if crimen_trend else None)
    
    # Ruido
    ruido_data = kpis.get("ruido", {})
    ruido_value = ruido_data.get("value")
    ruido_trend = ruido_data.get("trend")
    ruido_icon, ruido_color = _format_trend_icon(-ruido_trend if ruido_trend else None)
    
    kpi_data = [
        KPIMetric(
            title="📊 Precio vs Índice",
            value=f"{precio_value:+.1f}%" if precio_value is not None else "Sin datos",
            style="white",
            delta=f"{precio_icon} {precio_trend:+.1f}%" if precio_trend is not None else "Sin datos",
            delta_color=precio_color,
        ),
        KPIMetric(
            title="🏖️ Presión Turística",
            value=f"{turismo_value:.1f}%" if turismo_value is not None else "Sin datos",
            style="warm",
            delta=f"{turismo_icon} {turismo_trend:+.1f}%" if turismo_trend is not None else "Sin datos",
            delta_color=turismo_color,
        ),
        KPIMetric(
            title="🚨 Crimen",
            value=f"{crimen_value:.1f}" if crimen_value is not None else "Sin datos",
            style="cool",
            delta=f"{crimen_icon} {abs(crimen_trend):.1f}" if crimen_trend is not None else "Sin datos",
            delta_color=crimen_color,
        ),
        KPIMetric(
            title="🔊 Ruido Ambiente",
            value=f"{ruido_value:.1f} dB" if ruido_value is not None else "Sin datos",
            style="white",
            delta=f"{ruido_icon} {abs(ruido_trend):.1f} dB" if ruido_trend is not None else "Sin datos",
            delta_color=get_noise_level_color(ruido_value) if ruido_value is not None else "normal",
        ),
    ]
    
    render_responsive_kpi_grid(kpi_data)


def render_top_vulnerable_barrios_list(year: Optional[int] = None, top_n: int = 5) -> None:
    """
    Renderiza lista de Top 5 barrios más vulnerables con mejor UX.
    
    Mejoras:
    - Título único y claro
    - Tooltip explicando qué significa "vulnerabilidad"
    - Barras de progreso visuales para comparación rápida
    - Badges con mejor contraste
    
    Args:
        year: Año a mostrar. Si es None, usa el más reciente.
        top_n: Número de barrios a mostrar.
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

    df = load_top_vulnerable_barrios(year, top_n)
    
    if df.empty:
        render_empty_state(
            title="Sin datos de vulnerabilidad",
            description="No se encontraron datos de riesgo de gentrificación.",
            icon="📊"
        )
        return
    
    # Título único con tooltip explicativo
    st.markdown(
        f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px; margin-top: -8px;">'
        f'<h3 style="font-size: 14px; font-weight: 700; color: #1A1A1A; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">'
        f'Top {top_n}: Barrios con Mayor Índice de Riesgo</h3>'
        f'<span title="El índice de riesgo de gentrificación combina factores como: variación de precios, presión turística, cambios demográficos y transformación urbana. Un valor alto indica mayor vulnerabilidad a procesos de gentrificación." '
        f'style="cursor: help; font-size: 14px; color: #2F80ED;">ℹ️</span></div>',
        unsafe_allow_html=True
    )
    
    for idx, row in df.iterrows():
        score = row.get("score_riesgo_gentrificacion", 0)
        categoria = row.get("categoria_riesgo", "Desconocido")
        barrio_nombre = row.get("barrio_nombre", f"Barrio {row.get('barrio_id', 'N/A')}")
        
        # Determinar color según categoría con mejor contraste
        if score >= 70:
            color_emoji = "🔴"
            color_bg = "rgba(220, 38, 38, 0.12)"
            color_border = "#DC2626"
            badge_bg = "#DC2626"
            badge_color = "#FFFFFF"
        elif score >= 40:
            color_emoji = "🟠"
            color_bg = "rgba(245, 158, 11, 0.12)"
            color_border = "#F59E0B"
            badge_bg = "#F59E0B"
            badge_color = "#FFFFFF"
        else:
            color_emoji = "🟡"
            color_bg = "rgba(234, 179, 8, 0.12)"
            color_border = "#EAB308"
            badge_bg = "#EAB308"
            badge_color = "#1A1A1A"
        
        # Calcular porcentaje para la barra de progreso
        progress_pct = min(score, 100)  # Asegurar que no exceda 100
        
        st.markdown(
            f'<div style="padding: 14px 16px; margin-bottom: 10px; background: {color_bg}; '
            f'border-radius: 12px; border-left: 4px solid {color_border}; '
            f'box-shadow: 0 2px 4px rgba(0,0,0,0.06); transition: all 0.2s ease; cursor: pointer;" '
            f'onmouseover="this.style.transform=\'translateY(-2px)\'; this.style.boxShadow=\'0 4px 8px rgba(0,0,0,0.12)\';" '
            f'onmouseout="this.style.transform=\'translateY(0)\'; this.style.boxShadow=\'0 2px 4px rgba(0,0,0,0.06)\';">'
            f'<div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 10px;">'
            f'<span style="font-size: 18px; flex-shrink: 0;">{color_emoji}</span>'
            f'<div style="flex: 1; min-width: 0;">'
            f'<div style="font-size: 14px; font-weight: 700; color: #1A1A1A; margin-bottom: 6px; line-height: 1.3;">'
            f'{idx + 1}. {barrio_nombre}</div>'
            f'<div style="width: 100%; height: 6px; background: rgba(0,0,0,0.08); border-radius: 3px; overflow: hidden; margin-bottom: 8px;">'
            f'<div style="width: {progress_pct}%; height: 100%; background: linear-gradient(90deg, {color_border} 0%, {color_border}CC 100%); border-radius: 3px; transition: width 0.3s ease;"></div></div></div></div>'
            f'<div style="display: flex; align-items: center; justify-content: space-between; margin-top: 8px;">'
            f'<div style="display: inline-block; padding: 4px 10px; border-radius: 8px; background: {badge_bg}; border: 1px solid {color_border};">'
            f'<span style="font-size: 10px; font-weight: 700; color: {badge_color}; text-transform: uppercase; letter-spacing: 0.5px;">{categoria}</span></div>'
            f'<div style="text-align: right;">'
            f'<div style="font-size: 20px; font-weight: 800; color: #1A1A1A; line-height: 1;">{score:.1f}</div>'
            f'<div style="font-size: 10px; color: #6B7280; margin-top: 2px;">/100</div></div></div></div>',
            unsafe_allow_html=True,
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Ver ranking completo →", key="btn_ver_ranking_completo", width='stretch'):
        st.session_state["nav_to_recommendations"] = True


def render_secondary_metrics(year: Optional[int] = None) -> None:
    """
    Renderiza métricas secundarias (Tendencia, Regulación, Asequibilidad).
    Mejorado con mejor UX, diseño visual y alineación perfecta.
    
    Sistema de grid consistente:
    - Altura mínima uniforme para todas las cards (420px)
    - Padding consistente (24px)
    - Espaciado entre columnas (24px)
    
    Args:
        year: Año a mostrar. Si es None, usa el más reciente.
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

    # CSS para asegurar altura uniforme en las cards
    st.markdown(
        '''<style>
        .secondary-metric-card {
            min-height: 420px;
            display: flex;
            flex-direction: column;
        }
        .secondary-metric-card > div {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        </style>''',
        unsafe_allow_html=True
    )

    # Grid de 3 columnas con espaciado consistente (24px = 3 × 8px)
    col1, col2, col3 = st.columns(3, gap="large")
    
    with col1:
        # Tendencia de precios (v1.2 MVP - Dinámico)
        years_info = load_available_years()
        max_y = years_info.get("fact_precios", {}).get("max") or 2023
        min_y = years_info.get("fact_precios", {}).get("min") or 2015
        
        st.markdown('<div class="secondary-metric-card">', unsafe_allow_html=True)
        with card_standard(title="📈 Tendencia", subtitle=f"Evolución Precios {min_y}-{max_y}", padding="24px"):
            try:
                df_trends = load_price_trends()
                if not df_trends.empty:
                    # Agregar por año
                    df_agg = df_trends.groupby("anyo")["precio_venta_m2"].mean().reset_index()
                    df_agg = df_agg[df_agg["anyo"] >= min_y]
                    
                    if not df_agg.empty:
                        # Calcular variación para contexto
                        precio_inicial = df_agg["precio_venta_m2"].iloc[0]
                        precio_final = df_agg["precio_venta_m2"].iloc[-1]
                        variacion_pct = ((precio_final - precio_inicial) / precio_inicial) * 100
                        
                        fig = px.line(
                            df_agg,
                            x="anyo",
                            y="precio_venta_m2",
                            markers=True,
                            title="",
                            labels={"anyo": "Año", "precio_venta_m2": "Precio (€/m²)"},
                            color_discrete_sequence=["#2F80ED"],
                        )
                        fig.update_traces(
                            line=dict(width=3),
                            marker=dict(size=6),
                        )
                        fig.update_layout(
                            height=240,
                            showlegend=False,
                            margin=dict(l=45, r=25, t=15, b=45),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            xaxis=dict(
                                showgrid=True, 
                                gridcolor="rgba(0,0,0,0.05)",
                                linecolor="rgba(0,0,0,0.1)",
                            ),
                            yaxis=dict(
                                showgrid=True, 
                                gridcolor="rgba(0,0,0,0.05)",
                                linecolor="rgba(0,0,0,0.1)",
                            ),
                        )
                        st.plotly_chart(fig, width='stretch', key="trend_chart", config={"displayModeBar": False})
                        
                        # Mostrar variación como contexto
                        color_var = "#27AE60" if variacion_pct > 0 else "#EB5757"
                        st.markdown(
                            f'<div style="text-align: center; margin-top: 8px;">'
                            f'<span style="font-size: 11px; color: #8E92BC;">Variación total: </span>'
                            f'<span style="font-size: 12px; font-weight: 600; color: {color_var};">'
                            f'{"+" if variacion_pct > 0 else ""}{variacion_pct:.1f}%</span></div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.caption("Sin datos de tendencia")
                else:
                    st.caption("Sin datos disponibles")
            except Exception as e:
                logger.error("Error cargando tendencia: %s", e)
                st.caption("Error al cargar datos")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Regulación
        st.markdown('<div class="secondary-metric-card">', unsafe_allow_html=True)
        with card_standard(title="🏘️ Regulación", subtitle="Zonas Tensionadas y VUT", padding="24px"):
            try:
                reg_data = load_regulation_summary(year)
                zonas = reg_data.get("zonas_tensionadas", 0)
                licencias = reg_data.get("total_licencias_vut", 0)
                
                # Calcular porcentaje de zonas tensionadas
                pct_zonas = (zonas / 73) * 100 if zonas > 0 else 0
                
                st.markdown(
                    f'<div style="padding: 4px 0;">'
                    f'<div style="margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid rgba(0,0,0,0.08);">'
                    f'<div style="font-size: 11px; color: #8E92BC; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Zonas Tensión</div>'
                    f'<div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 10px;">'
                    f'<div style="font-size: 32px; font-weight: 700; color: #1A1A1A; line-height: 1.2;">{zonas}</div>'
                    f'<div style="font-size: 15px; color: #8E92BC; font-weight: 500;">/73 barrios</div></div>'
                    f'<div style="margin-top: 12px; height: 6px; background: rgba(0,0,0,0.06); border-radius: 3px; overflow: hidden;">'
                    f'<div style="height: 100%; width: {pct_zonas}%; background: linear-gradient(90deg, #F59E0B 0%, #DC2626 100%); border-radius: 3px; transition: width 0.3s ease;"></div></div></div>'
                    f'<div style="padding-top: 4px;">'
                    f'<div style="font-size: 11px; color: #8E92BC; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Lic. VUT</div>'
                    f'<div style="font-size: 32px; font-weight: 700; color: #1A1A1A; line-height: 1.2;">{licencias:,}</div></div></div>',
                    unsafe_allow_html=True,
                )
            except Exception as e:
                logger.error("Error cargando regulación: %s", e)
                st.caption("Error al cargar datos")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        # Asequibilidad
        st.markdown('<div class="secondary-metric-card">', unsafe_allow_html=True)
        with card_standard(title="💰 Asequibilidad", subtitle="Ratio Precio/Renta", padding="24px"):
            try:
                aff_data = load_affordability_summary(year)
                ratio_anios = aff_data.get("ratio_precio_renta_anios")
                
                if ratio_anios is not None:
                    # Determinar nivel de asequibilidad y color del ratio
                    if ratio_anios <= 10:
                        nivel = "Asequible"
                        color_nivel = "#27AE60"
                        bg_nivel = "rgba(39, 174, 96, 0.1)"
                        ratio_color = "#27AE60"
                    elif ratio_anios <= 15:
                        nivel = "Moderado"
                        color_nivel = "#F59E0B"
                        bg_nivel = "rgba(245, 158, 11, 0.1)"
                        ratio_color = "#F59E0B"
                    else:
                        nivel = "Difícil"
                        color_nivel = "#EB5757"
                        bg_nivel = "rgba(235, 87, 87, 0.1)"
                        ratio_color = "#EB5757"
                    
                    st.markdown(
                        f'<div style="padding: 4px 0;">'
                        f'<div style="font-size: 11px; color: #8E92BC; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Ratio Precio/Renta</div>'
                        f'<div style="font-size: 40px; font-weight: 700; color: {ratio_color}; line-height: 1.2; margin-bottom: 14px;">{ratio_anios:.1f}<span style="font-size: 22px; font-weight: 500; color: #8E92BC; margin-left: 4px;">años</span></div>'
                        f'<div style="display: inline-block; padding: 6px 14px; border-radius: 14px; background: {bg_nivel}; margin-bottom: 12px; border: 1px solid {color_nivel}30;">'
                        f'<span style="font-size: 11px; font-weight: 600; color: {color_nivel}; text-transform: uppercase; letter-spacing: 0.5px;">{nivel}</span></div>'
                        f'<div style="font-size: 11px; color: #8E92BC; margin-top: 16px; padding-top: 12px; border-top: 1px solid rgba(0,0,0,0.06);">Para vivienda tipo (70m²)</div></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("Sin datos disponibles")
            except Exception as e:
                logger.error("Error cargando asequibilidad: %s", e)
                st.caption("Error al cargar datos")
        st.markdown('</div>', unsafe_allow_html=True)


def render_quick_actions() -> None:
    """
    Renderiza acciones rápidas del Market Cockpit con mejor UX y diseño moderno.
    
    Grid 2x2 con espaciado consistente y alineación perfecta.
    """
    # CSS para grid de acciones con altura uniforme
    st.markdown(
        '''<style>
        .quick-action-card {
            min-height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        </style>''',
        unsafe_allow_html=True
    )
    
    # Grid 2x2 con mejor espaciado (24px = 3 × 8px)
    col1, col2 = st.columns(2, gap="large")
    
    # Contar alertas activas
    num_alertas = 12  # Placeholder
    try:
        from src.alerts.detector import detect_all_changes
        # Se puede calcular realmente aquí
    except Exception:
        pass
    
    # Definir acciones con iconos, títulos y descripciones
    actions_left = [
        {
            "icon": "📊",
            "title": "Analizar Barrio",
            "description": "Análisis detallado por barrio",
            "key": "btn_analizar_barrio",
            "color": "#2F80ED",
        },
        {
            "icon": "💡",
            "title": "Recomendaciones",
            "description": "Barrios recomendados",
            "key": "btn_recomendaciones",
            "color": "#27AE60",
        },
    ]
    
    actions_right = [
        {
            "icon": "🔔",
            "title": "Ver Alertas",
            "description": f"{num_alertas} alertas activas",
            "key": "btn_alertas",
            "color": "#EB5757",
            "badge": str(num_alertas),
        },
        {
            "icon": "📄",
            "title": "Reporte Ejecutivo",
            "description": "Generar reporte PDF",
            "key": "btn_reporte",
            "color": "#8E92BC",
        },
    ]
    
    with col1:
        for action in actions_left:
            _render_action_card(action)
    
    with col2:
        for action in actions_right:
            _render_action_card(action)
    
    # CSS global para ocultar todos los botones secundarios vacíos y elementos code que muestran HTML
    st.markdown(
        '''<style>
        /* Ocultar todos los contenedores de botones secundarios que están dentro de columnas después de "Acciones Rápidas" */
        div[data-testid="column"] div.stButton:has(button[data-testid*="Button-secondary"]),
        div[data-testid="column"] div[data-testid="stButton"]:has(button[data-testid*="Button-secondary"]),
        div.stButton:has(button[data-testid*="Button-secondary"][aria-label=""]),
        div[data-testid="stButton"]:has(button[data-testid*="Button-secondary"][aria-label=""]) {
            display:none!important;
            visibility:hidden!important;
            height:0!important;
            min-height:0!important;
            max-height:0!important;
            padding:0!important;
            margin:0!important;
            overflow:hidden!important;
            width:0!important;
            line-height:0!important;
            opacity:0!important;
            position:absolute!important;
            top:-9999px!important;
            left:-9999px!important;
            z-index:-1!important;
        }
        /* Ocultar elementos code que están dentro de columnas y contienen texto de cierre de divs */
        div[data-testid="column"] code,
        div[data-testid="column"] div:has(> code) {
            display:none!important;
            visibility:hidden!important;
            height:0!important;
            min-height:0!important;
            max-height:0!important;
            padding:0!important;
            margin:0!important;
            overflow:hidden!important;
            width:0!important;
            line-height:0!important;
            opacity:0!important;
            position:absolute!important;
            top:-9999px!important;
            left:-9999px!important;
        }
        </style>
        <script>
        (function() {
            // Ocultar elementos code que contienen HTML de cierre de divs o scripts
            const codes = document.querySelectorAll('code');
            codes.forEach(code => {
                const text = code.textContent || '';
                if (text.includes('</div>') || text.includes('<script>') || text.includes('function()')) {
                    code.style.display = 'none';
                    code.style.visibility = 'hidden';
                    code.style.height = '0';
                    code.style.width = '0';
                    code.style.padding = '0';
                    code.style.margin = '0';
                    code.style.opacity = '0';
                    code.style.position = 'absolute';
                    code.style.top = '-9999px';
                    code.style.left = '-9999px';
                    // También ocultar el contenedor padre si solo contiene el code
                    const parent = code.parentElement;
                    if (parent && parent.children.length === 1 && parent.children[0] === code) {
                        parent.style.display = 'none';
                        parent.style.visibility = 'hidden';
                        parent.style.height = '0';
                        parent.style.width = '0';
                        parent.style.padding = '0';
                        parent.style.margin = '0';
                        parent.style.opacity = '0';
                    }
                }
            });
        })();
        </script>''',
        unsafe_allow_html=True
    )


def _render_action_card(action: dict) -> None:
    """
    Renderiza una tarjeta de acción con diseño mejorado y mejor UX.
    
    Args:
        action: Diccionario con icon, title, description, key, color, y opcional badge
    """
    color = action.get("color", "#2F80ED")
    color_rgb = "47, 128, 237" if color == "#2F80ED" else "39, 174, 96" if color == "#27AE60" else "235, 87, 87" if color == "#EB5757" else "142, 146, 188"
    
    # Construir badge HTML si existe
    badge_value = action.get("badge", "")
    badge_html = ""
    if badge_value:
        badge_html = f'<span style="position:absolute;top:-8px;right:-8px;background:linear-gradient(135deg,#EB5757 0%,#DC2626 100%);color:white;font-size:11px;font-weight:700;padding:4px 8px;border-radius:12px;box-shadow:0 2px 8px rgba(235,87,87,0.4);z-index:10;min-width:24px;text-align:center;white-space:nowrap;">{badge_value}</span>'
    
    # Determinar acción a ejecutar
    action_map = {
        "btn_analizar_barrio": "nav_to_insights",
        "btn_alertas": "nav_to_alerts",
        "btn_recomendaciones": "nav_to_recommendations",
        "btn_reporte": "show_report_info"
    }
    session_key = action_map.get(action["key"], "")
    
    # Crear contenedor wrapper para la tarjeta
    container_id = f"action-wrapper-{action['key']}"
    
    # Renderizar wrapper con tarjeta HTML (en una sola línea para evitar que Streamlit lo interprete como código)
    card_html_single_line = f'<div id="{container_id}" style="position:relative;margin-bottom:16px;"><div class="action-card-{action["key"]}" style="width:100%;padding:22px 20px;background:#FFFFFF;border:2px solid #E5E7EB;border-radius:16px;cursor:pointer;transition:all 0.3s cubic-bezier(0.4,0,0.2,1);box-shadow:0 2px 8px rgba(0,0,0,0.06);position:relative;overflow:visible;z-index:1;"><div style="display:flex;align-items:flex-start;gap:16px;"><div style="width:52px;height:52px;background:linear-gradient(135deg,{color}15 0%,{color}25 100%);border-radius:14px;display:flex;align-items:center;justify-content:center;flex-shrink:0;border:1px solid {color}30;"><span style="font-size:26px;">{action["icon"]}</span></div><div style="flex:1;min-width:0;"><div style="font-size:16px;font-weight:600;color:#1A1A1A;margin-bottom:6px;line-height:1.3;">{action["title"]}</div><div style="font-size:13px;color:#8E92BC;line-height:1.4;">{action["description"]}</div></div><div style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><span class="action-arrow" style="font-size:20px;color:{color};transition:transform 0.2s ease;">→</span></div></div>{badge_html}</div></div>'
    st.markdown(card_html_single_line, unsafe_allow_html=True)
    
    # Botón invisible que será completamente ocultado
    button_clicked = st.button("", key=action["key"], width='content', type="secondary")
    
    # CSS agresivo para ocultar el botón y todos sus contenedores padre
    # Ocultar directamente todos los botones secundarios vacíos en la sección de acciones rápidas
    st.markdown(
        f'''<style>
        .action-card-{action["key"]}:hover{{
            border-color:{color}!important;
            box-shadow:0 8px 24px rgba({color_rgb},0.25)!important;
            transform:translateY(-4px)!important;
        }}
        .action-card-{action["key"]}:hover .action-arrow{{
            transform:translateX(4px)!important;
        }}
        /* Ocultar todos los contenedores de botones de Streamlit que contienen botones vacíos */
        div.stButton:has(button[data-testid*="Button-secondary"]:empty),
        div[data-testid="stButton"]:has(button[data-testid*="Button-secondary"]:empty),
        div.stButton:has(button[data-testid*="Button-secondary"]:not(:has(*))),
        div[data-testid="stButton"]:has(button[data-testid*="Button-secondary"]:not(:has(*))){{
            display:none!important;
            visibility:hidden!important;
            height:0!important;
            min-height:0!important;
            max-height:0!important;
            padding:0!important;
            margin:0!important;
            overflow:hidden!important;
            width:0!important;
            line-height:0!important;
            opacity:0!important;
            position:absolute!important;
            top:-9999px!important;
            left:-9999px!important;
            z-index:-1!important;
        }}
        /* Ocultar botones secundarios vacíos directamente */
        button[data-testid*="Button-secondary"]:empty,
        button[data-testid*="Button-secondary"]:not(:has(*)){{
            display:none!important;
            visibility:hidden!important;
            height:0!important;
            width:0!important;
            padding:0!important;
            margin:0!important;
            opacity:0!important;
            position:fixed!important;
            top:-9999px!important;
            left:-9999px!important;
        }}
        </style>''',
        unsafe_allow_html=True
    )


    if button_clicked:
        if action["key"] == "btn_analizar_barrio":
            st.session_state["nav_to_insights"] = True
        elif action["key"] == "btn_alertas":
            st.session_state["nav_to_alerts"] = True
        elif action["key"] == "btn_recomendaciones":
            st.session_state["nav_to_recommendations"] = True
        elif action["key"] == "btn_reporte":
            st.info("Ejecuta: `python scripts/generate_reports.py --type executive_summary`")


def render_hero_section() -> None:
    """
    Renderiza una sección Hero optimizada: altura reducida, mejor contraste y texto blanco bold.
    Opción minimalista que no empuja el contenido hacia abajo.
    """
    st.markdown(
        f"""
        <div style="position: relative; border-radius: 16px; overflow: hidden; margin-bottom: 20px; height: 100px;">
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
                        background: linear-gradient(135deg, rgba(29, 53, 87, 0.9) 0%, rgba(47, 128, 237, 0.5) 100%); 
                        z-index: 1;"></div>
            <img src="https://images.unsplash.com/photo-1583997051651-8255c4236318?auto=format&fit=crop&q=80&w=2000" 
                 style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; z-index: 0; opacity: 0.4;">
            <div style="position: absolute; top: 50%; left: 40px; transform: translateY(-50%); z-index: 2;">
                <h1 style="color: #FFFFFF !important; font-size: 32px !important; margin: 0; font-weight: 800; text-shadow: 0 2px 8px rgba(0,0,0,0.5); letter-spacing: -0.5px;">Market Cockpit</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render(year: Optional[int] = None, distrito_filter: Optional[str] = None, barrio_id: Optional[int] = None) -> None:
    """
    Renderiza el Market Cockpit completo con estructura de wireframe mejorada.
    
    Sistema de grid basado en 8px para mayor cohesión y alineación:
    - Espaciado consistente entre secciones (32px)
    - Alturas uniformes para cards del mismo nivel
    - Alineación vertical perfecta
    
    Args:
        year: Año seleccionado. Si es None, usa el más reciente.
        distrito_filter: Filtro opcional por distrito.
        barrio_id: ID del barrio seleccionado (viene del sidebar).
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

    # CSS global para sistema de grid consistente (8px base system)
    st.markdown(
        '''<style>
        /* ============================================
           SISTEMA DE GRID CONSISTENTE - 8px BASE
           ============================================ */
        
        /* Espaciado entre secciones principales (32px = 4 × 8px) */
        .market-cockpit-section {
            margin-bottom: 32px;
        }
        .market-cockpit-section:last-child {
            margin-bottom: 0;
        }
        
        /* Headings uniformes - mismo estilo y espaciado */
        h2.market-cockpit-heading {
            margin-top: 0;
            margin-bottom: 24px; /* 24px = 3 × 8px */
            font-size: 20px;
            font-weight: 700;
            color: #1A1A1A;
            letter-spacing: -0.3px;
            line-height: 1.3;
            font-family: 'Inter', sans-serif;
        }
        
        /* Cards con altura mínima consistente para alineación vertical */
        .market-cockpit-card {
            min-height: 400px;
            display: flex;
            flex-direction: column;
        }
        
        /* Asegurar que todas las cards de métricas secundarias tengan la misma altura */
        .secondary-metric-card {
            min-height: 420px;
            display: flex;
            flex-direction: column;
        }
        .secondary-metric-card > div {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        /* Grid para KPIs - espaciado consistente */
        .bh-kpi-grid {
            gap: 24px !important; /* 24px = 3 × 8px */
            margin-bottom: 0 !important;
        }
        
        /* Asegurar que las columnas de Streamlit tengan gap consistente */
        div[data-testid="column"] {
            gap: 24px;
        }
        
        /* Cards estándar con padding uniforme */
        .card {
            padding: 24px !important; /* 24px = 3 × 8px */
        }
        
        /* Alineación vertical de contenido en cards */
        .card > * {
            flex: 1;
        }
        </style>''',
        unsafe_allow_html=True
    )

    render_hero_section()
    
    # Los filtros ahora están en el sidebar, no se muestran aquí
    # Esto libera espacio para los KPIs y gráficos

    # === SECCIÓN 1: KPIs CRÍTICOS ===
    st.markdown('<div class="market-cockpit-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="market-cockpit-heading">KPIs Críticos</h2>', unsafe_allow_html=True)
    render_critical_kpis(year=year, barrio_id=barrio_id)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # === SECCIÓN 2: ANÁLISIS ESPACIAL (Mapa + Top 5) ===
    st.markdown('<div class="market-cockpit-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="market-cockpit-heading">Análisis Espacial</h2>', unsafe_allow_html=True)
    
    # Grid 2 columnas con proporción 2.5:1 para mejor balance visual
    col_map, col_top5 = st.columns([2.5, 1], gap="large")
    
    with col_map:
        with card_standard(title="🗺️ Mapa de Barcelona", subtitle="Distribución por barrios", padding="24px"):
            from src.app.views import map_analysis
            map_analysis.render_snapshot(year=year, key="cockpit_map")
    
    with col_top5:
        # Contenedor con card para mantener consistencia visual y altura mínima
        with card_standard(title="", padding="24px"):
            st.markdown('<div class="market-cockpit-card">', unsafe_allow_html=True)
            render_top_vulnerable_barrios_list(year=year, top_n=5)
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # === SECCIÓN 3: MÉTRICAS SECUNDARIAS ===
    st.markdown('<div class="market-cockpit-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="market-cockpit-heading">Métricas Secundarias</h2>', unsafe_allow_html=True)
    render_secondary_metrics(year=year)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # === SECCIÓN 4: ACCIONES RÁPIDAS ===
    st.markdown('<div class="market-cockpit-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="market-cockpit-heading">Acciones Rápidas</h2>', unsafe_allow_html=True)
    render_quick_actions()
    st.markdown('</div>', unsafe_allow_html=True)

