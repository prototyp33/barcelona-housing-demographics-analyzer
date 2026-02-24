"""
Price Predictor View - Interactive panel for housing price forecasting.
"""

from __future__ import annotations

import logging
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import os
import json

from src.models.price_predictor import PricePredictor, MODELS_DIR
from src.app.components import card_standard, render_section_header, create_metric_grid, render_kpi_card, create_two_column_layout, render_spacer
from src.app.utils import PROFESSIONAL_COLORS
from src.app.design_system import COLORS
from src.app.data_loader import get_connection, get_geojson

logger = logging.getLogger(__name__)

def load_all_sim_data(year: int = 2023) -> pd.DataFrame:
    """Carga los datos de todos los barrios para el mapa predictivo."""
    query = """
    SELECT * FROM vw_model_prices_demografia 
    WHERE anio = ?
    """
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=(year,))
    return df

def load_barrio_factors(barrio_id: int) -> pd.DataFrame:
    """Carga los factores reales más recientes de un barrio para inicializar el simulador."""
    query = """
    SELECT * FROM vw_model_prices_demografia 
    WHERE barrio_id = ? 
    ORDER BY anio DESC LIMIT 1
    """
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=(barrio_id,))
    return df

def render(year: int = 2023) -> None:
    """
    Renderiza la vista del Predictor de Precios con visualizaciones avanzadas.
    """
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(86, 204, 242, 0.1) 0%, rgba(47, 128, 237, 0.1) 100%); 
                    padding: 24px; border-radius: 16px; margin-bottom: 24px; border: 1px solid rgba(47, 128, 237, 0.2);">
            <h2 style="margin-top: 0; color: #1A1A1A; font-size: 24px;">🔮 Predictor Inteligente de Precios v2.1</h2>
            <p style="color: #4A5568; margin-bottom: 0;">
                Analiza el impacto de factores socioeconómicos y presión turística en el valor del m². 
                <b>Baseline Model:</b> R² 0.51 • Incluye impacto acumulado de Airbnb.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    predictor = PricePredictor()
    
    # Check if models exist
    models_exist = os.path.exists(os.path.join(MODELS_DIR, "ridge_price_model.joblib"))

    if not models_exist:
        st.warning("⚠️ Los modelos predictivos no han sido entrenados todavía.")
        if st.button("Entrenar Modelos Ahora"):
            with st.spinner("Entrenando modelos (Linear, Ridge, Lasso)..."):
                try:
                    predictor.train()
                    predictor.save_models()
                    st.success("✅ Modelos entrenados y guardados con éxito!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al entrenar: {e}")
        return

    # Sidebar for Model Selection and Metadata
    with st.sidebar:
        st.markdown("---")
        st.subheader("Configuración del Modelo")
        model_type = st.radio("Algoritmo", ["ridge", "lasso", "linear"], horizontal=True, key="model_choice")
        
        try:
            insights = predictor.get_model_insights(model_name=model_type)
            metrics = insights["metrics"]
            st.caption(f"**R² Score:** {metrics.get('r2', 0):.3f}")
            st.caption(f"**Error Medio (RMSE):** ±{metrics.get('rmse', 0):.0f} €/m²")
        except:
            insights = {}
            metrics = {}

    # Multi-tab strategy
    tab_pred, tab_insights, tab_map, tab_sensitivity = st.tabs([
        "🎯 Simulador", 
        "📊 Drivers de Mercado", 
        "🗺️ Impacto Espacial",
        "📈 Sensibilidad"
    ])

    from src.app.data_loader import load_barrios
    barrios_df = load_barrios()
    
    # Pre-loading data for map and analysis early
    map_data = load_all_sim_data(2023) if not models_exist else load_all_sim_data(2023)
    
    with tab_pred:
        col_inputs, col_results = create_two_column_layout(left_ratio=1, gap="large")

        with col_inputs:
            with card_standard(title="⚙️ Configuración Escenario", subtitle="Carga datos reales o ajusta manual"):
                selected_barrio_name = st.selectbox(
                    "Inicializar con barrio:", 
                    options=["Valores por defecto"] + barrios_df["barrio_nombre"].tolist()
                )
                
                defaults = {
                    "renta_media": 25000, "poblacion_total": 20000, "porc_extranjeros": 15.0,
                    "porc_jovenes": 12.0, "porc_mayores": 18.0, "tasa_paro": 8.0, 
                    "tam_medio_hogar": 2.4, "num_airbnb": 150
                }
                
                if selected_barrio_name != "Valores por defecto":
                    barrio_id = barrios_df[barrios_df["barrio_nombre"] == selected_barrio_name]["barrio_id"].iloc[0]
                    barrio_data = load_barrio_factors(int(barrio_id))
                    if not barrio_data.empty:
                        for col in defaults.keys():
                            if col in barrio_data.columns and not pd.isna(barrio_data[col].iloc[0]):
                                defaults[col] = barrio_data[col].iloc[0]

                renta = st.slider("Renta Media (€)", 10000, 50000, int(defaults["renta_media"]), step=500)
                num_airbnb = st.slider("Listings Airbnb", 0, 2000, int(defaults["num_airbnb"]), step=10, help="Representa el número medio de listings anuales por barrio. Fuente: Ripoll/InsideAirbnb.")
                porc_extranjeros = st.slider("% Extranjeros", 0.0, 60.0, float(defaults["porc_extranjeros"]), 0.1)
                tasa_paro = st.slider("Tasa de Paro (%)", 0.0, 25.0, float(defaults["tasa_paro"]), 0.1)
                
                with st.expander("Variables Demográficas"):
                    poblacion = st.number_input("Población Total", 1000, 100000, int(defaults["poblacion_total"]), step=1000)
                    porc_jovenes = st.slider("% Jóvenes", 0.0, 30.0, float(defaults["porc_jovenes"]), 0.1)
                    porc_mayores = st.slider("% Mayores", 0.0, 40.0, float(defaults["porc_mayores"]), 0.1)
                    tam_hogar = st.slider("Hogar (pers.)", 1.0, 5.0, float(defaults["tam_medio_hogar"]), 0.1)

                # Guardrails logic
                if num_airbnb > 500:
                    st.warning("⚠️ **Alta Densidad:** Estás simulando un nivel de presión turística muy superior a la media de la ciudad. Los resultados pueden ser menos precisos.")
                if renta > 45000:
                    st.info("💡 **Renta Alta:** Este nivel de renta se sitúa en el percentil superior (ej. neighborhoods como Pedralbes).")

        with col_results:
            # Simulation results
            input_df = pd.DataFrame([{
                "renta_media": renta, "poblacion_total": poblacion, "porc_jovenes": porc_jovenes,
                "porc_mayores": porc_mayores, "tasa_paro": tasa_paro, "porc_extranjeros": porc_extranjeros,
                "tam_medio_hogar": tam_hogar, "num_airbnb": num_airbnb
            }])

            try:
                prediction = predictor.predict(input_df, model_name=model_type)[0]
                
                st.markdown(f"""
                <div style="text-align: center; padding: 40px 20px; background: white; border-radius: 20px; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); margin-bottom: 20px;">
                    <p style="color: #64748b; font-size: 14px; margin-bottom:-5px; font-weight:600;">PRECIO ESTIMADO</p>
                    <h1 style="color: {PROFESSIONAL_COLORS['primary']}; font-size: 64px; font-weight: 800; margin: 0;">{prediction:,.0f}€<small style="font-size:24px; color:#64748b;">/m²</small></h1>
                </div>
                """, unsafe_allow_html=True)
                
                if insights:
                    real_impacts = insights.get("real_world_impacts", {})
                    airbnb_impact = num_airbnb * real_impacts.get("num_airbnb", 0)
                    renta_impact = renta * real_impacts.get("renta_media", 0)
                    
                    st.markdown("### 📊 Atribución del Valor")
                    cols_impact = st.columns(2)
                    with cols_impact[0]:
                        st.metric("Driver Renta", f"+{renta_impact:,.0f} €", delta=None)
                    with cols_impact[1]:
                        st.metric("Driver Turismo", f"+{airbnb_impact:,.0f} €", delta=None, delta_color="inverse")
                    
                    # Progress bars for impact relative to base?
                    st.caption("Nota: La suma de contribuciones individuales más el intercepto resulta en el precio predicho.")

            except Exception as e:
                st.error(f"Error en simulación: {e}")

    with tab_insights:
        render_section_header("Drivers del Mercado Inmobiliario", icon="🧬", subtitle="Peso relativo de cada factor en el precio final")
        
        if insights:
            norm_coeffs = insights.get("normalized_coefficients", {})
            if norm_coeffs:
                df_coeffs = pd.Series(norm_coeffs).reset_index()
                df_coeffs.columns = ["Factor", "Importancia"]
                df_coeffs = df_coeffs.sort_values("Importancia", ascending=True)
                
                name_map = {
                    "renta_media": "Renta Familiar", "num_airbnb": "Presión Airbnb",
                    "porc_extranjeros": "% Inmigración", "tasa_paro": "Desempleo",
                    "tam_medio_hogar": "Tamaño Hogar", "poblacion_total": "Población",
                    "porc_jovenes": "% Jóvenes", "porc_mayores": "% Mayores"
                }
                df_coeffs["Factor"] = df_coeffs["Factor"].map(lambda x: name_map.get(x, x))
                
                fig = px.bar(
                    df_coeffs, y="Factor", x="Importancia", orientation="h",
                    color="Importancia", color_continuous_scale="RdBu", color_continuous_midpoint=0,
                    text_auto='.2f'
                )
                fig.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='white')
                st.plotly_chart(fig, width="stretch")
                
                st.info("💡 **Gini Inmobiliario:** En Barcelona, la **Renta Familiar** y la **Presión de Airbnb** son los dos motores más potentes de revalorización, seguidos de cerca por la estructura demográfica (% extranjeros y tamaño del hogar).")

    with tab_map:
        render_section_header("Análisis Espacial del Modelo", icon="🌍", subtitle="Predicciones vs Realidad por Barrio (2023)")
        
        map_view_type = st.radio("Capa del Mapa:", ["Predicción del Modelo", "Presión Airbnb", "Error (Residuales)"], horizontal=True)
        
        geojson = get_geojson()
        if not map_data.empty and geojson:
            # Predict for all barrios to show residuals
            all_features = map_data[predictor.feature_cols].fillna(0)
            map_data["prediction"] = predictor.predict(all_features, model_name=model_type)
            map_data["residual"] = map_data["target_precio_m2"] - map_data["prediction"]
            
            if map_view_type == "Predicción del Modelo":
                val_col = "prediction"
                colors = "Blues"
                label = "Precio Predicho (€/m²)"
            elif map_view_type == "Presión Airbnb":
                val_col = "num_airbnb"
                colors = "YlOrRd"
                label = "Densidad Airbnb"
            else:
                val_col = "residual"
                colors = "RdBu"
                label = "Diferencia Real-Predicho"

            fig_map = px.choropleth_mapbox(
                map_data, geojson=geojson, locations="barrio_nombre", featureidkey="properties.NOM",
                color=val_col, mapbox_style="carto-positron", zoom=11, 
                center={"lat": 41.3851, "lon": 2.1734}, opacity=0.7,
                color_continuous_scale=colors, labels={val_col: label},
                hover_data=["barrio_nombre", "target_precio_m2", "prediction", "renta_media"]
            )
            fig_map.update_layout(height=600, margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig_map, width="stretch")
            
            if map_view_type == "Error (Residuales)":
                st.markdown("""
                <div style="background-color: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0;">
                    <p style="margin-bottom: 5px;"><b>🎨 Guía de Color (Residuales):</b></p>
                    <ul style="margin-top: 0; font-size: 13px;">
                        <li><span style="color: #ef4444; font-weight: bold;">🔴 Rojo (Positivo):</span> Barrio <b>más caro</b> de lo esperado. Sugiere plusvalía por "premium de barrio", seguridad o calidad arquitectónica no capturada por los datos.</li>
                        <li><span style="color: #3b82f6; font-weight: bold;">🔵 Azul (Negativo):</span> Barrio <b>más barato</b> de lo esperado. Puede indicar potencial de revalorización (oportunidad) o factores de degradación no modelados.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            elif map_view_type == "Predicción del Modelo":
                st.caption("🔍 Este mapa visualiza lo que el modelo considera el 'justiprecio' basado puramente en estadística socioeconómica.")

    with tab_sensitivity:
        render_section_header("Curvas de Sensibilidad", icon="📈", subtitle="Efecto marginal de variar un factor")
        
        feat_choice = st.selectbox(
            "Selecciona factor:", options=["renta_media", "num_airbnb", "porc_extranjeros", "tasa_paro"],
            format_func=lambda x: name_map.get(x, x)
        )
        
        if 'input_df' in locals():
            sens_df = predictor.get_marginal_effects(model_type, input_df, feat_choice, range_pct=0.7)
            fig_sens = px.line(sens_df, x="value", y="prediction", title=f"Variación de Precio vs {name_map.get(feat_choice, feat_choice)}")
            fig_sens.add_scatter(x=[input_df[feat_choice].iloc[0]], y=[prediction], mode='markers', marker=dict(size=12, color='red'), name="Actual")
            fig_sens.update_layout(height=450, plot_bgcolor='white', xaxis_title=name_map.get(feat_choice, feat_choice), yaxis_title="Precio (€/m²)")
            st.plotly_chart(fig_sens, width="stretch")

    # Interpretation Help Footer
    st.markdown("---")
    with st.expander("📖 Guía Rápida: ¿Cómo interpretar estos datos?"):
        st.markdown("""
        ### 1. El Valor Predicho
        Es el **precio teórico** basado en estadística. Si el precio real es muy diferente, el barrio tiene atributos (positivos o negativos) que el modelo no está viendo.
        
        ### 2. Mapa de Residuales
        * **🔴 Rojo:** Barrio "caro" para su estadística. Tiene un **plus de prestigio** o calidad no medible.
        * **🔵 Azul:** Barrio "barato" para su estadística. Puede ser una **oportunidad de inversión** o reflejar problemas sociales no capturados.
        
        ### 3. Driver de Turismo
        Representa cuánto del precio actual se explica por la densidad de Airbnb. En barrios céntricos, esto puede suponer más de 1.500€/m² de "sobreprecio turístico".
        
        *Para más detalles, consulta el archivo `docs/PREDICTOR_GUIDE.md`.*
        
        ---
        **⚠️ Limitaciones Técnicas:**
        * **Linealidad:** El modelo asume que los cambios son proporcionales (ej. cada Airbnb extra suma lo mismo). En la realidad, el efecto puede ser exponencial o saturarse.
        * **Datos Faltantes:** Algunos barrios tienen lagunas históricas de renta, lo que puede reducir la precisión en zonas muy específicas.
        * **Causalidad:** El modelo muestra correlación. No "garantiza" que subir la renta suba el precio, sino que históricamente ambos han ido de la mano.
        """)
