"""
Chart Utilities for Barcelona Housing Analytics
Provides standardized Plotly chart configurations and themes.
"""

import plotly.graph_objects as go
from src.app.design_system import COLORS, get_chart_layout, get_color_palette


def apply_standard_theme(
    fig: go.Figure,
    height_mode: str = 'standard',
    show_legend: bool = True,
    title: str = None
) -> go.Figure:
    """
    Applies the global design system theme to any Plotly figure.
    
    Args:
        fig: The Plotly figure object
        height_mode: 'compact', 'standard', 'expanded', or 'tall'
        show_legend: Boolean to toggle legend visibility
        title: Optional chart title
    
    Returns:
        Modified figure with applied theme
    """
    # Get standardized layout from design system
    layout = get_chart_layout(height_mode, title=title, showlegend=show_legend)
    
    # Apply layout
    fig.update_layout(**layout)
    
    # Update axes for clean look
    fig.update_xaxes(
        showgrid=False,
        linecolor='rgba(0,0,0,0.1)',
        zeroline=False,
        tickfont=dict(size=11, color=COLORS['text']['secondary'])
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor='rgba(0,0,0,0.05)',
        zeroline=False,
        tickfont=dict(size=11, color=COLORS['text']['secondary'])
    )
    
    return fig


def get_standard_colors(palette: str = 'primary') -> list:
    """
    Returns a list of colors for chart series.
    
    Args:
        palette: 'primary', 'categorical', 'diverging', 'sequential_blue', etc.
    
    Returns:
        List of hex color codes
    """
    return get_color_palette(palette)


def create_bar_chart(
    data,
    x: str,
    y: str,
    title: str = None,
    color: str = None,
    height_mode: str = 'standard'
) -> go.Figure:
    """
    Creates a standardized bar chart.
    
    Args:
        data: DataFrame with data
        x: Column name for x-axis
        y: Column name for y-axis
        title: Chart title
        color: Optional column for color coding
        height_mode: Chart height preset
    
    Returns:
        Configured Plotly figure
    """
    import plotly.express as px
    
    colors = get_standard_colors('primary')
    
    fig = px.bar(
        data,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=colors,
        title=title
    )
    
    return apply_standard_theme(fig, height_mode=height_mode, title=title)


def create_line_chart(
    data,
    x: str,
    y: str,
    title: str = None,
    color: str = None,
    height_mode: str = 'standard',
    markers: bool = True
) -> go.Figure:
    """
    Creates a standardized line chart.
    
    Args:
        data: DataFrame with data
        x: Column name for x-axis
        y: Column name for y-axis
        title: Chart title
        color: Optional column for color coding
        height_mode: Chart height preset
        markers: Show markers on data points
    
    Returns:
        Configured Plotly figure
    """
    import plotly.express as px
    
    colors = get_standard_colors('primary')
    
    fig = px.line(
        data,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=colors,
        title=title,
        markers=markers
    )
    
    # Make lines thicker
    fig.update_traces(line=dict(width=3))
    
    return apply_standard_theme(fig, height_mode=height_mode, title=title)


def create_scatter_chart(
    data,
    x: str,
    y: str,
    title: str = None,
    color: str = None,
    size: str = None,
    height_mode: str = 'standard'
) -> go.Figure:
    """
    Creates a standardized scatter plot.
    
    Args:
        data: DataFrame with data
        x: Column name for x-axis
        y: Column name for y-axis
        title: Chart title
        color: Optional column for color coding
        size: Optional column for bubble size
        height_mode: Chart height preset
    
    Returns:
        Configured Plotly figure
    """
    import plotly.express as px
    
    colors = get_standard_colors('primary')
    
    fig = px.scatter(
        data,
        x=x,
        y=y,
        color=color,
        size=size,
        color_discrete_sequence=colors,
        title=title
    )
    
    return apply_standard_theme(fig, height_mode=height_mode, title=title)


def add_annotation(
    fig: go.Figure,
    text: str,
    x: float,
    y: float,
    color: str = None
) -> go.Figure:
    """
    Adds a text annotation to a chart.
    
    Args:
        fig: Plotly figure
        text: Annotation text
        x: X coordinate
        y: Y coordinate
        color: Optional text color
    
    Returns:
        Figure with annotation added
    """
    if color is None:
        color = COLORS['text']['primary']
    
    fig.add_annotation(
        text=text,
        x=x,
        y=y,
        showarrow=False,
        font=dict(size=12, color=color),
        bgcolor='rgba(255,255,255,0.8)',
        borderpad=4
    )
    
    return fig
