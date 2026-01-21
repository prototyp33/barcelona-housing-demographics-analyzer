# Guía: Usar CSV Files en Looker Studio

## ✅ Exportación Completada

**Archivos exportados**: 25  
**Total de filas**: 21,948  
**Ubicación**: `data/exports/looker_studio/`

## Estructura de Archivos

Los archivos están organizados en carpetas por categoría:

```
data/exports/looker_studio/
├── 01_dimensions/          # Datos maestros (barrios, tiempo)
├── 02_market/              # Datos de mercado (precios, oferta)
├── 03_demographics/        # Demografía y renta
├── 04_environment/         # Calidad ambiental
├── 05_social/              # Servicios sociales
├── 06_tourism/             # Turismo
├── 07_housing/             # Vivienda
├── 08_advanced/            # Métricas avanzadas
└── README.md               # Documentación completa
```

## Archivos Esenciales para Empezar

### Para Análisis Básico de Precios

**Archivos necesarios**:
1. `01_dimensions/dim_barrios.csv` - **OBLIGATORIO** (para joins)
2. `02_market/fact_precios.csv` - Precios de vivienda

**Cómo usar**:
1. Sube ambos archivos a Looker Studio
2. Crea un blend usando `barrio_id` como clave de unión
3. Visualiza precios por barrio/distrito

### Para Análisis Demográfico

**Archivos necesarios**:
1. `01_dimensions/dim_barrios.csv` - **OBLIGATORIO**
2. `03_demographics/fact_demografia_ampliada.csv` - Demografía detallada
3. `03_demographics/fact_renta.csv` - Datos de renta

### Para Análisis de Gentrificación

**Archivos necesarios**:
1. `01_dimensions/dim_barrios.csv` - **OBLIGATORIO**
2. `02_market/fact_precios.csv` - Evolución de precios
3. `06_tourism/fact_turismo_intensidad.csv` - Presión turística
4. `03_demographics/fact_renta.csv` - Cambios en renta

### Para Dashboard Completo

**Archivos recomendados** (sube todos estos):
- `01_dimensions/dim_barrios.csv` ⭐ **SIEMPRE NECESARIO**
- `01_dimensions/dim_tiempo.csv` (opcional, para análisis temporal)
- `02_market/fact_precios.csv`
- `03_demographics/fact_demografia_ampliada.csv`
- `03_demographics/fact_renta.csv`
- `04_environment/fact_calidad_aire.csv`
- `05_social/fact_seguridad.csv`
- `06_tourism/fact_turismo_intensidad.csv`

## Cómo Subir Archivos a Looker Studio

### Paso 1: Crear Data Source

1. En Looker Studio: **Create** → **Data Source**
2. Selecciona **File Upload**
3. Arrastra o selecciona el archivo CSV
4. Looker Studio detectará automáticamente las columnas

### Paso 2: Configurar Campos

Looker Studio detectará automáticamente:
- **Dimensiones**: `barrio_id`, `barrio_nombre`, `distrito_nombre`, `anio`
- **Métricas**: `precio_m2_venta`, `poblacion_total`, `renta_mediana`, etc.

**Ajusta tipos de datos si es necesario**:
- `barrio_id` → Number
- `anio` → Number (Year)
- `precio_m2_venta` → Number (Currency)
- Fechas → Date

### Paso 3: Crear Blend (Para Múltiples Archivos)

Si necesitas combinar múltiples archivos:

1. Crea data sources para cada archivo
2. En tu reporte: **Resource** → **Manage Blended Data**
3. Añade las data sources
4. Configura la unión:
   - **Join keys**: `barrio_id` (y opcionalmente `anio`)
   - **Join type**: Left outer join (para incluir todos los barrios)

## Ejemplos de Uso

### Ejemplo 1: Precio Promedio por Distrito

**Data Source**: `fact_precios.csv` + `dim_barrios.csv` (blended)

**Campos**:
- Dimension: `distrito_nombre`
- Metric: `AVG(precio_m2_venta)`

**Visualización**: Tabla o gráfico de barras

### Ejemplo 2: Evolución Temporal de Precios

**Data Source**: `fact_precios.csv`

**Campos**:
- Dimension: `anio`
- Metric: `AVG(precio_m2_venta)`

**Visualización**: Línea de tiempo

### Ejemplo 3: Mapa de Calor por Barrio

**Data Source**: `fact_precios.csv` + `dim_barrios.csv` (blended)

**Campos**:
- Dimension: `barrio_nombre`
- Metric: `AVG(precio_m2_venta)`

**Visualización**: Mapa geográfico (si Looker Studio tiene datos de ubicación)

### Ejemplo 4: Correlación Precio vs Renta

**Data Sources**: 
- `fact_precios.csv`
- `fact_renta.csv`
- `dim_barrios.csv` (para blend)

**Campos**:
- X-axis: `AVG(renta_mediana)`
- Y-axis: `AVG(precio_m2_venta)`
- Dimension: `barrio_nombre` (para tooltips)

**Visualización**: Scatter plot

## Claves de Unión (Join Keys)

Para combinar archivos, usa estas claves:

| Clave | Descripción | Archivos que la tienen |
|-------|-------------|------------------------|
| `barrio_id` | ID único del barrio (1-73) | Todos los fact_* y dim_barrios |
| `barrio_nombre` | Nombre del barrio | dim_barrios, algunos fact_* |
| `anio` | Año | La mayoría de fact_* |
| `distrito_nombre` | Nombre del distrito | dim_barrios |

## Actualizar Datos

Para refrescar los datos después de actualizar la base de datos:

```bash
python scripts/export_data_for_looker_studio.py
```

Luego:
1. Descarga los nuevos CSV
2. Reemplaza los archivos en Looker Studio
3. O crea nuevas data sources con los archivos actualizados

## Limitaciones de File Upload

- ⚠️ **Tamaño máximo**: 100 MB por archivo (Looker Studio)
- ⚠️ **Sin actualización automática**: Debes re-subir archivos manualmente
- ⚠️ **Sin conexión en tiempo real**: Los datos son estáticos hasta que re-subas

## Ventajas

- ✅ **No requiere configuración de conexión**
- ✅ **Funciona inmediatamente**
- ✅ **No requiere tarjetas de crédito**
- ✅ **Fácil de compartir y versionar**

---

**Para más detalles**: Ver `data/exports/looker_studio/README.md`
