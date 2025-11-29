"""
Design System - Barcelona Housing Analytics
UI/UX Component Library y CSS Injection

Implementa el estilo "Kristin" adaptado: Soft UI con tarjetas flotantes,
gradientes mesh y tipografía moderna.
"""

from __future__ import annotations

from textwrap import dedent

import streamlit as st


# Tokens de Color del Design System
COLOR_TOKENS = {
    "bg_canvas": "#F4F5F7",
    "bg_card": "#FFFFFF",
    "text_primary": "#1A1A1A",
    "text_secondary": "#8E92BC",
    "accent_blue": "#2F80ED",
    "accent_red": "#EB5757",
    "accent_green": "#27AE60",
    "border_radius": "24px",
    "shadow_elevation_1": "0px 10px 40px rgba(29, 22, 23, 0.1)",
}

# Gradientes Mesh (para KPIs destacados)
GRADIENTS = {
    "warm": "linear-gradient(135deg, #FF9966 0%, #FF5E62 100%)",
    "cool": "linear-gradient(135deg, #56CCF2 0%, #2F80ED 100%)",
}


def inject_global_css() -> None:
    """
    Inyecta el CSS global del Design System en la aplicación Streamlit.
    
    Debe llamarse una vez al inicio de main.py.
    Aplica los Fundamentos Visuales: Paleta de Colores, Tipografía, Sombras y Bordes.
    """
    css = f"""
    <style>
    /* Importar Font Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* ============================================
       FONDO GENERAL (Mesh Gradient)
       ============================================ */
    .stApp {{
        background-color: #F4F5F7;
        background-image:
            radial-gradient(at 10% 10%, rgba(47, 128, 237, 0.15) 0px, transparent 50%),
            radial-gradient(at 50% 50%, rgba(255, 153, 102, 0.08) 0px, transparent 50%);
        background-attachment: fixed;
        font-family: 'Inter', 'DM Sans', 'Roboto', sans-serif !important;
    }}
    
    /* ============================================
       TARJETAS Y CONTENEDORES (bg-card + Soft UI)
       ============================================ */
    /* Contenedores principales */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    
    /* Tarjetas de métricas nativas de Streamlit */
    [data-testid="stMetricValue"] {{
        color: {COLOR_TOKENS['text_primary']} !important;
        font-size: 36px !important;
        font-weight: 700 !important;
        font-family: 'Inter', sans-serif !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {COLOR_TOKENS['text_secondary']} !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
    }}
    
    [data-testid="stMetricDelta"] {{
        font-size: 14px !important;
        font-family: 'Inter', sans-serif !important;
    }}
    
    /* Contenedores de métricas con sombra Soft UI */
    [data-testid="metric-container"] {{
        background-color: {COLOR_TOKENS['bg_card']} !important;
        border-radius: {COLOR_TOKENS['border_radius']} !important;
        padding: 24px !important;
        box-shadow: {COLOR_TOKENS['shadow_elevation_1']} !important;
        border: none !important;
    }}
    
    /* Estilo de Tarjetas personalizadas */
    .css-card, .soft-card {{
        background-color: {COLOR_TOKENS['bg_card']};
        border-radius: {COLOR_TOKENS['border_radius']};
        padding: 24px;
        box-shadow: {COLOR_TOKENS['shadow_elevation_1']};
        border: none;
        margin-bottom: 24px;
    }}
    
    /* Botón Ghost */
    .btn-ghost {{
        background-color: transparent;
        border: 1px solid {COLOR_TOKENS['accent_blue']};
        color: {COLOR_TOKENS['accent_blue']};
        padding: 8px 16px;
        border-radius: 12px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
        width: 100%;
        margin-top: 12px;
    }}
    
    .btn-ghost:hover {{
        background-color: {COLOR_TOKENS['accent_blue']};
        color: white;
    }}
    
    /* ============================================
       TIPOGRAFÍA (H1, H2, H3, Body)
       ============================================ */
    /* H1 (Page Title): 24px - 32px, Bold */
    h1 {{
        color: {COLOR_TOKENS['text_primary']} !important;
        font-size: 32px !important;
        font-weight: 700 !important;
        font-family: 'Inter', sans-serif !important;
        line-height: 1.2 !important;
    }}
    
    /* H2 (Card Title): 18px, Semi-Bold */
    h2 {{
        color: {COLOR_TOKENS['text_primary']} !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        line-height: 1.3 !important;
    }}
    
    /* H3: 16px, Semi-Bold */
    h3 {{
        color: {COLOR_TOKENS['text_primary']} !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        line-height: 1.3 !important;
    }}
    
    /* Body: 14px, Regular */
    p, .stMarkdown, .stText {{
        color: {COLOR_TOKENS['text_primary']} !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        font-family: 'Inter', sans-serif !important;
        line-height: 1.5 !important;
    }}
    
    /* Texto secundario (Subtítulos, etiquetas) */
    .text-secondary, [data-testid="stCaption"] {{
        color: {COLOR_TOKENS['text_secondary']} !important;
        font-size: 14px !important;
        font-weight: 400 !important;
    }}
    
    /* ============================================
       KPIs CON GRADIENTES MESH
       ============================================ */
    .bh-kpi-card {{
        min-height: 160px;
        height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 20px;
        transition: box-shadow 0.3s ease, transform 0.3s ease;
        width: 100%;
    }}

    .bh-kpi-card:hover {{
        box-shadow: 0px 15px 45px rgba(29, 22, 23, 0.12);
        transform: translateY(-2px);
    }}

    @media (max-width: 1100px) {{
        .bh-kpi-card {{
            height: auto;
            min-height: 150px;
        }}
    }}

    .bh-kpi-grid {{
        width: 100%;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
    }}

    @media (max-width: 640px) {{
        .bh-kpi-grid {{
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        }}
    }}

    .kpi-gradient-warm {{
        background: {GRADIENTS['warm']};
        color: white;
        border-radius: {COLOR_TOKENS['border_radius']};
        padding: 24px;
        box-shadow: {COLOR_TOKENS['shadow_elevation_1']};
        border: none;
    }}
    
    .kpi-gradient-cool {{
        background: {GRADIENTS['cool']};
        color: white;
        border-radius: {COLOR_TOKENS['border_radius']};
        padding: 24px;
        box-shadow: {COLOR_TOKENS['shadow_elevation_1']};
        border: none;
    }}
    
    .metric-label {{
        color: rgba(255, 255, 255, 0.9);
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 8px;
    }}
    
    .bh-kpi-value {{
        display: flex;
        align-items: flex-end;
        gap: 6px;
        flex-wrap: wrap;
    }}

    .bh-kpi-value-main {{
        font-size: 32px;
        font-weight: 700;
        line-height: 1.1;
    }}

    .bh-kpi-unit {{
        font-size: 18px;
        font-weight: 600;
        opacity: 0.85;
    }}

    .bh-kpi-badge {{
        max-width: 100%;
        white-space: nowrap;
    }}
    
    .metric-value {{
        color: white;
        font-size: 42px;
        font-weight: 700;
        line-height: 1.2;
    }}
    
    /* ============================================
       COMPONENTES NATIVOS DE STREAMLIT
       ============================================ */
    /* Sidebar Frosted Glass */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.45) !important;
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.7) !important;
        box-shadow: 10px 0 30px rgba(0, 0, 0, 0.03) !important;
        color: #2D3748 !important;
    }}

    [data-testid="stSidebar"] > div {{
        background: transparent !important;
    }}
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stMarkdown {{
        color: #2D3748 !important;
        text-shadow: 0 1px 0 rgba(255, 255, 255, 0.8);
    }}

    [data-testid="collapsedControl"] {{
        display: none;
    }}
    
    /* Tabs */
    [data-baseweb="tab-list"] {{
        gap: 1rem !important;
    }}
    
    [data-baseweb="tab"] {{
        padding: 0.75rem 1.5rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        color: {COLOR_TOKENS['text_secondary']} !important;
    }}
    
    [data-baseweb="tab"][aria-selected="true"] {{
        color: {COLOR_TOKENS['accent_blue']} !important;
        font-weight: 600 !important;
    }}
    
    /* Inputs y Selectboxes en Sidebar */
    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stMultiSelect > div > div,
    [data-testid="stSidebar"] .stTextInput > div > div,
    [data-testid="stSidebar"] .stNumberInput > div > div,
    [data-testid="stSidebar"] .stTextArea > div > textarea,
    [data-testid="stSidebar"] .stSlider,
    [data-testid="stSidebar"] .stDateInput > div > div {{
        background-color: rgba(255, 255, 255, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 16px !important;
        color: #1A1A1A !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02) !important;
        backdrop-filter: none !important;
    }}

    .stSlider {{
        margin-top: 0.5rem;
    }}
    
    /* Expanders personalizados */
    .bh-expander {{
        background-color: {COLOR_TOKENS['bg_card']};
        border-radius: {COLOR_TOKENS['border_radius']};
        box-shadow: {COLOR_TOKENS['shadow_elevation_1']};
        margin-bottom: 1rem;
        border: none;
        overflow: hidden;
    }}

    .bh-expander summary {{
        padding: 16px 24px;
        cursor: pointer;
        font-weight: 600;
        color: {COLOR_TOKENS['text_primary']};
        list-style: none;
        position: relative;
    }}

    .bh-expander summary::-webkit-details-marker {{
        display: none;
    }}

    .bh-expander summary::after {{
        content: "›";
        position: absolute;
        right: 24px;
        top: 50%;
        transform: translateY(-50%) rotate(0deg);
        transition: transform 0.2s ease;
        color: {COLOR_TOKENS['text_secondary']};
        font-size: 18px;
    }}

    .bh-expander[open] summary::after {{
        transform: translateY(-50%) rotate(90deg);
    }}

    .bh-expander-content {{
        padding: 0 24px 24px 24px;
    }}

    .bh-expander-content h3 {{
        margin-top: 16px;
        margin-bottom: 8px;
        font-size: 16px;
        font-weight: 600;
        color: {COLOR_TOKENS['text_primary']};
    }}

    .bh-expander-content ul {{
        padding-left: 20px;
        color: {COLOR_TOKENS['text_primary']};
    }}

    .bh-expander-content table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 16px;
        font-size: 14px;
    }}

    .bh-expander-content th,
    .bh-expander-content td {{
        border: 1px solid #E0E0E0;
        padding: 8px 12px;
        text-align: left;
    }}

    .bh-expander-content th {{
        background-color: #F8F9FB;
        font-weight: 600;
    }}
    
    /* ============================================
       GRÁFICOS PLOTLY
       ============================================ */
    .js-plotly-plot .plotly .main-svg {{
        background: rgba(0,0,0,0) !important;
    }}
    
    /* ============================================
       BARRAS DE PROGRESO
       ============================================ */
    .progress-bar-container {{
        background-color: #F0F2F5;
        border-radius: 3px;
        height: 6px;
        overflow: hidden;
        margin: 8px 0;
    }}
    
    .progress-bar-fill {{
        background-color: {COLOR_TOKENS['accent_blue']};
        height: 100%;
        border-radius: 3px;
        transition: width 0.3s ease;
    }}
    
    /* ============================================
       ALERTAS Y MENSAJES
       ============================================ */
    [data-testid="stAlert"] {{
        border-radius: 12px !important;
        border: none !important;
    }}
    
    /* Info (accent-blue) */
    [data-testid="stAlert"][data-base="info"] {{
        background-color: rgba(47, 128, 237, 0.1) !important;
        border-left: 3px solid {COLOR_TOKENS['accent_blue']} !important;
    }}
    
    /* Warning (accent-red) */
    [data-testid="stAlert"][data-base="warning"] {{
        background-color: rgba(235, 87, 87, 0.1) !important;
        border-left: 3px solid {COLOR_TOKENS['accent_red']} !important;
    }}
    
    /* Success (accent-green) */
    [data-testid="stAlert"][data-base="success"] {{
        background-color: rgba(39, 174, 96, 0.1) !important;
        border-left: 3px solid {COLOR_TOKENS['accent_green']} !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_kpi_card(
    title: str,
    value: str | float | int,
    style: str = "white",
    delta: str | None = None,
    delta_color: str = "green",
    render: bool = True,
) -> str:
    """
    Renderiza una tarjeta KPI alineada con el Design System Kristin.
    
    Args:
        title: Título de la métrica
        value: Valor a mostrar (se formatea automáticamente)
        style: "white", "warm", o "cool"
        delta: Texto opcional para la etiqueta/badge
        delta_color: "green" o "red" (solo aplica en tarjetas white)
        render: Si True, se imprime en Streamlit; si False, retorna el HTML
    """
    # Formatear valor - si es string, usarlo directamente; si es número, formatearlo
    if isinstance(value, (int, float)):
        if value >= 1000:
            value_str = f"{value:,.0f}"
        else:
            value_str = f"{value:.0f}"  # Sin decimales para números pequeños
    else:
        value_str = str(value)  # Strings se usan tal cual (ej: "34,787 €")
    
    # Determinar estilos según tipo de tarjeta
    if style == "warm":
        bg_card = GRADIENTS["warm"]
        color_title = "rgba(255, 255, 255, 0.9)"
        color_value = "#FFFFFF"
        badge_base = (
            "background: rgba(255, 255, 255, 0.25); "
            "backdrop-filter: blur(10px); "
            "border: 1px solid rgba(255, 255, 255, 0.35); "
            "color: #FFFFFF;"
        )
    elif style == "cool":
        bg_card = GRADIENTS["cool"]
        color_title = "rgba(255, 255, 255, 0.9)"
        color_value = "#FFFFFF"
        badge_base = (
            "background: rgba(255, 255, 255, 0.25); "
            "backdrop-filter: blur(10px); "
            "border: 1px solid rgba(255, 255, 255, 0.35); "
            "color: #FFFFFF;"
        )
    else:  # white
        bg_card = COLOR_TOKENS["bg_card"]
        color_title = COLOR_TOKENS["text_secondary"]
        color_value = COLOR_TOKENS["text_primary"]
        if delta_color == "green":
            badge_base = (
                "background: #E8F8F0; "
                f"color: {COLOR_TOKENS['accent_green']};"
            )
        else:
            badge_base = (
                "background: #FFE8E8; "
                f"color: {COLOR_TOKENS['accent_red']};"
            )
    
    # Construir HTML completo de forma segura
    unit_block = ""
    base_value = value_str
    if "/" in value_str:
        base_value, unit = value_str.split("/", 1)
        base_value = base_value.strip()
        unit_block = (
            f'<span style="font-size: 18px; font-weight: 600; margin-left: 6px; '
            f'color: {color_value}; opacity: 0.85;">/{unit.strip()}</span>'
        )

    value_block = (
        f'<div style="font-size: 32px; font-weight: 700; color: {color_value}; '
        f'margin-bottom: 8px; line-height: 1.1; font-family: Inter, sans-serif; '
        f'white-space: nowrap;">{base_value}{unit_block}</div>'
    )
    if delta:
        badge_part = (
            f'\n    <div class="bh-kpi-badge" style="display: inline-block; padding: 4px 12px; '
            f'border-radius: 12px; font-size: 12px; font-weight: 600; font-family: Inter, sans-serif; '
            f'{badge_base}">{delta}</div>'
        )
    else:
        badge_part = ""
    
    html = dedent(
        f"""\
