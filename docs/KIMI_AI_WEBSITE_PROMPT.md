# Kimi AI Website Builder - Comprehensive Project Prompt

## 🎯 Project Overview

Create a **modern, premium web application** to showcase the **Barcelona Housing Demographics Analyzer** - a comprehensive data analytics platform that combines housing market data, demographic insights, and machine learning to provide actionable intelligence about Barcelona's real estate market.

This website should serve as a **professional alternative to Streamlit**, featuring:

- Modern, dynamic UI with rich aesthetics
- Interactive data visualizations
- Real-time analytics dashboard
- Professional presentation of complex data insights

---

## 🏗️ Project Context

### What is Barcelona Housing Demographics Analyzer?

A sophisticated ETL pipeline and analytics platform that:

- **Analyzes 73 Barcelona neighborhoods** with comprehensive demographic and housing data
- **Integrates 20+ data sources**: TMB transit data, OpenStreetMap, Open Data BCN, INE statistics, Idealista real estate listings
- **Processes 98,604+ records** across 21 database tables
- **Provides ML-powered insights**: Price predictions (Linear, Lasso, Ridge), gentrification risk analysis, investment opportunity mapping
- **Award-winning accuracy**: Predictive models ranked **Top of Class** in the Barcelona Apartment Price Prediction competition (Team Sarria)
- **Tracks temporal trends**: Historical data from 2011-2025 (14+ years)

### Current State

- **Backend**: Python-based ETL pipeline with SQLite database (star schema)
- **Current UI**: Streamlit dashboard (functional but basic)
- **Goal**: Create a modern, production-ready web interface that wows users

---

## 🎨 Design Requirements

### Visual Excellence (CRITICAL)

**This is NOT a simple MVP - create a PREMIUM, state-of-the-art design:**

1. **Color Palette** (Use these exact colors):
   - **Primary Blue**: `#2F80ED` (Bright, professional)
   - **Secondary Cyan**: `#56CCF2` (Accents, highlights)
   - **Dark Blue**: `#005EB8` (Headers, important elements)
   - **Success Green**: `#10B981`
   - **Warning Yellow**: `#F59E0B`
   - **Danger Red**: `#EF4444`
   - **Background Light**: `#F4F5F7`
   - **Card Background**: `#FFFFFF`
   - **Text Primary**: `#1A1A1A`
   - **Text Secondary**: `#8E92BC`

2. **Typography**:
   - **Font Family**: Use Google Fonts - "Inter" for body, "Outfit" for headings
   - **Heading Hierarchy**:
     - H1: 32px, weight 700
     - H2: 24px, weight 600
     - H3: 20px, weight 600
     - Body: 16px, weight 400
     - Caption: 14px, weight 400

3. **Spacing System** (4px grid):
   - xs: 4px
   - sm: 8px
   - md: 16px
   - lg: 24px
   - xl: 32px
   - xxl: 48px

4. **Visual Effects**:
   - **Glassmorphism**: Use for cards and overlays
   - **Smooth gradients**: Linear gradients for hero sections and CTAs
   - **Micro-animations**: Hover effects, loading states, transitions
   - **Shadows**: Subtle elevation (0px 2px 8px rgba(29, 22, 23, 0.05))
   - **Border radius**: 12-16px for cards, 8px for buttons

---

## 📐 Website Structure

### Navigation (4 Main Sections)

#### 1. 🏠 **Home / Overview**

**Purpose**: First impression, project introduction, key metrics

**Components**:

- **Hero Section**:
  - Gradient background (primary → secondary)
  - Main title: "Barcelona Housing Analytics"
  - Subtitle: "Data-driven insights for Barcelona's real estate market"
  - CTA buttons: "Explore Dashboard" | "View Analytics"
  - Animated statistics counter: "73 Neighborhoods | 98K+ Records | 20+ Data Sources"

- **Key Metrics Dashboard** (4 KPI cards):
  - **Average Price/m²**: €3,161 (with trend indicator)
  - **Neighborhoods Analyzed**: 73/73 (100% coverage)
  - **Data Quality Score**: 100/100 ✅
  - **Years of Data**: 2011-2025 (14 years)

- **Interactive Map Preview**:
  - Barcelona neighborhoods map with color-coded price ranges
  - Hover to see neighborhood details
  - Click to navigate to detailed analytics

