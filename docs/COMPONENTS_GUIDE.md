# Reusable Components Guide

**Version**: 2.3  
**Date**: 2026-01-23  
**Status**: ✅ Production Ready

---

## 📋 Overview

This guide explains how to use the reusable component system built on top of the design system. These components ensure visual consistency across all views.

---

## 📁 Component Structure

```
src/app/components/
├── __init__.py          # Package exports
├── cards.py             # KPI cards, info cards, stat cards
├── charts.py            # Plotly chart utilities
└── layout.py            # Page headers, grids, spacers
```

---

## 🎨 Component Categories

### 1. **Cards** (`cards.py`)

#### `render_kpi_card()`

Standardized KPI card with hover effects.

**Usage:**

```python
from src.app.components import render_kpi_card

render_kpi_card(
    title="Precio Medio",
    value="4,118 €/m²",
    delta="+5.2%",
    help_text="Precio medio de venta en 2025",
    icon="💰",
    color_scheme="primary"  # 'primary', 'secondary', 'success', 'warning', 'danger'
)
```

**Features:**

- Hover animation (lifts up)
- Optional delta indicator
- Tooltip support
- Color schemes from design system
- Consistent 140px min-height

#### `render_info_card()`

Information/callout card.

**Usage:**

```python
from src.app.components import render_info_card

render_info_card(
    title="Datos Actualizados",
    content="Los datos se actualizan mensualmente desde OpenData BCN.",
    icon="ℹ️",
    card_type="info"  # 'info', 'success', 'warning', 'danger'
)
```

#### `render_stat_card()`

Compact stat display.

**Usage:**

```python
from src.app.components import render_stat_card

render_stat_card(
    label="Fuentes de Datos",
    value="3",
    sublabel="OpenData BCN, Idealista, IDESCAT",
    compact=True
)
```

#### `render_metric_row()`

Row of metrics in equal columns.

**Usage:**

```python
from src.app.components import render_metric_row

metrics = [
    {'label': 'Barrios', 'value': '73'},
    {'label': 'Registros', 'value': '6,958'},
    {'label': 'Años', 'value': '2012-2025'}
]

render_metric_row(metrics)
```

---

### 2. **Charts** (`charts.py`)

#### `apply_standard_theme()`

Apply design system theme to any Plotly chart.

**Usage:**

```python
from src.app.components import apply_standard_theme
import plotly.express as px

fig = px.bar(df, x='barrio', y='precio')
fig = apply_standard_theme(
    fig,
    height_mode='standard',  # 'compact', 'standard', 'expanded', 'tall'
    show_legend=True,
    title='Precios por Barrio'
)

st.plotly_chart(fig, use_container_width=True)
```

#### `create_bar_chart()`

Quick standardized bar chart.

**Usage:**

```python
from src.app.components import create_bar_chart

fig = create_bar_chart(
    data=df,
    x='barrio',
    y='precio',
    title='Precios por Barrio',
    height_mode='standard'
)

st.plotly_chart(fig, use_container_width=True)
```

#### `create_line_chart()`

Quick standardized line chart.

**Usage:**

```python
from src.app.components import create_line_chart

fig = create_line_chart(
    data=df_trends,
    x='year',
    y='precio',
    title='Evolución de Precios',
    markers=True
)

st.plotly_chart(fig, use_container_width=True)
```

#### `get_standard_colors()`

Get color palette for charts.

**Usage:**

```python
from src.app.components import get_standard_colors

colors = get_standard_colors('primary')
# Returns: ['#2F80ED', '#56CCF2', '#10B981', ...]
```

---

### 3. **Layout** (`layout.py`)

#### `render_page_header()`

Standardized page header with breadcrumbs.

**Usage:**

```python
from src.app.components import render_page_header

render_page_header(
    title="Análisis de Mercado",
    subtitle="Visualización de precios y tendencias del mercado inmobiliario",
    breadcrumbs=["Home", "Analytics", "Market"],
    icon="📊"
)
```

#### `render_section_header()`

H2 section header.

**Usage:**

```python
from src.app.components import render_section_header

render_section_header(
    title="Métricas Principales",
    icon="📊",
    subtitle="Indicadores clave del mercado"
)
```

#### `render_hero_section()`

Hero banner with gradient.

**Usage:**

```python
from src.app.components import render_hero_section

render_hero_section(
    title="Barcelona Housing Analytics",
    subtitle="Dashboard de análisis inmobiliario • Año 2025",
    background_gradient=True
)
```

#### `create_metric_grid()`

Responsive grid for metrics.

**Usage:**

