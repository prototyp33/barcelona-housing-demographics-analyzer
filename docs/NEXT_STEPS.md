# 🚀 Next Steps - Barcelona Housing Demographics Analyzer

**Date:** 2026-01-03  
**Current Status:** Phase 2 Complete, Ready for Phase 3  
**Last Milestone:** TMB/OSM ingestion + Accessibility features + Fairness harness

---

## 📊 Current State

### ✅ What's Working

- **Data Pipeline:** TMB/OSM ingestion (1,071 bus stops, 165 rail stations)
- **Features:** Accessibility metrics (5 features per barrio)
- **Database:** `v_demografia_aggregated` view providing demographic metrics
- **Testing:** Fairness A/B harness with improved baseline (MAE: 422€, R²: 0.72)
- **Coverage:** 73/73 barrios with complete data

### ⚠️ What Needs Attention

- **Model Performance:** V2 (accessibility+) performs worse than V1 baseline
  - V2 MAE: 449€ vs V1: 422€ (+6.4%)
  - V2 R²: 0.67 vs V1: 0.72 (-6.7%)
- **Fairness Metrics:** GES dropped from 0.51 to 0.36 (equity worsened)
- **Test Debt:** 14 tests skipped (pre-existing issues)
- **Data Gaps:** Some fact tables still empty

---

## 🎯 Immediate Priorities (Next Sprint)

### 1. **Fix Accessibility Feature Engineering** 🔧

**Priority:** HIGH  
**Effort:** 2-3 days  
**Impact:** Critical for model performance

**Tasks:**

- [ ] Standardize features (z-score normalization)
  ```python
  from sklearn.preprocessing import StandardScaler
  scaler = StandardScaler()
  X_scaled = scaler.fit_transform(X)
  ```
- [ ] Test interaction terms: `renta_mediana * access_score`
- [ ] Create polynomial features for distances (non-linear relationships)
- [ ] Remove multicollinearity (dist_metro_m vs estaciones_metro)
- [ ] Add log transformations for distance features

**Expected Outcome:**

- V2 MAE < V1 MAE (target: <400€)
- GES > 0.70 (improved equity)
- R² > 0.75

---

### 2. **Create Tracking Issue for Skipped Tests** 📝

**Priority:** MEDIUM  
**Effort:** 1 hour  
**Impact:** Technical debt management

**Tasks:**

- [ ] Create GitHub issue using `.github/ISSUE_TEMPLATE_SKIPPED_TESTS.md`
- [ ] Assign to backlog
- [ ] Set priority: Medium
- [ ] Add labels: `technical-debt`, `testing`

**Command:**

```bash
gh issue create \
  --title "Fix 14 Pre-existing Test Failures" \
  --body-file .github/ISSUE_TEMPLATE_SKIPPED_TESTS.md \
  --label technical-debt,testing \
  --milestone "Phase 3"
```

---

### 3. **Update PROJECT_STATUS.md** 📄

**Priority:** MEDIUM  
**Effort:** 30 minutes  
**Impact:** Documentation completeness

**Tasks:**

- [ ] Mark Phase 2 as complete
- [ ] Update feature inventory
- [ ] Document new database views
- [ ] Add fairness testing section
- [ ] Update next steps

---

## 🔬 Feature Engineering Experiments (Week 1-2)

### Experiment 1: Feature Scaling & Normalization

**Hypothesis:** Raw distance features have different scales causing model instability

**Approach:**

```python
# Current (raw)
features = ['dist_metro_m', 'dist_bus_m', 'access_score']

# Proposed (scaled)
from sklearn.preprocessing import StandardScaler, RobustScaler
scaler = RobustScaler()  # Less sensitive to outliers
X_scaled = scaler.fit_transform(X[features])
```

**Success Criteria:**

- MAE improvement > 5%
- Feature importance more balanced

---

### Experiment 2: Interaction Terms

**Hypothesis:** Accessibility impact varies by income level

**Approach:**

```python
# Create interaction features
df['renta_x_access'] = df['renta_mediana'] * df['access_score']
df['renta_x_dist_metro'] = df['renta_mediana'] / (1 + df['dist_metro_m'])
df['poblacion_x_access'] = df['poblacion_total'] * df['access_score']
```

**Success Criteria:**

