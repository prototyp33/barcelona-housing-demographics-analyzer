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


def render(year: int = 2022, barrio_id: Optional[int] = None) -> None:
    """
    Renderiza la vista completa de Alertas.
    
    Args:
        year: Año seleccionado.
        barrio_id: ID opcional de barrio para filtrar alertas.
    """
    st.header("🚨 Alertas y Notificaciones")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        priority_filter = st.multiselect(
            "Filtrar por prioridad",
            options=[p.value for p in AlertPriority],
            default=[AlertPriority.CRITICAL.value, AlertPriority.HIGH.value],
            key="alerts_priority_filter"
        )
    
    with col2:
        show_resolved = st.checkbox("Mostrar alertas resueltas", value=False, key="alerts_show_resolved")
    
    # Selector de barrio si no se proporciona
    if barrio_id is None:
        barrios_df = load_barrios()
        barrio_options = {f"{row['barrio_nombre']} ({row['barrio_id']})": row['barrio_id'] 
                         for _, row in barrios_df.iterrows()}
        
        selected_barrio_name = st.selectbox(
            "Seleccionar Barrio (opcional)",
            options=["Todos"] + list(barrio_options.keys()),
            key="alerts_barrio_selector"
        )
        
        if selected_barrio_name != "Todos":
            barrio_id = barrio_options[selected_barrio_name]
    
    # Detectar alertas
    if barrio_id:
        st.info(f"Detectando alertas para barrio ID: {barrio_id}...")
        alerts = detect_all_changes(barrio_id)
    else:
        st.info("Selecciona un barrio para ver sus alertas.")
        alerts = []
    
    # Filtrar alertas
    filtered_alerts = [
        alert for alert in alerts
        if alert.priority.value in priority_filter
        and (show_resolved or not alert.resolved)
    ]
    
    # Ordenar por prioridad
    priority_order = {AlertPriority.CRITICAL: 0, AlertPriority.HIGH: 1, 
                     AlertPriority.MEDIUM: 2, AlertPriority.LOW: 3}
    filtered_alerts.sort(key=lambda a: priority_order.get(a.priority, 99))
    
    # Mostrar alertas
    if not filtered_alerts:
        render_empty_state(
            title="No hay alertas activas",
            description="No se detectaron cambios significativos para los criterios seleccionados.",
            icon="✅"
        )
        return
    
    st.subheader(f"📋 {len(filtered_alerts)} Alertas Detectadas")
    
    for alert in filtered_alerts:
        render_alert_card(alert)
    
    # Resumen
    st.markdown("---")
    st.subheader("📊 Resumen")
    
    col1, col2, col3, col4 = st.columns(4)
    
    counts = {p: sum(1 for a in filtered_alerts if a.priority == p) for p in AlertPriority}
    
    with col1:
        st.metric("Críticas", counts.get(AlertPriority.CRITICAL, 0))
    with col2:
        st.metric("Altas", counts.get(AlertPriority.HIGH, 0))
    with col3:
        st.metric("Medias", counts.get(AlertPriority.MEDIUM, 0))
    with col4:
        st.metric("Bajas", counts.get(AlertPriority.LOW, 0))

