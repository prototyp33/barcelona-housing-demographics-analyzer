# Plan de Implementación - Matching Geográfico

**Fecha**: 20 de diciembre de 2025  
**Issue**: #202 - Mejora de matching  
**Estado**: ✅ Script implementado, pendiente ejecución

---

## 🎯 Objetivo

Implementar matching geográfico basado en coordenadas (lat/lon) para mejorar la calidad del matching entre Idealista y Catastro, resolviendo el problema de correlaciones negativas identificado.

---

## 📊 Contexto

### Problema Actual

- **Matching heurístico**: 77.8% match rate, pero 40% de baja calidad (score < 0.6)
- **Correlaciones negativas**: `superficie_m2` - `precio_m2` = -0.186 (debería ser positiva)
- **Causa probable**: Matching incorrecto (propiedades de Idealista no corresponden a Catastro)

### Solución Propuesta

**Matching geográfico** usando coordenadas:
- Catastro tiene coordenadas (lat/lon) para cada edificio
- Idealista necesita geocodificación de direcciones
- Distancia máxima: 50m (ajustable)
- Combinación ponderada: 60% geográfico + 40% heurístico

---

## ✅ Tareas Completadas

- [x] Verificar disponibilidad de coordenadas en Catastro ✅
  - Catastro tiene `lat` y `lon` para 77.8% de matches
- [x] Implementar función `match_by_coordinates()` ✅
- [x] Implementar geocoding de direcciones Idealista ✅
- [x] Combinar con matching heurístico (score ponderado) ✅
- [x] Script completo: `match_idealista_catastro_geographic.py` ✅

---

## ⏳ Tareas Pendientes

- [ ] **Ejecutar geocoding de Idealista** (puede tardar 10-15 minutos)
  - 505 propiedades a geocodificar
  - Rate limit: 1 request/segundo (Nominatim)
  - Tiempo estimado: ~8-10 minutos
- [ ] **Ejecutar matching geográfico completo**
  - Comparar con matching heurístico actual
  - Verificar mejora en correlaciones
- [ ] **Re-entrenar modelo con nuevo matching**
  - Comparar R² y RMSE
  - Verificar si mejora sobre baseline MACRO
- [ ] **Documentar resultados**

---

## 🔧 Uso del Script

### Instalación de Dependencias

```bash
pip install geopy
```

### Ejecución Básica

```bash
python3 spike-data-validation/scripts/fase2/match_idealista_catastro_geographic.py
```

### Opciones Avanzadas

```bash
python3 spike-data-validation/scripts/fase2/match_idealista_catastro_geographic.py \
    --idealista spike-data-validation/data/processed/fase2/idealista_gracia_comet.csv \
    --catastro spike-data-validation/data/processed/catastro_gracia_real.csv \
    --output spike-data-validation/data/processed/fase2/idealista_catastro_matched_geographic.csv \
    --max-distance 50 \
    --geographic-weight 0.6 \
    --min-score 0.5
```

### Parámetros

- `--max-distance`: Distancia máxima en metros (default: 50)
- `--geographic-weight`: Peso del score geográfico 0-1 (default: 0.6)
- `--min-score`: Score mínimo para considerar match (default: 0.5)
- `--skip-geocoding`: Saltar geocoding si ya tienes coordenadas

---

## 📊 Métricas Esperadas

### Mejoras Esperadas

- **Match rate**: Mantener o mejorar 77.8%
- **Calidad de matches**: Reducir % de score < 0.6
- **Correlaciones**: Cambiar de negativas a positivas
  - `superficie_m2` - `precio_m2`: De -0.186 a >0.2
  - `habitaciones` - `precio_m2`: De -0.202 a >0.1
- **R² del modelo**: Mejorar de 0.21 a >0.5 (objetivo: 0.75)

### Criterios de Éxito

- ✅ Correlaciones positivas con `superficie_m2` y `habitaciones`
- ✅ R² del modelo ≥ 0.5 (mejora significativa)
- ✅ RMSE < 1,500 €/m² (mejora sobre 2,113 actual)
- ✅ Match rate ≥ 70% (mantener calidad)

---

## ⚠️ Consideraciones

### Rate Limits de Geocoding

- **Nominatim (OpenStreetMap)**: 1 request/segundo
- **Tiempo estimado**: ~8-10 minutos para 505 propiedades
- **Alternativas**: 
  - Usar API de Google Maps (requiere API key, tiene costo)
  - Cachear resultados para evitar re-geocodificar

### Calidad de Geocoding

- **Depende de calidad de direcciones** en Idealista
- Algunas direcciones pueden ser ambiguas
- Verificar manualmente una muestra después de geocodificar

### Distancia Máxima

- **50m**: Estricto, solo matches muy cercanos
- **100m**: Más permisivo, puede incluir matches incorrectos
- **Recomendación**: Empezar con 50m, ajustar según resultados

---

## 📝 Próximos Pasos

1. **Ejecutar geocoding** (10-15 min)
   ```bash
   python3 match_idealista_catastro_geographic.py
   ```

2. **Verificar resultados de geocoding**
   - Revisar `idealista_gracia_comet_with_coords.csv`
   - Verificar que coordenadas están en rango de Barcelona

3. **Ejecutar matching completo**
   - Comparar métricas con matching heurístico
   - Verificar mejora en correlaciones

4. **Re-entrenar modelo**
   - Usar nuevo dataset matched
   - Comparar R² y RMSE

5. **Documentar resultados**
   - Actualizar Issue #202
   - Crear comparativa matching heurístico vs geográfico

---

## 🔗 Archivos Relacionados

- **Script**: `scripts/fase2/match_idealista_catastro_geographic.py`
- **Matching heurístico**: `scripts/fase2/match_idealista_catastro_improved.py`
- **Notebook entrenamiento**: `notebooks/06_train_micro_hedonic_model.ipynb`
- **Resultados actuales**: `docs/MODELO_MICRO_RESULTADOS_FINALES.md`

---

**Última actualización**: 2025-12-20  
**Estado**: ✅ Script listo, pendiente ejecución

