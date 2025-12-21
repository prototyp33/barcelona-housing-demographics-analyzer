# [FUTURO] Modelo MICRO v0.2 - Enfoque No-Lineal

**Estado**: 📋 Placeholder para futuras exploraciones  
**Prioridad**: Baja  
**Milestone**: Q2 2026 (tentativo)  
**Dependencias**: MACRO v0.2 completado

---

## Contexto

MICRO v0.1 fracasó debido a curva de demanda no-lineal identificada en Issue #202. Este issue es un placeholder para futuras exploraciones con modelos no-lineales.

**Issue relacionado**: #202 (cerrado - investigación completa)

---

## Propuesta

Explorar modelos no-lineales para predicción micro-level que puedan capturar la curva de demanda no-lineal del mercado de Gràcia.

**Motivación**:
- MACRO (R²=0.71) funciona bien para agregados
- MICRO permitiría estimaciones a nivel propiedad individual
- Curva no-lineal identificada requiere algoritmos no-lineales

---

## Enfoque Propuesto

### 1. Modelos a Explorar

- **Random Forest**
  - Ventaja: Captura interacciones no-lineales automáticamente
  - Desventaja: Menos interpretable que OLS
  
- **Gradient Boosting** (XGBoost, LightGBM)
  - Ventaja: Alta performance, maneja no-linealidades
  - Desventaja: Requiere tuning de hiperparámetros
  
- **Redes Neuronales** (MLP)
  - Ventaja: Máxima flexibilidad
  - Desventaja: Requiere más datos y computación
  
- **Regresión Polinómica**
  - Ventaja: Interpretable, simple
  - Desventaja: Puede sobreajustar

### 2. Features Adicionales

- **Geográficas**:
  - Distancia a metro (más cercano)
  - Distancia a parques principales
  - Distancia a centro de barrio
  
- **Estructurales**:
  - Estado de conservación (si disponible)
  - Edad del edificio (ya disponible)
  - Tipo de construcción
  
- **Amenidades**:
  - Ascensor (sí/no)
  - Terraza (sí/no)
  - Parking (sí/no)
  - Trastero (sí/no)

### 3. Segmentación

- **Por rango de superficie**:
  - Modelo para <70m² (estudios)
  - Modelo para 70-110m² (viviendas estándar)
  - Modelo para >110m² (viviendas grandes)
  
- **Por distrito/barrio**:
  - Modelo específico por barrio si hay suficientes datos
  - O modelo con features de barrio como variables

---

## Criterios de Éxito

- **R² ≥ 0.75** (test set)
- **RMSE ≤ 500 €/m²** (mejor que MICRO v0.1: 2,113 €/m²)
- **Mejor que MACRO v0.1** (R² = 0.71) o justificación de trade-off

---

## Esfuerzo Estimado

**Total**: 20-30h

**Desglose**:
- Feature engineering: 4-6h
- Implementación modelos: 8-12h
- Tuning hiperparámetros: 4-6h
- Validación y documentación: 4-6h

---

## Dependencias

1. **MACRO v0.2 completado** (prioridad más alta)
2. **Validación de business case** para modelo MICRO
3. **Datos adicionales** (amenidades, estado conservación) si disponibles

---

## Notas

- Este issue es un **placeholder** para futuras exploraciones
- **No iniciar** hasta completar MACRO v0.2
- Revisar Issue #202 antes de comenzar para contexto completo
- Considerar si el esfuerzo justifica la mejora sobre MACRO

---

**Labels**: `enhancement`, `model`, `future`, `low-priority`, `micro`  
**Milestone**: Q2 2026 (tentativo)

