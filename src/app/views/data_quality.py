"""
Data Quality view - Monitoring dashboard for data quality metrics.

Muestra métricas de calidad de datos en tiempo real y permite ejecutar validaciones.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import plotly.express as px
import streamlit as st

from src.app.components import card_standard, render_empty_state
from src.app.config import COLORS
from src.app.data_quality_metrics import (
    calculate_completeness,
    calculate_consistency,
    calculate_timeliness,
    calculate_validity,
    detect_quality_issues,
    get_quality_history,
)


def render_quality_metrics() -> None:
    """Renderiza las métricas principales de calidad."""
    col1, col2, col3, col4 = st.columns(4)
    
    completeness = calculate_completeness()
    validity = calculate_validity()
    consistency = calculate_consistency()
    timeliness_days = calculate_timeliness()
    
    # Calcular deltas (comparar con objetivos)
    completeness_delta = completeness - 95.0
    validity_delta = validity - 98.0
    consistency_delta = consistency - 95.0
    
    with col1:
        st.metric(
            "Completeness",
            f"{completeness}%",
            delta=f"{completeness_delta:+.1f}%",
            delta_color="normal" if completeness >= 95 else "inverse",
            help="Porcentaje de campos no nulos en tablas principales",
        )
    
    with col2:
        st.metric(
            "Validity",
            f"{validity}%",
            delta=f"{validity_delta:+.1f}%",
            delta_color="normal" if validity >= 98 else "inverse",
            help="Datos dentro de rangos esperados (precios, población, etc.)",
        )
    
    with col3:
        st.metric(
            "Consistency",
            f"{consistency}%",
            delta=f"{consistency_delta:+.1f}%",
            delta_color="normal" if consistency >= 95 else "inverse",
            help="Coherencia entre fuentes (barrios presentes en todas las tablas)",
        )
    
    with col4:
        timeliness_status = "✅ Actualizado" if timeliness_days < 90 else "⚠️ Desactualizado"
        st.metric(
            "Timeliness",
            f"{timeliness_days} días",
            delta=timeliness_status,
            delta_color="inverse" if timeliness_days >= 90 else "normal",
            help="Antigüedad del dato más reciente",
        )


def render_quality_evolution() -> None:
    """Renderiza gráfico de evolución temporal de calidad."""
    st.subheader("📈 Evolución de Calidad de Datos")
    
    quality_history = get_quality_history()
    
    if quality_history.empty:
        render_empty_state(
            title="Sin historial",
            description="No hay datos históricos de calidad disponibles.",
            icon="📉"
        )
        return
    
    # Preparar datos para Plotly
    df_melted = quality_history.melt(
        id_vars='fecha',
        value_vars=['completeness', 'validity', 'consistency'],
        var_name='métrica',
        value_name='porcentaje'
    )
    
    # Traducir nombres de métricas
    df_melted['métrica'] = df_melted['métrica'].map({
        'completeness': 'Completeness',
        'validity': 'Validity',
        'consistency': 'Consistency'
    })
    
    fig = px.line(
        df_melted,
        x='fecha',
        y='porcentaje',
        color='métrica',
        title='Métricas de Calidad (Últimos 24 Meses)',
        labels={
            'fecha': 'Fecha',
            'porcentaje': 'Porcentaje (%)',
            'métrica': 'Métrica'
        },
        color_discrete_map={
            'Completeness': COLORS['accent_blue'],
            'Validity': COLORS['accent_green'],
            'Consistency': COLORS['accent_red']
        }
    )
    
    # Añadir línea de objetivo
    fig.add_hline(
        y=95,
        line_dash="dash",
        line_color=COLORS['text_secondary'],
        annotation_text="Target: 95%",
        annotation_position="right"
    )
    
    fig.update_layout(
        hovermode='x unified',
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_quality_issues() -> None:
    """Renderiza tabla de issues detectados."""
    st.subheader("⚠️ Issues Detectados")
    
    issues_df = detect_quality_issues()
    
    if issues_df.empty:
        render_empty_state(
            title="Todo en orden",
            description="No se detectaron issues de calidad en los datos.",
            icon="✅"
        )
        return
    
    # Configurar columna de severidad como selectbox
    st.dataframe(
        issues_df,
        use_container_width=True,
        column_config={
            "Severidad": st.column_config.SelectboxColumn(
                "Severidad",
                options=["Low", "Medium", "High"],
                required=True,
            ),
            "Barrio": st.column_config.TextColumn(
                "Barrio",
                width="medium",
            ),
            "Issue": st.column_config.TextColumn(
                "Issue",
                width="large",
            ),
            "Detectado": st.column_config.DateColumn(
                "Detectado",
                format="YYYY-MM-DD",
            ),
        },
        hide_index=True,
    )


def render_manual_validation() -> None:
    """Renderiza botón y resultados de validación manual."""
    st.subheader("🔄 Validación Manual")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("Ejecutar Validación", type="primary", use_container_width=True):
            st.session_state['run_validation'] = True
    
    if st.session_state.get('run_validation', False):
        script_path = Path("scripts/verify_integrity.py")
        
        if not script_path.exists():
            st.error(f"Script de validación no encontrado: {script_path}")
            return
        
        with st.spinner("Validando datos..."):
            try:
                result = subprocess.run(
                    ["python", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=Path.cwd()
                )
                
                if result.returncode == 0:
                    st.success("✅ Validación completada")
                    if result.stdout:
                        st.code(result.stdout, language="text")
                    else:
                        st.info("No se encontraron problemas en la validación.")
                else:
                    st.error("❌ Error ejecutando validación")
                    st.code(result.stderr, language="text")
                    
            except subprocess.TimeoutExpired:
                st.error("⏱️ La validación tardó demasiado (>30s). Revisa el script.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
        
        # Resetear flag después de mostrar resultados
        st.session_state['run_validation'] = False


def render(year: int, key_prefix: str = "data_quality") -> None:
    """
    Renderiza la vista completa de Data Quality.
    
    Args:
        year: Año seleccionado (no usado en esta vista pero requerido por convención).
        key_prefix: Prefijo para keys únicos de componentes Streamlit.
    """
    st.title("🔍 Data Quality Monitor")
    
    st.markdown(
        """
        <p style="color: #4A5568; font-size: 14px; margin-bottom: 20px;">
        Monitoreo en tiempo real de la calidad de datos. Las métricas se actualizan 
        automáticamente cada 5 minutos.
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    # Métricas principales
    with card_standard():
        render_quality_metrics()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Evolución temporal
    with card_standard():
        render_quality_evolution()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Issues detectados
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with card_standard():
            render_quality_issues()
    
    with col2:
        with card_standard():
            render_manual_validation()

