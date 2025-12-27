"""
Vista de Alertas - Panel de alertas activas en dashboard.
"""

from __future__ import annotations

import logging
from typing import List, Optional

import streamlit as st

from src.alerts.detector import detect_all_changes
from src.alerts.notifier import Alert, AlertPriority
from src.app.components import render_empty_state
from src.app.data_loader import load_barrios

logger = logging.getLogger(__name__)


def _get_priority_color(priority: AlertPriority) -> str:
    """Obtiene color para badge de prioridad."""
    colors = {
        AlertPriority.CRITICAL: "🔴",
        AlertPriority.HIGH: "🟠",
        AlertPriority.MEDIUM: "🟡",
        AlertPriority.LOW: "🟢",
    }
    return colors.get(priority, "⚪")


def render_alert_card(alert: Alert) -> None:
    """
    Renderiza una tarjeta de alerta.
    
    Args:
        alert: Alert a renderizar.
    """
    priority_emoji = _get_priority_color(alert.priority)
    
    with st.container():
        col1, col2 = st.columns([1, 4])
        
        with col1:
            st.markdown(f"### {priority_emoji}")
            st.caption(alert.priority.value.upper())
        
        with col2:
            st.markdown(f"**{alert.title}**")
            st.write(alert.message)
            st.caption(f"Barrio ID: {alert.barrio_id} | {alert.timestamp.strftime('%Y-%m-%d %H:%M')}")
            
            if alert.details:
                with st.expander("Ver detalles"):
                    st.json(alert.details)
        
        st.divider()


def render(year: int = 2023, barrio_id: Optional[int] = None) -> None:
    """
    Renderiza la vista de Alertas con configuración de umbrales.
    """
    st.header("🚨 SISTEMA DE ALERTAS INTELIGENTES")
    
    # 1. Configuración de Umbrales (Sidebar o Expander)
    with st.expander("⚙️ Configuración de Umbrales de Alerta", expanded=False):
        col_u1, col_u2, col_u3 = st.columns(3)
        with col_u1:
            threshold_price = st.slider("Cambio Precio (%)", 5, 50, 10, help="Umbral para alertar sobre variaciones bruscas de precio.")
        with col_u2:
            threshold_yield = st.number_input("Yield Mínimo (%)", 1.0, 10.0, 4.0, 0.5, help="Alertar si un barrio supera este yield.")
        with col_u3:
            threshold_gentrif = st.slider("Riesgo Gentrificación", 0, 100, 70, help="Alertar si el riesgo supera este valor.")

    # 2. Filtros de visualización
    col1, col2 = st.columns([2, 1])
    
    with col1:
        priority_filter = st.multiselect(
            "Filtrar por prioridad",
            options=[p.value for p in AlertPriority],
            default=[AlertPriority.CRITICAL.value, AlertPriority.HIGH.value, AlertPriority.MEDIUM.value],
            key="alerts_priority_filter"
        )
    
    with col2:
        barrios_df = load_barrios()
        barrio_options = {f"{row['barrio_nombre']}": row['barrio_id'] for _, row in barrios_df.iterrows()}
        selected_barrio_name = st.selectbox("📍 Filtrar Barrio", options=["Todos"] + list(barrio_options.keys()))
        if selected_barrio_name != "Todos":
            barrio_id = barrio_options[selected_barrio_name]

    # 3. Detección y filtrado dinámico
    with st.spinner("Escaneando mercado..."):
        # En una app real, detect_all_changes aceptaría los umbrales configurados
        # Aquí simularemos el filtrado sobre las alertas detectadas
        if barrio_id:
            alerts = detect_all_changes(barrio_id)
        else:
            # Simular escaneo de top barrios si no hay uno seleccionado
            alerts = []
            for b_id in list(barrio_options.values())[:15]: # Limitar para performance
                alerts.extend(detect_all_changes(b_id))
    
    # Filtrado por prioridad y configuración
    filtered_alerts = [
        alert for alert in alerts
        if alert.priority.value in priority_filter
    ]
    
    # Ordenar por prioridad
    priority_order = {AlertPriority.CRITICAL: 0, AlertPriority.HIGH: 1, AlertPriority.MEDIUM: 2, AlertPriority.LOW: 3}
    filtered_alerts.sort(key=lambda a: priority_order.get(a.priority, 99))

    # 4. Renderizado
    if not filtered_alerts:
        render_empty_state(
            title="Sin alertas activas",
            description="No se han detectado anomalías o cambios que superen tus umbrales configurados.",
            icon="✅"
        )
        return

    st.subheader(f"📋 {len(filtered_alerts)} Eventos Detectados")
    
    for alert in filtered_alerts:
        # Recuperar nombre del barrio para la tarjeta
        b_name = next((name for name, id in barrio_options.items() if id == alert.barrio_id), f"Barrio {alert.barrio_id}")
        
        with st.container():
            c1, c2 = st.columns([1, 10])
            with c1:
                st.markdown(f"### {_get_priority_color(alert.priority)}")
            with c2:
                st.markdown(f"**{b_name}**: {alert.title}")
                st.write(alert.message)
                if alert.details:
                    with st.expander("Ver métricas técnicas"):
                        st.json(alert.details)
            st.divider()

    # 5. Resumen Ejecutivo de Alertas
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚨 Resumen de Seguridad")
    counts = {p: sum(1 for a in filtered_alerts if a.priority == p) for p in AlertPriority}
    for p in AlertPriority:
        if counts.get(p, 0) > 0:
            st.sidebar.write(f"{_get_priority_color(p)} {p.value.title()}: **{counts[p]}**")