```python
from src.app.components import create_metric_grid, render_kpi_card

cols = create_metric_grid(num_columns=4, gap="medium")

with cols[0]:
    render_kpi_card("Precio Medio", "4,118 €/m²", "+5.2%")
with cols[1]:
    render_kpi_card("Barrios", "73")
# ...
```

#### `create_two_column_layout()`

Two-column layout with custom ratio.

**Usage:**

```python
from src.app.components import create_two_column_layout

col_left, col_right = create_two_column_layout(left_ratio=1.6, gap="large")

with col_left:
    # Map or main content
    pass

with col_right:
    # Sidebar or secondary content
    pass
```

#### `render_spacer()`

Vertical spacing.

**Usage:**

```python
from src.app.components import render_spacer

render_spacer('xl')  # 'xs', 'sm', 'md', 'lg', 'xl', 'xxl'
```

#### `render_divider()`

Horizontal divider.

**Usage:**

```python
from src.app.components import render_divider

render_divider('md')
```

---

## 🚀 **Complete Example: Refactoring a View**

### **Before** (Old Pattern)

```python
import streamlit as st

def render():
    st.title("🌱 Social ESG")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric("ESG Score", "85", "+2%")
    col2.metric("Green Space", "12 m²", "-0.5%")
    col3.metric("Safety Index", "7.8", "+0.3")

    # Chart with inconsistent styling
    fig = px.bar(df, x='barrio', y='score')
    fig.update_layout(height=500)
    st.plotly_chart(fig)
```

### **After** (Using Components)

```python
import streamlit as st
from src.app.components import (
    render_page_header,
    render_section_header,
    create_metric_grid,
    render_kpi_card,
    create_bar_chart,
    render_spacer
)

def render():
    # Standardized header
    render_page_header(
        title="Social ESG Analysis",
        subtitle="Evaluating neighborhood impact through social, environmental, and governance metrics",
        breadcrumbs=["Home", "Territory", "ESG"],
        icon="🌱"
    )

    # Section with KPIs
    render_section_header("Key Performance Indicators", icon="📊")

    cols = create_metric_grid(num_columns=3, gap="medium")

    with cols[0]:
        render_kpi_card(
            title="ESG Score",
            value="85/100",
            delta="+2.4%",
            help_text="Composite index based on 2025 data",
            color_scheme="success"
        )

    with cols[1]:
        render_kpi_card(
            title="Green Space",
            value="12 m²",
            delta="-0.5%",
            help_text="Per inhabitant",
            color_scheme="warning"
        )

    with cols[2]:
        render_kpi_card(
            title="Safety Index",
            value="7.8/10",
            delta="+0.3",
            color_scheme="primary"
        )

    render_spacer('xl')

    # Standardized chart
    render_section_header("ESG Score by Neighborhood", icon="📊")

    fig = create_bar_chart(
        data=df,
        x='barrio',
        y='score',
        title='ESG Score Distribution',
        height_mode='standard'
    )

    st.plotly_chart(fig, use_container_width=True)
```

---

## ✅ **Benefits**

1. **Consistency**: All views look like they belong to the same app
2. **Maintainability**: Change once in components, applies everywhere
3. **Speed**: Faster development with pre-built components
4. **Quality**: Professional, tested components
5. **Accessibility**: Built-in hover states, tooltips, responsive design

---

## 📝 **Best Practices**

### **DO:**

✅ Use components for all new views  
✅ Import only what you need  
✅ Use color schemes from design system  
✅ Apply standard themes to all charts  
✅ Use semantic component names

### **DON'T:**

❌ Mix components with raw HTML  
❌ Hard-code colors or spacing  
❌ Create custom cards when components exist  
❌ Skip the design system  
❌ Duplicate component logic

---

## 🔄 **Migration Checklist**

When refactoring an existing view:

- [ ] Replace `st.title()` with `render_page_header()`
- [ ] Replace `st.metric()` with `render_kpi_card()`
- [ ] Replace `st.columns()` with `create_metric_grid()`
- [ ] Apply `apply_standard_theme()` to all charts
- [ ] Use `render_section_header()` for sections
- [ ] Replace `st.markdown("---")` with `render_divider()`
- [ ] Use `render_spacer()` for vertical spacing
- [ ] Test on different screen sizes

---

## 📚 **Additional Resources**

- **Design System**: `docs/DESIGN_SYSTEM_GUIDE.md`
- **Quick Reference**: `docs/DESIGN_SYSTEM_QUICK_REFERENCE.md`
- **Architecture**: `docs/ARCHITECTURE_DIAGRAM.md`
- **Source Code**: `src/app/components/`

---

**Version**: 2.3  
**Last Updated**: 2026-01-23  
**Status**: ✅ Production Ready
