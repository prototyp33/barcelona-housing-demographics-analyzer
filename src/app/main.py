from __future__ import annotations

"""
Barcelona Housing Analytics - Dashboard Principal

Dashboard interactivo para analizar el mercado inmobiliario de Barcelona
y su relación con factores demográficos.
"""

import sys
from pathlib import Path

# Configurar el path ANTES de importar streamlit o cualquier módulo src
# Crítico cuando se ejecuta sin PYTHONPATH (ej: streamlit run directo)
_file_path = Path(__file__).resolve()
PROJECT_ROOT = _file_path.parent.parent.parent
_project_root_str = str(PROJECT_ROOT)
if _project_root_str not in sys.path:
    sys.path.insert(0, _project_root_str)

import streamlit as st
import logging

from src.app.config import PAGE_CONFIG, DB_PATH
from src.app.data_loader import (
    load_distritos, 
    load_kpis, 
    log_user_query,
    get_dynamic_metric_metadata
)
# Import from old components.py file (not the new components/ package)
# Use importlib to avoid conflict with components/ package
import importlib.util
import sys
spec = importlib.util.spec_from_file_location("old_components", "src/app/components.py")
old_components = importlib.util.module_from_spec(spec)
sys.modules["old_components"] = old_components
spec.loader.exec_module(old_components)

from src.app.styles import inject_global_css
from src.app.design_system import COLORS, SPACING, FONTS  # New centralized design system
from src.app.state_manager import (  # New global state management
    init_session_state,
    update_filter_state,
    get_filter_state,
    sync_widgets_to_filters,
    increment_page_view,
)
from src.app.views import (
    overview,
    map_analysis,
    correlations,
    demographics,
    data_quality,
    market_view,
    advanced_analytics,
    alerts,
    recommendations,
    market_cockpit,
    investment_analysis,
    data_dictionary,
    market_intelligence,
    esg_view,
    price_predictor,
)


def configure_page() -> None:
    """Configura la página de Streamlit con Design System."""
    st.set_page_config(**PAGE_CONFIG)
    
    # Inyectar CSS global del Design System
    inject_global_css()
    
    # Configurar logging a archivo si está habilitado
    try:
        # Verificar si secrets está disponible y tiene la configuración de logging
        if hasattr(st, 'secrets'):
            try:
                log_config = st.secrets.get("logging", {})
                if isinstance(log_config, dict) and log_config.get("enabled", False):
                    from src.app.components.performance_monitor import setup_logging_to_file
                    log_level = logging.DEBUG if log_config.get("level", "").upper() == "DEBUG" else logging.INFO
                    setup_logging_to_file(log_level)
            except (AttributeError, RuntimeError, KeyError):
                # st.secrets no disponible o no configurado, usar logging básico
                pass
    except Exception:
        # Cualquier otro error, continuar sin logging a archivo
        pass


