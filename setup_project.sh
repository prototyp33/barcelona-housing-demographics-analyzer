#!/usr/bin/env bash
set -euo pipefail

create_issue () {
  local title="$1"
  local body="$2"
  local label="$3"

  gh issue create \
    --title "${title}" \
    --body "${body}" \
    --label "${label}"
}

echo ">> Creando issues (asocia cada una al proyecto desde la UI)"

create_issue "[S0] Setup operativo + Baseline KPIs" \
"- [ ] Verificar/renovar credenciales (IDESCAT, Incasòl)
- [ ] Actualizar requirements-dev (playwright, nbconvert)
- [ ] Backup DB y dataset (zip en docs/backups)
- [ ] Publicar baseline 2025Q4 (docs/reports/baseline_2025Q4.md)
- [ ] Enlazar docs/PROJECT_CHARTER.md desde README" \
"roadmap"

create_issue "[S1] Implementar IDESCATExtractor + tests" \
"- [ ] Investigar API (formato, endpoints, rate limit)
- [ ] Implementar src/extraction/idescat.py con manifest
- [ ] Tests unitarios con respuestas mock
- [ ] Doc rápida en docs/sources/idescat.md" \
"roadmap"

create_issue "[S2] Pipeline renta histórica" \
"- [ ] Migración SQLite (tabla fact_renta_hist)
- [ ] Pipeline ETL + DQCs (cobertura >=80%)
- [ ] Notebook QA (notebooks/renta_historica.ipynb)
- [ ] Actualizar data_loader + cache" \
"roadmap"

create_issue "[S3] Dashboard Índice de Asequibilidad" \
"- [ ] Calcular métrica (compra + alquiler)
- [ ] Visualizaciones: mapa + sparkline
- [ ] Tooltips/feature flag
- [ ] Demo (gif/video) y README" \
"dashboard"

create_issue "[S4] Integrar datos de alquiler Incasòl" \
"- [ ] Scraper/API analysi.transparenciat
- [ ] Normalización barrios (mapping persistente)
- [ ] Tests del extractor
- [ ] Documentar fuente + limitaciones" \
"roadmap"

create_issue "[S5] Enriquecer fact_precios con Incasòl" \
"- [ ] Merge + reconciliación con fuente actual
- [ ] Nuevos KPIs alquiler (heatmap, ratio venta/alquiler)
- [ ] Alertas DQC si cobertura <70%" \
"dashboard"

create_issue "[S6] fact_socioeconomico (paro, estudios, hogares)" \
"- [ ] Extractores Open Data BCN
- [ ] Tabla fact_socioeconomico + migrations
- [ ] Pruebas + manifest" \
"roadmap"

create_issue "[S7] Dashboard Vulnerabilidad" \
"- [ ] Métrica Índice de Vulnerabilidad
- [ ] Visuales comparativas (paralelas, ranking)
- [ ] Tooltips + disclaimers" \
"dashboard"

create_issue "[S8] Storytelling y documentación" \
"- [ ] Notebook notebooks/vulnerabilidad.ipynb
- [ ] README sección “Indicadores Sociales”
- [ ] Publicar demo (Streamlit) + changelog" \
"documentation"

echo ">> Issues creadas. Añádelas al proyecto (Board) desde la UI de GitHub."