- **Project Highlights** (3 columns):
  - **Comprehensive Data**: 21 database tables, star schema architecture
  - **ML-Powered**: Ridge/Lasso/Linear price forecasting (Top of Class Accuracy), clustering analysis
  - **Real-time Updates**: ETL pipeline with 95%+ success rate

#### 2. 📊 **Analytics Dashboard**

**Purpose**: Interactive data exploration and visualization

**Sub-sections** (Tabs or Accordion):

**A. Market Analysis**:

- **Price Evolution Chart** (Line chart, 2012-2025):
  - Interactive time-series with zoom/pan
  - Toggle between sale prices and rental prices
  - District filter dropdown
  - Annotations for key market events

- **Price Distribution** (Box plot + Histogram):
  - Price per m² distribution across neighborhoods
  - Outlier detection visualization
  - Statistical summary panel

- **Heatmap**:
  - Barcelona map with price intensity
  - Color gradient from low (green) to high (red)
  - Interactive tooltips with neighborhood details

**B. Demographics**:

- **Population Pyramid**:
  - Age distribution by gender
  - Animated transitions between years
  - Compare multiple neighborhoods

- **Immigration Trends**:
  - Percentage of foreign population over time
  - Top nationalities breakdown (pie chart)

- **Household Statistics**:
  - Average household size
  - Density (inhabitants/km²)
  - Aging index visualization

**C. Investment Intelligence**:

- **Yield Analysis** (Scatter plot):
  - X-axis: Entry cost (sale price/m²)
  - Y-axis: Return (rental price)
  - Bubble size: Number of listings
  - Color: Neighborhood category

- **Opportunity Score**:
  - Custom metric combining price, yield, demographics
  - Top 10 neighborhoods ranking
  - Risk indicators (gentrification, tourist pressure)

- **Correlation Matrix**:
  - Heatmap showing relationships between variables
  - Interactive: click to see detailed scatter plots

**D. Predictive Forecasting (NEW)**:

- **Price Prediction Engine**:
  - Showcase the **Ridge Model** (Best performer: MSE 29165.37)
  - Interactive "What-if" scenario builder: input surface area, bedrooms, and neighborhood to see predicted price
  - Model Comparison: Visual comparison of Linear, Lasso, and Ridge performance metrics

- **Feature Importance**:
  - Bar chart showing which factors (e.g., transit proximity, income, density) most impact property value
  - Explainer on how Lasso regression was used for feature selection

#### 3. 🗺️ **Territory Explorer**

**Purpose**: Geographic and neighborhood-specific insights

**Components**:

- **Interactive Map** (Full-screen):
  - GeoJSON boundaries for 73 neighborhoods
  - Layer toggles:
    - Housing prices
    - Demographics
    - Transit accessibility
    - Tourist pressure (Airbnb density)
    - Environmental quality (air quality, noise)
  - Click neighborhood → Side panel with detailed scorecard

- **Neighborhood Scorecard** (Side panel):
  - Name, district, population
  - Key metrics:
    - Price/m² (sale & rental)
    - Yield percentage
    - Population density
    - Average income
    - Accessibility score
    - Environmental score
  - Trend indicators (↑↓ vs previous year)
  - "Compare" button to add to comparison view

- **District Comparison Tool**:
  - Select up to 4 neighborhoods
  - Radar chart comparing 8-10 dimensions
  - Table with detailed metrics

#### 4. 🔬 **Data & Methodology**

**Purpose**: Transparency, technical details, data quality

**Components**:

- **Data Sources** (Cards grid):
  - Each source as a card:
    - Logo/icon
    - Name (e.g., "TMB - Public Transit")
    - Description
    - Coverage (e.g., "1,071 bus stops, 165 rail stations")
    - Last updated date
  - Sources to include:
    - TMB (Transports Metropolitans de Barcelona)
    - OpenStreetMap
    - Open Data BCN
    - INE (Instituto Nacional de Estadística)
    - Idealista
    - IDESCAT
    - Portal de Dades

- **Database Schema Visualization**:
  - Interactive ERD (Entity-Relationship Diagram)
  - Show star schema: 1 dimension table (dim_barrios) → 21 fact tables
  - Hover over table to see columns
  - Click to see sample data

- **Data Quality Dashboard**:
  - Overall health score: 100/100 ✅
  - Completeness by table (bar chart)
  - Temporal consistency (timeline)
  - Outlier detection summary
  - Coverage map (90.1% of neighborhoods)

