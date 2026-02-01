# Design System Implementation Guide

**Version**: 2.3 - Centralized Design System  
**Date**: 2026-01-22  
**Status**: ✅ Implemented

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Design System Components](#design-system-components)
4. [Navigation Structure](#navigation-structure)
5. [Global State Management](#global-state-management)
6. [Migration Guide](#migration-guide)
7. [Best Practices](#best-practices)

---

## Overview

This implementation addresses the **Critical UX/UI Issues** identified in the audit:

### Problems Solved

✅ **Cognitive Overload** - Reduced from 14 tabs to 4 main categories  
✅ **Style Drift** - Centralized design tokens in `design_system.py`  
✅ **User Journey Fragmentation** - Global context pattern maintains state across tabs  
✅ **Inconsistent Chart Heights** - Standardized presets (compact, standard, expanded)

### Key Benefits

- **Single Source of Truth (SSOT)** for all visual design decisions
- **Consistent user experience** across all views
- **Maintainable codebase** with centralized configuration
- **Improved navigation** with logical grouping and sub-tabs

---

## Architecture

### File Structure

```
src/app/
├── design_system.py      # 🆕 Centralized design tokens
├── state_manager.py      # 🆕 Global session state management
├── main.py              # ✏️ Updated with new navigation
├── styles.py            # Existing CSS injection (now imports from design_system)
└── views/               # Individual view modules
```

### Dependency Flow

```
main.py
  ├─→ design_system.py (COLORS, SPACING, FONTS, CHART_CONFIG)
  ├─→ state_manager.py (init_session_state, sync_filters)
  └─→ styles.py (inject_global_css)
       └─→ design_system.py (COLOR_TOKENS, GRADIENTS)
```

---

## Design System Components

### 1. Color Palette (`design_system.py`)

```python
from src.app.design_system import COLORS

# Primary Brand Colors
COLORS['primary']           # '#2F80ED' - Bright Blue
COLORS['primary_dark']      # '#005EB8' - Dark Blue (Reports)
COLORS['secondary']         # '#56CCF2' - Cyan

# Background System
COLORS['background_light']  # '#F4F5F7' - Light Canvas
COLORS['bg_card']          # '#FFFFFF' - Card Background

# Text Hierarchy
COLORS['text']['primary']   # '#1A1A1A' - Main Text
COLORS['text']['secondary'] # '#8E92BC' - Subtle Text
COLORS['text']['success']   # '#48BB78' - Success Messages

# Semantic Colors
COLORS['accent_blue']       # '#005EB8'
COLORS['accent_red']        # '#EF4444'
COLORS['accent_green']      # '#10B981'
COLORS['accent_yellow']     # '#F59E0B'
```

### 2. Spacing System (4px Grid)

```python
from src.app.design_system import SPACING, get_spacing_value

SPACING['xs']   # '4px'
SPACING['sm']   # '8px'
SPACING['md']   # '16px'
SPACING['lg']   # '24px'
SPACING['xl']   # '32px'
SPACING['xxl']  # '48px'

# Usage in code
margin = get_spacing_value('lg')  # Returns '24px'
```

### 3. Typography Scale

```python
from src.app.design_system import FONTS

# Heading Styles (as dictionaries)
FONTS['h1']  # {'size': '32px', 'weight': '700', ...}
FONTS['h2']  # {'size': '24px', 'weight': '600', ...}

# Direct CSS Strings (for st.markdown)
st.markdown(f'<h1 style="{FONTS["h1_css"]}">Title</h1>', unsafe_allow_html=True)
```

### 4. Chart Configurations

```python
from src.app.design_system import get_chart_layout, get_color_palette

# Get standardized chart layout
layout = get_chart_layout('standard', title='My Chart')

# Apply to Plotly figure
fig.update_layout(**layout)

# Use color palettes
colors = get_color_palette('primary')  # Returns list of hex codes
```

#### Chart Presets

| Preset     | Height | Use Case                          |
| ---------- | ------ | --------------------------------- |
| `compact`  | 300px  | Dashboard KPIs, small widgets     |
| `standard` | 500px  | Main analysis charts              |
| `expanded` | 700px  | Detailed visualizations           |
| `tall`     | 600px  | Time-series, vertical comparisons |

### 5. Shadows & Elevation

```python
from src.app.design_system import SHADOWS

SHADOWS['sm']  # '0px 2px 8px rgba(29, 22, 23, 0.05)'
SHADOWS['md']  # '0px 10px 40px rgba(29, 22, 23, 0.1)'
SHADOWS['lg']  # '0px 15px 45px rgba(29, 22, 23, 0.12)'
```

---

## Navigation Structure

### Before (7 Tabs - Fragmented)

```
🏠 Overview
📊 Analytics
💼 Investment
🌍 Territory
🌱 Social ESG
📄 Reports
⚙️ Settings
```

### After (4 Tabs - Consolidated)

```
🏠 Overview
  └─ Market Cockpit (Primary Dashboard)

📊 Analytics
  ├─ 📈 Análisis Estadístico
  ├─ 👥 Demografía
  └─ 🔗 Correlaciones

💼 Investment
  ├─ 💡 Oportunidades
  ├─ 🧠 Inteligencia de Mercado
  ├─ 🚨 Alertas
  └─ ⭐ Recomendaciones

🌍 Territory
  ├─ 🗺️ Mapa Interactivo
  ├─ 🌱 Social ESG
  └─ ✅ Calidad de Datos

⚙️ Utilidades (Sidebar Expander)
  ├─ 📖 Diccionario
  ├─ 📥 Descargas
  └─ 📄 Reportes
```

### Navigation Principles

1. **Logical Grouping** - Related views are grouped together
2. **Progressive Disclosure** - Sub-tabs reveal details without overwhelming
3. **Persistent Context** - Filters maintained across all tabs
4. **Accessibility** - Clear visual hierarchy with icons and labels

---

## Global State Management

### Session State Structure

```python
from src.app.state_manager import (
    init_session_state,
    update_filter_state,
    get_filter_state,
    sync_widgets_to_filters,
)

# Initialize (called once in main.py)
init_session_state()

# Update filters
update_filter_state(
    district='Eixample',
    year=2024,
    metric='price_per_sqm'
)

# Get current state
filter_state = get_filter_state()
print(filter_state.selected_district)  # 'Eixample'
print(filter_state.selected_year)      # 2024
```

### State Objects

#### FilterState

```python
@dataclass
class FilterState:
    selected_district: str = 'All'
    selected_barrio_id: Optional[int] = None
    selected_year: int = 2025
    active_metric: str = 'price_per_sqm'
```

#### ComparisonState

```python
@dataclass
class ComparisonState:
    compare_mode: bool = False
    comparison_districts: List[str] = []
    comparison_barrios: List[int] = []
    max_comparisons: int = 4
```

#### ViewState

```python
@dataclass
class ViewState:
    active_tab: str = 'overview'
    active_subtab: Optional[str] = None
    last_visited_tabs: List[str] = []
```

### Synchronization Pattern

```python
# In main.py
selected_year, distrito_filter, selected_metric = render_sidebar()

# Sync to global state
sync_widgets_to_filters(
    district=distrito_filter if distrito_filter else 'All',
    year=selected_year,
    metric=selected_metric,
)

# Now all views can access consistent state
filter_state = get_filter_state()
```

---

## Migration Guide

### For View Developers

#### Before (Old Pattern)

```python
def render(year: int, distrito_filter: Optional[str] = None):
    # Manually handle parameters
    if distrito_filter:
        data = load_data(year, distrito_filter)
    else:
        data = load_data(year)
```

#### After (New Pattern)

```python
from src.app.state_manager import get_filter_state
from src.app.design_system import get_chart_layout, COLORS

def render():
    # Get state from global context
    state = get_filter_state()

    # Use centralized design tokens
    layout = get_chart_layout('standard')

    # Load data with consistent filters
    data = load_data(state.selected_year, state.selected_district)
```

### Updating Chart Configurations

#### Before

```python
fig.update_layout(
    height=500,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    # ... many lines of config
)
```

#### After

```python
from src.app.design_system import get_chart_layout

layout = get_chart_layout('standard', title='My Chart')
fig.update_layout(**layout)
```

### Using Color Tokens

#### Before

```python
colors = ['#2F80ED', '#56CCF2', '#10B981']  # Hard-coded
```

#### After

```python
from src.app.design_system import get_color_palette

colors = get_color_palette('primary')
```

---

## Best Practices

### 1. Always Use Design Tokens

❌ **Don't:**

```python
st.markdown('<div style="color: #1A1A1A; padding: 16px;">', unsafe_allow_html=True)
```

✅ **Do:**

```python
from src.app.design_system import COLORS, SPACING

st.markdown(
    f'<div style="color: {COLORS["text"]["primary"]}; padding: {SPACING["md"]};">',
    unsafe_allow_html=True
)
```

### 2. Use Centralized Chart Layouts

❌ **Don't:**

```python
fig.update_layout(height=500, margin=dict(l=40, r=40, t=40, b=40))
```

✅ **Do:**

```python
from src.app.design_system import get_chart_layout

fig.update_layout(**get_chart_layout('standard'))
```

### 3. Access State Through Manager

❌ **Don't:**

```python
if 'selected_year' in st.session_state:
    year = st.session_state.selected_year
```

✅ **Do:**

```python
from src.app.state_manager import get_filter_state

state = get_filter_state()
year = state.selected_year
```

### 4. Maintain Consistent Spacing

Use the 4px grid system:

- `xs` (4px) - Minimal spacing
- `sm` (8px) - Tight spacing
- `md` (16px) - Standard spacing
- `lg` (24px) - Section spacing
- `xl` (32px) - Large gaps

### 5. Typography Hierarchy

```python
from src.app.design_system import FONTS

# Page Title
st.markdown(f'<h1 style="{FONTS["h1_css"]}">Page Title</h1>', unsafe_allow_html=True)

# Section Title
st.markdown(f'<h2 style="{FONTS["h2_css"]}">Section</h2>', unsafe_allow_html=True)

# Caption
st.markdown(f'<p style="{FONTS["caption_css"]}">Helper text</p>', unsafe_allow_html=True)
```

---

## Testing Checklist

When implementing changes:

- [ ] All colors use `COLORS` tokens
- [ ] All spacing uses `SPACING` values
- [ ] Charts use `get_chart_layout()`
- [ ] State accessed via `state_manager`
- [ ] Typography uses `FONTS` constants
- [ ] No hard-coded design values
- [ ] Responsive on mobile/tablet/desktop
- [ ] Consistent with design system

---

## Future Enhancements

### Planned Features

1. **Theme Switcher** - Dark mode support
2. **Accessibility Mode** - High contrast, larger text
3. **Custom Color Palettes** - User-defined brand colors
4. **Export/Import State** - Save and restore user preferences
5. **A/B Testing Framework** - Test design variations

### Extensibility

The design system is built to be extensible:

```python
# Add new color
COLORS['custom_purple'] = '#8B5CF6'

# Add new spacing
SPACING['jumbo'] = '96px'

# Add new chart preset
CHART_CONFIG['ultra_compact'] = {
    'height': 200,
    'margin': {'l': 10, 'r': 10, 't': 20, 'b': 10}
}
```

---

## Support & Feedback

For questions or suggestions:

- Review the code in `src/app/design_system.py`
- Check examples in `src/app/main.py`
- Consult the UX/UI Audit Report in `docs/UX_UI_AUDIT_REPORT.md`

**Version History:**

- v2.3 (2026-01-22): Initial centralized design system
- v2.2: Previous iteration with 7 tabs
- v2.1: Original implementation

---

**Status**: ✅ Production Ready  
**Last Updated**: 2026-01-22  
**Maintainer**: Barcelona Housing Analytics Team
