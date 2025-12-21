# Plan de Implementación: Datos Reales Idealista

**Fecha**: 2025-12-19  
**Issue**: #202 - Fase 2  
**Objetivo**: Reemplazar datos mock con datos reales de Idealista API

---

## 🎯 Objetivo

Obtener datos reales de Idealista para Gràcia y re-entrenar el modelo MICRO para validar si mejora el rendimiento.

---

## 📋 Checklist de Preparación

### **Paso 1: Verificar Credenciales API** ⏳

- [ ] Verificar si hay credenciales API en variables de entorno
- [ ] Verificar si hay credenciales en `.env` o archivo de configuración
- [ ] Si no hay credenciales, documentar cómo obtenerlas

**Comando de verificación**:
```bash
# Verificar variables de entorno
echo $IDEALISTA_API_KEY
echo $IDEALISTA_API_SECRET

# O verificar en .env
grep IDEALISTA .env 2>/dev/null || echo "No hay .env con credenciales"
```

---

### **Paso 2: Configurar Credenciales** (si no existen)

**Opciones**:

1. **Variables de entorno** (recomendado):
```bash
export IDEALISTA_API_KEY="tu_api_key"
export IDEALISTA_API_SECRET="tu_api_secret"
```

2. **Archivo .env**:
```bash
# Crear/actualizar .env
echo "IDEALISTA_API_KEY=tu_api_key" >> .env
echo "IDEALISTA_API_SECRET=tu_api_secret" >> .env
```

3. **Argumentos del script**:
```bash
python3 extract_idealista_api_gracia.py --api-key KEY --api-secret SECRET
```

**Documentación**: Ver `spike-data-validation/docs/IDEALISTA_API_SETUP.md`

---

### **Paso 3: Extraer Datos Reales de Idealista**

**Script**: `spike-data-validation/scripts/fase2/extract_idealista_api_gracia.py`

**Comando**:
```bash
python3 spike-data-validation/scripts/fase2/extract_idealista_api_gracia.py \
  --output-dir spike-data-validation/data/processed/fase2 \
  --max-properties 100
```

**Parámetros**:
- `--max-properties`: Número máximo de propiedades a extraer (50-100 recomendado)
- `--operation`: `sale` o `rent` (default: `sale`)
- `--api-key`: API key (opcional si está en env)
- `--api-secret`: API secret (opcional si está en env)

**Output esperado**:
- `idealista_gracia_api.csv`: Datos reales de Idealista
- `idealista_api_metadata.json`: Metadata de la extracción

---

### **Paso 4: Re-ejecutar Matching**

**Script**: `spike-data-validation/scripts/fase2/match_catastro_idealista.py`

**Comando**:
```bash
python3 spike-data-validation/scripts/fase2/match_catastro_idealista.py \
  --catastro-path spike-data-validation/data/processed/fase2/catastro_gracia_real.csv \
  --idealista-path spike-data-validation/data/processed/fase2/idealista_gracia_api.csv \
  --output-csv-path spike-data-validation/data/processed/fase2/catastro_idealista_matched_REAL.csv \
  --output-metadata-path spike-data-validation/data/processed/fase2/matching_REAL_metadata.json
```

**Validación esperada**:
- Match rate: ≥40% (típico para datos reales)
- Observaciones matched: ≥50 (mínimo para modelo)

---

### **Paso 5: Re-ejecutar EDA con Datos Reales**

**Notebook**: `spike-data-validation/notebooks/03_EDA_micro_hedonic.ipynb`

**Pasos**:
1. Actualizar ruta de datos en celda de carga
2. Ejecutar todas las celdas
3. Comparar correlaciones mock vs real
4. Validar si mejoran las relaciones

**Comparación esperada**:
- Correlaciones deberían ser más altas y positivas
- Menos outliers o outliers más razonables
- Distribuciones más realistas

---

### **Paso 6: Re-entrenar Modelo con Datos Reales**

**Script**: `spike-data-validation/scripts/fase2/train_micro_hedonic.py`

**Comando**:
```bash
python3 spike-data-validation/scripts/fase2/train_micro_hedonic.py \
  --input spike-data-validation/data/processed/fase2/catastro_idealista_matched_REAL.csv \
  --model linear \
  --log-transform \
  --interactions \
  --use-cv
```

**Métricas objetivo** (con datos reales):
- R² test: ≥0.75
- RMSE test: ≤250 €/m²
- Bias test: ≤±100 €/m²
- Mejora vs MACRO: R² +0.05, RMSE -50 €/m²

---

### **Paso 7: Comparación Mock vs Real**

**Análisis a realizar**:

1. **Correlaciones**:
   - Mock: superficie_m2 = -0.091, habitaciones = -0.223
   - Real: Esperado superficie_m2 = +0.3 a +0.5, habitaciones = +0.2 a +0.4

