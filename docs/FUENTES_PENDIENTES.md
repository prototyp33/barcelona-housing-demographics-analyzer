# Fuentes de Datos Pendientes

Este documento rastrea el estado de búsqueda e integración de fuentes adicionales para enriquecer el análisis.

## Prioridad Alta 🔴

### 1. Demografía Ampliada ✅ COMPLETADO
- **Fuente**: Open Data BCN (`pad_mdb_lloc-naix-continent_edat-q_sexe`)
- **Datos**: Edad quinquenal, nacionalidad (por continente de nacimiento), composición por sexo
- **Estado**: ✅ Completado
- **Implementación**: 
  - Extractor: `DemografiaAmpliadaExtractor` en `scripts/extract_priority_sources.py`
  - Procesamiento: `prepare_demografia_ampliada()` en `src/data_processing.py`
  - Tabla: `fact_demografia_ampliada` en la base de datos
- **Notas**: Agrupa edades quinquenales en grupos personalizados (18-34, 35-49, 50-64, 65+)

### 2. GeoJSON de Barrios/Distritos ✅ COMPLETADO
- **Fuente**: Open Data BCN (`20170706-districtes-barris` - recursos `BarcelonaCiutat_Barris`)
- **Datos**: Geometrías en formato GeoJSON (Polygon) para los 73 barrios
- **Estado**: ✅ Completado
- **Implementación**:
  - Extractor: `GeoJSONExtractor` en `scripts/extract_priority_sources.py`
  - Conversión: WKT a GeoJSON usando `shapely`
  - Integración: `prepare_dim_barrios()` carga geometrías automáticamente
- **Notas**: Campo `geometry_json` en `dim_barrios` ahora contiene geometrías completas

### 3. Datos Socioeconómicos ✅ COMPLETADO
- **Fuente**: Open Data BCN (`renda-disponible-llars-bcn`, `atles-renda-bruta-per-llar`, `atles-renda-bruta-per-persona`)
- **Datos**: Renta Familiar Disponible (RFD) por barrio, agregada desde sección censal
- **Estado**: ✅ Completado
- **Implementación**:
  - Extractor: `RentaExtractor` en `scripts/extract_priority_sources.py`
  - Procesamiento: `prepare_renta_barrio()` en `src/data_processing.py`
  - Tabla: `fact_renta` en la base de datos
- **Notas**: Calcula promedio, mediana, min, max y número de secciones censales por barrio

## Prioridad Media 🟡

### 4. Mercado Inmobiliario Privado
- **Fuente**: Idealista API, Fotocasa, pisos.com
- **Datos**: Oferta actual, tiempo en mercado, precios por tipología
- **Estado**: ✅ COMPLETADO (requiere API credentials)
- **Notas**: 
  - `IdealistaExtractor` implementado con autenticación OAuth
  - Script de extracción: `scripts/extract_idealista.py`
  - Requiere `IDEALISTA_API_KEY` y `IDEALISTA_API_SECRET`
  - Extrae oferta de venta y alquiler por barrio
  - Función de procesamiento: `prepare_idealista_oferta()` en `data_processing.py`
  - Tabla: `fact_oferta_idealista` en la base de datos
  - Integrado en pipeline ETL: búsqueda automática, procesamiento y carga

### 5. Datos de Vivienda Pública
- **Fuente**: INCASÒL, Observatori Metropolità de l'Habitatge
- **Datos**: Stock de vivienda protegida, contratos de alquiler social
- **Estado**: ⏳ Pendiente

### 6. Indicadores de Movilidad y Turismo
- **Fuente**: Ajuntament (movilidad), ATM, InsideAirbnb
- **Datos**: Presión turística, desplazamientos diarios
- **Estado**: ⏳ Pendiente
- **Notas**: Ayuda a entender demanda transitoria

## Prioridad Baja 🟢

### 7. Indicadores Socioambientales
- **Fuente**: Barcelona Open Data, Agencia de Salut Pública
- **Datos**: Contaminación, ruido, zonas verdes
- **Estado**: ⏳ Pendiente

### 8. Catastro Detallado
- **Fuente**: Catastro, ATLL
- **Datos**: Superficies reales, eficiencia energética
- **Estado**: ⏳ Pendiente
- **Notas**: Mejoraría cálculos de densidad sin proxies

---

## Checklist de Integración

Para cada fuente nueva:

- [ ] Identificar URL/API/endpoint
- [ ] Revisar términos de uso y licencia
- [ ] Crear extractor en `src/data_extraction.py` (siguiendo patrón existente)
- [ ] Agregar procesamiento en `src/data_processing.py` si requiere transformación
- [ ] Actualizar `src/etl/pipeline.py` para incluir en el flujo
- [ ] Probar con datos de prueba
- [ ] Documentar en este archivo (cambiar estado a ✅ Completado)
- [ ] Actualizar `docs/DATA_STRUCTURE.md` con nuevos campos/tablas

---

## Notas de Implementación

### Estructura de Extractores

Los extractores siguen este patrón:

```python
class NuevaFuenteExtractor:
    def __init__(self, output_dir: Path = DATA_RAW_DIR):
        self.output_dir = output_dir
    
    def extract_datos(self, year_start: int, year_end: int):
        # Lógica de extracción
        # Guardar en self.output_dir / "nuevafuente" / "archivo.csv"
        return df, metadata
```

### Integración en ETL

1. Agregar llamada en `extract_all_sources()` (si aplica)
2. Crear función de preparación en `data_processing.py`
3. Incluir en `run_etl()` del pipeline

---

## Recursos Útiles

- **Open Data BCN**: https://opendata-ajuntament.barcelona.cat/
- **Portal de Dades**: https://portaldades.ajuntament.barcelona.cat/
- **INE**: https://www.ine.es/
- **IDESCAT**: https://www.idescat.cat/
- **CartoBCN**: https://www.cartobcn.cat/

---

*Última actualización: 2025-11-16*

