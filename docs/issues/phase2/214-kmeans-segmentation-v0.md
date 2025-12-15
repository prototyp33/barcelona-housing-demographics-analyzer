## Descripción
Implementar segmentación K-Means sobre 73 barrios usando SOLO datos existentes en DB.

## Objetivo
Validar si clustering produce submarkets urbanos interpretables con Silhouette > 0.4.

## Tareas

### Preparación de Datos
- [ ] Query SQL para extraer features (porc_inmigracion, precio_alquiler, renta_mediana)
- [ ] Calcular distancia al centro usando centroides existentes
- [ ] Normalizar features (StandardScaler)

### Modeling
- [ ] Método del codo (k=2..10)
- [ ] Silhouette analysis para determinar k óptimo
- [ ] Bootstrap stability test (100 iteraciones)

### Validación
- [ ] Verificar Silhouette Score > 0.4
- [ ] Validar CV < 15% en bootstrap
- [ ] Generar perfiles de cluster interpretables

### Entregables
- [ ] Notebook completo en `notebooks/analysis/01_market_segmentation_v0.ipynb`
- [ ] Mapa choropleth con clusters
- [ ] Documento: `docs/analysis/MARKET_SEGMENTATION_V0_RESULTS.md`

## Criterios de Aceptación
- Silhouette Score > 0.4 (clusters distintos)
- Bootstrap stability CV < 15% (reproducible)
- Cada cluster tiene perfil urbano claro (ej: "Centro-Alto-Renta", "Periferia-Inmigrante")
- Mapa choropleth visualiza clusters
- Documentación de resultados completa

## Estimación
10-12 horas

## Prioridad
Alta

## Dependencies
**Depends On:** #211 (códigos INE) - SOFT  
**Feeds Into:** #218 (Bayesian Networks) - Submarkets informan segmentación causal

## Archivos relacionados
- `src/analysis/market_segmentation.py` (a crear)
- `notebooks/analysis/01_market_segmentation_v0.ipynb` (a crear)
- `docs/analysis/MARKET_SEGMENTATION_V0_RESULTS.md` (a crear)
