"""
Reusable Card Components for Barcelona Housing Analytics
Provides standardized KPI cards, info cards, and other UI elements.
"""

import streamlit as st
from src.app.design_system import COLORS, SPACING, FONTS


def render_kpi_card(
    title: str,
    value: str,
    delta: str = None,
    help_text: str = None,
    icon: str = None,
    color_scheme: str = "primary"
) -> None:
    """
    Renders a consistent KPI card with optional delta and help text.
    
    Args:
        title: Card title/label
        value: Main value to display
        delta: Optional change indicator (e.g., "+5.2%")
        help_text: Optional tooltip text
        icon: Optional emoji icon
        color_scheme: 'primary', 'secondary', 'success', 'warning', 'neutral'
    """
    # Determine colors based on scheme
    color_map = {
        'primary': COLORS['primary'],
        'secondary': COLORS['secondary'],
        'success': COLORS['accent_green'],
        'warning': COLORS['accent_yellow'],
        'danger': COLORS['accent_red'],
        'neutral': COLORS['text']['secondary']
    }
    
    accent_color = color_map.get(color_scheme, COLORS['primary'])
    
    # Delta styling
    delta_html = ""
    if delta:
        delta_color = COLORS['accent_green'] if "+" in delta or "↗" in delta else COLORS['accent_red']
        delta_html = '<div style="font-size: 14px; font-weight: 600; color: ' + delta_color + '; margin-top: 8px;">' + str(delta) + '</div>'
    
    # Icon
    icon_html = '<span style="font-size: 20px; margin-right: 8px;">' + str(icon) + '</span>' if icon else ""
    
    # Tooltip
    tooltip_attr = 'title="' + str(help_text) + '"' if help_text else ""
    
    # Ensure value is a clean string
    value_str = str(value).strip()
    title_str = str(title).strip()
    
    # Build HTML using string concatenation to avoid f-string issues
    html_parts = []
    html_parts.append('<div ' + tooltip_attr + ' style="')
    html_parts.append('min-height: 140px;')
    html_parts.append('display: flex;')
    html_parts.append('flex-direction: column;')
    html_parts.append('justify-content: space-between;')
    html_parts.append('background: linear-gradient(135deg, ' + accent_color + '15 0%, ' + accent_color + '05 100%);')
    html_parts.append('border-left: 4px solid ' + accent_color + ';')
    html_parts.append('border-radius: 16px;')
    html_parts.append('padding: 24px;')
    html_parts.append('box-shadow: 0 2px 8px rgba(0,0,0,0.06);')
    html_parts.append('transition: transform 0.2s ease, box-shadow 0.2s ease;')
    html_parts.append('cursor: pointer;')
    html_parts.append('" onmouseover="this.style.transform=\'translateY(-4px)\'; this.style.boxShadow=\'0 4px 16px rgba(0,0,0,0.12)\';"')
    html_parts.append(' onmouseout="this.style.transform=\'translateY(0)\'; this.style.boxShadow=\'0 2px 8px rgba(0,0,0,0.06)\';">')
    
    # Title section
    html_parts.append('<div style="font-size: 12px; color: ' + COLORS['text']['secondary'] + ';')
    html_parts.append('font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px;">')
    html_parts.append(icon_html + title_str)
    html_parts.append('</div>')
    
    # Value section
    html_parts.append('<div>')
    html_parts.append('<div style="font-size: 36px; font-weight: 800; color: ' + accent_color + ';')
    html_parts.append('line-height: 1; margin-bottom: 4px;">')
    html_parts.append(value_str)
    html_parts.append('</div>')
    html_parts.append(delta_html)
    html_parts.append('</div>')
    
    html_parts.append('</div>')
    
    html_content = ''.join(html_parts)
    st.markdown(html_content, unsafe_allow_html=True)