- **ETL Pipeline Diagram**:
  - Visual flowchart: Extract → Transform → Load
  - Show data sources → processing steps → database tables
  - Success rate: 95%+
  - Processing time metrics

- **Methodology**:
  - **Yield Calculation**:
    - Dual methodology: Real Yield (Incasòl data) vs Market Yield (Idealista)
    - Formula: `(Monthly Rent * 12) / (Sale Price/m² * 70m²)`
  - **Gentrification Index**:
    - Based on education levels, income changes, price evolution
  - **Accessibility Score**:
    - Distance to metro, bus stops, bike stations
    - Weighted by frequency and coverage

---

## 🎯 Key Features to Implement

### 1. **Interactive Visualizations**

Use **Chart.js**, **Plotly.js**, or **D3.js** for:

- Line charts (time-series)
- Bar charts (comparisons)
- Scatter plots (correlations)
- Heatmaps (geographic and correlation)
- Box plots (distributions)
- Radar charts (multi-dimensional comparisons)

**Requirements**:

- Smooth animations on load
- Hover tooltips with detailed info
- Responsive (adapt to mobile/tablet/desktop)
- Export options (PNG, SVG, CSV)
- Dark mode support (optional)

### 2. **Filters & Controls**

**Global Filters** (Sticky sidebar or top bar):

- **Year Selector**: Slider (2011-2025) or dropdown
- **District Filter**: Multi-select dropdown (10 districts)
- **Neighborhood Filter**: Searchable dropdown (73 neighborhoods)
- **Metric Toggle**: Switch between sale/rental prices
- **Reset Filters** button

**Filter Behavior**:

- Apply to all charts simultaneously
- Smooth transitions when changing filters
- Show loading state during data fetch
- Persist filters in URL (shareable links)

### 3. **Responsive Design**

**Breakpoints**:

- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

**Adaptations**:

- Mobile: Single column, collapsible sections, bottom navigation
- Tablet: 2-column grid, side navigation
- Desktop: 3-column grid, persistent sidebar

### 4. **Performance Optimization**

- **Lazy loading**: Load charts only when visible
- **Data pagination**: Limit initial data load
- **Caching**: Cache API responses
- **Code splitting**: Separate bundles for each section
- **Image optimization**: Use WebP, lazy load images

### 5. **Accessibility (A11y)**

- **ARIA labels**: All interactive elements
- **Keyboard navigation**: Tab through all controls
- **Color contrast**: WCAG AA compliant
- **Screen reader support**: Descriptive alt text
- **Focus indicators**: Clear visual feedback

---

## 📊 Sample Data to Display

### Key Statistics (for Hero Section)

```json
{
  "totalNeighborhoods": 73,
  "totalRecords": 98604,
  "dataSources": 20,
  "avgPricePerSqm": 3161,
  "priceRange": { "min": 343, "max": 12154 },
  "avgPopulation": 23469,
  "dataQualityScore": 100,
  "completenessAvg": 88.31,
  "yearsOfData": "2011-2025"
}
```

### Top 5 Most Expensive Neighborhoods (Example)

```json
[
  {
    "name": "Pedralbes",
    "pricePerSqm": 6723,
    "district": "Les Corts",
    "trend": "+5.2%"
  },
  {
    "name": "Sarrià",
    "pricePerSqm": 6154,
    "district": "Sarrià-Sant Gervasi",
    "trend": "+3.8%"
  },
  {
    "name": "Tres Torres",
    "pricePerSqm": 5892,
    "district": "Sarrià-Sant Gervasi",
    "trend": "+4.1%"
  },
  {
    "name": "Sant Gervasi - Galvany",
    "pricePerSqm": 5234,
    "district": "Sarrià-Sant Gervasi",
    "trend": "+2.9%"
  },
  {
    "name": "Dreta de l'Eixample",
    "pricePerSqm": 4987,
    "district": "Eixample",
    "trend": "+6.3%"
  }
]
```

### Top 5 Best Investment Opportunities (Example)

