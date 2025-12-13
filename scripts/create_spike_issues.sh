#!/bin/bash
# Create all Spike Issues (Dec 16-20, 2025)
# Master Tracker + 9 issues

set -e

echo "🚀 Creando Issues del Spike (Dec 16-20, 2025)..."
echo ""

MILESTONE="Spike Validation (Dec 16-20)"

# Verificar que el milestone existe
if ! gh milestone list | grep -q "Spike Validation"; then
    echo "⚠️  Milestone '$MILESTONE' no encontrado"
    echo "   Creando milestone..."
    gh api -X POST "repos/prototyp33/barcelona-housing-demographics-analyzer/milestones" \
      -f title="$MILESTONE" \
      -f description="Data validation spike for hedonic pricing model viability" \
      -f due_on="2025-12-20T23:59:59Z" || echo "   Milestone puede que ya exista"
    echo ""
fi

# Master Tracker Issue
echo "1️⃣ Creando Master Tracker Issue..."

MASTER_TRACKER_URL=$(gh issue create \
  --title "🎯 SPIKE Master Tracker - Data Validation (Dec 16-20)" \
  --body "## 📋 Objetivo del Spike

Validar si el modelo hedónico de precios de vivienda es viable con datos públicos.

**Duración:** Dec 16-20, 2025 (5 días)  
**Barrio Piloto:** Gràcia  
**Decision Gate:** Go / No-Go para v2.0

---

## 📅 Daily Progress

### Monday (Dec 16)
- [ ] #TBD: Extract INE Price Data
- [ ] #TBD: Extract Catastro Attributes

### Tuesday (Dec 17)
- [ ] #TBD: Data Linking & Cleaning
- [ ] #TBD: EDA - Exploratory Data Analysis

### Wednesday (Dec 18)
- [ ] #TBD: Build OLS Hedonic Pricing Model

### Thursday (Dec 19)
- [ ] #TBD: OLS Model Diagnostics & Validation
- [ ] #TBD: Alternative Model Specifications

### Friday (Dec 20)
- [ ] #TBD: Write Viability Report (PDF)
- [ ] #TBD: Update PRD v2.0 Based on Findings
- [ ] Decision Meeting at 2:00 PM

---

## 🎯 Success Criteria (Go/No-Go)

- [ ] Match Rate ≥70%
- [ ] R² Ajustado ≥0.55
- [ ] Sample Size ≥100
- [ ] 4/5 OLS Assumptions Pass
- [ ] Coeficientes económicamente plausibles
- [ ] Documentation Complete

---

## 📊 Current Status

**As of:** $(date '+%Y-%m-%d')  
**Match Rate:** TBD  
**R²:** TBD  
**Decision:** PENDING

---

## 🔗 Related Issues

Ver issues individuales del spike abajo.

---

## 📝 Quick Links

- [Spike README](spike-data-validation/README.md)
- [Viability Report Template](docs/templates/VIABILITY_REPORT_TEMPLATE.md)
- [Decision Record Template](docs/templates/DECISION_RECORD_TEMPLATE.md)
- [Main Notebook](spike-data-validation/notebooks/01-gracia-hedonic-model.ipynb)" \
  --label "spike,p0-critical" \
  --milestone "$MILESTONE")

MASTER_NUMBER=$(echo "$MASTER_TRACKER_URL" | grep -oE '[0-9]+$')
echo "   ✅ Master Tracker creado: #$MASTER_NUMBER"
echo "   URL: $MASTER_TRACKER_URL"
echo ""

# Issue 1: Extract INE Price Data
echo "2️⃣ Creando Issue 1: Extract INE Price Data..."

ISSUE_1_URL=$(gh issue create \
  --title "[SPIKE] Extract INE Price Data - Gràcia 2020-2025" \
  --body "## 📋 Objetivo

Extraer datos de precios de transacciones de vivienda para Gràcia (2020-2025).

## 🎯 Criterios de Aceptación

- [ ] ≥100 registros obtenidos
- [ ] Dataset guardado en \`spike-data-validation/data/raw/ine_precios_gracia.csv\`
- [ ] Log en \`spike-data-validation/data/logs/ine_extraction.log\`

## 📊 Fuentes

1. INE - Estadística Registral Inmobiliaria
2. Portal de Dades (fallback)
3. INCASÒL (último recurso)

## ⏱️ Estimación

4-6 horas

## 📝 Outcome

**Records:** [TBD]  
**Granularidad:** [TBD]

## 🔗 Relacionado

Part of #$MASTER_NUMBER" \
  --label "spike,data-extraction,p0-critical,go-criterion" \
  --milestone "$MILESTONE")

ISSUE_1=$(echo "$ISSUE_1_URL" | grep -oE '[0-9]+$')

echo "   ✅ Issue 1 creado: #$ISSUE_1"

# Issue 2: Extract Catastro Attributes
ISSUE_2_URL=$(gh issue create \
  --title "[SPIKE] Extract Catastro/Open Data Attributes - Gràcia" \
  --body "## 📋 Objetivo

Obtener características de viviendas en Gràcia: superficie, año construcción, plantas.

## 🎯 Criterios de Aceptación

- [ ] ≥50 registros de edificios
- [ ] Dataset guardado en \`spike-data-validation/data/raw/catastro_gracia.csv\`
- [ ] Columnas: superficie_m2, ano_construccion, plantas

## 📊 Fuentes

1. Catastro
2. Open Data BCN - Edificios

## ⏱️ Estimación

4-6 horas

## 🔗 Relacionado

Part of #$MASTER_NUMBER" \
  --label "spike,data-extraction,p0-critical,go-criterion" \
  --milestone "$MILESTONE")

ISSUE_2=$(echo "$ISSUE_2_URL" | grep -oE '[0-9]+$')

echo "   ✅ Issue 2 creado: #$ISSUE_2"

# Issue 3: Data Linking & Cleaning
ISSUE_3_URL=$(gh issue create \
  --title "[SPIKE] Data Linking & Cleaning" \
  --body "## 📋 Objetivo

Cruzar precios con atributos. Target: Match rate ≥70%.

## 🎯 Criterios de Aceptación

- [ ] Match rate ≥70% (ideal) o ≥50% (mínimo)
- [ ] Dataset en \`spike-data-validation/data/processed/gracia_merged.csv\`
- [ ] Outliers removidos
- [ ] Documentación de método de linking

## 🔗 Métodos

1. Referencia Catastral
2. Dirección Normalizada (fuzzy)
3. Barrio-Mes (fallback)

## ⏱️ Estimación

4-6 horas

## 🔗 Relacionado

Part of #$MASTER_NUMBER  
**Depends on:** #$ISSUE_1, #$ISSUE_2" \
  --label "spike,data-processing,p0-critical,go-criterion" \
  --milestone "$MILESTONE")

ISSUE_3=$(echo "$ISSUE_3_URL" | grep -oE '[0-9]+$')
echo "   ✅ Issue 3 creado: #$ISSUE_3"

# Issue 4: EDA
ISSUE_4_URL=$(gh issue create \
  --title "[SPIKE] EDA - Exploratory Data Analysis" \
  --body "## 📋 Objetivo

Análisis exploratorio: distribuciones, correlaciones, outliers.

## 🎯 Criterios de Aceptación

- [ ] Notebook con sección EDA completa
- [ ] 5 visualizaciones generadas
- [ ] Matriz de correlaciones

## ⏱️ Estimación

2-3 horas

## 🔗 Relacionado

Part of #$MASTER_NUMBER  
**Depends on:** #$ISSUE_3" \
  --label "spike,modeling,p1-high" \
  --milestone "$MILESTONE")

ISSUE_4=$(echo "$ISSUE_4_URL" | grep -oE '[0-9]+$')
echo "   ✅ Issue 4 creado: #$ISSUE_4"

# Issue 5: Build OLS Model
ISSUE_5_URL=$(gh issue create \
  --title "[SPIKE] Build OLS Hedonic Pricing Model" \
  --body "## 📋 Objetivo

Estimar modelo hedónico. Target: R² ≥0.55.

## 🎯 Criterios de Aceptación

- [ ] Modelo OLS estimado
- [ ] R² ajustado documentado
- [ ] Coeficientes con signos plausibles

## 📐 Especificación

ln(precio) = β₀ + β₁·ln(superficie) + β₂·antiguedad + β₃·plantas + ε

## ⏱️ Estimación

6 horas

## 🔗 Relacionado

Part of #$MASTER_NUMBER  
**Depends on:** #$ISSUE_3, #$ISSUE_4

## 🎯 CRITICAL GO CRITERION

R² ≥0.55. Si R² <0.40, escalar a Data Scientist lead." \
  --label "spike,modeling,p0-critical,go-criterion" \
  --milestone "$MILESTONE")

ISSUE_5=$(echo "$ISSUE_5_URL" | grep -oE '[0-9]+$')
echo "   ✅ Issue 5 creado: #$ISSUE_5"

# Issue 6: Model Diagnostics
ISSUE_6_URL=$(gh issue create \
  --title "[SPIKE] OLS Model Diagnostics & Validation" \
  --body "## 📋 Objetivo

Validar supuestos OLS. Target: 4/5 tests pasan.

## ✅ Tests

1. Normalidad (Shapiro-Wilk)
2. Homocedasticidad (Breusch-Pagan)
3. No Multicolinealidad (VIF)
4. No Autocorrelación (Durbin-Watson)
5. Outliers (Q-Q plot)

## ⏱️ Estimación

4 horas

## 🔗 Relacionado

Part of #$MASTER_NUMBER  
**Depends on:** #$ISSUE_5

## 🎯 CRITICAL GO CRITERION

≥4/5 tests pasan" \
  --label "spike,modeling,p0-critical,go-criterion" \
  --milestone "$MILESTONE")

ISSUE_6=$(echo "$ISSUE_6_URL" | grep -oE '[0-9]+$')
echo "   ✅ Issue 6 creado: #$ISSUE_6"

# Issue 7: Alternative Models
ISSUE_7_URL=$(gh issue create \
  --title "[SPIKE] Alternative Model Specifications" \
  --body "## 📋 Objetivo

Probar especificaciones alternativas para robustez.

## 🔄 Modelos

1. Robust Linear Model (RLM)
2. Agregado Barrio-Año (si N<50)

## ⏱️ Estimación

3-4 horas

## 🔗 Relacionado

Part of #$MASTER_NUMBER  
**Depends on:** #$ISSUE_6" \
  --label "spike,modeling,p2-medium" \
  --milestone "$MILESTONE")

ISSUE_7=$(echo "$ISSUE_7_URL" | grep -oE '[0-9]+$')
echo "   ✅ Issue 7 creado: #$ISSUE_7"

# Issue 8: Viability Report
ISSUE_8_URL=$(gh issue create \
  --title "[SPIKE] Write Viability Report (PDF)" \
  --body "## 📋 Objetivo

Escribir reporte 3-5 páginas con recomendación Go/No-Go.

## 📄 Secciones

1. Resumen Ejecutivo
2. Metodología
3. Resultados del Modelo
4. Lecciones Aprendidas
5. Cambios al PRD
6. Decision Record

## ⏱️ Estimación

4 horas

## 🔗 Relacionado

Part of #$MASTER_NUMBER  
**Depends on:** #$ISSUE_6, #$ISSUE_7

## 🎯 DELIVERABLE FINAL DEL SPIKE

**Template:** Ver \`docs/templates/VIABILITY_REPORT_TEMPLATE.md\`" \
  --label "spike,documentation,p0-critical" \
  --milestone "$MILESTONE")

ISSUE_8=$(echo "$ISSUE_8_URL" | grep -oE '[0-9]+$')
echo "   ✅ Issue 8 creado: #$ISSUE_8"

# Issue 9: Update PRD
ISSUE_9_URL=$(gh issue create \
  --title "[SPIKE] Update PRD v2.0 Based on Findings" \
  --body "## 📋 Objetivo

Actualizar PRD con hallazgos del spike.

## 📝 Cambios Obligatorios

1. Success Metrics (R² target)
2. Data Layer (unit of analysis)
3. ETL Pipeline (fuentes viables)
4. Arquitectura (PostgreSQL confirmado)
5. Timeline ajustado

## ⏱️ Estimación

4 horas

## 🔗 Relacionado

Part of #$MASTER_NUMBER  
**Depends on:** #$ISSUE_8

## ⚠️ Solo ejecutar si Decision = GO o GO WITH CONDITIONS

Si Decision = NO-GO, crear issue separado: \"Post-Mortem: Spike Failure Analysis\"" \
  --label "documentation,p0-critical" \
  --milestone "$MILESTONE")

ISSUE_9=$(echo "$ISSUE_9_URL" | grep -oE '[0-9]+$')
echo "   ✅ Issue 9 creado: #$ISSUE_9"

# Actualizar Master Tracker con números de issues
echo ""
echo "## Actualizando Master Tracker con referencias..."

gh issue comment "$MASTER_NUMBER" --body "## Sub-Issues Creados

- #$ISSUE_1: Extract INE Price Data
- #$ISSUE_2: Extract Catastro/Open Data Attributes
- #$ISSUE_3: Data Linking & Cleaning
- #$ISSUE_4: EDA - Exploratory Data Analysis
- #$ISSUE_5: Build OLS Hedonic Pricing Model
- #$ISSUE_6: OLS Model Diagnostics & Validation
- #$ISSUE_7: Alternative Model Specifications
- #$ISSUE_8: Write Viability Report (PDF)
- #$ISSUE_9: Update PRD v2.0 Based on Findings

**Total:** 9 issues del spike

---

## Dependencies

\`\`\`
#$ISSUE_1, #$ISSUE_2 (Extraction)
    ↓
#$ISSUE_3 (Linking)
    ↓
#$ISSUE_4 (EDA)
    ↓
#$ISSUE_5 (Model)
    ↓
#$ISSUE_6 (Diagnostics)
    ↓
#$ISSUE_7 (Alternatives)
    ↓
#$ISSUE_8 (Report)
    ↓
#$ISSUE_9 (PRD Update)
\`\`\`"

echo ""
echo "========================================="
echo "✅ SPIKE ISSUES CREADAS"
echo "========================================="
echo ""
echo "Master Tracker: #$MASTER_NUMBER"
echo "Sub-issues: #$ISSUE_1, #$ISSUE_2, #$ISSUE_3, #$ISSUE_4, #$ISSUE_5, #$ISSUE_6, #$ISSUE_7, #$ISSUE_8, #$ISSUE_9"
echo ""
echo "⚠️  NEXT STEPS:"
echo ""
echo "1. Agregar issues al proyecto GitHub"
echo "2. Configurar custom fields en GitHub Projects UI"
echo ""
echo "Script completado! 🎉"