<div class="bh-kpi-card" style="background: {bg_card}; padding: 24px; border-radius: 24px; box-shadow: {COLOR_TOKENS['shadow_elevation_1']}; font-family: Inter, sans-serif; border: none;">
  <div style="font-size: 14px; font-weight: 500; color: {color_title}; font-family: Inter, sans-serif; line-height: 1.4;">{title}</div>
  <div>
    {value_block}{badge_part}
  </div>
</div>
"""
    ).strip()
    
    if render:
        st.markdown(html, unsafe_allow_html=True)
        return ""

    return html


def render_responsive_kpi_grid(metrics_data: list[dict[str, str]]) -> None:
    """
    Renderiza un grid responsive de tarjetas KPI usando CSS Grid.

    Args:
        metrics_data: lista de diccionarios con llaves title, value, style, delta, delta_color
    """
    cards_html: list[str] = []
    for metric in metrics_data:
        cards_html.append(
            render_kpi_card(
                title=metric.get("title", ""),
                value=metric.get("value", ""),
                style=metric.get("style", "white"),
                delta=metric.get("delta"),
                delta_color=metric.get("delta_color", "green"),
                render=False,
            )
        )

    grid_style = (
        "display: grid; "
        "grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); "
        "gap: 24px; margin-bottom: 30px;"
    )
    st.markdown(
        f'<div class="bh-kpi-grid" style="{grid_style}">{"".join(cards_html)}</div>',
        unsafe_allow_html=True,
    )


def render_gradient_kpi(
    title: str,
    value: str | float | int,
    gradient: str = "cool",
    delta: str | None = None,
) -> None:
    """
    Renderiza una tarjeta KPI con gradiente mesh (alias para compatibilidad).
    
    Args:
        title: Título de la métrica
        value: Valor a mostrar (se formatea automáticamente)
        gradient: "warm" o "cool"
        delta: Texto opcional para mostrar debajo del valor
    """
    render_kpi_card(title, value, style=gradient, delta=delta)


def render_ranking_item(
    name: str,
    value: float | int | str,
    max_value: float | None = None,
    trend: str | None = None,
    show_percentage: bool = False,
    color: str = "accent",
    progress_value: float | None = None,
    value_display: str | None = None,
) -> None:
    """
    Renderiza un item de ranking con barra de progreso.
    
    Args:
        name: Nombre del barrio
        value: Valor numérico
        max_value: Valor máximo para calcular el porcentaje de la barra
        trend: "up", "down" o None para mostrar icono de tendencia
        show_percentage: Si mostrar el valor como porcentaje
    """
    color_map = {
        "accent": COLOR_TOKENS["accent_blue"],
        "blue": COLOR_TOKENS["accent_blue"],
        "red": COLOR_TOKENS["accent_red"],
        "green": COLOR_TOKENS["accent_green"],
    }
    bar_color = color_map.get(color, COLOR_TOKENS["accent_blue"])
    
    numeric_value: float | None
    if isinstance(value, (int, float)):
        numeric_value = float(value)
    else:
        try:
            numeric_value = float(
                str(value)
                .replace("€", "")
                .replace("k", "")
                .replace("%", "")
                .replace(",", "")
                .strip()
            )
            if "k" in str(value).lower():
                numeric_value *= 1000
        except ValueError:
            numeric_value = None
    
    if progress_value is not None:
        percentage = max(0, min(100, progress_value))
    elif max_value and max_value > 0 and numeric_value is not None:
        percentage = (numeric_value / max_value) * 100
    else:
        percentage = 0
    
    if value_display:
        value_str = value_display
    elif show_percentage and numeric_value is not None:
        value_str = f"{numeric_value:.1f}%"
    elif numeric_value is not None:
        value_str = f"{numeric_value:,.0f}" if numeric_value >= 1000 else f"{numeric_value:.1f}"
    else:
        value_str = str(value)
    
    trend_icon = ""
    if trend == "up":
        trend_icon = "📈"
    elif trend == "down":
        trend_icon = "📉"
    
    html = f"""
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #F0F2F5;">
        <div style="flex: 1; color: {COLOR_TOKENS['text_primary']}; font-weight: 500;">
            {name} {trend_icon}
        </div>
        <div style="flex: 2; margin: 0 16px;">
            <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: {percentage}%; background-color: {bar_color};"></div>
            </div>
        </div>
        <div style="flex: 0 0 80px; text-align: right; color: {COLOR_TOKENS['text_primary']}; font-weight: 600;">
            {value_str}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def apply_plotly_theme(fig) -> None:
    """
    Aplica el tema del Design System a un gráfico Plotly.
    
    Args:
        fig: Figura de Plotly a modificar
    """
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color=COLOR_TOKENS["text_primary"]),
        xaxis=dict(
            gridcolor="#E0E0E0",
            gridwidth=1,
            showgrid=True,
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor="#E0E0E0",
            gridwidth=1,
            showgrid=True,
            zeroline=False,
        ),
        margin=dict(l=20, r=20, t=40, b=20),
    )