- R² improvement > 0.05
- GES improvement (better equity)

---

### Experiment 3: Non-linear Transformations

**Hypothesis:** Distance impact is logarithmic, not linear

**Approach:**

```python
import numpy as np

# Log transformations for distances
df['log_dist_metro'] = np.log1p(df['dist_metro_m'])
df['log_dist_bus'] = np.log1p(df['dist_bus_m'])

# Inverse transformations (closer = higher value)
df['proximity_metro'] = 1 / (1 + df['dist_metro_m'] / 100)
df['proximity_bus'] = 1 / (1 + df['dist_bus_m'] / 50)
```

**Success Criteria:**

- Better fit for peripheral barrios
- Reduced MAE in Nou Barris, Sant Andreu

---

### Experiment 4: Feature Selection

**Hypothesis:** Some features add noise, not signal

**Approach:**

```python
from sklearn.feature_selection import SelectKBest, f_regression

# Test different feature combinations
combinations = [
    ['renta_mediana', 'poblacion_total', 'edad_media', 'access_score'],
    ['renta_mediana', 'poblacion_total', 'proximity_metro', 'proximity_bus'],
    ['renta_mediana', 'edad_media', 'log_dist_metro', 'estaciones_metro']
]

# Use SelectKBest to identify top features
selector = SelectKBest(f_regression, k=5)
X_selected = selector.fit_transform(X, y)
```

**Success Criteria:**

- Simpler model with equal/better performance
- Reduced overfitting

---

## 📈 Model Improvements (Week 3-4)

### 1. **Regularization & Hyperparameter Tuning**

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [100, 200, 300],
    'reg_alpha': [0, 0.1, 1.0],  # L1 regularization
    'reg_lambda': [0, 0.1, 1.0]  # L2 regularization
}

grid_search = GridSearchCV(
    XGBRegressor(),
    param_grid,
    cv=5,
    scoring='neg_mean_absolute_error'
)
```

---

### 2. **Segment-Weighted Training**

**Goal:** Improve fairness by giving more weight to underrepresented segments

```python
# Calculate sample weights based on district
district_counts = df['distrito_nombre'].value_counts()
df['sample_weight'] = df['distrito_nombre'].map(
    lambda x: 1.0 / district_counts[x]
)

# Train with weights
model.fit(X_train, y_train, sample_weight=weights_train)
```

---

### 3. **Ensemble Methods**

**Goal:** Combine multiple models for better robustness

```python
from sklearn.ensemble import VotingRegressor

ensemble = VotingRegressor([
    ('xgb', XGBRegressor()),
    ('rf', RandomForestRegressor()),
    ('gb', GradientBoostingRegressor())
])
```

---

## 🗄️ Data Completeness (Ongoing)

### Priority Tables to Populate

1. **fact_educacion** (Currently: Some data)

   - Source: Open Data BCN
   - Metrics: Schools, universities per barrio
   - Impact: Education access features

2. **fact_seguridad** (Currently: Some data)

   - Source: Open Data BCN
   - Metrics: Crime rates, police stations
   - Impact: Safety perception features

3. **fact_vivienda_publica** (Currently: Some data)

   - Source: INCASOL, Open Data BCN
   - Metrics: Public housing availability
   - Impact: Affordability features

4. **fact_presion_turistica** (Currently: Some data)
   - Source: Airbnb, Open Data BCN
   - Metrics: Tourist density, rental pressure
   - Impact: Gentrification indicators

---

## 🎨 Dashboard & API Enhancements

### 1. **Add Accessibility View to Streamlit Dashboard**

```python
# New view: src/app/views/accessibility.py
def render_accessibility_view():
    st.title("🚇 Accessibility Analysis")

    # Map: Access score by barrio
    # Chart: Distance to transit vs prices
    # Table: Top/bottom 10 barrios by access_score
```

### 2. **API Endpoints for Accessibility**

```python
# src/api/routers/accessibility.py
@router.get("/barrios/{barrio_id}/accessibility")
async def get_barrio_accessibility(barrio_id: int):
    # Return accessibility metrics for barrio
    pass

@router.get("/accessibility/rankings")
async def get_accessibility_rankings():
    # Return barrios ranked by access_score
    pass
