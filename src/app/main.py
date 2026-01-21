from __future__ import annotations

"""
Barcelona Housing Analytics - Dashboard Principal

Dashboard interactivo para analizar el mercado inmobiliario de Barcelona
y su relación con factores demográficos.
"""

import sys
import os
from pathlib import Path

# Configurar el path ANTES de importar streamlit o cualquier módulo src
# Esto es crítico para que las importaciones funcionen correctamente
_file_path = Path(__file__).resolve()
PROJECT_ROOT = _file_path.parent.parent.parent

# Añadir al path de múltiples formas para asegurar compatibilidad
project_root_str = str(PROJECT_ROOT)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)
# También añadir al PYTHONPATH de entorno si no está
if 'PYTHONPATH' not in os.environ or project_root_str not in os.environ.get('PYTHONPATH', ''):
    os.environ['PYTHONPATH'] = f"{project_root_str}:{os.environ.get('PYTHONPATH', '')}"

import streamlit as st
import logging

from src.app.config import PAGE_CONFIG, DB_PATH
from src.app.data_loader import (
    load_distritos, 
    load_kpis, 
    log_user_query,
    get_dynamic_metric_metadata
)
from src.app.components import render_breadcrumbs
from src.app.styles import inject_global_css
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
    
    # Registro de actividad (v1.1 SSOT)
    log_user_query(distrito_filter, selected_metric, selected_year)
    
    # Breadcrumbs Navigation
    crumbs = [{"label": "Home", "path": "home"}, {"label": "Dashboard", "path": "dashboard"}]
    if distrito_filter:
        crumbs.append({"label": distrito_filter, "path": "district"})
    else:
        crumbs.append({"label": "Global BCN", "path": "global"})
        
    render_breadcrumbs(crumbs)
    
    # Navegación principal con tabs traducidos al español y con iconos
    tab1, tab2, tab_intel, tab_inv, tab3, tab4, tab5, tab_esg = st.tabs([
        "🏘️ Mercado",
        "📊 Análisis",
        "🧠 Inteligencia",
        "💰 Inversión",
        "🚨 Alertas",
        "💡 Recomendaciones",
        "📄 Reportes",
        "🌱 Social ESG",
    ])
    
    with tab1:
        # Market Cockpit - Wireframe 1 (usa filtros del sidebar)
        market_cockpit.render(year=selected_year, distrito_filter=distrito_filter, barrio_id=selected_barrio_id)
    
    with tab2:
        advanced_analytics.render(year=selected_year)

    with tab_intel:
        market_intelligence.render(distrito_filter=distrito_filter)

    with tab_inv:
        try:
            investment_analysis.render(year=selected_year)
        except Exception as e:
            st.error(f"⚠️ Error loading Investment Analysis view: {str(e)}")
            st.info("This view is temporarily unavailable. Please try another view or contact support.")
            st.caption("Tip: Try navigating to other tabs like Market or Insights.")
    
    with tab3:
        try:
            alerts.render(year=selected_year)
        except Exception as e:
            st.error(f"⚠️ Error loading Alerts view: {str(e)}")
            st.info("This view is temporarily unavailable. Please try another view.")
    
    with tab4:
        try:
            recommendations.render(year=selected_year)
        except Exception as e:
            st.error(f"⚠️ Error loading Recommendations view: {str(e)}")
            st.info("This view is temporarily unavailable. Please try another view.")
    
    with tab5:
        st.header("📝 Reportes Ejecutivos")
        st.write(
            "En esta sección puedes acceder a los reportes de inteligencia de mercado generados. "
            "Estos reportes son snapshots profesionales diseñados para stakeholders."
        )
        
        col_rep1, col_rep2 = st.columns(2)
        
        with col_rep1:
            st.subheader("Reporte de Mercado (Último)")
            try:
                report_files = list((PROJECT_ROOT / "docs" / "reports").glob("stakeholder_report_*.html"))
                if report_files:
                    latest_report = sorted(report_files)[-1]
                    st.success(f"✅ Reporte disponible: {latest_report.name}")
                    with open(latest_report, "rb") as f:
                        st.download_button(
                            label="Descargar Reporte HTML (Snapshot)",
                            data=f,
                            file_name=latest_report.name,
                            mime="text/html",
                            width="stretch"
                        )
                else:
                    st.warning("⚠️ No se han encontrado reportes generados.")
            except Exception as e:
                st.error(f"Error al localizar reportes: {e}")

        with col_rep2:
            st.subheader("Generación de Reportes")
            st.info("Para generar un nuevo reporte actualizado con los datos más recientes, ejecuta:")
            st.code("python scripts/generate_stakeholder_report.py")
            st.write("Esto creará un nuevo archivo en `docs/reports/` con el año de datos detectado.")

    with tab_esg:
        esg_view.render(year=selected_year, distrito_filter=distrito_filter)
    
    # Tabs secundarios (legacy - mantener para compatibilidad)
    st.markdown("---")
    st.markdown("### 📚 Módulos Adicionales")
    
    tab_sec1, tab_sec2, tab_sec3, tab_sec4, tab_sec5, tab_sec6 = st.tabs([
        "Territorio",
        "Demografía",
        "Correlaciones",
        "Calidad de Datos",
        "Diccionario Datos",
        "Market View (Legacy)",
    ])
    
    with tab_sec1:
        map_analysis.render(
            year=selected_year,
            distrito_filter=distrito_filter,
            key_prefix="tab_territorio",
        )
    
    with tab_sec2:
        demographics.render(year=selected_year)
    
    with tab_sec3:
        correlations.render(year=selected_year)
    
    with tab_sec4:
        data_quality.render(year=selected_year, key_prefix="tab_data_quality")
    
    with tab_sec5:
        data_dictionary.render()
    
    with tab_sec6:
        market_view.render_market_cockpit()


if __name__ == "__main__":
    main()
