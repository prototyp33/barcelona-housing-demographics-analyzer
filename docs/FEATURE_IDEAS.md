# Feature Ideas for Barcelona Housing Demographics Analyzer

Based on the current infrastructure (SQLite, ETL pipeline) and data availability (Open Data BCN, Portal de Dades, Idealista), here are three proposed high-value features.

## 1. 📊 Gentrification Risk & Early Warning System

**Description:**
A predictive model and visualization module that identifies neighborhoods at high risk of rapid gentrification. It analyzes the rate of change in key indicators over time to flag "heating up" areas before prices peak.

**Rationale:**
- **Social Impact:** Helps policymakers and NGOs intervene early.
- **Investment Insight:** Identifies areas with high potential for appreciation.
- **Data Usage:** Leverages the historical depth (2015-2025) of the `fact_demografia` and `fact_precios` tables.

**Implementation:**
1.  **Metric Engineering:**
    - Calculate YoY change for:
        - Price/m² (Sale and Rent).
        - % Foreign Population (`porc_inmigracion` in `fact_demografia`).
        - Household Income (`fact_renta`).
        - "Churn" rate (population turnover, if available).
2.  **Scoring Algorithm:**
    - Create a composite "Gentrification Score" (0-100).
    - Use a weighted moving average of the rates of change.
3.  **Visualization:**
    - Add a "Risk Map" layer to the Streamlit dashboard (`src/app.py`).
    - Color-code neighborhoods from Green (Stable) to Red (High Risk).

## 2. ⚖️ "Buy vs. Rent" Affordability Calculator

**Description:**
An interactive tool allowing users to determine whether it is financially better to buy or rent in a specific neighborhood, personalized to their financial situation.

**Rationale:**
- **User Engagement:** High utility for the general public looking for housing.
- **Market Analysis:** Highlights disparities between rental yields and sales prices.
- **Data Usage:** Utilizes `fact_precios` (Sale vs. Rent) and `fact_renta` (Income context).

**Implementation:**
1.  **Financial Engine (`src/analysis.py`):**
    - Implement a Net Present Value (NPV) comparison model.
    - Inputs: Savings, Monthly Income, Mortgage Rate (static or API), Time Horizon.
    - Data: Median Buy Price vs. Median Rent for the selected barrio.
2.  **Frontend (`src/app.py`):**
    - Input form in the sidebar (Investment amount, years).
    - Output: "Breakeven Year" chart and a recommendation ("Buy if staying > 5 years").
    - "Affordability Gap" Map: Visualizing (Mortgage Payment / Average Rent) ratio.

## 3. 🎯 Investment "Hotspot" Clustering

**Description:**
Unsupervised machine learning to group neighborhoods into clusters based on their investment profile, identifying "hidden gems" that statistically resemble high-performing neighborhoods but are currently undervalued.

**Rationale:**
- **Data Discovery:** Reveals non-obvious relationships between neighborhoods.
- **Strategic Value:** Helps investors find "The next [Trendiest Neighborhood]" (e.g., "The next Poblenou").
- **Data Usage:** Uses all dimensions: `dim_barrios`, `fact_demografia` (Age, Density), `fact_precios`, and `fact_renta`.

**Implementation:**
1.  **Feature Vector Creation:**
    - Normalize metrics per barrio: Density, Age Profile (18-34%), Income, Price/m², Yield (Rent/Price).
2.  **Clustering (`src/analysis.py`):**
    - Apply K-Means or DBSCAN clustering.
    - Determine optimal $k$ (e.g., "Premium", "Up-and-Coming", "Stagnant", "Family-Residential").
3.  **Visualization:**
    - Scatter plot (Price vs. Growth) colored by Cluster.
    - Map visualization where selecting a "Target" neighborhood highlights all similar neighborhoods in the city.
