"""
Main Application Module
Streamlit dashboard for Barcelona Housing Demographics Analyzer
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
import pydeck as pdk
from pathlib import Path
from typing import List, Optional
import logging

from src.analysis import (
    get_available_years,
    get_neighborhood_data,
    get_yield_analysis,
    get_kpis,
    get_geojson,
    get_accessibility_metrics,
    get_safety_and_tourism
)
from src.app.config import PAGE_CONFIG, DB_PATH

# Page config
st.set_page_config(**PAGE_CONFIG)

@st.cache_data(ttl=3600)
def load_map_data(year: Optional[int] = None, distrito: Optional[str] = None) -> pd.DataFrame:
    """
    Loads and prepares data for the map view.
    
    Args:
        year: Year to load. If None, uses the latest available year.
        distrito: Optional district filter.
        
    Returns:
        DataFrame with yield metrics and geometry.
    """
    if year is None:
        try:
            years_info = get_available_years()
            year = years_info.get("fact_precios", {}).get("max") or 2023
        except Exception:
            year = 2023

    if not DB_PATH.exists():
        st.error(f"Database not found at {DB_PATH}")
        return pd.DataFrame()

    try:
        # Check connection (required for legacy test monkeypatching)
        conn = sqlite3.connect(DB_PATH)
        conn.close()
        
        df_yield = get_yield_analysis(year, distrito=distrito)
        if df_yield.empty:
            return pd.DataFrame()
            
        # Transform geometry_json to geometry object
        df_yield['geometry'] = df_yield['geometry_json'].apply(
            lambda x: json.loads(x) if isinstance(x, str) else x
        )
        # Drop geometry_json as expected by tests
        if 'geometry_json' in df_yield.columns:
            df_yield = df_yield.drop(columns=['geometry_json'])
            
        return df_yield
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def main():
    # Inject some styles for a premium look
    st.markdown("""
        <style>
        .main { background-color: #F4F5F7; }
        .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🏠 Barcelona Housing & Demographics Analyzer")
    
    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    
    # Get available years (Real Prices as reference)
    years_info = get_available_years()
    years = years_info.get("fact_precios", [])
    if not years: years = [2023]
    
    selected_year = st.sidebar.selectbox("Year", sorted(years, reverse=True), index=0)
    
    # Get districts
    df_barrios = get_neighborhood_data()
    distritos = sorted(df_barrios['distrito_nombre'].unique())
    selected_distrito = st.sidebar.selectbox("District (Optional)", ["All"] + distritos)
    distrito_filter = None if selected_distrito == "All" else selected_distrito
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🗺️ Yield Map", "📈 Yield Analysis", "🏫 Accessibility & Safety"])
    
    # Fetch KPIs
    kpis = get_kpis()
    
    with tab1:
        st.header("City-wide Performance")
        
        # KPI Row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Neighborhoods", kpis['total_barrios'])
        c2.metric("Avg Rent (Real)", f"{kpis['alquiler_medio_real']:,.0f}€")
        c3.metric("Real Yield", f"{kpis['yield_real_pct']:.2f}%")
        c4.metric("Market Yield (Offer)", f"{kpis['yield_market_pct']:.2f}%")
        
        st.markdown("---")
        st.subheader("Project Context")
        st.markdown("""
        This dashboard integrates dual housing metrics:
        - **Real Market**: Based on Incasòl contract data (Actual transactions).
        - **Offer Market**: Based on Idealista offering data (Asking prices).
        
        The **Yield Analysis** module helps investors find the 'Sweet Spot' between actual rent performance and market entry prices.
        """)
        
    with tab2:
        st.header(f"Performance Map - {selected_year}")
        
        # Load yield analysis for the selected filters
        df_yield = load_map_data(selected_year, distrito=distrito_filter)
        
        if df_yield.empty:
            st.warning("No data available for the selected filters.")
        else:
            # Map metric selector
            map_metric = st.segmented_control(
                "Map Layer Metric",
                ["yield_real", "yield_market", "yield_gap"],
                default="yield_real"
            )
            
            # Map coloring logic (Red-Green scale for yield)
            # Normalization
            min_val = df_yield[map_metric].min()
            max_val = df_yield[map_metric].max()
            
            def get_color(val):
                if pd.isna(val): return [200, 200, 200, 150]
                # Simple linear scale: 0% -> Red, 10% -> Green
                # For yield_gap, we might want different colors, but local yield is priority.
                norm = (val - min_val) / (max_val - min_val) if max_val > min_val else 0.5
                return [int(255 * (1 - norm)), int(255 * norm), 0, 180]
            
            df_yield['fill_color'] = df_yield[map_metric].apply(get_color)
            
            geojson_layer = pdk.Layer(
                "GeoJsonLayer",
                data=df_yield,
                opacity=0.8,
                stroked=True,
                filled=True,
                get_fill_color="fill_color",
                get_line_color=[255, 255, 255],
                get_line_width=2,
                pickable=True,
                auto_highlight=True
            )
            
            view_state = pdk.ViewState(
                latitude=41.3851, longitude=2.1734, zoom=11, pitch=0
            )
            
            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=view_state,
                layers=[geojson_layer],
                tooltip={
                    "html": "<b>{barrio_nombre}</b><br/>Distrito: {distrito_nombre}<br/>Value: {" + map_metric + ":.2f}%",
                    "style": {"backgroundColor": "steelblue", "color": "white"}
                }
            ))
            
            st.subheader("Data Highlights")
            st.dataframe(df_yield.drop(columns=['geometry_json']), width="stretch", hide_index=True)

    with tab3:
        st.header("Dual Comparative Yield")
        
        df_yield = get_yield_analysis(selected_year, distrito=distrito_filter)
        
        if not df_yield.empty:
            # Bar chart comparing real vs market yield
            import plotly.express as px
            
            # Melt for comparison
            df_melt = df_yield.melt(
                id_vars=['barrio_nombre'], 
                value_vars=['yield_real', 'yield_market'],
                var_name='Yield Type', value_name='Yield %'
            )
            
            fig = px.bar(
                df_melt, 
                x="barrio_nombre", 
                y="Yield %", 
                color="Yield Type",
                barmode="group",
                title=f"Yield Comparison: Real vs Market ({selected_year})"
            )
            fig.update_layout(xaxis_title="Neighborhood", yaxis_title="Annual Yield %")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Please select a year with data.")
    with tab4:
        st.header(f"Social Infrastructure & Safety ({selected_year})")
        
        # Load accessibility and safety metrics
        df_acc = get_accessibility_metrics(selected_year, distrito=distrito_filter)
        df_safe = get_safety_and_tourism(selected_year, distrito=distrito_filter)
        
        if df_acc.empty and df_safe.empty:
            st.info("No accessibility or safety data for the selected year.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Education & Public Housing")
                if not df_acc.empty:
                    # Education metrics overview
                    total_edu = df_acc['total_centros_educativos'].sum()
                    st.metric("Total Educational Centers", f"{total_edu:,.0f}")
                    
                    import plotly.express as px
                    fig_edu = px.bar(
                        df_acc.sort_values("total_centros_educativos", ascending=False).head(15),
                        x="total_centros_educativos",
                        y="barrio_nombre",
                        orientation='h',
                        title="Top Neighborhoods by Educational Centers",
                        color="total_centros_educativos",
                        color_continuous_scale="Blues"
                    )
                    st.plotly_chart(fig_edu, width="stretch")
                else:
                    st.warning("No education/housing data available.")
                    
            with col2:
                st.subheader("Safety & Tourism Pressure")
                if not df_safe.empty:
                    # Safety and tourism overview
                    avg_crime = df_safe['tasa_criminalidad_1000hab'].mean()
                    st.metric("Avg Crime Rate (per 1k hab)", f"{avg_crime:.2f}")
                    
                    fig_safe = px.scatter(
                        df_safe,
                        x="num_listings_airbnb",
                        y="tasa_criminalidad_1000hab",
                        size="num_listings_airbnb",
                        hover_name="barrio_nombre",
                        title="Airbnb Listings vs. Crime Rate",
                        labels={"num_listings_airbnb": "Airbnb listings", "tasa_criminalidad_1000hab": "Crime Rate"}
                    )
                    st.plotly_chart(fig_safe, width="stretch")
                else:
                    st.warning("No safety/tourism data available.")

            st.subheader("Detailed Neighborhood Metrics")
            # Merge for table
            full_metrics = df_acc.merge(
                df_safe[['barrio_id', 'tasa_criminalidad_1000hab', 'num_listings_airbnb', 'pct_entire_home']], 
                on='barrio_id', 
                how='outer'
            )
            st.dataframe(
                full_metrics.drop(columns=['geometry_json']), 
                width="stretch", 
                hide_index=True
            )

if __name__ == "__main__":
    main()