def render_sidebar() -> tuple[int, str | None, str]:
    """
    Renderiza el sidebar estilo cockpit con identidad, filtros y metadatos.
    """
    with st.sidebar:
        # 0. Cargar metadatos dinámicos de la BD (v1.2 MVP)
        dynamic_metadata = get_dynamic_metric_metadata()

        # ... (logo and identity remain the same)
        st.markdown(
            f'<div style="display: flex; align-items: center; margin-bottom: 30px;">'
            f'<div style="width: 44px; height: 44px; background: linear-gradient(135deg, #2F80ED 0%, #56CCF2 100%); '
            f'border-radius: 14px; display: flex; align-items: center; justify-content: center; '
            f'color: white; font-weight: bold; font-size: 22px; '
            f'box-shadow: 0 8px 20px rgba(47, 128, 237, 0.35);">🏙️</div>'
            f'<div style="margin-left: 12px;">'
            f'<div style="font-size: 16px; font-weight: 700; color: #1A1A1A;">Barcelona</div>'
            f'<div style="font-size: 12px; color: #4A5568;">Housing Analytics</div></div></div>',
            unsafe_allow_html=True,
        )
        
        st.markdown(
            '<p style="font-size: 11px; font-weight: 600; color: #8E92BC; letter-spacing: 1px; margin-bottom: 6px;">CONFIGURACIÓN DE VISTA</p>',
            unsafe_allow_html=True,
        )
        
        selected_metric = st.selectbox(
            "Métrica Principal",
            options=list(dynamic_metadata.keys()),
            help="Define la variable principal para los KPIs y mapas.",
        )
        
        distritos = load_distritos()
        distrito_options = ["Todos"] + distritos
        selected_distrito = st.selectbox("Filtro por Distrito", options=distrito_options)
        distrito_filter = None if selected_distrito == "Todos" else selected_distrito
        
        # Filtro adicional de Barrio para Market Cockpit (más granular que distrito)
        st.markdown("---")
        st.markdown(
            '<p style="font-size: 11px; font-weight: 600; color: #8E92BC; letter-spacing: 1px; margin-bottom: 6px;">FILTROS ADICIONALES</p>',
            unsafe_allow_html=True,
        )
        
        # Cargar barrios para el filtro específico
        selected_barrio_id = None
        try:
            from src.app.data_loader import load_barrios
            barrios_df = load_barrios()
            barrio_options = ["Todos"] + barrios_df["barrio_nombre"].tolist()
            selected_barrio = st.selectbox(
                "📍 Barrio",
                options=barrio_options,
                key="sidebar_barrio_filter",
                help="Selecciona un barrio específico o 'Todos' para ver el análisis completo"
            )
            if selected_barrio != "Todos":
                selected_barrio_id = int(barrios_df[barrios_df["barrio_nombre"] == selected_barrio]["barrio_id"].iloc[0])
        except Exception:
            selected_barrio_id = None
        
        # Opción para mostrar métricas de rendimiento (solo en desarrollo)
        try:
            if hasattr(st, 'secrets'):
                try:
                    log_config = st.secrets.get("logging", {})
                    if isinstance(log_config, dict) and log_config.get("show_performance", False):
                        from src.app.components.performance_monitor import render_performance_metrics
                        render_performance_metrics(show_details=True)
                except (AttributeError, RuntimeError, KeyError):
                    # st.secrets no disponible o no configurado, no mostrar métricas
                    pass
        except Exception:
            # Cualquier otro error, continuar sin métricas
            pass
        
        # Lógica Temporal Dinámica (v1.2 MVP - SSOT)
        meta = dynamic_metadata.get(selected_metric, {})
        min_year = meta.get("min_year", 2015)
        max_year = meta.get("max_year", 2023)
        
        if min_year == max_year:
            st.info(meta.get("info", f"Mostrando datos para **{max_year}**"))
            selected_year = max_year
            disable_slider = True
        else:
            disable_slider = False
            selected_year = st.slider(
                "Año de Análisis",
                min_value=min_year,
                max_value=max_year,
                value=max_year,
                disabled=disable_slider,
            )
        
        st.markdown("---")
        
        with st.expander("ℹ️ Sobre los datos", expanded=False):
            from datetime import datetime
            current_date = datetime.now().strftime("%B %Y")
            
            # Obtener resumen de la BD (v1.3 - Dynamic Stats)
            kpis = load_kpis()
            registros = kpis.get("registros_precios", 9000)
            
            st.caption(f"📅 **Actualización:** {current_date}")
            st.caption("📡 **Fuentes:** OpenData BCN, Idealista, IDESCAT")
            st.caption(f"🔢 **Registros:** +{registros:,} puntos de datos")
            st.caption("v2.2 - Logic Clean Release")
            
            st.markdown("---")
            
            # Botón de Descarga del Reporte Ejecutivo HTML
            try:
                # Buscar el reporte más reciente (ej. 2024)
                report_files = list((PROJECT_ROOT / "docs" / "reports").glob("stakeholder_report_*.html"))
                if report_files:
                    latest_report = sorted(report_files)[-1]
                    with open(latest_report, "rb") as fr:
                        st.download_button(
                            label="📥 Descargar Reporte Ejecutivo",
                            data=fr,
                            file_name=latest_report.name,
                            mime="text/html",
                            width="stretch",
                            help="Descarga el último reporte ejecutivo generado en formato HTML (interactivo/offline)."
                        )
                else:
                    st.info("Reporte ejecutivo no encontrado.")
            except Exception:
                pass

            if DB_PATH.exists():
                with open(DB_PATH, "rb") as fp:
                    st.download_button(
                        label="📥 Descargar Base de Datos",
                        data=fp,
                        file_name="barcelona_housing.db",
                        mime="application/x-sqlite3",
                        width="stretch",
                        help="Descarga el archivo SQLite completo con todas las tablas procesadas."
                    )
        
        st.markdown(
            f'<div style="display: flex; align-items: center; background: rgba(255,255,255,0.5); '
            f'padding: 12px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.7); margin-top: 20px;">'
            f'<div style="width: 36px; height: 36px; background: #E2E8F0; border-radius: 50%;"></div>'
            f'<div style="margin-left: 10px;">'
            f'<div style="font-size: 12px; font-weight: 600; color: #1A1A1A;">Usuario Admin</div>'
            f'<div style="font-size: 10px; color: #2F80ED;">● Conectado</div></div></div>',
            unsafe_allow_html=True,
        )
        
    
    return selected_year, distrito_filter, selected_metric, selected_barrio_id