```json
[
  {
    "name": "Poblenou",
    "yield": 4.8,
    "pricePerSqm": 3890,
    "score": 8.5,
    "reason": "High growth potential"
  },
  {
    "name": "Gràcia",
    "yield": 4.2,
    "pricePerSqm": 4120,
    "score": 8.2,
    "reason": "Strong rental demand"
  },
  {
    "name": "Sant Antoni",
    "yield": 4.5,
    "pricePerSqm": 4350,
    "score": 8.0,
    "reason": "Central location"
  },
  {
    "name": "Sants",
    "yield": 4.1,
    "pricePerSqm": 3650,
    "score": 7.8,
    "reason": "Good transport links"
  },
  {
    "name": "Horta",
    "yield": 5.2,
    "pricePerSqm": 2890,
    "score": 7.5,
    "reason": "Affordable entry"
  }
]
```

### Database Tables Overview

```json
{
  "dimensionTables": [
    {
      "name": "dim_barrios",
      "records": 73,
      "description": "Master table of 73 Barcelona neighborhoods"
    },
    {
      "name": "dim_tiempo",
      "records": 168,
      "description": "Time dimension (annual & quarterly periods)"
    }
  ],
  "factTables": [
    {
      "name": "fact_precios",
      "records": 6356,
      "completeness": 100,
      "description": "Housing prices (sale & rental)"
    },
    {
      "name": "fact_demografia_ampliada",
      "records": 2256,
      "completeness": 100,
      "description": "Detailed demographics by age, sex, nationality"
    },
    {
      "name": "fact_oferta_idealista",
      "records": 1898,
      "completeness": 100,
      "description": "Idealista real estate listings"
    },
    {
      "name": "fact_presion_turistica",
      "records": 2141,
      "completeness": 100,
      "description": "Airbnb tourist pressure"
    },
    {
      "name": "fact_renta",
      "records": 73,
      "completeness": 100,
      "description": "Household income statistics"
    },
    {
      "name": "fact_movilidad",
      "records": 73,
      "completeness": 100,
      "description": "Transit accessibility metrics"
    }
  ],
  "mlModelPerformance": {
    "bestModel": "Ridge Regression",
    "metrics": {
      "MSE": 29165.37,
      "alpha": 0
    },
    "competition": "Top of the Class - Team Sarria (Kaggle 2023)"
  }
}
```

---

## 🛠️ Technical Specifications

### Technology Stack Recommendations

**Frontend**:

- **Framework**: Next.js 14+ (React) or Vite + React
- **Styling**: Vanilla CSS with CSS Variables (for design system)
- **Charts**: Plotly.js or Chart.js
- **Maps**: Leaflet.js or Mapbox GL JS
- **Icons**: Lucide React or Heroicons
- **Animations**: Framer Motion

**Backend** (if needed):

- **API**: FastAPI (already exists in project)
- **Database**: SQLite (already exists: `data/processed/database.db`)
- **Endpoints**:
  - `GET /barrios` - List all neighborhoods
  - `GET /barrios/{id}` - Neighborhood details
  - `GET /stats/prices` - Price statistics
  - `GET /stats/demographics` - Demographic data
  - `GET /accessibility/rankings` - Accessibility scores

**Deployment**:

- **Hosting**: Vercel, Netlify, or AWS Amplify
- **API**: Docker container on AWS ECS or Railway
- **Database**: SQLite file on S3 or local to API container

### File Structure

```
barcelona-housing-website/
├── public/
│   ├── images/
│   │   ├── logo.svg
│   │   ├── hero-background.webp
│   │   └── data-sources/
│   └── data/
│       └── barcelona-neighborhoods.geojson
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.jsx
│   │   │   ├── Footer.jsx
│   │   │   └── Navigation.jsx
│   │   ├── charts/
│   │   │   ├── PriceEvolutionChart.jsx
│   │   │   ├── DistributionChart.jsx
│   │   │   ├── CorrelationMatrix.jsx
│   │   │   └── YieldScatterPlot.jsx
│   │   ├── maps/
│   │   │   ├── InteractiveMap.jsx
│   │   │   └── NeighborhoodLayer.jsx
│   │   ├── cards/
│   │   │   ├── KPICard.jsx
│   │   │   ├── NeighborhoodCard.jsx
│   │   │   └── DataSourceCard.jsx
│   │   └── filters/
│   │       ├── YearSelector.jsx
│   │       ├── DistrictFilter.jsx
│   │       └── MetricToggle.jsx
│   ├── pages/
│   │   ├── index.jsx (Home)
│   │   ├── analytics.jsx
│   │   ├── territory.jsx
│   │   └── methodology.jsx
│   ├── styles/
│   │   ├── globals.css
│   │   ├── design-system.css
│   │   └── components.css
│   ├── utils/
│   │   ├── api.js (API client)
│   │   ├── formatters.js (Number, date formatting)
│   │   └── colors.js (Color palettes)
│   └── data/
│       └── mockData.js (Sample data for development)
├── package.json
└── README.md
```

