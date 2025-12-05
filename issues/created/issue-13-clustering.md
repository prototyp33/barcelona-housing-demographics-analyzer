---
title: [FEATURE-13] Segmentación Automática de Barrios con K-Means
labels: sprint-1, priority-high, type-feature, area-ml
milestone: 1
---

## 🎯 Contexto
**Feature ID:** #13
**Sprint:** Sprint 1 (Quick Wins)
**Esfuerzo estimado:** 15-18h

## 📝 Descripción
Implementación de algoritmo K-Means para agrupar los 73 barrios de Barcelona en clusters según similitud demográfica y de mercado (ej: "Alto standing", "Familiar asequible", "Oportunidad inversión").

## 🔧 Componentes Técnicos
- [ ] `src/analytics/segmentation.py`: Pipeline de preprocesamiento y modelo K-Means
- [ ] `src/app/pages/segmentation_analysis.py`: Visualización de clusters (Radar Charts)
- [ ] Base de datos: Nueva tabla `dim_segmento_barrio`

## ✅ Criterios de Aceptación
- [ ] 5-8 clusters identificados y caracterizados
- [ ] Radar charts comparativos por cluster
- [ ] Persistencia de resultados en SQLite
- [ ] Análisis de "Codo" (Elbow method) documentado para elección de K

