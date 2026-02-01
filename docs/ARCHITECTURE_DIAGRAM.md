# Barcelona Housing Analytics - Architecture Diagram

## System Architecture (v2.3)

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                         (Streamlit App)                         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                           main.py                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Navigation (4 Main Tabs)                                 │  │
│  │  ┌──────────┬──────────┬──────────┬──────────┐           │  │
│  │  │ Overview │Analytics │Investment│Territory │           │  │
│  │  └──────────┴──────────┴──────────┴──────────┘           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                 │                                │
│         ┌───────────────────────┼───────────────────────┐       │
│         ▼                       ▼                       ▼       │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐ │
│  │design_system│        │state_manager│        │   styles    │ │
│  │    .py      │        │    .py      │        │    .py      │ │
│  └─────────────┘        └─────────────┘        └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Design Tokens   │    │ Session State    │    │ CSS Injection   │
│ • Colors        │    │ • FilterState    │    │ • Global Styles │
│ • Spacing       │    │ • ComparisonState│    │ • Components    │
│ • Typography    │    │ • ViewState      │    │ • Animations    │
│ • Charts        │    │ • Preferences    │    │ • Responsive    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Navigation Structure (v2.3)

```
┌─────────────────────────────────────────────────────────────────┐
│                        MAIN NAVIGATION                          │
└─────────────────────────────────────────────────────────────────┘

🏠 OVERVIEW
   └─ Market Cockpit
      • KPIs Dashboard
      • Quick Insights
      • Top Alerts

📊 ANALYTICS
   ├─ 📈 Análisis Estadístico
   │  • Distributions
   │  • Time Series
   │  • Statistical Tests
   │
   ├─ 👥 Demografía
   │  • Population Metrics
   │  • Age Distribution
   │  • Household Data
   │
   └─ 🔗 Correlaciones
      • Correlation Matrix
      • Scatter Plots
      • Relationship Analysis

💼 INVESTMENT
   ├─ 💡 Oportunidades
   │  • Yield Analysis
   │  • ROI Calculator
   │  • Investment Matrix
   │
   ├─ 🧠 Inteligencia de Mercado
   │  • Market Trends
   │  • Price Evolution
   │  • Demand Analysis
   │
   ├─ 🚨 Alertas
   │  • Price Alerts
   │  • Market Anomalies
   │  • Risk Indicators
   │
   └─ ⭐ Recomendaciones
      • Top Neighborhoods
      • Investment Strategies
      • Risk Assessment

🌍 TERRITORY
   ├─ 🗺️ Mapa Interactivo
   │  • Choropleth Maps
   │  • Geographic Filters
   │  • Spatial Analysis
   │
   ├─ 🌱 Social ESG
   │  • Education Index
   │  • Safety Metrics
   │  • Housing Quality
   │
   └─ ✅ Calidad de Datos
      • Completeness
      • Consistency
      • Data Quality Metrics

⚙️ UTILITIES (Sidebar)
   ├─ 📖 Diccionario
   ├─ 📥 Descargas
   └─ 📄 Reportes
```

## State Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION                         │
│              (Sidebar Filters: District, Year, Metric)          │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  sync_widgets_to_      │
                    │  filters()             │
                    └────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GLOBAL SESSION STATE                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FilterState                                             │   │
│  │  • selected_district: 'Eixample'                         │   │
│  │  • selected_barrio_id: 42                                │   │
│  │  • selected_year: 2024                                   │   │
│  │  • active_metric: 'price_per_sqm'                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
         ┌──────────┐    ┌──────────┐    ┌──────────┐
         │ Tab 1    │    │ Tab 2    │    │ Tab 3    │
         │ Overview │    │Analytics │    │Investment│
         └──────────┘    └──────────┘    └──────────┘
                 │               │               │
                 └───────────────┼───────────────┘
                                 ▼
                    ┌────────────────────────┐
                    │  get_filter_state()    │
                    │  Returns: FilterState  │
                    └────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  All views access      │
                    │  same consistent state │
                    └────────────────────────┘
```

## Design System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      design_system.py                           │
│                   (Single Source of Truth)                      │
└─────────────────────────────────────────────────────────────────┘
         │
         ├─────────────────────────────────────────────┐
         │                                             │
         ▼                                             ▼
┌──────────────────┐                          ┌──────────────────┐
│   styles.py      │                          │   views/*.py     │
│                  │                          │                  │
│ inject_global_   │                          │ • market_cockpit │
│ css()            │                          │ • demographics   │
│                  │                          │ • map_analysis   │
│ Uses:            │                          │                  │
│ • COLOR_TOKENS   │                          │ Uses:            │
│ • GRADIENTS      │                          │ • get_chart_     │
│ • SPACING        │                          │   layout()       │
│                  │                          │ • COLORS         │
└──────────────────┘                          │ • SPACING        │
                                              │ • FONTS          │
                                              └──────────────────┘
```

## Component Hierarchy

```
App (main.py)
│
├─ configure_page()
│  └─ inject_global_css()
│     └─ Uses design_system tokens
│
├─ init_session_state()
│  └─ Initialize all state objects
│
├─ render_sidebar()
│  ├─ Filters (District, Year, Metric)
│  ├─ Utilities Expander
│  └─ User Profile
│
└─ Main Tabs
   │
   ├─ 🏠 Overview
   │  └─ market_cockpit.render()
   │
   ├─ 📊 Analytics
   │  ├─ Sub-navigation (Radio)
   │  ├─ advanced_analytics.render()
   │  ├─ demographics.render()
   │  └─ correlations.render()
   │
   ├─ 💼 Investment
   │  ├─ Sub-navigation (Radio)
   │  ├─ investment_analysis.render()
   │  ├─ market_intelligence.render()
   │  ├─ alerts.render()
   │  └─ recommendations.render()
   │
   └─ 🌍 Territory
      ├─ Sub-navigation (Radio)
      ├─ map_analysis.render()
      ├─ esg_view.render()
      └─ data_quality.render()
```

## Data Flow

```
┌─────────────┐
│  Database   │
│  (SQLite)   │
└─────────────┘
       │
       ▼
┌─────────────┐
│data_loader  │
│    .py      │
└─────────────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│ API Client  │   │ Direct DB   │
│ (FastAPI)   │   │ Access      │
└─────────────┘   └─────────────┘
       │                 │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │  Views (render) │
       └─────────────────┘
                │
                ▼
       ┌─────────────────┐
       │ Plotly Charts   │
       │ + Design System │
       └─────────────────┘
                │
                ▼
       ┌─────────────────┐
       │  User Display   │
       └─────────────────┘
```

## Key Principles

### 1. Single Source of Truth (SSOT)

```
design_system.py
    ↓
All visual decisions flow from here
    ↓
No hard-coded colors, spacing, or typography
```

### 2. Global Context Pattern

```
User Action → sync_widgets_to_filters() → Global State
                                              ↓
                                    All tabs access same state
```

### 3. Progressive Disclosure

```
4 Main Tabs (High-level)
    ↓
Sub-navigation (Contextual)
    ↓
Detailed Views (Focused)
```

### 4. Backward Compatibility

```
New System (design_system.py)
    ↓
Legacy Support Layer (COLOR_TOKENS, GRADIENTS)
    ↓
Old Code Still Works
```

---

**Version**: 2.3  
**Last Updated**: 2026-01-22  
**Status**: ✅ Production Ready
