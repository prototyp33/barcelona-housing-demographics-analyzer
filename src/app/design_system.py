"""
Design System for Barcelona Housing Analytics
Centralizes styles, colors, typography, spacing, and chart configurations.

This module serves as the Single Source of Truth (SSOT) for all visual design tokens,
preventing style drift across the application.

Version: 2.3 - Centralized Design System
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional


# ============================================
# 1. COLOR PALETTE (Glassmorphism & Theming)
# ============================================

COLORS = {
    # Primary Brand Colors
    'primary': '#2F80ED',           # Bright Blue (Barcelona Brand)
    'primary_dark': '#005EB8',      # Dark Blue (Professional Reports)
    'secondary': '#56CCF2',         # Cyan (Accent)
    
    # Background System
    'background': '#0E1117',        # Streamlit Dark Mode
    'background_light': '#F4F5F7',  # Light Canvas
    'bg_card': '#FFFFFF',           # Card Background
    
    # Glassmorphism Effects
    'glass': 'rgba(255, 255, 255, 0.05)',
    'glass_hover': 'rgba(255, 255, 255, 0.10)',
    'glass_sidebar': 'rgba(255, 255, 255, 0.45)',
    
    # Text Hierarchy
    'text': {
        'primary': '#1A1A1A',       # Main Text
        'secondary': '#8E92BC',     # Subtle Text
        'tertiary': '#A0AEC0',      # Muted Text
        'success': '#48BB78',       # Success Messages
        'warning': '#ED8936',       # Warning Messages
        'danger': '#F56565',        # Error Messages
        'info': '#2F80ED',          # Info Messages
    },
    
    # Semantic Colors (Aligned with Professional Reports)
    'accent_blue': '#005EB8',
    'accent_red': '#EF4444',
    'accent_green': '#10B981',
    'accent_yellow': '#F59E0B',
    
    # Gradient Mesh (for KPIs)
    'gradient_warm': 'linear-gradient(135deg, #FF9966 0%, #FF5E62 100%)',
    'gradient_cool': 'linear-gradient(135deg, #56CCF2 0%, #2F80ED 100%)',
    'gradient_success': 'linear-gradient(135deg, #48BB78 0%, #38A169 100%)',
}


# ============================================
# 2. SPACING SYSTEM (The 4px Grid)
# ============================================

SPACING = {
    'xs': '4px',
    'sm': '8px',
    'md': '16px',
    'lg': '24px',
    'xl': '32px',
    'xxl': '48px',
    'xxxl': '64px',
}


# ============================================
# 3. TYPOGRAPHY SCALE
# ============================================

FONTS = {
    'family': "'Inter', 'DM Sans', 'Roboto', sans-serif",
    'family_mono': "'JetBrains Mono', 'Fira Code', monospace",
    
    # Heading Styles
    'h1': {
        'size': '32px',
        'weight': '700',
        'line_height': '1.2',
        'color': COLORS['text']['primary'],
    },
    'h2': {
        'size': '24px',
        'weight': '600',
        'line_height': '1.3',
        'color': COLORS['text']['primary'],
    },
    'h3': {
        'size': '18px',
        'weight': '600',
        'line_height': '1.3',
        'color': COLORS['text']['primary'],
    },
    
    # Body Text
    'body': {
        'size': '14px',
        'weight': '400',
        'line_height': '1.5',
        'color': COLORS['text']['primary'],
    },
    'caption': {
        'size': '12px',
        'weight': '400',
        'line_height': '1.4',
        'color': COLORS['text']['secondary'],
    },
    
    # Utility Styles (as CSS strings for direct use)
    'h1_css': f"font-size: 32px; font-weight: 700; color: {COLORS['text']['primary']}; line-height: 1.2;",
    'h2_css': f"font-size: 24px; font-weight: 600; color: {COLORS['text']['primary']}; line-height: 1.3;",
    'h3_css': f"font-size: 18px; font-weight: 600; color: {COLORS['text']['primary']}; line-height: 1.3;",
    'caption_css': f"font-size: 12px; font-weight: 400; color: {COLORS['text']['secondary']}; line-height: 1.4;",
}


# ============================================
# 4. ELEVATION & SHADOWS
# ============================================

SHADOWS = {
    'none': 'none',
    'sm': '0px 2px 8px rgba(29, 22, 23, 0.05)',
    'md': '0px 10px 40px rgba(29, 22, 23, 0.1)',
    'lg': '0px 15px 45px rgba(29, 22, 23, 0.12)',
    'xl': '0px 20px 50px rgba(29, 22, 23, 0.15)',
}


# ============================================
# 5. BORDER RADIUS SYSTEM
# ============================================

RADIUS = {
    'sm': '8px',
    'md': '12px',
    'lg': '16px',
    'xl': '20px',
    'xxl': '24px',
    'round': '50%',
}


# ============================================
# 6. CHART CONFIGURATIONS (Standardization)
# ============================================

CHART_CONFIG = {
    # Preset Sizes
    'compact': {
        'height': 300,
        'margin': {'l': 20, 'r': 20, 't': 30, 'b': 20}
    },
    'standard': {
        'height': 500,
        'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40}
    },
    'expanded': {
        'height': 700,
        'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50}
    },
    'tall': {
        'height': 600,
        'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40}
    },
    
    # Common Layout Settings (apply to all charts)
    'common_layout': {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {
            'family': FONTS['family'],
            'color': COLORS['text']['secondary'],
            'size': 12,
        },
        'title': {
            'font': {
                'size': 16,
                'weight': 600,
                'color': COLORS['text']['primary'],
            }
        },
        'hoverlabel': {
            'bgcolor': 'rgba(26, 26, 26, 0.92)',
            'font': {
                'family': FONTS['family'],
                'size': 12,
                'color': '#FFFFFF',
            },
            'bordercolor': 'transparent',
        },
        'xaxis': {
            'gridcolor': 'rgba(142, 146, 188, 0.1)',
            'zerolinecolor': 'rgba(142, 146, 188, 0.2)',
        },
        'yaxis': {
            'gridcolor': 'rgba(142, 146, 188, 0.1)',
            'zerolinecolor': 'rgba(142, 146, 188, 0.2)',
        },
    },
    
    # Color Palettes for Charts
    'color_sequences': {
        'primary': [COLORS['primary'], COLORS['secondary'], COLORS['accent_green'], 
                   COLORS['accent_yellow'], COLORS['accent_red']],
        'categorical': ['#2F80ED', '#56CCF2', '#10B981', '#F59E0B', '#EF4444', 
                       '#8B5CF6', '#EC4899', '#06B6D4'],
        'diverging': ['#EF4444', '#F59E0B', '#F4F5F7', '#56CCF2', '#2F80ED'],
        'sequential_blue': ['#EBF5FF', '#BFDBFE', '#93C5FD', '#60A5FA', '#3B82F6', '#2563EB', '#1D4ED8'],
    }
}


# ============================================
# 7. COMPONENT PRESETS
# ============================================

@dataclass
class KPICardConfig:
    """Configuration for KPI card components"""
    style: Literal['white', 'warm', 'cool', 'success'] = 'white'
    show_delta: bool = True
    show_icon: bool = True
    height: str = '160px'
    padding: str = SPACING['lg']
    border_radius: str = RADIUS['xl']
    shadow: str = SHADOWS['md']


@dataclass
class ButtonConfig:
    """Configuration for button components"""
    variant: Literal['primary', 'secondary', 'ghost', 'danger'] = 'primary'
    size: Literal['sm', 'md', 'lg'] = 'md'
    full_width: bool = False
    border_radius: str = RADIUS['md']


# ============================================
# 8. ANIMATION & TRANSITIONS
# ============================================

TRANSITIONS = {
    'fast': '0.15s ease',
    'normal': '0.3s ease',
    'slow': '0.5s ease',
    'smooth': '0.35s cubic-bezier(0.4, 0, 0.2, 1)',
}


# ============================================
# 9. BREAKPOINTS (Responsive Design)
# ============================================

BREAKPOINTS = {
    'mobile': '640px',
    'tablet': '768px',
    'desktop': '1024px',
    'wide': '1280px',
    'ultrawide': '1536px',
}


# ============================================
# 10. UTILITY FUNCTIONS
# ============================================

def get_chart_layout(
    preset: Literal['compact', 'standard', 'expanded', 'tall'] = 'standard',
    **overrides: Any
) -> Dict[str, Any]:
    """
    Get a complete chart layout configuration with common settings applied.
    
    Args:
        preset: Size preset ('compact', 'standard', 'expanded', 'tall')
        **overrides: Additional layout properties to override defaults
    
    Returns:
        Complete Plotly layout dictionary
    
    Example:
        >>> layout = get_chart_layout('compact', title='My Chart')
    """
    base_config = CHART_CONFIG[preset].copy()
    common = CHART_CONFIG['common_layout'].copy()
    
    # Merge configurations
    layout = {**common, **base_config, **overrides}
    
    return layout


def get_color_palette(
    palette: Literal['primary', 'categorical', 'diverging', 'sequential_blue'] = 'primary'
) -> list[str]:
    """
    Get a predefined color palette for charts.
    
    Args:
        palette: Name of the color palette
    
    Returns:
        List of color hex codes
    """
    return CHART_CONFIG['color_sequences'][palette]


def create_gradient_css(
    gradient_type: Literal['warm', 'cool', 'success'] = 'cool'
) -> str:
    """
    Create CSS gradient string for backgrounds.
    
    Args:
        gradient_type: Type of gradient ('warm', 'cool', 'success')
    
    Returns:
        CSS gradient string
    """
    gradient_map = {
        'warm': COLORS['gradient_warm'],
        'cool': COLORS['gradient_cool'],
        'success': COLORS['gradient_success'],
    }
    return gradient_map.get(gradient_type, COLORS['gradient_cool'])


def get_spacing_value(size: Literal['xs', 'sm', 'md', 'lg', 'xl', 'xxl', 'xxxl']) -> str:
    """
    Get spacing value from the design system.
    
    Args:
        size: Spacing size key
    
    Returns:
        Spacing value in pixels
    """
    return SPACING[size]


# ============================================
# 11. VALIDATION & CONSISTENCY CHECKS
# ============================================

def validate_color(color: str) -> bool:
    """
    Validate if a color string is properly formatted.
    
    Args:
        color: Color string (hex, rgb, rgba)
    
    Returns:
        True if valid, False otherwise
    """
    import re
    
    # Check hex format
    if re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color):
        return True
    
    # Check rgb/rgba format
    if re.match(r'^rgba?\([\d\s,\.]+\)$', color):
        return True
    
    return False


# ============================================
# 12. EXPORT CONSTANTS FOR BACKWARD COMPATIBILITY
# ============================================

# Legacy support - map to new system
COLOR_TOKENS = {
    'bg_canvas': COLORS['background_light'],
    'bg_card': COLORS['bg_card'],
    'text_primary': COLORS['text']['primary'],
    'text_secondary': COLORS['text']['secondary'],
    'accent_blue': COLORS['accent_blue'],
    'accent_red': COLORS['accent_red'],
    'accent_green': COLORS['accent_green'],
    'accent_yellow': COLORS['accent_yellow'],
    'border_radius': RADIUS['xxl'],
    'shadow_elevation_1': SHADOWS['md'],
}

GRADIENTS = {
    'warm': COLORS['gradient_warm'],
    'cool': COLORS['gradient_cool'],
}
