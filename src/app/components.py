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
    key: str | None = None,
) -> Generator[Any, None, None]:
    """
    Componente: StandardCard (Contenedor Base)
    Bloque constructor fundamental con padding y sombra suave.
    
    Uso:
        with card_standard(title="Título", subtitle="Descripción"):
            st.write("Contenido...")
    """
    html_start = '<div class="card">'
    
    if title or subtitle:
        html_start += '<div class="card-header">'
        if title:
            html_start += f'<div class="card-title">{title}</div>'
        if subtitle:
            html_start += f'<div class="card-subtitle">{subtitle}</div>'
        html_start += '</div>'
    
    st.markdown(html_start, unsafe_allow_html=True)
    
    yield
    
    st.markdown('</div>', unsafe_allow_html=True)


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

