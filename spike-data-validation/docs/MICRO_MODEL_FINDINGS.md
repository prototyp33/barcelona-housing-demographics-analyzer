# Hallazgos Modelo Hedonic MICRO v1.0

**Fecha**: 2025-12-19  
**Issue**: #202 - Fase 2  
**Estado**: ⚠️ Modelo con bajo rendimiento (datos mock)

---

## 📊 Resumen Ejecutivo

### **Resultados Actuales**

| Modelo | R² Test | RMSE Test | Bias Test | Status |
|--------|---------|-----------|-----------|--------|
| Linear | 0.21 | 497 €/m² | 75 €/m² | ❌ Bajo |
| Random Forest | -0.10 | 585 €/m² | 71 €/m² | ❌ Overfitting |
| GBM | -0.55 | 695 €/m² | 78 €/m² | ❌ Overfitting extremo |

**Comparación con MACRO Baseline**:
- MACRO: R² = 0.71, RMSE = 323 €/m²
- MICRO: R² = 0.21, RMSE = 497 €/m²
- **Delta**: MICRO es **peor** que MACRO

---

## 🔍 Análisis de Causas

### **Causa Principal: Datos Mock**

**Problema identificado**:
- Datos mock fueron generados con relaciones estadísticas simples
- Correlaciones con precio_m2 son muy bajas o negativas:
  - `superficie_m2`: -0.091 (esperado: +0.3 a +0.5)
  - `habitaciones`: -0.223 (esperado: +0.2 a +0.4)
- Esto sugiere que los datos mock **no capturan relaciones reales** del mercado

**Evidencia**:
```
Correlación superficie-precio (sin outliers): 0.020
→ Prácticamente cero, lo cual es inusual en mercado real
```

---

### **Causa Secundaria: Tamaño de Muestra**

- **100 observaciones** es el mínimo para modelos hedonic
- **11 features** → ratio ~9:1 (recomendado: ≥10:1)
- **Test set**: Solo 20 observaciones (muy pequeño para evaluación confiable)

**Impacto**: Métricas pueden ser volátiles con muestra tan pequeña.

---

### **Causa Terciaria: Outliers**

- Superficie tiene valores extremos (2.92 m² a 473 m²)
- Aunque solo 4% son outliers, pueden afectar el modelo
- Limpieza mejora ligeramente pero no resuelve el problema principal

---

## 💡 Interpretación para Spike

### **¿Son estos resultados válidos?**

**Para validación técnica del pipeline**: ✅ **SÍ**
- El pipeline funciona correctamente
- Matching Catastro ↔ Idealista funciona
- Modelo se entrena sin errores
- Métricas se calculan correctamente

**Para evaluación de rendimiento**: ❌ **NO**
- Datos mock no representan relaciones reales del mercado
- Correlaciones artificiales no capturan variabilidad real
- Resultados no son representativos de producción

---

## 🎯 Conclusión para Issue #202

### **Pipeline Técnico: ✅ VALIDADO**

```
✅ Extracción Catastro: 731 inmuebles MICRO
✅ Matching Catastro ↔ Idealista: Funciona
✅ Modelo se entrena: Sin errores técnicos
✅ Métricas se calculan: Correctamente
```

### **Rendimiento del Modelo: ⏳ PENDIENTE DATOS REALES**

```
❌ R² test: 0.21 (objetivo: ≥0.75)
❌ RMSE test: 497 €/m² (objetivo: ≤250)
⚠️  Resultados con datos mock (no representativos)
```

---

## 📋 Recomendaciones

### **Para Spike (Ahora)**

1. ✅ **Documentar hallazgos** (este documento)
2. ✅ **Validar que pipeline funciona** técnicamente
3. ⏳ **Esperar datos reales** de Idealista API
4. ⏳ **Re-entrenar con datos reales** cuando lleguen

### **Para Producción**

1. **Aumentar muestra**: Objetivo ≥200 observaciones
2. **Usar datos reales**: Reemplazar mock con API Idealista
3. **Validar correlaciones**: Verificar que relaciones son realistas
4. **Ajustar modelo**: Basado en datos reales

---

## 🔄 Próximos Pasos

### **Inmediato**

1. ✅ Pipeline técnico validado
2. ⏳ Documentar que resultados son con datos mock
3. ⏳ Actualizar Issue #202 con hallazgos

### **Cuando Lleguen Credenciales API**

1. Extraer datos reales de Idealista
2. Re-ejecutar matching
3. Re-entrenar modelo con datos reales
4. Comparar resultados mock vs reales

---

## 📊 Comparación Esperada: Mock vs Real

| Aspecto | Mock (Actual) | Real (Esperado) |
|---------|---------------|-----------------|
| Correlaciones | Muy bajas/negativas | Moderadas/positivas |
| R² test | 0.21 | ≥0.50-0.75 |
| RMSE test | 497 €/m² | 200-300 €/m² |
| Variabilidad | Artificial | Natural del mercado |

---

**Última actualización**: 2025-12-19  
**Nota**: Estos resultados son con datos mock. Rendimiento real se evaluará con datos de Idealista API.