---

## 🎨 Component Examples

### 1. KPI Card Component

```jsx
<KPICard
  title="Average Price/m²"
  value="€3,161"
  delta="+5.2%"
  trend="up"
  icon="💰"
  colorScheme="primary"
  helpText="Average sale price per square meter in 2024"
/>
```

**Visual Design**:

- Card with glassmorphism effect
- Large value (36px, bold)
- Small title (12px, uppercase, letter-spacing)
- Delta with color coding (green ↑, red ↓)
- Subtle gradient background
- Hover effect: slight elevation increase

### 2. Interactive Map

```jsx
<InteractiveMap
  neighborhoods={neighborhoodsGeoJSON}
  metric="pricePerSqm"
  colorScale="sequential"
  onNeighborhoodClick={handleClick}
  layers={["prices", "demographics", "transit"]}
/>
```

**Features**:

- GeoJSON rendering with Leaflet/Mapbox
- Color-coded by selected metric
- Hover tooltip with neighborhood name + value
- Click to open detail panel
- Layer toggle controls
- Zoom/pan controls
- Legend with color scale

### 3. Price Evolution Chart

```jsx
<PriceEvolutionChart
  data={priceTimeSeriesData}
  metric="pricePerSqm"
  neighborhoods={selectedNeighborhoods}
  yearRange={[2012, 2025]}
  showTrendline={true}
/>
```

**Features**:

- Multi-line chart (one line per neighborhood)
- X-axis: Years
- Y-axis: Price (€/m²)
- Interactive legend (click to toggle lines)
- Zoom/pan enabled
- Annotations for key events
- Export button

---

## 🎯 User Experience Flow

### First-Time Visitor Journey

1. **Land on Home Page**:
   - See impressive hero with gradient background
   - Animated statistics counter catches attention
   - Clear value proposition: "Data-driven insights for Barcelona's real estate"

2. **Scroll to Key Metrics**:
   - 4 KPI cards with impressive numbers
   - Micro-animations on scroll (fade-in, slide-up)
   - Trend indicators show data is current

3. **Interact with Map Preview**:
   - Hover over neighborhoods to see prices
   - Click "Explore Dashboard" CTA

4. **Navigate to Analytics**:
   - See comprehensive price evolution chart
   - Use filters to explore specific districts
   - Discover insights through interactive visualizations

5. **Explore Territory**:
   - Full-screen map with layer toggles
   - Click neighborhood to see detailed scorecard
   - Compare multiple neighborhoods

6. **Learn About Data**:
   - Navigate to Methodology section
   - See data sources, quality metrics
   - Understand how insights are generated

### Returning User Journey

1. **Direct to Analytics** (bookmarked URL with filters)
2. **Quick filter adjustments** (year, district)
3. **Export insights** (charts, data)
4. **Compare new neighborhoods**

---

## 📱 Mobile-First Considerations

### Mobile Layout

- **Navigation**: Bottom tab bar (4 icons)
- **Hero**: Reduced height, smaller text
- **KPI Cards**: Single column, full-width
- **Charts**: Simplified, touch-optimized
- **Map**: Full-screen mode, simplified controls
- **Filters**: Drawer/modal instead of sidebar

### Touch Interactions

- **Swipe**: Navigate between sections
- **Pinch-to-zoom**: On maps and charts
- **Long-press**: Show tooltips
- **Pull-to-refresh**: Update data

---

## 🚀 Performance Targets

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.5s
- **Lighthouse Score**: > 90
- **Bundle Size**: < 500KB (gzipped)
- **API Response Time**: < 200ms

---

## ✅ Success Criteria

The website is successful if:

1. ✅ **Visual Impact**: Users say "Wow!" on first visit
2. ✅ **Clarity**: Non-technical users understand the insights
3. ✅ **Performance**: Loads fast, smooth interactions
4. ✅ **Responsiveness**: Works perfectly on mobile/tablet/desktop
5. ✅ **Accessibility**: WCAG AA compliant
6. ✅ **Data Integrity**: All numbers match database
7. ✅ **Engagement**: Users explore multiple sections
8. ✅ **Shareability**: Users share specific insights (via URL)

