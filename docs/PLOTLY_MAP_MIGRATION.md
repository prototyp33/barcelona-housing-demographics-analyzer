# Migración de Mapbox a Map (Plotly)

**Fecha:** 2026-01-15  
**Motivo:** Eliminar warnings de deprecación de Plotly sobre `mapbox` subplots

---

## 📋 Cambios Realizados

### 1. Actualización de Configuración (`src/app/config.py`)

**Antes:**
```python
MAPBOX_CONFIG = {
    "mapbox_style": "carto-positron",
    ...
}
```

**Después:**
```python
MAP_CONFIG = {
    "map_style": "carto-positron",  # Compatible con MapLibre
    ...
}

# Mantener MAPBOX_CONFIG para compatibilidad
MAPBOX_CONFIG = MAP_CONFIG
```

---

### 2. Migración de Funciones Plotly

#### `px.choropleth_mapbox` → `px.choropleth_map`

**Archivos actualizados:**
- `src/app/views/map_analysis.py` (5 instancias)
- `src/app/views/demographics.py` (1 instancia)

**Cambios:**
- `px.choropleth_mapbox()` → `px.choropleth_map()`
- `mapbox_style` → `map_style`
- `featureidkey="id"` → `featureidkey="properties.barrio_id"`

#### `px.scatter_mapbox` → `px.scatter_map`

**Archivos actualizados:**
- `src/app/views/market_intelligence.py` (1 instancia)

**Cambios:**
- `px.scatter_mapbox()` → `px.scatter_map()`
- `mapbox_style` → `map_style`

---

## 🔍 Detalles Técnicos

### Feature ID Key

El `featureidkey` cambió de `"id"` a `"properties.barrio_id"` porque:

1. El GeoJSON generado en `build_geojson()` usa esta estructura:
```json
{
  "type": "Feature",
  "properties": {
    "barrio_id": 1,
    "barrio_nombre": "...",
    "distrito_nombre": "..."
  },
  "geometry": {...}
}
```

2. La nueva API `map` de Plotly requiere especificar la ruta completa a la propiedad.

---

## ✅ Verificación

### Antes de la migración:
```
WARN: mapbox subplots and traces are deprecated!
```

### Después de la migración:
- ✅ Sin warnings de deprecación
- ✅ Mapas funcionan correctamente
- ✅ Compatible con MapLibre (nueva tecnología de mapas de Plotly)

---

## 📚 Referencias

- [Plotly MapLibre Migration Guide](https://plotly.com/python/maplibre-migration/)
- [Plotly JavaScript MapLibre Migration](https://plotly.com/javascript/maplibre-migration/)

---

## 🔄 Compatibilidad

- ✅ **100% retrocompatible**: Los mapas funcionan igual que antes
- ✅ **Mismo estilo visual**: `carto-positron` sigue disponible
- ✅ **Mismas funcionalidades**: Zoom, center, opacity, etc.

---

**Última actualización:** 2026-01-15
