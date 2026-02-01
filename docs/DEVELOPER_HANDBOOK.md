# 📘 Barcelona Housing Analytics: Developer Handbook

**Version**: 2.3 (Design System + Components)  
**Date**: 2026-01-23  
**Framework**: Streamlit 1.51.0  
**Status**: 🟢 Production Ready

---

## 📋 Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [The Foundation (Copy-Paste Ready)](#2-the-foundation-copy-paste-ready)
3. [Navigation & Sitemap](#3-navigation--sitemap)
4. [The Golden Template for Views](#4-the-golden-template-for-views)
5. [Component Library](#5-component-library)
6. [Migration Checklist](#6-migration-checklist)
7. [Best Practices](#7-best-practices)
8. [Common Patterns](#8-common-patterns)

---

## 1. High-Level Architecture

We have moved from a flat, fragmented structure to a **centralized, component-based architecture**. This ensures that a change in `design_system.py` propagates instantly to all views.

### 🏗️ **The "Core Three" Files**

```
src/app/
├── design_system.py    # 🎨 Visual brain (Colors, Spacing, Typography)
├── state_manager.py    # 🧠 Memory (Filters, User selections, History)
└── components/         # 🧩 Lego blocks (Cards, Headers, Charts)
    ├── __init__.py
    ├── cards.py
    ├── charts.py
    └── layout.py
```

### 📊 **Architecture Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                     main.py (Entry Point)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Overview   │  │  Analytics   │  │  Investment  │ ...  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Components Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Cards     │  │    Charts    │  │    Layout    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
          ┌──────────────────────────────────────┐
          │       Design System (SSOT)           │
          │  ┌────────┐  ┌────────┐  ┌────────┐ │
          │  │ COLORS │  │SPACING │  │ FONTS  │ │
          │  └────────┘  └────────┘  └────────┘ │
          └──────────────────────────────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │       State Manager (Context)       │
          │  ┌────────┐  ┌────────┐  ┌────────┐│
          │  │Filters │  │  View  │  │  User  ││
          │  │ State  │  │ State  │  │  Prefs ││
          │  └────────┘  └────────┘  └────────┘│
          └─────────────────────────────────────┘
```

---

## 2. The Foundation (Copy-Paste Ready)

### 🎨 **`src/app/design_system.py`**

_This is the Single Source of Truth (SSOT). Do not hardcode hex values in views._

```python
"""
Design System for Barcelona Housing Analytics
Centralizes all visual tokens, spacing, typography, and chart configurations.
"""

# ============================================
# 1. COLOR PALETTE
# ============================================
COLORS = {
    # Primary Colors
    'primary': '#2F80ED',      # Bright Blue (Main actions, primary elements)
    'secondary': '#56CCF2',    # Cyan (Secondary actions, info)

    # Accent Colors
    'accent_green': '#10B981',   # Success, positive trends
    'accent_yellow': '#F59E0B',  # Warnings, attention
    'accent_red': '#EF4444',     # Errors, negative trends
    'accent_purple': '#8B5CF6',  # Special highlights

    # Text Colors
    'text': {
        'primary': '#1A1A1A',      # Main text (high contrast)
        'secondary': '#6B7280',    # Secondary text (medium contrast)
        'tertiary': '#9CA3AF',     # Tertiary text (low contrast)
    },

    # Background Colors
    'background': {
        'primary': '#FFFFFF',      # Main background
        'secondary': '#F9FAFB',    # Secondary background
        'tertiary': '#F3F4F6',     # Tertiary background
    },

    # Semantic Colors
    'success': '#10B981',
    'warning': '#F59E0B',
    'error': '#EF4444',
    'info': '#3B82F6',
}

# ============================================
# 2. SPACING SYSTEM (4px Grid)
# ============================================
SPACING = {
    'xs': '4px',    # Minimal spacing
    'sm': '8px',    # Small spacing
    'md': '16px',   # Medium spacing (default)
    'lg': '24px',   # Large spacing
    'xl': '32px',   # Extra large spacing
    'xxl': '48px',  # Extra extra large spacing
    'xxxl': '64px', # Maximum spacing
}

# ============================================
# 3. TYPOGRAPHY PRESETS
# ============================================
FONTS = {
    # Headings
    'h1_css': f"font-size: 32px; font-weight: 700; color: {COLORS['text']['primary']}; line-height: 1.2; margin: 0;",
    'h2_css': f"font-size: 24px; font-weight: 700; color: {COLORS['text']['primary']}; line-height: 1.3; margin: 0;",
    'h3_css': f"font-size: 20px; font-weight: 600; color: {COLORS['text']['primary']}; line-height: 1.4; margin: 0;",

    # Body Text
    'body_css': f"font-size: 16px; font-weight: 400; color: {COLORS['text']['primary']}; line-height: 1.6;",
    'caption_css': f"font-size: 14px; font-weight: 400; color: {COLORS['text']['secondary']}; line-height: 1.5;",
    'small_css': f"font-size: 12px; font-weight: 400; color: {COLORS['text']['tertiary']}; line-height: 1.4;",
}

# ============================================
# 4. CHART CONFIGURATIONS
# ============================================
def get_chart_layout(height_mode='standard', title=None, showlegend=True):
    """
    Returns standardized Plotly layout configuration.

    Args:
        height_mode: 'compact' (300px), 'standard' (500px), 'expanded' (700px), 'tall' (900px)
        title: Optional chart title
        showlegend: Show/hide legend

    Returns:
        dict: Plotly layout configuration
    """
    heights = {
        'compact': 300,
        'standard': 500,
        'expanded': 700,
        'tall': 900
    }

    return {
        'height': heights.get(height_mode, 500),
        'margin': dict(l=40, r=40, t=60 if title else 40, b=40),
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {
            'family': 'Inter, sans-serif',
            'size': 12,
            'color': COLORS['text']['secondary']
        },
        'title': {
            'text': title,
            'font': {'size': 18, 'color': COLORS['text']['primary'], 'weight': 600},
            'x': 0.5,
            'xanchor': 'center'
        } if title else None,
        'showlegend': showlegend,
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1
        },
        'hovermode': 'x unified'
    }

def get_color_palette(palette_name='primary'):
    """
    Returns color palette for charts.

    Args:
        palette_name: 'primary', 'categorical', 'diverging', 'sequential_blue', etc.

    Returns:
        list: List of hex color codes
    """
    palettes = {
        'primary': [COLORS['primary'], COLORS['secondary'], COLORS['accent_green'],
                   COLORS['accent_yellow'], COLORS['accent_purple']],
        'categorical': [COLORS['primary'], COLORS['accent_green'], COLORS['accent_yellow'],
                       COLORS['accent_red'], COLORS['secondary']],
        'diverging': [COLORS['accent_red'], COLORS['accent_yellow'], COLORS['accent_green']],
        'sequential_blue': ['#EFF6FF', '#DBEAFE', '#BFDBFE', '#93C5FD', '#60A5FA', '#3B82F6', '#2563EB'],
    }

    return palettes.get(palette_name, palettes['primary'])
```

### 🧠 **`src/app/state_manager.py`**

_Manages the global context so filters don't reset when switching tabs._

```python
"""
State Manager for Barcelona Housing Analytics
Manages global session state including filters, view state, and user preferences.
"""

import streamlit as st
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

# ============================================
# STATE DATA CLASSES
# ============================================

@dataclass
class FilterState:
    """Stores filter selections that persist across tabs"""
    selected_district: str = "Todos"
    selected_barrio: Optional[str] = None
    selected_year: int = 2023
    selected_metric: str = "precio_venta"
    year_range: tuple = (2015, 2023)

@dataclass
class ComparisonState:
    """Stores comparison mode settings"""
    enabled: bool = False
    compare_districts: List[str] = field(default_factory=list)
    compare_years: List[int] = field(default_factory=list)

@dataclass
class ViewState:
    """Tracks current view and navigation history"""
    current_tab: str = "overview"
    previous_tab: Optional[str] = None
    navigation_history: List[str] = field(default_factory=list)

@dataclass
class UserPreferences:
    """User preferences and settings"""
    theme: str = "light"
    chart_height_preference: str = "standard"
    language: str = "es"
    show_tooltips: bool = True

@dataclass
class SessionMetadata:
    """Session tracking and analytics"""
    session_id: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    page_views: int = 0
    last_action: Optional[str] = None

# ============================================
# STATE INITIALIZATION
# ============================================

def init_session_state():
    """
    Initialize all session state objects.
    Call this ONCE at the start of main.py
    """
    if 'filter_state' not in st.session_state:
        st.session_state.filter_state = FilterState()

    if 'comparison_state' not in st.session_state:
        st.session_state.comparison_state = ComparisonState()

    if 'view_state' not in st.session_state:
        st.session_state.view_state = ViewState()

    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = UserPreferences()

    if 'session_metadata' not in st.session_state:
        st.session_state.session_metadata = SessionMetadata()

# ============================================
# STATE GETTERS
# ============================================

def get_filter_state() -> FilterState:
    """Get current filter state"""
    return st.session_state.filter_state

def get_comparison_state() -> ComparisonState:
    """Get current comparison state"""
    return st.session_state.comparison_state

def get_view_state() -> ViewState:
    """Get current view state"""
    return st.session_state.view_state

def get_user_preferences() -> UserPreferences:
    """Get user preferences"""
    return st.session_state.user_preferences

# ============================================
# STATE UPDATERS
# ============================================

def update_filter_state(
    district: Optional[str] = None,
    barrio: Optional[str] = None,
    year: Optional[int] = None,
    metric: Optional[str] = None
):
    """Update filter state with new values"""
    state = get_filter_state()

    if district is not None:
        state.selected_district = district
    if barrio is not None:
        state.selected_barrio = barrio
    if year is not None:
        state.selected_year = year
    if metric is not None:
        state.selected_metric = metric

def update_view_state(current_tab: str):
    """Update view state when changing tabs"""
    state = get_view_state()
    state.previous_tab = state.current_tab
    state.current_tab = current_tab
    state.navigation_history.append(current_tab)

def increment_page_view():
    """Increment page view counter"""
    st.session_state.session_metadata.page_views += 1

# ============================================
# UTILITY FUNCTIONS
# ============================================

def sync_widgets_to_filters():
    """Sync Streamlit widgets with filter state"""
    state = get_filter_state()

    # This ensures widgets show the current state values
    return {
        'district': state.selected_district,
        'barrio': state.selected_barrio,
        'year': state.selected_year,
        'metric': state.selected_metric
    }

def reset_filters():
    """Reset all filters to default values"""
    st.session_state.filter_state = FilterState()

def get_current_context() -> dict:
    """Get all current state as a dictionary"""
    return {
        'filters': get_filter_state(),
        'comparison': get_comparison_state(),
        'view': get_view_state(),
        'preferences': get_user_preferences()
    }
```

---

## 3. Navigation & Sitemap

We have consolidated navigation into a **3-Tier Hierarchy**.

### 📊 **Navigation Structure**

| Tier 1: Main Tab  | Tier 2: Sub-Views                                                   | Tier 3: Features                      |
| ----------------- | ------------------------------------------------------------------- | ------------------------------------- |
| **🏠 Overview**   | Dashboard Home                                                      | Quick Stats, Map Preview, System Info |
| **📊 Analytics**  | • Estadístico<br>• Demografía<br>• Correlaciones                    | Data Filters (Sidebar), Export Tools  |
| **💼 Investment** | • Oportunidades<br>• Inteligencia<br>• Alertas<br>• Recomendaciones | Yield Calculator, ROI Tools           |
| **🌍 Territory**  | • Mapa<br>• Social ESG<br>• Calidad de Datos                        | District Drill-down, Spatial Analysis |

### 🗺️ **Tab Flow Diagram**

```
┌─────────────┐
│   Overview  │ ← Landing page with KPIs and quick navigation
└──────┬──────┘
       │
       ├──→ 📊 Analytics
       │    ├── Estadístico (Distributions, trends)
       │    ├── Demografía (Population metrics)
       │    └── Correlaciones (Correlation matrix)
       │
       ├──→ 💼 Investment
       │    ├── Oportunidades (Yield analysis)
       │    ├── Inteligencia (Market trends)
       │    ├── Alertas (Price alerts)
       │    └── Recomendaciones (Top neighborhoods)
       │
       └──→ 🌍 Territory
            ├── Mapa (Interactive choropleth)
            ├── Social ESG (Sustainability metrics)
            └── Calidad de Datos (Data completeness)
```

---

## 4. The Golden Template for Views

**Crucial:** Every new view created (`src/app/views/new_view.py`) must follow this structure to ensure consistency.

### 📝 **Template Code**

```python
"""
[View Name] - [Brief Description]

[Detailed description of what this view shows]
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Optional

# Import design system and components
from src.app.design_system import COLORS, SPACING, get_chart_layout, get_color_palette
from src.app.components import (
    render_page_header,
    render_section_header,
    render_kpi_card,
    create_metric_grid,
    create_two_column_layout,
    render_spacer,
    apply_standard_theme
)
from src.app.state_manager import get_filter_state, update_filter_state
from src.app.data_loader import load_your_data  # Replace with actual loader

# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render(
    year: Optional[int] = None,
    distrito_filter: Optional[str] = None,
    key_prefix: str = "view_name"
) -> None:
    """
    Main render function for this view.

    Args:
        year: Selected year (uses state if None)
        distrito_filter: District filter (uses state if None)
        key_prefix: Unique prefix for Streamlit keys
    """
    # 1. Get current state
    state = get_filter_state()

    # Use state values if not provided
    year = year or state.selected_year
    distrito_filter = distrito_filter or state.selected_district

    # 2. Page Header
    render_page_header(
        title="View Name",
        subtitle=f"Analysis for {distrito_filter} ({year})",
        breadcrumbs=["Home", "Category", "Current View"],
        icon="📊"
    )

    # 3. Load Data
    df = _load_view_data(year, distrito_filter)

    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    # 4. KPI Section
    render_section_header(
        title="Key Metrics",
        icon="📊",
        subtitle="Main indicators for this view"
    )

    cols = create_metric_grid(num_columns=4, gap="medium")

    with cols[0]:
        render_kpi_card(
            title="Metric A",
            value="1,200",
            delta="+5.2%",
            help_text="Description of metric A",
            icon="💰",
            color_scheme="primary"
        )

    with cols[1]:
        render_kpi_card(
            title="Metric B",
            value="85",
            delta="-2.1%",
            help_text="Description of metric B",
            icon="📈",
            color_scheme="success"
        )

    # Add more KPIs as needed

    render_spacer('xl')

    # 5. Main Visualization Section
    render_section_header(
        title="Detailed Analysis",
        icon="📊"
    )

    # Create chart
    fig = px.bar(
        df,
        x='category',
        y='value',
        color='category',
        color_discrete_sequence=get_color_palette('primary')
    )

    # CRITICAL: Apply standard theme
    fig = apply_standard_theme(
        fig,
        height_mode='standard',
        show_legend=True,
        title='Chart Title'
    )

    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart_1")

    render_spacer('lg')

    # 6. Additional Sections (Optional)
    col_left, col_right = create_two_column_layout(left_ratio=1.5, gap="large")

    with col_left:
        render_section_header("Left Section", icon="📊")
        # Left content
        pass

    with col_right:
        render_section_header("Right Section", icon="ℹ️")
        # Right content
        pass

# ============================================
# HELPER FUNCTIONS
# ============================================

@st.cache_data(ttl=3600)
def _load_view_data(year: int, distrito: str) -> pd.DataFrame:
    """
    Load data for this view.

    Args:
        year: Year to load
        distrito: District to filter

    Returns:
        DataFrame with view data
    """
    # Replace with actual data loading logic
    df = load_your_data(year, distrito)
    return df

def _calculate_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate metrics from data.

    Args:
        df: Input DataFrame

    Returns:
        Dictionary of calculated metrics
    """
    return {
        'metric_a': df['column_a'].sum(),
        'metric_b': df['column_b'].mean(),
        # Add more calculations
    }
```

---

## 5. Component Library

### 🎴 **Cards**

```python
from src.app.components import render_kpi_card, render_info_card, render_stat_card

# KPI Card
render_kpi_card(
    title="Precio Medio",
    value="4,118 €/m²",
    delta="+5.2%",
    help_text="Precio medio de venta en 2025",
    icon="💰",
    color_scheme="primary"  # 'primary', 'secondary', 'success', 'warning', 'danger', 'neutral'
)

# Info Card
render_info_card(
    title="Important Information",
    content="This is an informational message.",
    icon="ℹ️",
    card_type="info"  # 'info', 'success', 'warning', 'danger'
)

# Stat Card
render_stat_card(
    label="Data Sources",
    value="3",
    sublabel="OpenData BCN, Idealista, IDESCAT",
    compact=True
)
```

### 📊 **Charts**

```python
from src.app.components import apply_standard_theme, create_bar_chart, create_line_chart

# Apply theme to existing chart
fig = px.bar(df, x='x', y='y')
fig = apply_standard_theme(
    fig,
    height_mode='standard',  # 'compact', 'standard', 'expanded', 'tall'
    show_legend=True,
    title='Chart Title'
)

# Quick bar chart
fig = create_bar_chart(
    data=df,
    x='category',
    y='value',
    title='Sales by Category',
    height_mode='standard'
)

# Quick line chart
fig = create_line_chart(
    data=df_trends,
    x='year',
    y='price',
    title='Price Evolution',
    markers=True
)
```

### 📐 **Layout**

```python
from src.app.components import (
    render_page_header,
    render_section_header,
    create_metric_grid,
    create_two_column_layout,
    render_spacer,
    render_hero_section
)

# Page Header
render_page_header(
    title="Page Title",
    subtitle="Page description",
    breadcrumbs=["Home", "Category", "Page"],
    icon="📊"
)

# Section Header
render_section_header(
    title="Section Title",
    icon="📊",
    subtitle="Section description"
)

# Metric Grid
cols = create_metric_grid(num_columns=4, gap="medium")

# Two-Column Layout
col_left, col_right = create_two_column_layout(left_ratio=1.6, gap="large")

# Spacer
render_spacer('xl')  # 'xs', 'sm', 'md', 'lg', 'xl', 'xxl'

# Hero Section
render_hero_section(
    title="Barcelona Housing Analytics",
    subtitle="Dashboard de análisis inmobiliario",
    background_gradient=True
)
```

---

## 6. Migration Checklist

Use this checklist when refactoring old files:

### ✅ **Step-by-Step Migration**

- [ ] **1. Update Imports**

  ```python
  # Remove
  # import plotly.graph_objects as go

  # Add
  from src.app.design_system import COLORS, SPACING, get_chart_layout
  from src.app.components import render_page_header, render_kpi_card
  from src.app.state_manager import get_filter_state
  ```

- [ ] **2. Replace Colors**

  ```python
  # Before
  color = '#2F80ED'

  # After
  color = COLORS['primary']
  ```

- [ ] **3. Replace Headers**

  ```python
  # Before
  st.title("My Page")
  st.markdown("---")

  # After
  render_page_header("My Page", subtitle="Description")
  ```

- [ ] **4. Replace Metrics**

  ```python
  # Before
  col1, col2 = st.columns(2)
  col1.metric("Value", "100", "+5%")

  # After
  cols = create_metric_grid(2)
  with cols[0]:
      render_kpi_card("Value", "100", "+5.2%")
  ```

- [ ] **5. Apply Chart Themes**

  ```python
  # Before
  fig = px.bar(df, x='x', y='y')
  fig.update_layout(height=500)

  # After
  fig = px.bar(df, x='x', y='y')
  fig = apply_standard_theme(fig, height_mode='standard')
  ```

- [ ] **6. Use State Manager**

  ```python
  # Before
  year = st.sidebar.selectbox("Year", [2020, 2021, 2022])

  # After
  state = get_filter_state()
  year = state.selected_year
  ```

- [ ] **7. Test & Verify**
  - [ ] Run the view in isolation
  - [ ] Check all charts render correctly
  - [ ] Verify filters work
  - [ ] Test on different screen sizes

---

## 7. Best Practices

### ✅ **DO**

✅ **Use components for all UI elements**

```python
render_kpi_card("Title", "Value")  # Good
```

✅ **Import from design system**

```python
from src.app.design_system import COLORS  # Good
```

✅ **Apply themes to all charts**

```python
fig = apply_standard_theme(fig)  # Good
```

✅ **Use state manager for filters**

```python
state = get_filter_state()  # Good
```

✅ **Handle empty data gracefully**

```python
if df.empty:
    st.warning("No data available")
    return
```

### ❌ **DON'T**

❌ **Don't hardcode colors**

```python
color = '#2F80ED'  # Bad
```

❌ **Don't use raw st.markdown for headers**

```python
st.markdown("## Title")  # Bad
```

❌ **Don't create custom CSS blocks**

```python
st.markdown("<style>...</style>", unsafe_allow_html=True)  # Bad
```

❌ **Don't use st.divider()**

```python
st.divider()  # Bad - use render_spacer() instead
```

❌ **Don't mix component styles**

```python
# Bad - mixing components with raw HTML
render_kpi_card(...)
st.markdown("<div>...</div>")
```

---

## 8. Common Patterns

### 🔄 **Pattern 1: Data Loading with Cache**

```python
@st.cache_data(ttl=3600)
def load_data(year: int, district: str) -> pd.DataFrame:
    """Load and cache data"""
    df = load_from_database(year, district)
    return df
```

### 🔄 **Pattern 2: Conditional Rendering**

```python
if df.empty:
    render_info_card(
        title="No Data",
        content="No data available for selected filters.",
        icon="⚠️",
        card_type="warning"
    )
    return

# Continue with normal rendering
```

### 🔄 **Pattern 3: Dynamic KPIs**

```python
metrics = [
    {"title": "Metric A", "value": "100", "delta": "+5%"},
    {"title": "Metric B", "value": "200", "delta": "-2%"},
]

cols = create_metric_grid(len(metrics))

for col, metric in zip(cols, metrics):
    with col:
        render_kpi_card(**metric)
```

### 🔄 **Pattern 4: Responsive Charts**

```python
# Always use use_container_width=True
st.plotly_chart(fig, use_container_width=True, key="unique_key")
```

---

## 📚 **Additional Resources**

- **Components Guide**: `docs/COMPONENTS_GUIDE.md`
- **Design System**: `docs/DESIGN_SYSTEM_GUIDE.md`
- **Quick Reference**: `docs/DESIGN_SYSTEM_QUICK_REFERENCE.md`
- **Architecture**: `docs/ARCHITECTURE_DIAGRAM.md`
- **Refactoring Example**: `docs/OVERVIEW_REFACTORING.md`

---

## 🎯 **Next Steps**

1. ✅ **Read this handbook** - Understand the architecture
2. ✅ **Use the Golden Template** - Create new views
3. ✅ **Migrate existing views** - Follow the checklist
4. ✅ **Test thoroughly** - Verify all components work
5. ✅ **Iterate** - Improve based on feedback

---

**Version**: 2.3  
**Last Updated**: 2026-01-23  
**Maintainer**: Barcelona Housing Analytics Team  
**Status**: 🟢 Production Ready
