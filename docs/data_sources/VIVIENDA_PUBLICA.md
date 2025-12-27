## Fuente: Vivienda Pública - IDESCAT y Open Data BCN

### Descripción general

Los datos de **vivienda pública** son fundamentales para entender el mercado de alquiler protegido y la regulación del mercado inmobiliario en Barcelona. Estos datos provienen de dos fuentes:
1. **IDESCAT**: Datos a nivel municipal (Barcelona)
2. **Open Data BCN**: Datos de habitatge (cuotas catastrales, viviendas)

**⚠️ IMPORTANTE**: Los datos de IDESCAT son a nivel **municipal**, no por barrio. Se distribuyen proporcionalmente por barrio usando población o renta como peso. Estos son **valores estimados**, no datos reales por barrio.

**URLs**:
- IDESCAT API: https://api.idescat.cat/emex/v1
- Open Data BCN Habitatge: https://opendata-ajuntament.barcelona.cat/data/es/organization/habitatge

### Cobertura y granularidad

- **Ámbito geográfico**: Barcelona ciudad, nivel barrio (73 barrios objetivo).
- **Frecuencia temporal**: Anual (IDESCAT: según disponibilidad).
- **Variables clave**:
  - `contratos_alquiler_nuevos`: Número de contratos de alquiler nuevos (estimado)
  - `fianzas_depositadas_euros`: Fianzas depositadas en euros (estimado)
  - `renta_media_mensual_alquiler`: Renta media mensual de alquiler (estimado)
  - `viviendas_proteccion_oficial`: Número de viviendas de protección oficial

### Fuentes de datos

#### 1. IDESCAT - API REST

Datos de alquiler y vivienda pública a nivel municipal (Barcelona).

**Endpoint**: `https://api.idescat.cat/emex/v1`

**Parámetros**:
- `lang`: Idioma (es, ca)
- `year`: Año de los datos
- `territory`: Código INE de Barcelona (080193)

**Limitación**: Datos a nivel municipal, requiere distribución proporcional por barrio.

**Procesamiento**:
1. Extracción mediante `ViviendaPublicaExtractor.extract_idescat_alquiler(year)`
2. **Distribución proporcional** (opcional) mediante `distribute_to_barrios()`:
   - Usa `fact_demografia.poblacion_total` como peso (default)
   - O `fact_renta.renta_mediana` como peso alternativo
   - Calcula valores estimados por barrio usando la fórmula: `valor_barrio = valor_municipal × (peso_barrio / peso_total)`
3. Los valores distribuidos se marcan con `is_estimated=True` en el DataFrame
4. Inserción en `fact_vivienda_publica` con `source='idescat_distribuido'`

⚠️ **CRÍTICO**: La distribución proporcional genera **ESTIMACIONES**, no datos reales por barrio. El extractor incluye advertencias claras en los logs y metadata.

#### 2. Open Data BCN - Habitatge

Datos de vivienda del Ayuntamiento de Barcelona (cuotas catastrales, viviendas familiares).

**Estado**: Parcialmente implementado (requiere exploración de datasets específicos)

### Scripts de procesamiento

#### Extracción IDESCAT (sin distribución)
```bash
python -c "from src.extraction.vivienda_publica_extractor import ViviendaPublicaExtractor; e = ViviendaPublicaExtractor(); e.extract_all(2024, distribute=False)"
```

#### Extracción IDESCAT con distribución proporcional por barrio
⚠️ **IMPORTANTE**: Los valores resultantes son **ESTIMACIONES**, no datos reales por barrio.

```bash
python -c "from src.extraction.vivienda_publica_extractor import ViviendaPublicaExtractor; from pathlib import Path; e = ViviendaPublicaExtractor(); e.extract_all(2024, distribute=True, weight_type='poblacion', db_path=Path('data/processed/database.db'))"
```

#### Procesamiento y carga (método alternativo)
```bash
python scripts/process_vivienda_publica_data.py
```

### Estructura de datos

#### Tabla: `fact_vivienda_publica`

```sql
CREATE TABLE fact_vivienda_publica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    contratos_alquiler_nuevos INTEGER,
    fianzas_depositadas_euros REAL,
    renta_media_mensual_alquiler REAL,
    viviendas_proteccion_oficial INTEGER,
    dataset_id TEXT,
    source TEXT DEFAULT 'incasol_idescat',
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
```

### Distribución proporcional

Los datos municipales se distribuyen por barrio usando la siguiente fórmula:

```
valor_barrio = valor_municipal × (peso_barrio / peso_total)
```

Donde:
- `peso_barrio`: Población total o renta mediana del barrio
- `peso_total`: Suma de pesos de todos los barrios

**Ejemplo**:
- Barcelona total: 1000 contratos de alquiler
- Barrio A: 10% de la población → 100 contratos estimados
- Barrio B: 5% de la población → 50 contratos estimados

### Validaciones

- **Cobertura geográfica**: ≥ 95% barrios (≥69 de 73)
- **Completitud**: ≥ 95% campos obligatorios
- **Integridad referencial**: FK a `dim_barrios` validada
- **Advertencia**: Los valores son estimaciones, no datos reales por barrio

### Notas importantes

- **⚠️ CRÍTICO**: Los datos distribuidos son **ESTIMACIONES** por distribución proporcional, no datos reales por barrio
- La distribución usa población como peso por defecto (`weight_type='poblacion'`), pero se puede usar renta como alternativa (`weight_type='renta'`)
- El extractor incluye advertencias claras en:
  - Logs: Mensajes de warning con emoji ⚠️
  - Metadata: Campo `is_estimated=True` y `warning` con texto explicativo
  - DataFrame: Columna `is_estimated=True` para cada registro distribuido
- Documentar claramente en la BD que `source='idescat_distribuido'` indica valores estimados
- Si hay datos reales por barrio disponibles, preferirlos sobre la distribución proporcional
- El método `distribute_to_barrios()` puede fallar si:
  - La base de datos no existe
  - No hay barrios con pesos disponibles
  - Los datos municipales están vacíos

### Uso del extractor

#### Extracción básica (datos municipales)
```python
from src.extraction.vivienda_publica_extractor import ViviendaPublicaExtractor

extractor = ViviendaPublicaExtractor()
df_municipal, meta = extractor.extract_idescat_alquiler(2024)
# df_municipal contiene datos a nivel municipal (Barcelona)
```

#### Extracción con distribución proporcional
```python
from pathlib import Path

extractor = ViviendaPublicaExtractor()
db_path = Path("data/processed/database.db")

# Distribuir usando población como peso
df_distributed, meta = extractor.extract_all(
    year=2024,
    distribute=True,
    weight_type="poblacion",  # o "renta"
    db_path=db_path
)

# Verificar advertencias
assert meta["is_estimated"] is True
assert "warning" in meta
print(meta["warning"])  # Muestra advertencia sobre estimaciones
```

#### Distribución manual
```python
# Después de extraer datos municipales
df_municipal, meta = extractor.extract_idescat_alquiler(2024)

# Distribuir manualmente
df_distributed, dist_meta = extractor.distribute_to_barrios(
    df_municipal,
    db_path=db_path,
    weight_type="poblacion",
    year=2024
)

# Todos los registros tienen is_estimated=True
assert all(df_distributed["is_estimated"] == True)
```

### Referencias

- [IDESCAT API](https://api.idescat.cat/emex/v1)
- [Open Data BCN Habitatge](https://opendata-ajuntament.barcelona.cat/data/es/organization/habitatge)
- [IDESCAT - Renta de Alquiler](https://www.idescat.cat/pub/?id=lh)

