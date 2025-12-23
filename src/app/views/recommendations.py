"""
Vista de Recomendaciones - Motor de recomendaciones en dashboard.
"""

from __future__ import annotations

import logging

import streamlit as st

from src.recommendations.scenarios import get_recommendations, SCENARIO_TYPES
from src.app.components import render_empty_state

logger = logging.getLogger(__name__)


def render(year: int = 2022) -> None:
    """
    Renderiza la vista completa de Recomendaciones.
    
    Args:
        year: Año seleccionado.
    """
    st.header("💡 Recomendaciones de Barrios")
    
    # Selector de escenario
    scenario = st.selectbox(
        "Seleccionar Escenario",
        options=SCENARIO_TYPES,
        format_func=lambda x: x.replace("_", " ").title(),
        key="recommendations_scenario"
    )
    
    # Número de recomendaciones
    top_n = st.slider("Número de recomendaciones", min_value=5, max_value=20, value=10, key="recommendations_top_n")
    
    # Botón para generar recomendaciones
    if st.button("Generar Recomendaciones", key="recommendations_generate"):
        with st.spinner("Calculando recomendaciones..."):
            try:
                recommendations = get_recommendations(scenario, top_n=top_n)
                
                if not recommendations:
                    render_empty_state(
                        title="No hay recomendaciones",
                        description="No se encontraron barrios que cumplan los criterios del escenario seleccionado.",
                        icon="📊"
                    )
                    return
                
                st.success(f"✅ {len(recommendations)} recomendaciones encontradas")
                
                # Mostrar recomendaciones
                for idx, rec in enumerate(recommendations, 1):
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"### {idx}. {rec.get('barrio_nombre', f'Barrio {rec["barrio_id"]}')}")
                            st.write(rec.get("explanation", ""))
                            st.caption(rec.get("reason", ""))
                        
                        with col2:
                            st.metric("Score Total", f"{rec['total_score']:.1f}")
                        
                        with col3:
                            scores = rec.get("scores", {})
                            st.write("**Scores por criterio:**")
                            st.write(f"- Affordability: {scores.get('affordability', 0):.1f}")
                            st.write(f"- Calidad de vida: {scores.get('calidad_vida', 0):.1f}")
                            st.write(f"- Oportunidad: {scores.get('oportunidad', 0):.1f}")
                            st.write(f"- Estabilidad: {scores.get('estabilidad', 0):.1f}")
                        
                        st.divider()
            
            except Exception as e:
                st.error(f"Error generando recomendaciones: {e}")
                logger.error("Error en recomendaciones: %s", e)

