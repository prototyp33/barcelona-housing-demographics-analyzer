"""
Barcelona Housing Demographics Dashboard - Main Entry Point.

Dashboard interactivo para analizar el mercado inmobiliario de Barcelona
y su relación con factores demográficos.
"""

from __future__ import annotations

import streamlit as st

from src.app.config import PAGE_CONFIG, VIVIENDA_TIPO_M2, DB_PATH
from src.app.data_loader import load_distritos, load_available_years, load_kpis, load_precios
from src.app.components import card_standard, card_chart, card_snapshot, card_metric
from src.app.styles import inject_global_css, render_responsive_kpi_grid, render_ranking_item
from src.app.views import overview, map_analysis, correlations, demographics, data_quality


def configure_page() -> None:
    """Configura la página de Streamlit con Design System."""
    st.set_page_config(**PAGE_CONFIG)
    
    # Inyectar CSS global del Design System
    inject_global_css()


def render_sidebar() -> tuple[int, str | None, str]:
    """
    Renderiza el sidebar estilo cockpit con identidad, filtros y metadatos.
    """
    years_info = load_available_years()
    min_year = years_info["fact_precios"]["min"] or 2015
    max_year = years_info["fact_precios"]["max"] or 2022
    
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; margin-bottom: 30px;">
                <div style="
                    width: 44px; height: 44px;
                    background: linear-gradient(135deg, #2F80ED 0%, #56CCF2 100%);
                    border-radius: 14px; display: flex; align-items: center; justify-content: center;
                    color: white; font-weight: bold; font-size: 22px;
                    box-shadow: 0 8px 20px rgba(47, 128, 237, 0.35);
                ">
                    🏙️
                </div>
                <div style="margin-left: 12px;">
                    <div style="font-size: 16px; font-weight: 700; color: #1A1A1A;">Barcelona</div>
                    <div style="font-size: 12px; color: #4A5568;">Housing Analytics</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.markdown(
            '<p style="font-size: 11px; font-weight: 600; color: #8E92BC; letter-spacing: 1px; margin-bottom: 6px;">CONFIGURACIÓN DE VISTA</p>',
            unsafe_allow_html=True,
        )
        
        selected_metric = st.selectbox(
            "Métrica Principal",
            options=["Precio Venta", "Renta Mensual", "Esfuerzo Compra", "Demografía"],
            help="Define la variable principal para los KPIs y mapas.",
        )
        
        distritos = load_distritos()
        distrito_options = ["Todos"] + distritos
        selected_distrito = st.selectbox("Filtro por Distrito", options=distrito_options)
        distrito_filter = None if selected_distrito == "Todos" else selected_distrito
        
        if selected_metric == "Renta Mensual":
            st.info("Mostrando datos disponibles para **2022** (Único registro oficial de renta)")
            selected_year = 2022
            disable_slider = True
        else:
            disable_slider = False
            default_year = 2022 if 2022 <= max_year else max_year
            selected_year = st.slider(
                "Año de Análisis",
                min_value=min_year,
                max_value=max_year,
                value=default_year,
                disabled=disable_slider,
            )
        
        st.markdown("---")
        
        with st.expander("ℹ️ Sobre los datos", expanded=False):
            st.caption("📅 **Actualización:** Noviembre 2025")
            st.caption("📡 **Fuentes:** OpenData BCN, Idealista, IDESCAT")
            st.caption("🔢 **Registros:** +9,000 puntos de datos")
            st.caption("v2.1 - Cockpit Release")
            
            st.markdown("---")
            if DB_PATH.exists():
                with open(DB_PATH, "rb") as fp:
                    st.download_button(
                        label="📥 Descargar Base de Datos",
                        data=fp,
                        file_name="barcelona_housing.db",
                        mime="application/x-sqlite3",
                        use_container_width=True,
                        help="Descarga el archivo SQLite completo con todas las tablas procesadas."
                    )
        
        st.markdown(
            """
            <div style="
                display: flex; align-items: center;
                background: rgba(255,255,255,0.5);
                padding: 12px; border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.7);
                margin-top: 20px;
            ">
                <div style="width: 36px; height: 36px; background: #E2E8F0; border-radius: 50%;"></div>
                <div style="margin-left: 10px;">
                    <div style="font-size: 12px; font-weight: 600; color: #1A1A1A;">Usuario Admin</div>
                    <div style="font-size: 10px; color: #2F80ED;">● Conectado</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    
    return selected_year, distrito_filter, selected_metric


def render_custom_header(distrito_filter: str | None, metric_name: str, year: int) -> None:
    """Renderiza encabezado principal dinámico."""
    
    if distrito_filter:
        display_title = f"Monitor de Mercado: <span style='color: #2F80ED'>{distrito_filter}</span>"
    else:
        display_title = "Monitor de Mercado: Global BCN"
        
    display_subtitle = f"Analizando <strong>{metric_name}</strong> • Datos del año <strong>{year}</strong>"

    with card_standard():
        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <div>
                    <p style="color: #8E92BC; font-size: 12px; letter-spacing: 1px; margin: 0;">RADAR OPERACIONAL</p>
                    <h2 style="margin: 4px 0 0 0; font-size: 26px; color: #1A1A1A;">{display_title}</h2>
                    <p style="color: #4A5568; font-size: 14px; margin: 4px 0 0 0;">{display_subtitle}</p>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 10px;">
                    <!-- Search Placeholder -->
                    <input placeholder="Buscar barrio específico..." style="
                        flex: 1;
                        min-width: 220px;
                        padding: 12px 16px;
                        border-radius: 16px;
                        border: 1px solid rgba(0,0,0,0.08);
                        font-family: 'Inter', sans-serif;
                        font-size: 14px;
                        background: #F8FAFC;
                    " />
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Nota: El botón de descarga funcional requiere integración con st.download_button
        # que se implementará en la fase 'Bronce' para no romper el layout HTML actual.


def render_primary_dashboard(year: int, distrito_filter: str | None) -> None:
    """Sección principal con KPIs y visualizaciones clave."""
    kpis = load_kpis()
    
    # Calcular Rentabilidad Bruta (Yield)
    # Formula: (Alquiler * 12) / (Precio_m2 * 70) * 100
    if kpis["precio_medio_2022"] > 0 and kpis.get("alquiler_medio_2022", 0) > 0:
        yield_pct = (kpis["alquiler_medio_2022"] * 12) / (kpis["precio_medio_2022"] * VIVIENDA_TIPO_M2) * 100
    else:
        yield_pct = 0.0

    # Calcular Variación Interanual
    if kpis.get("precio_medio_2021", 0) > 0:
        yoy_growth = ((kpis["precio_medio_2022"] - kpis["precio_medio_2021"]) / kpis["precio_medio_2021"]) * 100
        yoy_delta = f"{yoy_growth:+.1f}% vs 2021"
        yoy_color = "normal" # Azul/Neutro para crecimiento
    else:
        yoy_delta = None
        yoy_color = "off"

    kpi_data = [
        {
            "title": "Rentabilidad Bruta",
            "value": f"{yield_pct:.1f}%",
            "style": "white",
            "delta": "Retorno Anual",
            "delta_color": "green",
        },
        {
            "title": "Registros de Precios",
            "value": f"{kpis['registros_precios']:,}",
            "style": "warm",
            "delta": f"{kpis['año_min']}-{kpis['año_max']}",
        },
        {
            "title": "Precio Medio Venta",
            "value": f"€{kpis['precio_medio_2022']:,.0f}/m²",
            "style": "cool",
            "delta": yoy_delta,
            "delta_color": yoy_color,
        },
        {
            "title": "Renta Media Anual",
            "value": f"€{kpis['renta_media_2022']:,.0f}",
            "style": "white",
            "delta": "Dato 2022",
            "delta_color": "red",
        },
    ]
    render_responsive_kpi_grid(kpi_data)
    
    col_main, col_details = st.columns([2, 1])
    with col_main:
        with card_chart(title="📈 Evolución del mercado"):
            overview.render_price_evolution(
                distrito_filter=distrito_filter,
                key="dashboard_price_evolution",
            )

    with col_details:
        with card_snapshot(
            title="🗺️ Distribución",
            badge_text="Snapshot"
        ):
            map_analysis.render_snapshot(
                year=year,
                key="home_map_snapshot",
            )
            if st.button("🔎 Ampliar en Territorio", key="btn_nav_territorio", type="secondary"):
                st.toast("👉 Ve a la pestaña 'Territorio' abajo para explorar el mapa interactivo", icon="🗺️")
    
    ranking_title = f"📋 Ranking de Barrios: {distrito_filter}" if distrito_filter else "📋 Desglose por distrito"
    st.markdown(f"### {ranking_title}")
    overview.render_distrito_comparison(
        year=year,
        distrito_filter=distrito_filter,
        key="dashboard_distrito_comparison"
    )


def main() -> None:
    """Punto de entrada principal del dashboard."""
    configure_page()
    
    # Sidebar con filtros (incluye Smart Date Selector)
    selected_year, distrito_filter, selected_metric = render_sidebar()
    
    render_custom_header(distrito_filter, selected_metric, selected_year)
    st.markdown("<br>", unsafe_allow_html=True)
    render_primary_dashboard(selected_year, distrito_filter)
    st.markdown("### 📚 Profundiza por módulo")
    
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Territorio", "Demografía", "Correlaciones", "Calidad de Datos"]
    )
    
    with tab1:
        map_analysis.render(
            year=selected_year,
            distrito_filter=distrito_filter,
            key_prefix="tab_territorio",
        )
    
    with tab2:
        demographics.render(year=selected_year)
    
    with tab3:
        correlations.render(year=selected_year)
    
    with tab4:
        data_quality.render(year=selected_year, key_prefix="tab_data_quality")


if __name__ == "__main__":
    main()