def render_info_card(
    title: str,
    content: str,
    icon: str = "ℹ️",
    card_type: str = "info"
) -> None:
    """
    Renders an information/callout card.
    
    Args:
        title: Card title
        content: Main content text (can include HTML)
        icon: Emoji icon
        card_type: 'info', 'success', 'warning', 'danger'
    """
    type_colors = {
        'info': COLORS['primary'],
        'success': COLORS['accent_green'],
        'warning': COLORS['accent_yellow'],
        'danger': COLORS['accent_red']
    }
    
    border_color = type_colors.get(card_type, COLORS['primary'])
    
    # Build HTML using concatenation to avoid f-string issues
    html_parts = []
    html_parts.append('<div style="')
    html_parts.append('background: white;')
    html_parts.append('border-left: 4px solid ' + border_color + ';')
    html_parts.append('padding: ' + SPACING['lg'] + ';')
    html_parts.append('border-radius: 12px;')
    html_parts.append('margin-bottom: ' + SPACING['lg'] + ';')
    html_parts.append('box-shadow: 0 2px 8px rgba(0,0,0,0.06);')
    html_parts.append('">')
    
    # Title section
    html_parts.append('<div style="font-size: 18px; font-weight: 700; color: ' + COLORS['text']['primary'] + ';')
    html_parts.append('display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">')
    html_parts.append('<span>' + str(icon) + '</span>')
    html_parts.append('<span>' + str(title) + '</span>')
    html_parts.append('</div>')
    
    # Content section
    html_parts.append('<div style="font-size: 14px; color: ' + COLORS['text']['secondary'] + '; line-height: 1.6;">')
    html_parts.append(content)  # Content can contain HTML
    html_parts.append('</div>')
    
    html_parts.append('</div>')
    
    html_content = ''.join(html_parts)
    st.markdown(html_content, unsafe_allow_html=True)


def render_stat_card(
    label: str,
    value: str,
    sublabel: str = None,
    compact: bool = False
) -> None:
    """
    Renders a simple stat card (smaller than KPI card).
    
    Args:
        label: Stat label
        value: Stat value
        sublabel: Optional secondary label
        compact: If True, uses smaller padding
    """
    padding = SPACING['md'] if compact else SPACING['lg']
    sublabel_html = f'<div style="font-size: 12px; color: {COLORS["text"]["secondary"]}; margin-top: 4px;">{sublabel}</div>' if sublabel else ""
    
    st.markdown(f"""
    <div style="
        background: white;
        padding: {padding};
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        text-align: center;
        border: 1px solid #E5E7EB;
    ">
        <div style="font-size: 13px; color: {COLORS['text']['secondary']}; 
                   font-weight: 600; margin-bottom: 8px; text-transform: uppercase;">
            {label}
        </div>
        <div style="font-size: 28px; font-weight: 800; color: {COLORS['text']['primary']};">
            {value}
        </div>
        {sublabel_html}
    </div>
    """, unsafe_allow_html=True)


def render_metric_row(metrics: list) -> None:
    """
    Renders a row of metrics in equal columns.
    
    Args:
        metrics: List of dicts with keys: 'label', 'value', 'sublabel' (optional)
    """
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            render_stat_card(
                label=metric.get('label', ''),
                value=metric.get('value', ''),
                sublabel=metric.get('sublabel'),
                compact=True
            )


def card_standard(title: str = None, subtitle: str = None, padding: str = "24px"):
    """
    A context manager for creating a standard card container.
    
    Args:
        title: Optional card title
        subtitle: Optional card subtitle
        padding: Card padding (default: 24px)
    
    Usage:
        with card_standard(title="My Card"):
            st.write("Card content")
    """
    from contextlib import contextmanager
    
    @contextmanager
    def _card():
        # Header
        if title or subtitle:
            header_html = ""
            if title:
                header_html += f'<h3 style="font-size: 18px; font-weight: 700; color: {COLORS["text"]["primary"]}; margin: 0 0 4px 0;">{title}</h3>'
            if subtitle:
                header_html += f'<p style="font-size: 14px; color: {COLORS["text"]["secondary"]}; margin: 0 0 16px 0;">{subtitle}</p>'
            
            st.markdown(header_html, unsafe_allow_html=True)
        
        # Content container
        container = st.container()
        yield container
    
    return _card()


def render_empty_state(
    title: str = "No hay datos disponibles",
    description: str = "No se encontraron datos para los filtros seleccionados.",
    icon: str = "📂"
) -> None:
    """
    Renders a consistent 'No Data' / empty state message.
    
    Args:
        title: Empty state title
        description: Empty state description
        icon: Emoji icon to display
    """
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: {SPACING['xl']};
        background-color: rgba(0,0,0,0.02);
        border: 2px dashed #E5E7EB;
        border-radius: 12px;
        margin: {SPACING['lg']} 0;
    ">
        <div style="font-size: 48px; margin-bottom: {SPACING['md']}; opacity: 0.5;">
            {icon}
        </div>
        <div style="font-size: 18px; font-weight: 600; color: {COLORS['text']['primary']}; 
                   margin-bottom: {SPACING['sm']};">
            {title}
        </div>
        <div style="font-size: 14px; color: {COLORS['text']['secondary']};">
            {description}
        </div>
    </div>
    """, unsafe_allow_html=True)

