## Fuente: Equipamientos Educativos - Open Data BCN

### Descripción general

Los datos de **equipamientos educativos** son fundamentales para entender la oferta educativa en los barrios de Barcelona. Estos datos provienen del **Open Data BCN** del Ayuntamiento de Barcelona y se utilizan para construir la tabla de hechos `fact_educacion`.

**URLs**:
- Portal: https://opendata-ajuntament.barcelona.cat/data/es/dataset/equipament-educacio
- API CKAN: `https://opendata-ajuntament.barcelona.cat/api/3/action/package_show?id=equipament-educacio`
- Resource ID: `d0471a29-821f-42aa-b631-19a76052bdff`

### Cobertura y granularidad

- **Ámbito geográfico**: Barcelona ciudad, nivel barrio (73 barrios objetivo).
- **Frecuencia temporal**: Anual (datos actualizados semanalmente).
- **Variables clave**:
  - `num_centros_infantil`: Número de centros de educación infantil
  - `num_centros_primaria`: Número de centros de educación primaria
  - `num_centros_secundaria`: Número de centros de educación secundaria
  - `num_centros_fp`: Número de centros de formación profesional
  - `num_centros_universidad`: Número de centros universitarios
  - `total_centros_educativos`: Total de centros educativos

### Fuentes de datos

#### 1. Open Data BCN - Equipament Educació

Dataset oficial del Ayuntamiento de Barcelona con todos los equipamientos educativos de la ciudad.

**Formato**: CSV, JSON (vía API CKAN)

**Datos disponibles**:
- Nombre del equipamiento
- Tipo de equipamiento
- Dirección completa
- Coordenadas geográficas (latitud, longitud)
- Código de distrito/barrio

**Procesamiento**:
1. Extracción mediante `EducacionExtractor` (usa `OpenDataBCNExtractor`)
2. **Validación de coordenadas**: Filtrado de registros con coordenadas válidas dentro del rango geográfico de Barcelona
   - Latitud: 41.35 - 41.45
   - Longitud: 2.05 - 2.25
   - Criterio: 100% de registros retornados tienen coordenadas válidas
3. Geocodificación de coordenadas → barrio usando `dim_barrios.geometry_json`
4. Clasificación por tipo educativo (infantil, primaria, secundaria, FP, universidad)
5. Agregación por barrio y año

### Rate Limits

- **Open Data BCN CKAN API**: 30 peticiones/minuto
- **Rate limit delay recomendado**: 2.0 segundos entre peticiones

### Scripts de procesamiento

#### Extracción
```bash
python -c "from src.extraction.educacion_extractor import EducacionExtractor; e = EducacionExtractor(); e.extract_equipamientos()"
```

#### Procesamiento y carga
```bash
python scripts/process_educacion_data.py
```

### Estructura de datos

#### Tabla: `fact_educacion`

```sql
CREATE TABLE fact_educacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    num_centros_infantil INTEGER DEFAULT 0,
    num_centros_primaria INTEGER DEFAULT 0,
    num_centros_secundaria INTEGER DEFAULT 0,
    num_centros_fp INTEGER DEFAULT 0,
    num_centros_universidad INTEGER DEFAULT 0,
    total_centros_educativos INTEGER DEFAULT 0,
    dataset_id TEXT,
    source TEXT DEFAULT 'opendata_bcn_educacion',
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
```

### Validaciones

- **Cobertura de equipamientos**: ≥500 equipamientos extraídos
- **Validación de coordenadas**: 100% de registros retornados tienen coordenadas válidas dentro del rango de Barcelona
- **Cobertura geográfica**: ≥ 95% barrios (≥69 de 73)
- **Completitud**: ≥ 95% campos obligatorios
- **Integridad referencial**: FK a `dim_barrios` validada
- **Tests unitarios**: Cobertura ≥80%

### Notas importantes

- Los datos se actualizan semanalmente en Open Data BCN
- **Validación automática**: El extractor valida automáticamente que todas las coordenadas estén dentro del rango geográfico de Barcelona antes de retornar los datos
- La geocodificación requiere que `dim_barrios` tenga `geometry_json` poblado
- La clasificación de tipos educativos se hace mediante keywords en el nombre del tipo
- El extractor detecta automáticamente diferentes nombres de columnas de coordenadas (latitud/longitud, latitude/longitude, coord_x/coord_y, etc.)

### Criterios de Aceptación

- ✅ ≥500 equipamientos extraídos
- ✅ 100% registros con coordenadas válidas (validación automática)
- ✅ Tests pasan con cobertura ≥80%
- ✅ Documentación completa
- ✅ Tabla `fact_educacion` poblada con datos de 73 barrios

### Referencias

- [Open Data BCN - Equipament Educació](https://opendata-ajuntament.barcelona.cat/data/es/dataset/equipament-educacio)
- [Documentación API CKAN](https://docs.ckan.org/en/latest/api/)

