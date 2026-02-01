# Design System Quick Reference

**Version**: 2.3 | **Date**: 2026-01-22

---

## 🎨 Colors

### Import

```python
from src.app.design_system import COLORS
```

### Primary Colors

```python
COLORS['primary']           # '#2F80ED' - Bright Blue
COLORS['primary_dark']      # '#005EB8' - Dark Blue
COLORS['secondary']         # '#56CCF2' - Cyan
```

### Text Colors

```python
COLORS['text']['primary']   # '#1A1A1A' - Main Text
COLORS['text']['secondary'] # '#8E92BC' - Subtle Text
COLORS['text']['success']   # '#48BB78' - Success
COLORS['text']['warning']   # '#ED8936' - Warning
COLORS['text']['danger']    # '#F56565' - Error
```

### Semantic Colors

```python
COLORS['accent_blue']       # '#005EB8'
COLORS['accent_red']        # '#EF4444'
COLORS['accent_green']      # '#10B981'
COLORS['accent_yellow']     # '#F59E0B'
```

---

## 📏 Spacing (4px Grid)

### Import

```python
from src.app.design_system import SPACING, get_spacing_value
```

### Values

```python
SPACING['xs']   # '4px'   - Minimal
SPACING['sm']   # '8px'   - Tight
SPACING['md']   # '16px'  - Standard
SPACING['lg']   # '24px'  - Section
SPACING['xl']   # '32px'  - Large
SPACING['xxl']  # '48px'  - Extra Large
```

### Usage

```python
margin = get_spacing_value('lg')  # Returns '24px'
```

---

## 🔤 Typography

### Import

```python
from src.app.design_system import FONTS
```

### Heading Styles

```python
# As dictionaries
FONTS['h1']  # {'size': '32px', 'weight': '700', ...}
FONTS['h2']  # {'size': '24px', 'weight': '600', ...}
FONTS['h3']  # {'size': '18px', 'weight': '600', ...}

# As CSS strings (for st.markdown)
FONTS['h1_css']      # Complete CSS string
FONTS['h2_css']      # Complete CSS string
FONTS['caption_css'] # Complete CSS string
```

### Example

```python
st.markdown(
    f'<h1 style="{FONTS["h1_css"]}">Page Title</h1>',
    unsafe_allow_html=True
)
```

---

## 📊 Chart Configurations

### Import

```python
from src.app.design_system import get_chart_layout, get_color_palette
```

### Presets

```python
# Get layout configuration
layout = get_chart_layout('compact')   # 300px height
layout = get_chart_layout('standard')  # 500px height
layout = get_chart_layout('expanded')  # 700px height
layout = get_chart_layout('tall')      # 600px height

# Apply to Plotly figure
fig.update_layout(**layout)
```

### Custom Overrides

```python
layout = get_chart_layout('standard', title='My Chart', showlegend=False)
fig.update_layout(**layout)
```

### Color Palettes

```python
colors = get_color_palette('primary')      # Primary brand colors
colors = get_color_palette('categorical')  # Multi-category
colors = get_color_palette('diverging')    # Diverging scale
colors = get_color_palette('sequential_blue')  # Sequential

# Use in chart
fig = px.bar(df, color_discrete_sequence=colors)
```

---

## 🔄 State Management

### Import

```python
from src.app.state_manager import (
    init_session_state,
    update_filter_state,
    get_filter_state,
    sync_widgets_to_filters,
)
```

### Initialize (Once in main.py)

```python
init_session_state()
```

### Update Filters

```python
update_filter_state(
    district='Eixample',
    barrio_id=42,
    year=2024,
    metric='price_per_sqm'
)
```

### Get Current State

```python
state = get_filter_state()
print(state.selected_district)  # 'Eixample'
print(state.selected_year)      # 2024
print(state.active_metric)      # 'price_per_sqm'
```

### Sync Widgets

```python
# After widget interactions
sync_widgets_to_filters(
    district=selected_district,
    year=selected_year,
    metric=selected_metric
)
```

---

## 🎯 Common Patterns

### Pattern 1: Styled Header

```python
from src.app.design_system import FONTS, SPACING

st.markdown(f"""
<div style="margin-bottom: {SPACING['lg']};">
    <h1 style="{FONTS['h1_css']}">Page Title</h1>
    <p style="{FONTS['caption_css']}">Subtitle or description</p>
</div>
""", unsafe_allow_html=True)
```

### Pattern 2: Standardized Chart

```python
from src.app.design_system import get_chart_layout, get_color_palette
import plotly.express as px

# Create chart
fig = px.bar(df, x='barrio', y='price')

# Apply design system
layout = get_chart_layout('standard', title='Price by Neighborhood')
colors = get_color_palette('primary')

fig.update_layout(**layout)
fig.update_traces(marker_color=colors[0])

st.plotly_chart(fig, use_container_width=True)
```