2. **Métricas del modelo**:
   - Mock: R² = -0.198, RMSE = 724.50 €/m²
   - Real: Esperado R² ≥0.50, RMSE ≤400 €/m²

3. **Match rate**:
   - Mock: 46.7% (28/60 referencias)
   - Real: Esperado 40-60% (típico para datos reales)

**Documento a crear**: `ANALISIS_MOCK_VS_REAL.md`

---

## 🚀 Ejecución Paso a Paso

### **Fase A: Preparación (5 min)**

```bash
# 1. Verificar credenciales
cd /Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer
python3 -c "import os; print('API Key:', '✅' if os.getenv('IDEALISTA_API_KEY') else '❌'); print('API Secret:', '✅' if os.getenv('IDEALISTA_API_SECRET') else '❌')"
```

**Si no hay credenciales**:
- Ver `spike-data-validation/docs/IDEALISTA_API_SETUP.md`
- Solicitar credenciales en https://developers.idealista.com/
- O usar cliente GitHub alternativo (ver script)

---

### **Fase B: Extracción (10-15 min)**

```bash
# 2. Extraer datos reales
python3 spike-data-validation/scripts/fase2/extract_idealista_api_gracia.py \
  --max-properties 100 \
  --output-dir spike-data-validation/data/processed/fase2
```

**Validación**:
- Verificar que se generó `idealista_gracia_api.csv`
- Verificar número de propiedades extraídas (≥50)
- Revisar metadata para validar calidad

---

### **Fase C: Matching (5 min)**

```bash
# 3. Matching con datos reales
python3 spike-data-validation/scripts/fase2/match_catastro_idealista.py \
  --catastro-path spike-data-validation/data/processed/fase2/catastro_gracia_real.csv \
  --idealista-path spike-data-validation/data/processed/fase2/idealista_gracia_api.csv \
  --output-csv-path spike-data-validation/data/processed/fase2/catastro_idealista_matched_REAL.csv
```

**Validación**:
- Match rate ≥40%
- Observaciones matched ≥50

---

### **Fase D: EDA y Modelo (20-30 min)**

```bash
# 4. Re-entrenar modelo con datos reales
python3 spike-data-validation/scripts/fase2/train_micro_hedonic.py \
  --input spike-data-validation/data/processed/fase2/catastro_idealista_matched_REAL.csv \
  --model linear \
  --log-transform \
  --interactions \
  --use-cv
```

**Validación**:
- R² test ≥0.50 (mejora significativa vs mock)
- Comparar con baseline MACRO
- Documentar resultados

---

## 📊 Métricas de Éxito

### **Checkpoint 1: Extracción**

- ✅ ≥50 propiedades extraídas
- ✅ Estructura compatible con matching
- ✅ Metadata completa

### **Checkpoint 2: Matching**

- ✅ Match rate ≥40%
- ✅ ≥50 observaciones matched
- ✅ Completitud de campos críticos ≥90%

### **Checkpoint 3: Modelo**

- ✅ R² test ≥0.50 (mejora vs mock)
- ✅ RMSE test ≤400 €/m² (mejora vs mock)
- ✅ Comparación con MACRO documentada

---

## ⚠️ Contingencias

### **Si no hay credenciales API**

**Opción 1**: Usar cliente GitHub alternativo
```bash
pip install git+https://github.com/yagueto/idealista-api.git
```

**Opción 2**: Continuar con datos mock y documentar limitación

**Opción 3**: Solicitar credenciales y esperar aprobación

---

### **Si match rate es muy bajo (<30%)**

**Acciones**:
1. Revisar normalización de referencias catastrales
2. Verificar formato de direcciones
3. Considerar fuzzy matching
4. Documentar limitación

---

### **Si modelo sigue con bajo rendimiento**

**Acciones**:
1. Revisar correlaciones en EDA
2. Validar calidad de datos reales
3. Considerar aumentar muestra
4. Documentar hallazgos

---

## 📝 Documentación a Generar

1. **`IDEALISTA_EXTRACTION_REAL.md`**: Resumen de extracción
2. **`MATCHING_REAL_RESULTS.md`**: Resultados de matching
3. **`EDA_REAL_VS_MOCK.md`**: Comparación EDA
4. **`MODEL_REAL_RESULTS.md`**: Resultados modelo con datos reales
5. **`ANALISIS_MOCK_VS_REAL.md`**: Análisis comparativo completo

---

## 🔗 Archivos Relacionados

- **Script extracción**: `spike-data-validation/scripts/fase2/extract_idealista_api_gracia.py`
- **Script matching**: `spike-data-validation/scripts/fase2/match_catastro_idealista.py`
- **Script modelo**: `spike-data-validation/scripts/fase2/train_micro_hedonic.py`
- **Notebook EDA**: `spike-data-validation/notebooks/03_EDA_micro_hedonic.ipynb`
- **Setup API**: `spike-data-validation/docs/IDEALISTA_API_SETUP.md`

---

**Última actualización**: 2025-12-19

