# Resumen Final - Spike de Validación de Datos (Gràcia)

**Fecha de cierre**: 21 de diciembre de 2025  
**Issues**: #199, #200, #201, #202, #203, #204  
**Estado**: ✅ Completado

---

## 🎯 Objetivo del Spike

Validar la viabilidad de un modelo hedónico de precios a nivel micro (propiedad individual) para el barrio de Gràcia, comparándolo con el baseline MACRO (nivel barrio).

---

## ✅ Issues Completados

### Issue #199: Extract INE/Portal Dades Price Data ✅

- **Estado**: Completado
- **Resultados**: 1,268 registros extraídos (2020-2025, 5 barrios Gràcia)
- **Archivo**: `data/raw/ine_precios_gracia_notebook.csv`

### Issue #200: Extract Catastro/Open Data Attributes ✅

- **Estado**: Completado (con workaround por coordenadas)
- **Resultados**: 60 edificios con coordenadas + referencia catastral
- **Limitación**: Features estructurales agregados por barrio (no micro)
- **Fase 2**: XML masivo enviado a Sede Electrónica (19/12/2025)

### Issue #201: Linking Precios ↔ Edificios ✅

- **Estado**: Completado
- **Método**: Matching por `barrio_id` (nivel macro)
- **Resultados**: 175 observaciones (`barrio_id × anio × dataset_id`)
- **Match rate**: 100% (pero nivel agregado)

### Issue #203: Baseline MACRO v0.1 ✅

- **Estado**: Completado
- **Modelo**: Structural-only (`anio_num` + estructurales + dummies dataset)
- **Performance**:
  - R² (test 2025): **0.710** ✅
  - RMSE: 323.47 €/m² ✅
  - Sesgo: +203.28 €/m² (subestima 2025)
- **Decisión**: ✅ **GO** - Modelo operativo recomendado

### Issue #204: Validación OLS ✅

- **Estado**: Completado
- **Resultado**: 2/5 checks passed (criterio ≥4/5 **NO** cumplido)
- **Limitaciones**: Heterocedasticidad, autocorrelación temporal, outliers influyentes
- **Recomendación**: No usar OLS "puro" en producción; preferir errores estándar robustos

### Issue #202: Modelo Hedonic Pricing MICRO ❌

- **Estado**: ✅ Investigación completada - **NO-GO**
- **Estrategias probadas**: 4 (geográfico, edificio, cuadrícula, heurístico)
- **Causa raíz**: Curva de demanda no-lineal en mercado de Gràcia
- **Performance**:
  - R²: 0.21 ❌ (target: ≥0.75)
  - RMSE: 2,113 €/m² ❌ (target: ≤250 €/m²)
  - Correlaciones negativas persistentes
- **Decisión**: ❌ **NO-GO** - Mantener MACRO v0.1 como baseline

---

## 📊 Resultados Finales

### Modelo MACRO v0.1 ✅ (Operativo)

- **Nivel**: Barrio × Año × Dataset
- **R²**: 0.710
- **RMSE**: 323.47 €/m²
- **Estado**: ✅ Modelo operativo recomendado

### Modelo MICRO v0.1 ❌ (No Viable)

- **Nivel**: Propiedad individual
- **R²**: 0.21
- **RMSE**: 2,113 €/m²
- **Estado**: ❌ NO-GO - Requiere modelos no-lineales

---

## 💡 Lecciones Aprendidas

1. **Validar supuestos económicos**: No asumir linealidad en mercados inmobiliarios
2. **Matching ≠ Modelo**: Matching correcto no garantiza modelo válido
3. **Inspeccionar correlaciones temprano**: Red flag inmediata para especificación
4. **Time-boxing efectivo**: Spike de 16h suficiente para identificar problema
5. **Documentación exhaustiva**: Permite retomar en futuro sin rehacer trabajo

---

## 🔮 Futuras Iteraciones

### MACRO v0.2 (Prioridad Alta)

- Integrar `fact_renta` y `fact_demografia_ampliada`
- Target: R² ≥ 0.80
- Esfuerzo: 8-12h

### MICRO v0.2 (Prioridad Baja - Futuro)

- Modelos no-lineales (Random Forest, XGBoost)
- Segmentación por tipo de propiedad
- Esfuerzo: 20-30h
- Ver: `ISSUE_FUTURO_MICRO_V02.md`

---

## 📚 Documentación Generada

### Técnica
- `INVESTIGACION_RESUMEN_FINAL.md` - Resumen completo
- `INVESTIGACION_DATOS_CORRELACIONES_NEGATIVAS.md` - Análisis técnico
- `ESTRATEGIAS_MATCHING_NIVEL_DIFERENTE.md` - Comparación de estrategias
- `MATCHING_GEOGRAFICO_RESULTADOS.md` - Resultados matching geográfico

### Para GitHub
- `GITHUB_ISSUE_202_CIERRE.md` - Comentario de cierre
- `GITHUB_ISSUE_202_INVESTIGACION_COMPLETA.md` - Documento completo

### Futuro
- `ISSUE_FUTURO_MICRO_V02.md` - Placeholder para futuras iteraciones

---

## 🏁 Cierre del Spike

**Tiempo total invertido**: ~16h (spike + investigación)  
**Modelo operativo**: MACRO v0.1 (R² = 0.71)  
**Aprendizajes**: Documentados para futuras iteraciones  
**Estado**: ✅ Spike completado exitosamente

---

**Última actualización**: 2025-12-21

