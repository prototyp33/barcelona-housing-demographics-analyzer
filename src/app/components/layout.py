"""
Layout Components for Barcelona Housing Analytics
Provides standardized page headers, section titles, and grid layouts.
"""

import streamlit as st
from src.app.design_system import COLORS, SPACING, FONTS


def render_page_header(
    title: str,
    subtitle: str = None,
    breadcrumbs: list = None,
    icon: str = None
) -> None:
    """
    Renders a consistent page header with optional breadcrumbs.
    
    Args:
        title: Main H1 title
        subtitle: Optional description
        breadcrumbs: List of strings e.g. ["Home", "Analytics", "Market"]
        icon: Optional emoji icon
    """
    # Breadcrumbs
    if breadcrumbs:
        crumb_html = " › ".join([
            f'<span style="opacity: 0.7;">{b}</span>' for b in breadcrumbs
        ])
        st.markdown(
            f'<div style="font-size: 12px; color: {COLORS["text"]["secondary"]}; '
            f'margin-bottom: {SPACING["xs"]};">{crumb_html}</div>',
            unsafe_allow_html=True
        )
    
    # Title with optional icon
    icon_html = f'<span style="margin-right: 12px;">{icon}</span>' if icon else ""
    st.markdown(
        f'<h1 style="{FONTS["h1_css"]}">{icon_html}{title}</h1>',
        unsafe_allow_html=True
    )
    
    # Subtitle
    if subtitle:
        st.markdown(
            f'<p style="{FONTS["caption_css"]} margin-bottom: {SPACING["xl"]};">{subtitle}</p>',
            unsafe_allow_html=True
        )
    
    # Divider
    st.markdown("---")


def render_section_header(
    title: str,
    icon: str = None,
    subtitle: str = None
) -> None:
    """
    Renders a standard H2 section header.
    
    Args:
        title: Section title
        icon: Optional emoji icon
        subtitle: Optional description
    """
    icon_html = f'<span style="margin-right: 8px;">{icon}</span>' if icon else ""
    
    st.markdown(
        f'<h2 style="{FONTS["h2_css"]}">{icon_html}{title}</h2>',
        unsafe_allow_html=True
    )
    
    if subtitle:
        st.markdown(
            f'<p style="{FONTS["caption_css"]} margin-bottom: {SPACING["md"]};">{subtitle}</p>',
            unsafe_allow_html=True
        )


def render_subsection_header(title: str, icon: str = None) -> None:
    """
    Renders a standard H3 subsection header.
    
    Args:
        title: Subsection title
        icon: Optional emoji icon
    """
    icon_html = f'<span style="margin-right: 8px;">{icon}</span>' if icon else ""
    
    st.markdown(
        f'<h3 style="{FONTS["h3_css"]}">{icon_html}{title}</h3>',
        unsafe_allow_html=True
    )


def create_metric_grid(num_columns: int = 4, gap: str = "medium"):
    """
    Creates a responsive grid for metrics/KPIs.
    
    Args:
        num_columns: Number of columns (2, 3, or 4)
        gap: Column gap ('small', 'medium', 'large')
    
    Returns:
        Streamlit columns object
    """
    return st.columns(num_columns, gap=gap)


def create_two_column_layout(left_ratio: float = 1.5, gap: str = "large"):
    """
    Creates a two-column layout with custom ratio.
    
    Args:
        left_ratio: Ratio for left column (e.g., 1.5 means 60/40 split)
        gap: Column gap
    
    Returns:
        Tuple of (left_column, right_column)
    """
    col_left, col_right = st.columns([left_ratio, 1], gap=gap)
    return col_left, col_right


def render_spacer(size: str = "md") -> None:
    """
    Renders a vertical spacer.
    
    Args:
        size: 'xs', 'sm', 'md', 'lg', 'xl', 'xxl'
    """
    spacing_value = SPACING.get(size, SPACING['md'])
    st.markdown(f'<div style="margin: {spacing_value} 0;"></div>', unsafe_allow_html=True)


def render_divider(margin: str = "md") -> None:
    """
    Renders a horizontal divider with custom margin.
    
    Args:
        margin: Margin size ('xs', 'sm', 'md', 'lg', 'xl')
    """
    margin_value = SPACING.get(margin, SPACING['md'])
    st.markdown(
        f'<hr style="border: none; border-top: 1px solid #E5E7EB; '
        f'margin: {margin_value} 0;">',
        unsafe_allow_html=True
    )


def render_card_container(content_func, padding: str = "lg", shadow: bool = True):
    """
    Wraps content in a card container.
    
    Args:
        content_func: Function that renders the content
        padding: Padding size
        shadow: Whether to show shadow
    """
    padding_value = SPACING.get(padding, SPACING['lg'])
    shadow_css = "box-shadow: 0 2px 12px rgba(0,0,0,0.08);" if shadow else ""
    
    st.markdown(
        f'<div style="background: white; padding: {padding_value}; '
        f'border-radius: 16px; {shadow_css} border: 1px solid #F3F4F6;">',
        unsafe_allow_html=True
    )
    
    content_func()
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_hero_section(
    title: str,
    subtitle: str,
    background_gradient: bool = True
) -> None:
    """
    Renders a hero section with gradient background.
    
    Args:
        title: Hero title
        subtitle: Hero subtitle
        background_gradient: Use gradient background
    """
    if background_gradient:
        bg_style = f"background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);"
    else:
        bg_style = f"background: {COLORS['primary']};"
    
    st.markdown(f"""
    <div style="{bg_style}
                padding: 48px 40px;
                border-radius: 20px;
                margin-bottom: 40px;
                box-shadow: 0 10px 30px rgba(47, 128, 237, 0.25);">
        <h1 style="color: white; font-size: 42px; font-weight: 800; margin: 0 0 12px 0;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            {title}
        </h1>
        <p style="color: rgba(255,255,255,0.95); font-size: 18px; margin: 0; font-weight: 500;">
            {subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)