def main() -> None:
    """Punto de entrada principal del dashboard."""
    configure_page()
    
    # Initialize global session state (v2.3 - Global Context Pattern)
    init_session_state()
    increment_page_view()
    
    # Health check de la API (solo una vez por sesión)
    from src.app.api_client import check_api_availability
    api_available = check_api_availability()
    
    # Mostrar warning si la API no está disponible (solo una vez)
    if not api_available and 'api_warning_shown' not in st.session_state:
        st.session_state['api_warning_shown'] = True
        with st.container():
            st.warning(
                "⚠️ **API Backend no disponible**: El dashboard está funcionando en modo offline usando la base de datos local. "
                "Algunas funcionalidades avanzadas pueden estar limitadas. "
                "Para habilitar todas las funciones, inicia el servidor API en `localhost:8000`."
            )
    
    # Sidebar con filtros (incluye Smart Date Selector)
    sidebar_result = render_sidebar()
    selected_year, distrito_filter, selected_metric = sidebar_result[:3]
    selected_barrio_id = sidebar_result[3] if len(sidebar_result) > 3 else None
    
    # Sync filters to global state (v2.3)
    sync_widgets_to_filters(
        district=distrito_filter if distrito_filter else 'All',
        barrio_id=selected_barrio_id,
        year=selected_year,
        metric=selected_metric,
    )
    
    # Registro de actividad (v1.1 SSOT)
    log_user_query(distrito_filter, selected_metric, selected_year)
    
    # Breadcrumbs Navigation
    crumbs = [{"label": "Home", "path": "home"}, {"label": "Dashboard", "path": "dashboard"}]
    if distrito_filter:
        crumbs.append({"label": distrito_filter, "path": "district"})
    else:
        crumbs.append({"label": "Global BCN", "path": "global"})
        
    old_components.render_breadcrumbs(crumbs)
    
    
    # ============================================
    # NEW 4-TIER NAVIGATION STRUCTURE (v2.3)
    # Consolidates 14 tabs into 4 main categories
    # ============================================
    
    tab_overview, tab_analytics, tab_investment, tab_territory = st.tabs([
        "🏠 Overview",
        "📊 Analytics", 
        "💼 Investment",
        "🌍 Territory",
    ])
    
    # ============================================
    # TAB 1: OVERVIEW - Using Reusable Components
    # ============================================
    with tab_overview:
        # Import components
        from src.app.components import (
            render_hero_section,
            render_section_header,
            create_metric_grid,
            render_kpi_card,
            create_two_column_layout,
            render_spacer,
            render_info_card
        )
        
        # Load data once
        kpis = load_kpis()
        
        # Hero Section using component
        render_hero_section(
            title="Barcelona Housing Analytics",
            subtitle=f"Dashboard de análisis inmobiliario • Año {selected_year}",
            background_gradient=True
        )
        
        # Key Metrics Section
        render_section_header(
            title="Métricas Principales",
            icon="📊",
            subtitle="Indicadores clave del mercado inmobiliario"
        )
        
        # Extract KPI values
        precio_medio = kpis.get("precio_medio_actual", 0)
        total_barrios = kpis.get("total_barrios", 73)
        registros = kpis.get("registros_precios", 0)
        year_min = kpis.get("año_min", 2015)
        year_max = kpis.get("año_max", 2023)
        
        # Calculate year-over-year change if available
        precio_anterior = kpis.get("precio_medio_anterior", 0)
        yoy_change = ""
        if precio_anterior > 0:
            pct_change = ((precio_medio - precio_anterior) / precio_anterior) * 100
            yoy_change = f"{'↗' if pct_change > 0 else '↘'} {pct_change:+.1f}%"
        
        # Create KPI grid using component
        cols = create_metric_grid(num_columns=4, gap="medium")
        
        with cols[0]:
            render_kpi_card(
                title="Precio Medio",
                value=f"{precio_medio:,.0f} €/m²",
                delta=yoy_change if yoy_change else None,
                help_text=f"Precio medio de venta por m² en {selected_year}",
                icon="💰",
                color_scheme="primary"
            )
        
        with cols[1]:
            render_kpi_card(
                title="Barrios",
                value=str(total_barrios),
                help_text="Barrios analizados en Barcelona",
                icon="🏘️",
                color_scheme="secondary"
            )
        
        with cols[2]:
            render_kpi_card(
                title="Registros",
                value=f"{registros:,}",
                help_text="Total de registros de precios en la base de datos",
                icon="📈",
                color_scheme="secondary"
            )
        
        with cols[3]:
            num_years = year_max - year_min + 1
            render_kpi_card(
                title="Período",
                value=str(num_years),
                delta=f"{year_min}-{year_max}",
                help_text=f"Años de datos disponibles ({year_min} a {year_max})",
                icon="📅",
                color_scheme="warning"
            )
        
        # Spacer
        render_spacer('xl')
        
        # Main Content - Two Columns using component
        col_left, col_right = create_two_column_layout(left_ratio=1.6, gap="large")
        
        with col_left:
            # Map Section
            render_section_header(
                title="Mapa de Barcelona",
                icon="🗺️",
                subtitle="Distribución de precios por barrio"
            )
            
            # Map preview
            from src.app.views import map_analysis
            with st.container():
                map_analysis.render_snapshot(year=selected_year, key="overview_map_v3")
        
        with col_right:
            # Quick Navigation
            render_section_header(
                title="Navegación Rápida",
                icon="🎯",
                subtitle="Accede a las secciones principales"
            )
            
            # Navigation cards (keeping custom HTML for now as we don't have a nav card component yet)
            nav_items = [
                ("📊", "Analytics", "Análisis estadístico y demográfico", COLORS['primary']),
                ("💼", "Investment", "Oportunidades de inversión", COLORS['accent_green']),
                ("🌍", "Territory", "Mapas y análisis territorial", COLORS['secondary']),
            ]
            
            for icon, title, desc, color in nav_items:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {color}12 0%, {color}05 100%);
                            padding: 18px 20px; 
                            border-radius: 12px; 
                            margin-bottom: 12px;
                            border-left: 3px solid {color}; 
                            cursor: pointer;
                            transition: all 0.2s ease;
                            min-height: 76px;
                            display: flex;
                            align-items: center;">
                    <div style="display: flex; align-items: center; gap: 16px; width: 100%;">
                        <span style="font-size: 28px; flex-shrink: 0;">{icon}</span>
                        <div style="flex: 1; min-width: 0;">
                            <div style="font-size: 16px; font-weight: 700; color: {COLORS['text']['primary']}; 
                                       margin-bottom: 4px; line-height: 1.3;">
                                {title}
                            </div>
                            <div style="font-size: 13px; color: {COLORS['text']['secondary']}; line-height: 1.4;">
                                {desc}
                            </div>
                        </div>
                        <span style="color: {color}; font-size: 24px; font-weight: 600; flex-shrink: 0;">→</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            render_spacer('md')
            
            # System Info using info card component
            render_info_card(
                title="Información del Sistema",
                content=f"""
                <div style="display: grid; gap: 12px; margin-top: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;
                               padding: 8px 0; border-bottom: 1px solid rgba(0,0,0,0.05);">
                        <span style="font-size: 13px; color: {COLORS['text']['secondary']}; font-weight: 500;">
                            Fuentes de datos
                        </span>
                        <span style="font-size: 16px; font-weight: 700; color: {COLORS['text']['primary']};">
                            3
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;
                               padding: 8px 0; border-bottom: 1px solid rgba(0,0,0,0.05);">
                        <span style="font-size: 13px; color: {COLORS['text']['secondary']}; font-weight: 500;">
                            Última actualización
                        </span>
                        <span style="font-size: 16px; font-weight: 700; color: {COLORS['text']['primary']};">
                            {selected_year}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;
                               padding: 8px 0;">
                        <span style="font-size: 13px; color: {COLORS['text']['secondary']}; font-weight: 500;">
                            Versión
                        </span>
                        <span style="font-size: 16px; font-weight: 700; color: {COLORS['text']['primary']};">
                            2.3
                        </span>
                    </div>
                </div>
                """,
                icon="ℹ️",
                card_type="info"
            )
    
    # ============================================
    # TAB 2: ANALYTICS
    # Deep-dive data sandbox: Advanced Analytics, Demographics, Correlations
    # ============================================
    with tab_analytics:
        st.markdown(f"""
        <div style="margin-bottom: {SPACING['lg']};">
            <h1 style="{FONTS['h1_css']}">Análisis Avanzado</h1>
            <p style="{FONTS['caption_css']}">
                Análisis estadístico, demográfico y correlaciones
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sub-navigation within Analytics
        analytics_view = st.radio(
            "Selecciona vista:",
            ["📈 Análisis Estadístico", "👥 Demografía", "🔗 Correlaciones"],
            horizontal=True,
            key="analytics_subnav",
        )
        
        if analytics_view == "📈 Análisis Estadístico":
            with st.spinner("Cargando análisis estadístico..."):
                advanced_analytics.render(year=selected_year)
        
        elif analytics_view == "👥 Demografía":
            with st.spinner("Cargando datos demográficos..."):
                demographics.render(year=selected_year)
        
        else:  # Correlaciones
            with st.spinner("Calculando correlaciones..."):
                correlations.render(year=selected_year)
    
    # ============================================
    # TAB 3: INVESTMENT
    # Financials and decision-support: Opportunities, Intelligence, Alerts, Recommendations
    # ============================================
    with tab_investment:
        st.markdown(f"""
        <div style="margin-bottom: {SPACING['lg']};">
            <h1 style="{FONTS['h1_css']}">Análisis de Inversión</h1>
            <p style="{FONTS['caption_css']}">
                Oportunidades, inteligencia de mercado y recomendaciones
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sub-navigation within Investment
        investment_view = st.radio(
            "Selecciona vista:",
            ["💡 Oportunidades", "🧠 Inteligencia de Mercado", "🔮 Predictor de Precios", "🚨 Alertas", "⭐ Recomendaciones"],
            horizontal=True,
            key="investment_subnav",
        )
        
        if investment_view == "💡 Oportunidades":
            with st.spinner("Analizando oportunidades de inversión..."):
                try:
                    investment_analysis.render(year=selected_year)
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")
                    st.info("Vista temporalmente no disponible. Intenta otra sección.")
        
        elif investment_view == "🧠 Inteligencia de Mercado":
            with st.spinner("Cargando inteligencia de mercado..."):
                market_intelligence.render(distrito_filter=distrito_filter)
        
        elif investment_view == "🔮 Predictor de Precios":
            with st.spinner("Cargando predictor inteligente..."):
                price_predictor.render(year=selected_year)
                
        elif investment_view == "🚨 Alertas":
            with st.spinner("Verificando alertas..."):
                try:
                    alerts.render(year=selected_year)
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")
        
        else:  # Recomendaciones
            with st.spinner("Generando recomendaciones..."):
                try:
                    recommendations.render(year=selected_year)
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")
    
    # ============================================
    # TAB 4: TERRITORY
    # Geospatial and community impact: Map Analysis, Social ESG, Data Quality
    # ============================================
    with tab_territory:
        st.markdown(f"""
        <div style="margin-bottom: {SPACING['lg']};">
            <h1 style="{FONTS['h1_css']}">Análisis Territorial</h1>
            <p style="{FONTS['caption_css']}">
                Mapas interactivos, métricas ESG y calidad de datos
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sub-navigation
        territory_view = st.radio(
            "Selecciona vista:",
            ["🗺️ Mapa Interactivo", "🌱 Social ESG", "✅ Calidad de Datos"],
            horizontal=True,
            key="territory_subnav",
        )
        
        if territory_view == "🗺️ Mapa Interactivo":
            with st.spinner("Cargando mapa..."):
                map_analysis.render(
                    year=selected_year,
                    distrito_filter=distrito_filter,
                    key_prefix="tab_territorio",
                )
        
        elif territory_view == "🌱 Social ESG":
            with st.spinner("Cargando métricas ESG..."):
                esg_view.render(year=selected_year, distrito_filter=distrito_filter)
        
        else:  # Calidad de Datos
            with st.spinner("Analizando calidad de datos..."):
                data_quality.render(year=selected_year, key_prefix="tab_data_quality")
    
    # ============================================
    # UTILITIES SECTION (Moved to Sidebar Expander)
    # Data Dictionary, Downloads, Reports
    # ============================================
    with st.sidebar:
        st.markdown("---")
        
        with st.expander("⚙️ Utilidades", expanded=False):
            utility_section = st.radio(
                "Sección:",
                ["📖 Diccionario", "📥 Descargas", "📄 Reportes"],
                key="utility_nav",
                label_visibility="collapsed"
            )
            
            if utility_section == "📖 Diccionario":
                st.caption("Ver diccionario de datos completo en la pestaña principal")
                if st.button("Abrir Diccionario", width="stretch"):
                    st.info("Navega a Settings > Diccionario de Datos")
            
            elif utility_section == "📥 Descargas":
                st.caption("**Base de Datos**")
                if DB_PATH.exists():
                    with open(DB_PATH, "rb") as fp:
                        st.download_button(
                            label="📥 SQLite DB",
                            data=fp,
                            file_name="barcelona_housing.db",
                            mime="application/x-sqlite3",
                            width="stretch",
                        )
                
                st.caption("**Reporte Ejecutivo**")
                try:
                    report_files = list((PROJECT_ROOT / "docs" / "reports").glob("stakeholder_report_*.html"))
                    if report_files:
                        latest_report = sorted(report_files)[-1]
                        with open(latest_report, "rb") as fr:
                            st.download_button(
                                label="📥 Reporte HTML",
                                data=fr,
                                file_name=latest_report.name,
                                mime="text/html",
                                width="stretch",
                            )
                except Exception:
                    pass
            
            else:  # Reportes
                st.caption("**Generación de Reportes**")
                st.code("python scripts/generate_stakeholder_report.py", language="bash")
                st.caption("Ejecuta este comando para generar un nuevo reporte actualizado.")


if __name__ == "__main__":
    main()
