"""
Barcelona Housing Analytics - Component Library
Implementación de los componentes del Design System "Kristin".
"""

from __future__ import annotations

import streamlit as st
from contextlib import contextmanager
from typing import Any, Generator, Literal

from src.app.styles import COLOR_TOKENS, GRADIENTS


@contextmanager
def card_standard(
    title: str | None = None,
    subtitle: str | None = None,
    badge: str | None = None,
    badge_color: str = "blue",
    action_label: str | None = None,
    action_key: str | None = None,
    padding: str = "24px",
    key: str | None = None,
) -> Generator[Any, None, None]:
    """
    Componente: StandardCard (Contenedor Base) - Versión Refinada

    Mejoras:
    - Badge opcional en el header
    - Botón de acción opcional
    - Padding configurable
    - Mejor separación visual

    Args:
        title: Título principal de la tarjeta
        subtitle: Subtítulo opcional
        badge: Texto del badge opcional
        badge_color: Color del badge ("blue", "green", "red", "orange")
        action_label: Etiqueta del botón de acción opcional
        action_key: Clave única para el botón de acción
        padding: Padding personalizado (por defecto "24px")
        key: Clave única para el componente (reservado para uso futuro)

    Uso:
        with card_standard(
            title="Análisis Temporal",
            subtitle="Evolución 2015-2025",
            badge="Nuevo",
            action_label="Exportar",
            action_key="export_btn"
        ):
            st.plotly_chart(fig)
    """
    badge_colors = {
        "blue": (COLOR_TOKENS["accent_blue"], "rgba(47, 128, 237, 0.1)"),
        "green": (COLOR_TOKENS["accent_green"], "rgba(39, 174, 96, 0.1)"),
        "red": (COLOR_TOKENS["accent_red"], "rgba(235, 87, 87, 0.1)"),
        "orange": ("#F2994A", "rgba(242, 153, 74, 0.1)"),
    }

    # Construir HTML del header
    html_parts = [f'<div class="card" style="padding: {padding};">']

    # Renderizar header si hay título, subtítulo, badge o acción
    if title or subtitle or badge or action_label:
        html_parts.append(
            '<div class="card-header" style="display: flex; align-items: start; '
            'justify-content: space-between; margin-bottom: 20px;">'
        )
        html_parts.append('<div style="flex: 1;">')

        # Título con badge
        if title:
            title_line = (
                '<div class="card-title" style="display: flex; align-items: center; gap: 10px;">'
                f'{title}'
            )
            if badge:
                color, bg = badge_colors.get(badge_color, badge_colors["blue"])
                title_line += f'''
                    <span style="
                        font-size: 11px;
                        font-weight: 600;
                        padding: 3px 8px;
                        border-radius: 12px;
                        background: {bg};
                        color: {color};
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    ">{badge}</span>
                '''
            title_line += '</div>'
            html_parts.append(title_line)

        if subtitle:
            html_parts.append(
                f'<div class="card-subtitle" style="margin-top: 4px;">{subtitle}</div>'
            )

        html_parts.append('</div>')  # Cierra div de título/subtítulo

        # Si hay botón de acción, renderizar header y luego el botón
        if action_label and action_key:
            html_parts.append('</div>')  # Cierra card-header
            # Renderizar HTML del header
            st.markdown(''.join(html_parts), unsafe_allow_html=True)

            # Renderizar botón de acción usando columnas de Streamlit para alinearlo a la derecha
            # El botón se posiciona visualmente después del header
            col_spacer, col_btn = st.columns([4, 1])
            with col_btn:
                if st.button(action_label, key=action_key, type="secondary"):
                    st.session_state[f"{action_key}_clicked"] = True

            # Iniciar el body del card
            st.markdown('<div class="card-body">', unsafe_allow_html=True)
        else:
            html_parts.append('</div>')  # Cierra card-header
            # Renderizar HTML completo del header
            st.markdown(''.join(html_parts), unsafe_allow_html=True)
            # Iniciar el body del card
            st.markdown('<div class="card-body">', unsafe_allow_html=True)
    else:
        # Si no hay header, solo iniciar el card y el body
        st.markdown(''.join(html_parts), unsafe_allow_html=True)
        st.markdown('<div class="card-body">', unsafe_allow_html=True)

    # Contenedor para el contenido del with
    yield

    # Cerrar body y card
    st.markdown('</div></div>', unsafe_allow_html=True)


@contextmanager
def card_chart(
    title: str,
    subtitle: str | None = None,
    footer: str | None = None,
    key: str | None = None,
) -> Generator[Any, None, None]:
    """
    Componente: ChartCard (Visualizaciones)
    Tarjeta optimizada para contener gráficos de Plotly.
    """
    # Header
    html_start = '<div class="card card-chart"><div class="card-header">'
    html_start += f'<div class="card-title">{title}</div>'
    if subtitle:
        html_start += f'<div class="card-subtitle">{subtitle}</div>'
    html_start += '</div>'
    
    st.markdown(html_start, unsafe_allow_html=True)
    
    yield
    
    # Footer
    if footer:
        st.markdown(
            f'<div class="card-footer"><span>{footer}</span></div>',
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)