```

---

## 🧪 Testing Strategy

### 1. **Fix Skipped Tests** (14 tests)

- Pipeline tests (3): Fix mock data structure
- Servicios salud tests (5): Fix extractor logic
- Zonas verdes test (1): Fix assertion
- Educacion test (1): Fix empty DataFrame handling

### 2. **Add New Tests**

- [ ] Test `v_demografia_aggregated` view
- [ ] Test accessibility feature engineering
- [ ] Test fairness metrics calculation
- [ ] Integration test for full ETL pipeline

---

## 📊 Fairness Monitoring

### 1. **Automated Fairness CI/CD**

```yaml
# .github/workflows/fairness-check.yml
name: Fairness Check
on: [pull_request]
jobs:
  fairness:
    runs-on: ubuntu-latest
    steps:
      - name: Run A/B Harness
        run: python scripts/fairness_ab_harness.py
      - name: Check Metrics
        run: |
          # Fail if GES < 0.70 or IPR outside [0.8, 1.2]
```

### 2. **Fairness Dashboard**

- Real-time GES, IPR, PDI metrics
- District-level error heatmap
- Trend analysis over time

---

## 🎯 Phase 3 Goals (Next 4-6 Weeks)

### Week 1-2: Feature Engineering

- ✅ Fix accessibility features
- ✅ Test interaction terms
- ✅ Implement non-linear transformations
- ✅ Run experiments, document results

### Week 3-4: Model Optimization

- ✅ Hyperparameter tuning
- ✅ Segment-weighted training
- ✅ Ensemble methods
- ✅ Achieve target metrics (MAE <400€, R²>0.75, GES>0.70)

### Week 5-6: Integration & Deployment

- ✅ Add accessibility views to dashboard
- ✅ Create API endpoints
- ✅ Fix skipped tests
- ✅ Update documentation
- ✅ Deploy to production

---

## 📋 Backlog (Future Phases)

### Data Sources to Integrate

- [ ] IDESCAT (Catalan statistics)
- [ ] Cadastre data (building characteristics)
- [ ] Energy efficiency certificates
- [ ] Green space quality metrics
- [ ] Air quality sensors

### Advanced Features

- [ ] Time series forecasting (price trends)
- [ ] Gentrification risk scoring
- [ ] Investment opportunity ranking
- [ ] Neighborhood clustering
- [ ] Comparative analysis tool

### Infrastructure

- [ ] CI/CD pipeline for ETL
- [ ] Data quality monitoring
- [ ] Automated data refresh
- [ ] API rate limiting
- [ ] Caching layer

---

## 🎓 Success Metrics

### Model Performance

- ✅ **MAE:** <400€ (currently 422€)
- ✅ **R²:** >0.75 (currently 0.72)
- ✅ **Coverage:** 100% barrios (currently 100%)

### Fairness

- ✅ **GES:** >0.70 (currently 0.51)
- ✅ **IPR:** 0.8-1.2 (currently 0.88)
- ✅ **PDI:** <5.0 (currently 4.74)

### Technical

- ✅ **Test Coverage:** >80% (currently 34.53%)
- ✅ **Skipped Tests:** 0 (currently 14)
- ✅ **Data Completeness:** >90% critical tables

### Business

- ✅ **API Response Time:** <200ms
- ✅ **Dashboard Load Time:** <3s
- ✅ **User Satisfaction:** >4.5/5

---

## 🚀 Quick Start Commands

### Run Fairness A/B Test

```bash
python scripts/fairness_ab_harness.py
```

### Create Tracking Issue

```bash
gh issue create --title "Fix 14 Pre-existing Test Failures" \
  --body-file .github/ISSUE_TEMPLATE_SKIPPED_TESTS.md \
  --label technical-debt,testing
```

### Run Full ETL Pipeline

```bash
python -m src.etl.pipeline
```

### Start Dashboard

```bash
streamlit run src/app/main.py
```

### Start API

```bash
uvicorn src.api.main:app --reload
```

---

## 📞 Support & Resources

- **Documentation:** `docs/`
- **Sprint Summaries:** `docs/SPRINT_COMPLETION_*.md`
- **Database Schema:** `docs/DATABASE_SCHEMA.md`
- **API Docs:** `http://localhost:8000/docs` (when running)

---

**Last Updated:** 2026-01-03  
**Next Review:** After Week 2 experiments complete
