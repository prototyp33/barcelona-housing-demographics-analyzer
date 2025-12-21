# Próximos Pasos: Datos Reales Idealista

**Fecha**: 2025-12-19  
**Estado**: ⏳ Esperando credenciales API

---

## 🎯 Situación Actual

### ✅ Completado

1. ✅ **Pipeline técnico validado** con datos mock
2. ✅ **Scripts implementados**:
   - `extract_idealista_api_gracia.py` - Extracción API
   - `match_catastro_idealista.py` - Matching
   - `train_micro_hedonic.py` - Entrenamiento
   - `run_datos_reales_pipeline.py` - Pipeline completo
3. ✅ **Datos Catastro reales** disponibles (`catastro_gracia_real.csv`)
4. ✅ **Documentación completa** del proceso

### ⏳ Pendiente

1. ⏳ **Credenciales API Idealista** (requeridas)
2. ⏳ **Extracción datos reales** (bloqueada por credenciales)
3. ⏳ **Re-entrenamiento con datos reales**

---

## 🚀 Plan de Ejecución (Cuando Lleguen Credenciales)

### **Paso 1: Configurar Credenciales** (2 min)

```bash
# Opción A: Variables de entorno (recomendado)
export IDEALISTA_API_KEY=tu_api_key_aqui
export IDEALISTA_API_SECRET=tu_api_secret_aqui

# Opción B: Archivo .env
echo "IDEALISTA_API_KEY=tu_key" >> .env
echo "IDEALISTA_API_SECRET=tu_secret" >> .env
```

### **Paso 2: Ejecutar Pipeline Completo** (15-20 min)

```bash
# Pipeline automatizado (recomendado)
python3 spike-data-validation/scripts/fase2/run_datos_reales_pipeline.py
```

**Este script ejecuta automáticamente**:
1. ✅ Verificación de credenciales
2. ✅ Extracción Idealista API (100 propiedades)
3. ✅ Matching Catastro ↔ Idealista
4. ✅ Re-entrenamiento modelo con datos reales

### **Paso 3: Revisar Resultados** (10 min)

**Archivos generados**:
- `idealista_gracia_api.csv` - Datos reales extraídos
- `catastro_idealista_matched_REAL.csv` - Dataset matched
- `micro_hedonic_linear_results.json` - Métricas del modelo

**Comparar con mock**:
- Correlaciones: ¿Mejoran? (esperado: sí)
- Match rate: ¿Similar o mejor? (esperado: 40-60%)
- R² test: ¿Mejora? (esperado: ≥0.50 con datos reales)

---

## 📊 Métricas Esperadas (Con Datos Reales)

### **Correlaciones** (deberían mejorar)

| Variable | Mock (Actual) | Real (Esperado) |
|----------|---------------|-----------------|
| `superficie_m2` | -0.091 | +0.3 a +0.5 |
| `habitaciones` | -0.223 | +0.2 a +0.4 |
| `ano_construccion` | +0.212 | +0.2 a +0.4 |

### **Métricas del Modelo** (deberían mejorar)

| Métrica | Mock (Actual) | Real (Esperado) | Objetivo |
|---------|---------------|-----------------|----------|
| R² test | -0.198 | ≥0.50 | ≥0.75 |
| RMSE test | 724.50 €/m² | ≤400 €/m² | ≤250 €/m² |
| Bias test | 140.64 €/m² | ≤±100 €/m² | ≤±100 €/m² |

---

## 🔄 Alternativas si No Hay Credenciales

### **Opción 1: Solicitar Credenciales**

1. **Registrarse**: https://developers.idealista.com/
2. **Solicitar acceso**: Completar formulario
3. **Esperar aprobación**: 1-7 días típicamente
4. **Configurar y ejecutar**: Seguir plan arriba

### **Opción 2: Usar Cliente GitHub Alternativo**

```bash
pip install git+https://github.com/yagueto/idealista-api.git
```

**Nota**: También requiere credenciales API, pero puede tener mejor manejo.

### **Opción 3: Continuar con Mock (Documentado)**

**Acción**: Documentar que resultados son con mock y pipeline está listo.

**Ventajas**:
- ✅ Pipeline validado técnicamente
- ✅ Scripts listos para producción
- ✅ Documentación completa

---

## 📝 Documentación a Generar (Cuando Lleguen Datos Reales)

1. **`IDEALISTA_EXTRACTION_REAL.md`**: Resumen extracción
2. **`MATCHING_REAL_RESULTS.md`**: Resultados matching
3. **`EDA_REAL_VS_MOCK.md`**: Comparación EDA
4. **`MODEL_REAL_RESULTS.md`**: Resultados modelo
5. **`ANALISIS_MOCK_VS_REAL.md`**: Análisis comparativo completo

---

## ✅ Checklist de Preparación

- [x] Scripts implementados
- [x] Pipeline automatizado creado
- [x] Documentación del proceso
- [x] Datos Catastro reales disponibles
- [ ] Credenciales API configuradas
- [ ] Extracción ejecutada
- [ ] Matching ejecutado
- [ ] Modelo re-entrenado
- [ ] Comparación mock vs real documentada

---

## 🔗 Comandos Rápidos

### **Verificar Estado**

```bash
# Verificar credenciales
python3 -c "import os; print('API Key:', '✅' if os.getenv('IDEALISTA_API_KEY') else '❌')"

# Verificar dependencias
python3 -c "try: from idealista_api import Idealista; print('✅ Cliente GitHub disponible'); except: print('❌ Cliente GitHub no instalado')"
```

### **Ejecutar Pipeline**

```bash
# Todo en uno
python3 spike-data-validation/scripts/fase2/run_datos_reales_pipeline.py

# O paso a paso (ver DATOS_REALES_IMPLEMENTATION_PLAN.md)
```

---

**Última actualización**: 2025-12-19