@contextmanager
def card_snapshot(
    image_url: str | None = None,
    title: str | None = None,
    badge_text: str | None = None,
    actions: list[dict[str, str]] | None = None,
    key: str | None = None,
) -> Generator[Any, None, None]:
    """
    Componente: SnapshotCard (Mapas/Imágenes)
    Tarjeta sin padding para mapas o imágenes full-width.
    
    Args:
        image_url: URL opcional de imagen de fondo (si no se usa contenido interno)
        actions: Lista de dicts [{'label': 'Ver', 'type': 'primary'}]
    """
    st.markdown('<div class="card card-snapshot">', unsafe_allow_html=True)
    
    # Area de imagen/contenido
    st.markdown('<div class="snapshot-image-area">', unsafe_allow_html=True)
    
    # Si hay imagen estática
    if image_url:
        st.markdown(f'<img src="{image_url}" alt="Snapshot">', unsafe_allow_html=True)
    
    # Badge superpuesto
    if badge_text:
        st.markdown(
            f'<div style="position: absolute; top:1rem; right:1rem; background:white; '
            f'padding:4px 12px; border-radius:20px; font-size:0.75rem; font-weight:600; '
            f'box-shadow:0 2px 4px rgba(0,0,0,0.1); z-index:10;">{badge_text}</div>',
            unsafe_allow_html=True
        )
    
    # Aquí se renderiza el contenido del 'with' (ej. un mapa Plotly estático)
    yield
    
    st.markdown('</div>', unsafe_allow_html=True)  # Cierra snapshot-image-area
    
    # Action Area
    if title or actions:
        html_actions = '<div class="snapshot-actions">'
        if title:
            html_actions += f'<div style="font-size:0.9rem; font-weight:600;">{title}</div>'
        
        if actions:
            html_actions += '<div>'
            # Nota: Los botones HTML puros no ejecutan Python. 
            # Para interactividad real, usamos st.button dentro del yield o componentes nativos.
            # Esta sección es visual si se usa HTML, o contenedores para st.button.
            pass 
        html_actions += '</div></div>'
        
        st.markdown(html_actions, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Cierra card


def card_metric(
    label: str,
    value: str | float | int,
    subvalue: str | None = None,
    trend: str | None = None,
    trend_color: Literal["green", "red", "neutral"] = "green",
    style: Literal["solid", "warm", "cool"] = "solid",
    badge_text: str | None = None,
) -> None:
    """
    Componente: MetricCard (KPIs)
    Variante A (Solid) o B (Mesh/Gradient).
    """
    # Formateo básico de valor
    display_value = f"{value:,.0f}" if isinstance(value, (int, float)) and value > 1000 else str(value)
    
    if style == "solid":
        # Variant A: Solid
        badge_html = ""
        if badge_text:
            badge_class = "metric-badge green" if trend_color == "green" else "metric-badge"
            badge_html = f'<span class="{badge_class}">{badge_text}</span>'
        
        trend_html = ""
        if subvalue:
            color = "var(--text-muted)"
            if trend:
                color = "#166534" if trend_color == "green" else "#dc2626"
            trend_html = f'<div class="card-subtitle" style="font-size: 0.8rem;"><span style="color: {color}; font-weight:600;">{trend or ""}</span> {subvalue}</div>'

        html = f"""
        <div class="card card-metric-solid">
            <div>
                <div class="metric-label" style="color: var(--text-muted); margin-bottom:0;">{label}</div>
                {badge_html}
            </div>
            <div class="metric-value">{display_value}</div>
            {trend_html}
        </div>
        """
        
    else:
        # Variant B: Mesh (Gradient)
        gradient_class = "card-metric-mesh cool" if style == "cool" else "card-metric-mesh"
        
        html = f"""
        <div class="card {gradient_class}">
            <div class="card-header" style="margin-bottom:0.5rem;">
                <div class="card-title">{label}</div>
                <div class="card-subtitle">{subvalue or ""}</div>
            </div>
            <div class="metric-value">{display_value}</div>
            <!-- Sparkline Placeholder (Visual) -->
            <svg class="sparkline-area" viewBox="0 0 100 30" preserveAspectRatio="none" style="width:100%; height:40px; opacity:0.5;">
                <path class="sparkline-path" d="M0,25 Q10,25 20,15 T40,15 T60,5 T80,10 T100,2" style="stroke:white; fill:none; stroke-width:2;" />
            </svg>
        </div>
        """
    
    st.markdown(html, unsafe_allow_html=True)


def card_profile(
    title: str,
    subtitle: str,
    image_url: str | None = None,
    tags: list[str] | None = None,
    data_points: dict[str, str] | None = None,
) -> None:
    """
    Componente: ProfileCard (Ficha de Barrio)
    Layout de dos columnas para entidades.
    """
    img_src = image_url if image_url else "https://images.unsplash.com/photo-1583422409516-2895a77efded?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80"
    
    tags_html = ""
    if tags:
        tags_html = '<div class="profile-tags">' + "".join([f'<span class="tag">{tag}</span>' for tag in tags]) + '</div>'
    
    data_html = ""
    if data_points:
        data_html = '<div class="profile-right">'
        for label, value in data_points.items():
            data_html += f"""
            <div class="data-point">
                <label>{label}</label>
                <span>{value}</span>
            </div>
            """
        data_html += '</div>'

    html = f"""
    <div class="card card-profile-wide">
        <div class="profile-left">
            <img src="{img_src}" alt="{title}" class="profile-img">
            <div class="card-title">{title}</div>
            <div class="card-subtitle">{subtitle}</div>
            {tags_html}
        </div>
        {data_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def show_notification(message: str, type: str = "info", duration: int = 3000) -> None:
    """
    Muestra notificación toast con estilo Soft UI.
    
    Args:
        message: Texto a mostrar
        type: "info", "success", "warning", "error"
        duration: Duración en milisegundos
    """
    colors = {
        "info": ("#2F80ED", "#EBF5FF"),
        "success": ("#27AE60", "#E8F8F0"),
        "warning": ("#F2994A", "#FFF4E6"),
        "error": ("#EB5757", "#FFE8E8"),
    }
    
    icon_map = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
    }
    
    color, bg = colors.get(type, colors["info"])
    icon = icon_map.get(type, "ℹ️")
    
    st.markdown(
        f"""
        <div style="
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            background: {bg};
            border-left: 4px solid {color};
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            animation: slideInRight 0.4s ease-out, fadeOut 0.5s {duration/1000 - 0.5}s forwards;
            max-width: 350px;
        ">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 20px;">{icon}</span>
                <span style="color: #1A1A1A; font-weight: 500; font-size: 14px;">{message}</span>
            </div>
        </div>
        <style>
        @keyframes slideInRight {{
            from {{ transform: translateX(400px); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        @keyframes fadeOut {{
            from {{ opacity: 1; }}
            to {{ opacity: 0; }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def render_empty_state(
    icon: str = "📊",
    title: str = "No hay datos disponibles",
    description: str = "Intenta ajustar los filtros o seleccionar otro período",
    action_label: str | None = None,
    action_key: str | None = None
) -> None:
    """Renderiza un estado vacío elegante."""
    
    action_button = ""
    if action_label and action_key:
        action_button = f"""
        <button onclick="alert('Redirigiendo...')" style="
            margin-top: 20px;
            padding: 10px 24px;
            background: linear-gradient(135deg, #2F80ED 0%, #56CCF2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: transform 0.2s;
        " onmouseover="this.style.transform='translateY(-2px)'" 
           onmouseout="this.style.transform='translateY(0)'">
            {action_label}
        </button>
        """
    
    st.markdown(
        f"""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 80px 40px;
            background: {COLOR_TOKENS['bg_card']};
            border-radius: 24px;
            box-shadow: {COLOR_TOKENS['shadow_elevation_1']};
        ">
            <div style="font-size: 64px; opacity: 0.3; margin-bottom: 20px;">{icon}</div>
            <h3 style="color: {COLOR_TOKENS['text_primary']}; margin: 0 0 8px 0;">{title}</h3>
            <p style="color: {COLOR_TOKENS['text_secondary']}; margin: 0; text-align: center; max-width: 400px;">
                {description}
            </p>
            {action_button}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_skeleton_kpi(count: int = 4) -> None:
    """Muestra skeleton loaders para KPIs."""
    html = '<div class="bh-kpi-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px;">'
    
    for _ in range(count):
        html += f"""
        <div class="bh-kpi-card" style="
            background: {COLOR_TOKENS['bg_card']};
            padding: 24px;
            border-radius: 24px;
            box-shadow: {COLOR_TOKENS['shadow_elevation_1']};
        ">
            <div class="skeleton" style="width: 60%; height: 14px; margin-bottom: 16px;"></div>
            <div class="skeleton" style="width: 80%; height: 32px; margin-bottom: 8px;"></div>
            <div class="skeleton" style="width: 40%; height: 12px;"></div>
        </div>
        """
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_breadcrumbs(crumbs: list[dict[str, str]]) -> None:
    """
    Renderiza una barra de navegación tipo breadcrumbs.
    
    Args:
        crumbs: Lista de diccionarios con 'label' y 'path' (o 'action').
                Ej: [{'label': 'Home', 'path': 'home'}, {'label': 'Market', 'path': 'market'}]
    """
    html = '<div class="bh-breadcrumbs">'
    
    for i, crumb in enumerate(crumbs):
        is_last = i == len(crumbs) - 1
        label = crumb.get("label", "")
        
        html += '<div class="bh-breadcrumbs-item">'
        
        if is_last:
            html += f'<span class="bh-breadcrumbs-active">{label}</span>'
        else:
            # Nota: En Streamlit puro, los enlaces reales requieren query params o componentes extra.
            # Aquí usamos un estilo visual. Si se requiere navegación real, se podría usar st.button
            # pero rompería el flujo visual HTML. Por ahora es visual/informativo.
            html += f'<span class="bh-breadcrumbs-link">{label}</span>'
            html += '<span class="bh-breadcrumbs-separator">/</span>'
            
        html += '</div>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
