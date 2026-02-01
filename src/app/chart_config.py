"""
Chart Configuration Standards
Standardized heights and settings for all visualizations
"""

# Standard Chart Heights
CHART_HEIGHTS = {
    'compact': 400,      # For KPI supporting charts, small multiples
    'standard': 600,     # Default for most visualizations
    'expanded': 800,     # For primary/hero charts, detailed analysis
}

# Standard Chart Configurations by Type
SCATTER_CONFIG = {
    'height': CHART_HEIGHTS['standard'],
    'hover_data_format': ':.2f',
    'size_max': 30,
    'opacity': 0.7,
}

BAR_CONFIG = {
    'height': CHART_HEIGHTS['standard'],
    'orientation': 'h',  # Horizontal for better label readability
    'show_values': True,
}

LINE_CONFIG = {
    'height': CHART_HEIGHTS['compact'],
    'line_shape': 'spline',
    'show_markers': True,
}

MAP_CONFIG = {
    'height': CHART_HEIGHTS['expanded'],
    'zoom': 11,
    'center': {'lat': 41.3851, 'lon': 2.1734},  # Barcelona
}

# Color Scales
COLOR_SCALES = {
    'sequential_blue': 'Blues',
    'sequential_green': 'Greens',
    'sequential_red': 'Reds',
    'diverging': 'RdBu',
    'categorical': 'Set2',
}