### Pattern 3: Access Global State

```python
from src.app.state_manager import get_filter_state

def render():
    # Get current filters
    state = get_filter_state()

    # Use in queries
    data = load_data(
        year=state.selected_year,
        district=state.selected_district
    )

    # Display
    st.write(f"Showing data for {state.selected_district} in {state.selected_year}")
```

### Pattern 4: Colored Text

```python
from src.app.design_system import COLORS

st.markdown(
    f'<span style="color: {COLORS["text"]["success"]};">✓ Success</span>',
    unsafe_allow_html=True
)

st.markdown(
    f'<span style="color: {COLORS["text"]["danger"]};">✗ Error</span>',
    unsafe_allow_html=True
)
```

---

## ⚠️ Don'ts (Anti-Patterns)

### ❌ Don't Hard-code Colors

```python
# BAD
st.markdown('<div style="color: #1A1A1A;">')

# GOOD
from src.app.design_system import COLORS
st.markdown(f'<div style="color: {COLORS["text"]["primary"]};">')
```

### ❌ Don't Hard-code Spacing

```python
# BAD
st.markdown('<div style="padding: 16px;">')

# GOOD
from src.app.design_system import SPACING
st.markdown(f'<div style="padding: {SPACING["md"]};">')
```

### ❌ Don't Duplicate Chart Config

```python
# BAD
fig.update_layout(
    height=500,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    # ... many lines
)

# GOOD
from src.app.design_system import get_chart_layout
fig.update_layout(**get_chart_layout('standard'))
```

### ❌ Don't Pass State as Parameters

```python
# BAD
def render(year: int, distrito: str, metric: str):
    # Manual parameter passing

# GOOD
from src.app.state_manager import get_filter_state

def render():
    state = get_filter_state()
    year = state.selected_year
    distrito = state.selected_district
```

---

## 📱 Responsive Design

### Breakpoints

```python
from src.app.design_system import BREAKPOINTS

BREAKPOINTS['mobile']     # '640px'
BREAKPOINTS['tablet']     # '768px'
BREAKPOINTS['desktop']    # '1024px'
BREAKPOINTS['wide']       # '1280px'
```

### Usage

```python
st.markdown(f"""
<style>
@media (max-width: {BREAKPOINTS['mobile']}) {{
    .my-component {{
        font-size: 14px;
    }}
}}
</style>
""", unsafe_allow_html=True)
```

---

## 🎨 Shadows & Elevation

### Import

```python
from src.app.design_system import SHADOWS
```

### Values

```python
SHADOWS['sm']  # '0px 2px 8px rgba(29, 22, 23, 0.05)'
SHADOWS['md']  # '0px 10px 40px rgba(29, 22, 23, 0.1)'
SHADOWS['lg']  # '0px 15px 45px rgba(29, 22, 23, 0.12)'
SHADOWS['xl']  # '0px 20px 50px rgba(29, 22, 23, 0.15)'
```

### Usage

```python
st.markdown(f"""
<div style="box-shadow: {SHADOWS['md']}; padding: {SPACING['lg']};">
    Card content
</div>
""", unsafe_allow_html=True)
```

---

## 🔧 Utility Functions

### Gradient CSS

```python
from src.app.design_system import create_gradient_css

gradient = create_gradient_css('cool')  # Returns CSS gradient string
```

### Validate Color

```python
from src.app.design_system import validate_color

is_valid = validate_color('#2F80ED')  # True
is_valid = validate_color('invalid')  # False
```

---

## 📚 Full Documentation

For complete documentation, see:

- **Design System Guide**: `docs/DESIGN_SYSTEM_GUIDE.md`
- **Implementation Summary**: `docs/DESIGN_SYSTEM_IMPLEMENTATION.md`
- **Architecture Diagram**: `docs/ARCHITECTURE_DIAGRAM.md`

---

## 🆘 Quick Help

### I need to...

**...add a new color**

```python
# In design_system.py
COLORS['my_custom_color'] = '#FF5733'
```

**...create a custom chart preset**

```python
# In design_system.py
CHART_CONFIG['my_preset'] = {
    'height': 400,
    'margin': {'l': 30, 'r': 30, 't': 30, 'b': 30}
}
```

**...access user preferences**

```python
from src.app.state_manager import get_user_preference

theme = get_user_preference('theme', default='light')
```

**...track session analytics**

```python
from src.app.state_manager import increment_page_view, get_session_metadata

increment_page_view()
metadata = get_session_metadata()
print(f"Session duration: {metadata.session_duration}s")
```

---

**Version**: 2.3  
**Last Updated**: 2026-01-22  
**Status**: ✅ Production Ready
