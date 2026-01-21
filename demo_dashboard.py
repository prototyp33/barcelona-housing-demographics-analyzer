import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Configuración de la página
st.set_page_config(
    page_title="Barcelona Housing Intelligence",
    page_icon="🏠",
    layout="wide"
)

# Estilo personalizado
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .risk-critical { color: #dc3545; font-weight: bold; }
    .risk-high { color: #fd7e14; font-weight: bold; }
    .risk-medium { color: #ffc107; font-weight: bold; }
    .risk-low { color: #198754; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Cargar datos
@st.cache_data
def load_data():
    file_path = Path("data/exports/looker_studio/master_table_barcelona_housing.csv")
    if not file_path.exists():
        st.error(f"Archivo no encontrado: {file_path}")
        return pd.DataFrame()
    df = pd.read_csv(file_path)
    # Asegurar tipos de datos
    df['anio'] = df['anio'].astype(int)
    return df

df = load_data()

if df.empty:
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("🛠️ Filtros")
available_years = sorted(df['anio'].unique(), reverse=True)
selected_year = st.sidebar.selectbox("Año de análisis", available_years, index=0)

distritos = sorted(df['distrito_nombre'].unique())
selected_distrito = st.sidebar.multiselect("Distrito", distritos, default=distritos[:3])

# Filtrar dataframe
df_filtered = df[df['anio'] == selected_year]
if selected_distrito:
    df_filtered = df_filtered[df_filtered['distrito_nombre'].isin(selected_distrito)]

# --- HEADER ---
st.title("🏠 Barcelona Housing Intelligence")
st.markdown(f"### Análisis de Mercado y Riesgo Social - Año {selected_year}")

# --- TOP METRICS ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_price = df_filtered['precio_m2_venta_promedio'].mean()
    st.metric("Precio Venta Promedio", f"{avg_price:,.0f} €/m²")

with col2:
    avg_rent = df_filtered['precio_mes_alquiler_promedio'].mean()
    st.metric("Alquiler Promedio", f"{avg_rent:,.0f} €/mes")

with col3:
    avg_gap = df_filtered['negotiation_gap_pct'].mean()
    st.metric("Margen Negociación", f"{avg_gap:.1f} %", help="Diferencia entre oferta y venta real")

with col4:
    critical_count = len(df_filtered[df_filtered['gentrification_risk_level'].str.contains('🔴')])
    st.metric("Barrios en Riesgo Crítico", critical_count)

# --- MAIN CHARTS ---
tab1, tab2, tab3 = st.tabs(["📊 Mercado & Negociación", "🚦 Riesgo de Gentrificación", "📍 Mapa de Oportunidades"])

with tab1:
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Margen de Negociación por Barrio")
        # Filtrar por volumen suficiente para el gráfico
        df_gap_plot = df_filtered[df_filtered['negotiation_low_volume'] == 0].sort_values('negotiation_gap_pct', ascending=False)
        
        fig_gap = px.bar(
            df_gap_plot.head(15),
            x='negotiation_gap_pct',
            y='barrio_nombre',
            orientation='h',
            color='negotiation_gap_pct',
            color_continuous_scale='RdYlGn',
            labels={'negotiation_gap_pct': 'Margen (%)', 'barrio_nombre': 'Barrio'},
            title="TOP 15 Barrios con más Margen de Negociación"
        )
        st.plotly_chart(fig_gap, use_container_width=True)

    with col_right:
        st.subheader("Relación Oferta vs Transacción Real")
        fig_scatter = px.scatter(
            df_filtered,
            x='asking_price_m2',
            y='transaction_price_m2',
            color='distrito_nombre',
            size='avg_num_anuncios_venta',
            hover_name='barrio_nombre',
            labels={'asking_price_m2': 'Precio Oferta (€/m²)', 'transaction_price_m2': 'Precio Real (€/m²)'},
            trendline="ols"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    st.subheader("Semáforo de Riesgo de Gentrificación 2025")
    
    # Tabla de riesgo
    risk_summary = df_filtered.groupby('gentrification_risk_level').size().reset_index(name='Cuenta')
    
    col_table, col_pie = st.columns([1, 1])
    
    with col_table:
        st.dataframe(
            df_filtered[['barrio_nombre', 'distrito_nombre', 'renta_bruta_llar', 'gentrification_rent_increase_pct', 'gentrification_risk_level']]
            .sort_values('gentrification_rent_increase_pct', ascending=False)
            .style.applymap(lambda x: 'background-color: #ffcccc' if '🔴' in str(x) else ('background-color: #ffe5cc' if '🟠' in str(x) else ''), subset=['gentrification_risk_level']),
            use_container_width=True,
            height=400
        )
    
    with col_pie:
        fig_pie = px.pie(
            risk_summary, 
            values='Cuenta', 
            names='gentrification_risk_level',
            color='gentrification_risk_level',
            color_discrete_map={
                'CRÍTICO 🔴': '#dc3545',
                'ALTO 🟠': '#fd7e14',
                'MEDIO 🟡': '#ffc107',
                'BAJO 🟢': '#198754',
                'DESCONOCIDO ⚪': '#6c757d'
            },
            title="Distribución de Riesgo"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.subheader("Mapa de Calor: Margen de Negociación")
    
    # Mapa usando los centroides guardados en la master table
    if 'centroide_lat' in df_filtered.columns and 'centroide_lon' in df_filtered.columns:
        fig_map = px.scatter_mapbox(
            df_filtered.dropna(subset=['centroide_lat', 'centroide_lon']),
            lat="centroide_lat",
            lon="centroide_lon",
            color="negotiation_gap_pct",
            size="avg_num_anuncios_venta",
            color_continuous_scale="RdYlGn",
            hover_name="barrio_nombre",
            hover_data=["asking_price_m2", "transaction_price_m2", "gentrification_risk_level"],
            zoom=11,
            height=600,
            mapbox_style="carto-positron"
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("Coordenadas no disponibles en el dataset para mostrar el mapa.")

# Footer
st.markdown("---")
st.markdown("📊 **Dataset**: `master_table_barcelona_housing.csv` | **Última actualización**: 2026-01-14")
