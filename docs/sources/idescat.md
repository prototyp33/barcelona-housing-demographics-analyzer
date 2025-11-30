# IDESCAT Extractor - Guía Rápida

**Fuente:** Institut d'Estadística de Catalunya (IDESCAT)  
**Datos:** Renta histórica por barrio (2015-2023)  
**Estado:** ✅ Funcional

---

## ¿Qué hace este extractor?

Extrae datos de **renta disponible por barrio** de Barcelona. La idea original era usar la API de IDESCAT, pero resulta que no tiene datos desagregados por barrio (solo a nivel de Cataluña). Así que el extractor usa **Open Data BCN** como fuente principal, que sí tiene los datos que necesitamos.

---

## Uso Básico

```python
from src.extraction.idescat import IDESCATExtractor

# Crear el extractor
extractor = IDESCATExtractor()

# Extraer datos de renta (2015-2023)
df, metadata = extractor.get_renta_by_barrio(year_start=2015, year_end=2023)

# Ver qué pasó
print(f"Éxito: {metadata['success']}")
print(f"Estrategia usada: {metadata['strategy_used']}")
print(f"Registros: {len(df)}")
```

---

## ¿Cómo funciona?

El extractor prueba 3 estrategias en orden:

1. **Open Data BCN** (principal) - Tiene 3 datasets confirmados con datos por barrio
2. **API IDESCAT** (fallback) - Solo datos agregados a nivel de Cataluña
3. **Web scraping** (último recurso) - Por si acaso

Normalmente funciona con la primera estrategia (Open Data BCN).

---

## Datasets que usa

Cuando usa Open Data BCN, prueba estos datasets en orden:

- `renda-disponible-llars-bcn` - Renda disponible per càpita (€)
- `atles-renda-bruta-per-llar` - Renda bruta mitjana per llar (€)  
- `atles-renda-bruta-per-persona` - Renda bruta mitjana per persona (€)

Todos tienen `Codi_Barri` y `Nom_Barri`, así que se pueden agregar fácilmente por barrio.

---

## ¿Qué datos devuelve?

Un DataFrame con:
- `Codi_Barri` o `barrio_id` - Código del barrio
- `Nom_Barri` - Nombre del barrio
- Columnas de renta (varían según el dataset)
- `dataset_id` - De qué dataset vino
- `source` - Siempre "opendatabcn"

Si los datos vienen por sección censal, el extractor los agrega automáticamente por barrio.

---

## Dónde se guardan los datos

Los datos raw se guardan en:
```
data/raw/idescat/idescat_renta_{year_start}_{year_end}_{timestamp}.csv
```

También se registra en `data/raw/manifest.json` con `data_type="renta_historica"` para que el pipeline ETL los encuentre fácilmente.

---

## Limitaciones

- **API IDESCAT:** Solo tiene datos agregados (nivel Cataluña), no por barrio
- **Open Data BCN:** Funciona bien, pero los datasets pueden no tener todos los años
- **Cobertura temporal:** Depende de qué años tenga cada dataset

---

## Ejemplo Completo

```python
from src.extraction.idescat import IDESCATExtractor

extractor = IDESCATExtractor(rate_limit_delay=1.0)

# Extraer datos
df, metadata = extractor.get_renta_by_barrio(2020, 2022)

if metadata['success']:
    print(f"✅ Datos extraídos: {len(df)} registros")
    print(f"   Estrategia: {metadata['strategy_used']}")
    print(f"   Columnas: {list(df.columns)}")
    print(f"\nPrimeras filas:")
    print(df.head())
else:
    print(f"❌ Error: {metadata.get('error', 'Desconocido')}")
```

---

## Notas Técnicas

- **Rate limiting:** Por defecto 1 segundo entre peticiones (configurable)
- **Manejo de errores:** Si una estrategia falla, prueba la siguiente automáticamente
- **Logging:** Todo se registra en `logs/data_extraction_YYYYMMDD.log`
- **Tests:** 13 tests unitarios (todos pasando ✅)

---

## Más Información

- **Investigación completa:** `docs/IDESCAT_INVESTIGATION_FINAL.md`
- **Código:** `src/extraction/idescat.py`
- **Tests:** `tests/test_idescat.py`
- **Issue relacionada:** #32 (completada)

---

**Última actualización:** Noviembre 2025