---

## 🎨 Design Inspiration

**Reference these modern dashboards**:

- Stripe Dashboard (clean, professional)
- Notion (smooth interactions, glassmorphism)
- Linear (modern, fast, beautiful)
- Vercel Analytics (data visualization excellence)
- Airbnb Insights (geographic data presentation)

**Key Design Principles**:

- **Clarity over complexity**: Don't overwhelm with data
- **Progressive disclosure**: Show summary → details on demand
- **Consistent visual language**: Use design system religiously
- **Meaningful animations**: Enhance understanding, not just decoration
- **Data storytelling**: Guide users through insights

---

## 📝 Content Guidelines

### Tone of Voice

- **Professional** but approachable
- **Data-driven** but human-readable
- **Confident** but transparent about limitations
- **Educational** but not condescending

### Text Examples

**Hero Headline**: "Barcelona Housing Analytics"
**Hero Subheadline**: "Comprehensive data platform analyzing 73 neighborhoods across 14 years of housing market evolution"

**Section Titles**:

- "Market Intelligence at a Glance"
- "Explore Neighborhood Dynamics"
- "Investment Opportunities Uncovered"
- "Data You Can Trust"

**Button Labels**:

- Primary CTA: "Explore Dashboard"
- Secondary CTA: "View Methodology"
- Tertiary: "Download Report"

---

## 🔧 Development Phases

### Phase 1: Foundation (Week 1)

- Set up Next.js/Vite project
- Implement design system (CSS variables)
- Create layout components (Header, Footer, Navigation)
- Build Home page with hero and KPI cards

### Phase 2: Analytics (Week 2)

- Implement chart components
- Create Analytics page with filters
- Connect to API (or use mock data)
- Add responsive behavior

### Phase 3: Territory (Week 3)

- Integrate map library (Leaflet/Mapbox)
- Load GeoJSON neighborhood boundaries
- Implement layer toggles
- Create neighborhood detail panel

### Phase 4: Polish (Week 4)

- Add animations and micro-interactions
- Optimize performance
- Accessibility audit and fixes
- Cross-browser testing
- Deploy to production

---

## 🎁 Bonus Features (If Time Permits)

1. **Dark Mode**: Toggle between light/dark themes
2. **Export Reports**: Generate PDF reports with selected insights
3. **Saved Views**: Bookmark specific filter combinations
4. **Comparison Mode**: Side-by-side neighborhood comparison
5. **Alerts**: Set price alerts for specific neighborhoods
6. **Social Sharing**: Share specific insights on social media
7. **Multi-language**: Spanish/English/Catalan support
8. **AI Insights**: GPT-powered narrative summaries

---

## 📚 Additional Resources

### Project Links

- **GitHub Repository**: `prototyp33/barcelona-housing-demographics-analyzer`
- **Current Streamlit Dashboard**: Run with `./run_dashboard.sh`
- **API Documentation**: `http://localhost:8000/docs` (FastAPI)
- **Database**: `data/processed/database.db` (SQLite)

### Documentation Files

- `README.md` - Project overview
- `docs/DATABASE_SCHEMA.md` - Complete database schema
- `docs/DESIGN_SYSTEM_GUIDE.md` - Design system specifications
- `docs/DATA_QUALITY_REPORT_20260105.md` - Data quality metrics
- `docs/OVERVIEW_REFACTORING.md` - Component architecture

### Data Files

- `data/raw/` - Raw extracted data
- `data/processed/database.db` - Main SQLite database
- GeoJSON files for neighborhood boundaries

---

## 🎯 Final Notes

**Remember**:

- This is NOT a simple dashboard - it's a **premium analytics platform**
- **Visual excellence is mandatory** - use gradients, glassmorphism, smooth animations
- **Performance matters** - lazy load, optimize, cache
- **Accessibility is not optional** - WCAG AA compliance required
- **Mobile-first** - but desktop experience should be exceptional
- **Data integrity** - all numbers must be accurate and traceable

**The goal**: Create a website that makes users think "This is what modern data analytics should look like."

---

**Generated**: 2026-01-30
**Version**: 1.0
**Status**: Ready for Implementation ✅
