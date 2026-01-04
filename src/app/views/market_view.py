"""
Vista del Market Cockpit para análisis avanzado de mercado.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app.components import card_standard, render_empty_state
import src.app.data_loader as dl
from src.app.styles import render_responsive_kpi_grid


def render_kpi_cards(year: int, distritos: list[str]) -> None:
    """
    Renderiza tarjetas de KPI filtradas.
    """
    # Cargar datos filtrados (simulado con lógica simple por ahora, idealmente usaría data_loader filtrado)
    # Para KPIs rápidos, podemos reusar load_price_trends filtrado al año
    df_trends = dl.load_price_trends(distritos if distritos else None)
    
    if df_trends.empty:
        render_empty_state(
            title="Sin datos para KPIs",
            description="No se encontraron registros para los distritos seleccionados."
        )
        return

    df_year = df_trends[df_trends["anyo"] == year]
    
    if df_year.empty:
        # Fallback si no hay datos exactos del año, mostrar último disponible o 0
        avg_price = 0.0
        avg_rent = 0.0
        n_barrios = 0
    else:
        avg_price = df_year["precio_venta_m2"].mean()
        avg_rent = df_year["precio_alquiler_m2"].mean()
        n_barrios = df_year["barrio_nombre"].nunique()

    kpi_data = [
        {
            "title": "Precio Medio Venta",
            "value": f"€{avg_price:,.0f}/m²",
            "style": "cool",
            "delta": f"Año {year}",
        },
        {
            "title": "Alquiler Medio",
            "value": f"€{avg_rent:,.0f}/mes",
            "style": "warm",
            "delta": f"Año {year}",
        },
        {
            "title": "Barrios Analizados",
            "value": str(n_barrios),
            "style": "white",
            "delta": "Cobertura",
        },
    ]
    render_responsive_kpi_grid(kpi_data)


def render_correlation_scatter(year: int) -> None:
    """
    Renderiza gráfico de dispersión precio vs demografía.
    """
    df_demo = dl.load_demographics_by_barrio(year)
    # Necesitamos unir con precios. 
    # Nota: load_demographics_by_barrio ya tiene datos demográficos.
    # Vamos a obtener precios para ese año también.
    df_prices = dl.load_price_trends(None) # Cargar todos para filtrar en memoria o mejorar data_loader
    df_prices_year = df_prices[df_prices["anyo"] == year]
    
    # Merge
    if not df_prices_year.empty and not df_demo.empty:
        # Asumiendo coincidencia por nombre de barrio, idealmente ID pero load_price_trends devuelve nombres
        # Mejorar load_price_trends para devolver ID si fuera crítico, pero por ahora nombre sirve
        df_merged = pd.merge(
            df_prices_year, 
            df_demo, 
            on=["barrio_nombre", "distrito_nombre"], 
            how="inner"
        )
        
        if not df_merged.empty:
            with card_standard(title="🧩 Correlación Precio vs Demografía"):
                fig = px.scatter(
                    df_merged,
                    x="indice_envejecimiento", 
                    y="precio_venta_m2",
                    size="poblacion_total",
                    color="distrito_nombre",
                    hover_name="barrio_nombre",
                    title=f"Precio vs Envejecimiento ({year})",
                    labels={
                        "precio_venta_m2": "Precio Venta €/m²",
                        "indice_envejecimiento": "Índice Envejecimiento",
                        "poblacion_total": "Población"
                    }
                )
                st.plotly_chart(fig, width="stretch")
        else:
            render_empty_state(
                title="Correlación no disponible",
                description=f"No hay suficientes datos cruzados para el año {year}.",
                icon="📉"
            )
    else:
        render_empty_state(
            title="Datos insuficientes",
            description=f"Faltan datos de precios o demografía para el año {year}.",
            icon="📉"
        )


def render_supply_analysis(distritos: list[str] | None) -> None:
    """
    Renderiza análisis de oferta inmobiliaria (Idealista).
    """
    st.subheader("Oferta en Tiempo Real (Idealista)")
    
    df = dl.load_idealista_supply(distritos)
    
    if df.empty:
        render_empty_state(
            title="Sin datos de oferta",
            description="No se encontraron anuncios activos.",
            icon="📢"
        )
        return

    # Check for mock data (defensive: column might not exist in old databases)
    is_mock = False
    if "is_mock" in df.columns:
        is_mock = df["is_mock"].any() if not df.empty else False
    elif not df.empty:
        # Fallback: detectar mock por source column
        is_mock = (df["source"] == "mock_generator").any() if "source" in df.columns else False
    
    if is_mock:
        st.warning("⚠️ **Datos Simulados**: Mostrando datos generados sintéticamente (Mock) porque no hay credenciales de API activas.")

    # KPIs
    col1, col2, col3 = st.columns(3)
    
    total_anuncios = df["num_anuncios"].sum()
    avg_price_sale = df[df["operacion"] == "sale"]["precio_m2_medio"].mean()
    avg_price_rent = df[df["operacion"] == "rent"]["precio_m2_medio"].mean()
    
    with col1:
        st.metric("Total Anuncios Activos", f"{total_anuncios:,}")
    with col2:
        st.metric("Precio Medio Venta (Oferta)", f"€{avg_price_sale:,.0f}/m²" if pd.notna(avg_price_sale) else "N/A")
    with col3:
        st.metric("Precio Medio Alquiler (Oferta)", f"€{avg_price_rent:,.1f}/m²" if pd.notna(avg_price_rent) else "N/A")

    # Chart: Listings by District
    if not df.empty:
        with card_standard(title="📊 Distribución de Oferta por Distrito"):
            # Aggregate by district and operation
            df_agg = df.groupby(["distrito_nombre", "operacion"])["num_anuncios"].sum().reset_index()
            
            fig = px.bar(
                df_agg,
                x="distrito_nombre",
                y="num_anuncios",
                color="operacion",
                barmode="group",
                title="Anuncios Activos por Distrito",
                labels={"num_anuncios": "Cantidad de Anuncios", "distrito_nombre": "Distrito"},
                color_discrete_map={"sale": "#FF5A5F", "rent": "#00A699"} # Airbnb-ish colors
            )
            st.plotly_chart(fig, width="stretch")


def render_market_cockpit() -> None:
    """
    Renderiza la vista principal del Market Cockpit.
    """
    st.header("📊 Market Cockpit")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    years_data = dl.load_available_years()
    min_year = years_data["fact_precios"]["min"] or 2015
    max_year = years_data["fact_precios"]["max"] or 2022
    
    distritos_opts = dl.load_distritos()
    
    with col1:
        selected_year = st.selectbox("Año Análisis", range(max_year, min_year - 1, -1))
    with col2:
        selected_distritos = st.multiselect("Filtrar Distritos", distritos_opts)
    with col3:
        price_metric = st.selectbox(
            "Métrica Evolución", 
            ["precio_venta_m2", "precio_alquiler_m2"],
            format_func=lambda x: x.replace("_", " ").title()
        )
    
    st.markdown("---")
    
    # KPIs
    render_kpi_cards(selected_year, selected_distritos)
    
    # Gráfico Evolución
    st.subheader("📈 Tendencias de Mercado")
    df_trends = dl.load_price_trends(selected_distritos)
    
    if not df_trends.empty:
        # Filtrar por rango razonable si hay muchos datos, o mostrar todo
        fig_trends = px.line(
            df_trends, 
            x='anyo', 
            y=price_metric, 
            color='barrio_nombre',
            title=f"Evolución {price_metric.replace('_', ' ').title()}",
            markers=True
        )
        st.plotly_chart(fig_trends, width="stretch")
    else:
        render_empty_state(
            title="Sin tendencias",
            description="No hay datos históricos para la selección actual.",
            icon="📉"
        )
        
    # Scatter
    render_correlation_scatter(selected_year)

    # Real-time Supply (Idealista)
    st.markdown("---")
    render_supply_analysis(selected_distritos)
