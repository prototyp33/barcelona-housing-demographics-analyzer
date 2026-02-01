"""
Reusable UI Components for Barcelona Housing Analytics

This package provides standardized, reusable components that follow
the design system defined in design_system.py.

Components:
- cards: KPI cards, info cards, stat cards
- charts: Plotly chart utilities and themes
- layout: Page headers, sections, grids, spacers
"""

from src.app.components.cards import (
    render_kpi_card,
    render_info_card,
    render_stat_card,
    render_metric_row,
    card_standard,
    render_empty_state
)

from src.app.components.charts import (
    apply_standard_theme,
    get_standard_colors,
    create_bar_chart,
    create_line_chart,
    create_scatter_chart,
    add_annotation
)

from src.app.components.layout import (
    render_page_header,
    render_section_header,
    render_subsection_header,
    create_metric_grid,
    create_two_column_layout,
    render_spacer,
    render_divider,
    render_card_container,
    render_hero_section
)

__all__ = [
    # Cards
    'render_kpi_card',
    'render_info_card',
    'render_stat_card',
    'render_metric_row',
    'card_standard',
    'render_empty_state',
    
    # Charts
    'apply_standard_theme',
    'get_standard_colors',
    'create_bar_chart',
    'create_line_chart',
    'create_scatter_chart',
    'add_annotation',
    
    # Layout
    'render_page_header',
    'render_section_header',
    'render_subsection_header',
    'create_metric_grid',
    'create_two_column_layout',
    'render_spacer',
    'render_divider',
    'render_card_container',
    'render_hero_section',
]
