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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="BCN Housing Analyzer",
    page_icon="🏠",
    layout="wide"
)

# Constants
DB_PATH = Path("data/processed/database.db")

@st.cache_data
def load_map_data():
    """Load neighborhood data with geometries from database."""
    if not DB_PATH.exists():
        st.error(f"Database not found at {DB_PATH}")
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT 
                barrio_id,
                barrio_nombre,
                distrito_nombre,
                geometry_json
            FROM dim_barrios
            WHERE geometry_json IS NOT NULL
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Parse geometry_json string to dict
        if not df.empty:
            df['geometry'] = df['geometry_json'].apply(lambda x: json.loads(x) if x else None)
            # Drop the string column to save memory
            df = df.drop(columns=['geometry_json'])
            
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        logger.error(f"Error loading map data: {e}")
        return pd.DataFrame()

def main():
    st.title("🏠 Barcelona Housing & Demographics Analyzer")
    
    # Sidebar
    st.sidebar.header("Navigation")
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🗺️ Map Visualization", "📈 Analysis"])
    
    with tab1:
        st.header("Project Overview")
        st.markdown("""
        Welcome to the Barcelona Housing Demographics Analyzer.
        
        This dashboard integrates data from:
        - **Open Data BCN**: Demographics and housing data
        - **Portal de Dades**: Extended housing indicators
        - **Idealista**: Real estate market offers
        
        Use the tabs above to explore the data.
        """)
        
    with tab2:
        st.header("Neighborhood Map")
        
        df_map = load_map_data()
        
        if df_map.empty:
            st.warning("No geometry data available. Please ensure the ETL pipeline has populated 'geometry_json' in 'dim_barrios'.")
        else:
            # Metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Neighborhoods", len(df_map))
            with col2:
                st.metric("Districts", df_map['distrito_nombre'].nunique())
            
            # Map controls
            st.subheader("Interactive Map")
            
            # Prepare data for PyDeck
            # We create a FeatureCollection-like structure or just pass the DF with a geometry column
            # PyDeck handles pandas DataFrame with a geometry column if configured correctly,
            # but usually it's safer to pass records for GeoJsonLayer if the geometry is complex.
            
            # Let's define the layer
            geojson_layer = pdk.Layer(
                "GeoJsonLayer",
                data=df_map,
                opacity=0.8,
                stroked=True,
                filled=True,
                extruded=False,
                wireframe=True,
                get_fill_color=[200, 30, 0, 160],
                get_line_color=[255, 255, 255],
                get_line_width=20,
                pickable=True,
                auto_highlight=True,
                get_geometry="geometry" # Column name containing the geometry dict
            )
            
            # Initial view state (centered on Barcelona)
            view_state = pdk.ViewState(
                latitude=41.3851,
                longitude=2.1734,
                zoom=11,
                pitch=0,
            )
            
            # Render map
            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=view_state,
                layers=[geojson_layer],
                tooltip={
                    "html": "<b>{barrio_nombre}</b><br/>Distrito: {distrito_nombre}",
                    "style": {"backgroundColor": "steelblue", "color": "white"}
                }
            ))
            
            st.dataframe(df_map.drop(columns=['geometry']), use_container_width=True)

    with tab3:
        st.header("Analysis")
        st.info("Coming soon: Correlation analysis and price trends.")

if __name__ == "__main__":
    main()
