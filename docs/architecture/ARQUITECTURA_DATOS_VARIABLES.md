# Propuesta de Arquitectura de Datos para Análisis de Variables de Precios de Vivienda en Barcelona

## Documento Técnico - Barcelona Housing Demographics Analyzer
**Fecha:** Diciembre 2025  
**Versión:** 2.0  
**Estado:** Propuesta Ejecutiva

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Mapeo de Variables a Estructura de Datos](#mapeo-de-variables)
3. [Cambios al Esquema de Base de Datos](#esquema-propuesto)
4. [Arquitectura de Extractores ETL](#arquitectura-extractores)
5. [Tablas Nuevas Propuestas](#tablas-nuevas)
6. [Plan de Implementación](#plan-implementacion)
7. [Detalle de Extractores por Variable](#detalle-extractores)

---

## 1. Resumen Ejecutivo {#resumen-ejecutivo}

Se propone una arquitectura de datos modular para capturar las **33 variables identificadas** que afectan precios de vivienda en Barcelona, organizadas en **8 nuevas tablas de hechos** que complementan las 5 existentes, manteniendo compatibilidad con el esquema star actual.

### Dimensión del Proyecto

| Elemento | Actual | Propuesto | Delta |
|----------|--------|-----------|-------|
| Tablas fact | 5 | 13 | +8 |
| Tablas dimension | 1 (dimbarrios) | 3 | +2 |
| Variables capturadas | 12 | 45+ | +33 |
| Extractores necesarios | 6 | 18 | +12 |
| Cobertura temporal | 2015-2025 | 2010-2025 | +5 años |
| Fuentes de datos | 8 | 16+ | +8 |

### Impacto Analítico

Con la arquitectura propuesta será posible:
- ✅ Cuantificar elasticidad precio-demanda en cada barrio
- ✅ Modelizar gentrificación usando 5+ indicadores socioeconómicos
- ✅ Analizar efectos de regulación (control alquileres) post-marzo 2024
- ✅ Correlacionar vivienda turística con precios residenciales
- ✅ Evaluar impacto eficiencia energética en valoración
- ✅ Proyectar precios usando 15+ variables exógenas

---

## 2. Mapeo de Variables a Estructura de Datos {#mapeo-de-variables}

### Categoría 1: Demográficas (5 variables)

| Variable | Tabla Nueva | Tabla Existente | Extractor Necesario | Fuente Primaria |
|----------|-------------|-----------------|-------------------|-----------------|
| Crecimiento poblacional | - | fact_demografia | Existente | INE Open Data BCN |
| Estructura de edad | - | fact_demografia_ampliada | Existente | Portal Dades |
| Composición hogares | fact_socioeconomic | - | HogaresExtractor | Portal Dades |
| Población extranjera | - | fact_demografia_ampliada | Existente | Portal Dades |
| Movilidad interna | fact_movilidad | - | MovilidadExtractor | Padrón Municipal |

### Categoría 2: Económicas (4 variables)

| Variable | Tabla Nueva | Tabla Existente | Extractor Necesario | Fuente Primaria |
|----------|-------------|-----------------|-------------------|-----------------|
| Renta disponible | - | fact_renta | IDESCATExtractor* | IDESCAT/INE |
| Tasa de desempleo | fact_socioeconomic | - | DesempleoExtractor | SEPE/Portal Dades |
| Salario medio | fact_socioeconomic | - | SalarioExtractor | INE EPA |
| Nivel educativo | fact_socioeconomic | - | EducacionExtractor | Portal Dades |

*Existente pero requiere ampliación histórica

### Categoría 3: Oferta y Demanda (4 variables)

| Variable | Tabla Nueva | Tabla Existente | Extractor Necesario | Fuente Primaria |
|----------|-------------|-----------------|-------------------|-----------------|
| Stock vivienda | fact_oferta | - | OfertaHistoricaExtractor | Portal Dades/Catastro |
| Nuevas construcciones | fact_construccion | - | VisadosExtractor | Colegio Arquitectos |
| Días en mercado | - | fact_oferta_idealista | IdealistaExtractor* | Idealista API |
| Ratio oferta/demanda | - | CALCULADO | - | Derived metric |

### Categoría 4: Ubicación (5 variables)

| Variable | Tabla Nueva | Tabla Existente | Extractor Necesario | Fuente Primaria |
|----------|-------------|-----------------|-------------------|-----------------|
| Distrito/Barrio | - | dim_barrios | Existente | Geografía |
| Proximidad centro | dim_barrios_metricas | - | CentralidadExtractor | Cálculo distancia |
| Accesibilidad transporte | dim_barrios_metricas | - | AccesibilidadExtractor | TMB/OSM |
| Densidad urbana | - | fact_demografia | Existente | Derivado |
| Proximidad servicios | dim_barrios_metricas | - | EquipamientosExtractor | Portal Dades |

### Categoría 5: Turismo (3 variables)

| Variable | Tabla Nueva | Tabla Existente | Extractor Necesario | Fuente Primaria |
|----------|-------------|-----------------|-------------------|-----------------|
| Viviendas turísticas | fact_turismo | - | HUTExtractor | Portal Dades/Ajuntament |
| Airbnb/alquileres cortos | fact_turismo | - | AirbnbExtractor | InsideAirbnb API |
| Presión turística | fact_turismo | - | TurismoExtractor | Ajuntament Barcelona |

### Categoría 6: Regulación (4 variables)

| Variable | Tabla Nueva | Tabla Existente | Extractor Necesario | Fuente Primaria |
|----------|-------------|-----------------|-------------------|-----------------|
| Control precios alquiler | fact_regulacion | - | ControlAlquilerExtractor | Generalitat/Portal Dades |
| Suelo protegido | fact_regulacion | - | SueloProtegidoExtractor | Planejament Urbà |
| Stock vivienda pública | fact_regulacion | - | ViviendaPublicaExtractor | INCASL/Ajuntament |
| Ley Vivienda 2023 | fact_regulacion | - | LeyViviedaExtractor | BOE/Generalitat |

### Categoría 7: Características (4 variables)

| Variable | Tabla Nueva | Tabla Existente | Extractor Necesario | Fuente Primaria |
|----------|-------------|-----------------|-------------------|-----------------|
| Superficie m² | - | fact_precios | Existente | Portal Dades |
| Eficiencia energética | fact_eficiencia | - | EficienciaEnergeticaExtractor | Catastro/Certificados |
| Estado conservación | fact_eficiencia | - | EstadoConservacionExtractor | Portal Dades |
| Antigüedad edificios | - | fact_demografia_ampliada | Existente | Catastro |

### Categoría 8: Financieras (2 variables)

| Variable | Tabla Nueva | Tabla Existente | Extractor Necesario | Fuente Primaria |
|----------|-------------|-----------------|-------------------|-----------------|
| Tipos de interés | fact_financiera | - | EuriborExtractor | BCE/Banco de España |
| Condiciones hipotecarias | fact_financiera | - | HipotecasExtractor | Banco de España |

---

## 3. Cambios al Esquema de Base de Datos {#esquema-propuesto}

### 3.1 Nuevas Tablas de Hechos (8)

```sql
-- 1. Tabla de Composición de Hogares
CREATE TABLE fact_hogares (
    id INTEGER PRIMARY KEY,
    barrioid INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    tamanio_hogar INTEGER,  -- 1, 2, 3, 4, 5+
    numero_hogares INTEGER,
    porcentaje_total REAL,
    datasetid TEXT,
    source TEXT,
    etlloadedat TEXT,
    FOREIGN KEY(barrioid) REFERENCES dimbarrios(barrioid),
    UNIQUE(barrioid, anio, tamanio_hogar, datasetid, source)
);

-- 2. Tabla de Desempleo y Economía
CREATE TABLE fact_socioeconomic (
    id INTEGER PRIMARY KEY,
    barrioid INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    tasa_desempleo REAL,  -- %
    numero_parados INTEGER,
    poblacion_activa INTEGER,
    salario_medio REAL,   -- €
    nivel_educativo TEXT, -- Primaria, Secundaria, Universitaria
    porcentaje_nivel REAL,
    datasetid TEXT,
    source TEXT,
    etlloadedat TEXT,
    FOREIGN KEY(barrioid) REFERENCES dimbarrios(barrioid),
    UNIQUE(barrioid, anio, COALESCE(nivel_educativo, ''), datasetid, source)
);

-- 3. Tabla de Oferta Histórica (visados, construcción)
CREATE TABLE fact_construccion (
    id INTEGER PRIMARY KEY,
    barrioid INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    visados_vivienda INTEGER,
    nuevas_viviendas INTEGER,
    rehabilitaciones INTEGER,
    cambios_uso INTEGER,
    datasetid TEXT,
    source TEXT,
    etlloadedat TEXT,
    FOREIGN KEY(barrioid) REFERENCES dimbarrios(barrioid),
    UNIQUE(barrioid, anio, datasetid, source)
);

-- 4. Tabla de Movilidad Poblacional
CREATE TABLE fact_movilidad (
    id INTEGER PRIMARY KEY,
    barrioid_origen INTEGER NOT NULL,
    barrioid_destino INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    numero_traslados INTEGER,
    razon_movimiento TEXT,  -- Laboral, Familia, Acceso vivienda
    datasetid TEXT,
    source TEXT,
    etlloadedat TEXT,
    FOREIGN KEY(barrioid_origen) REFERENCES dimbarrios(barrioid),
    FOREIGN KEY(barrioid_destino) REFERENCES dimbarrios(barrioid),
    UNIQUE(barrioid_origen, barrioid_destino, anio, datasetid, source)
);

-- 5. Tabla de Turismo y Vivienda Turística
CREATE TABLE fact_turismo (
    id INTEGER PRIMARY KEY,
    barrioid INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    mes INTEGER,
    huts_registradas INTEGER,
    airbnb_listadas INTEGER,
    airbnb_operativas INTEGER,
    plazas_totales INTEGER,
    ocupacion_media REAL,  -- % anual
    plazas_hoteleras INTEGER,
    turistas_anuales INTEGER,
    datasetid TEXT,
    source TEXT,
    etlloadedat TEXT,
    FOREIGN KEY(barrioid) REFERENCES dimbarrios(barrioid),
    UNIQUE(barrioid, anio, COALESCE(mes, 0), datasetid, source)
);

-- 6. Tabla de Regulación y Política Pública
CREATE TABLE fact_regulacion (
    id INTEGER PRIMARY KEY,
    barrioid INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    zona_tensionada BOOLEAN,  -- Control alquileres
    suelo_protegido_m2 REAL,
    stock_vivienda_pública INTEGER,
    viviendas_alquiler_social INTEGER,
    cobertura_vivienda_pública REAL,  -- % población
    impacto_ley_vivienda TEXT,  -- Descriptivo
    datasetid TEXT,
    source TEXT,
    etlloadedat TEXT,
    FOREIGN KEY(barrioid) REFERENCES dimbarrios(barrioid),
    UNIQUE(barrioid, anio, datasetid, source)
);

-- 7. Tabla de Eficiencia Energética
CREATE TABLE fact_eficiencia (
    id INTEGER PRIMARY KEY,
    barrioid INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    viviendas_certificadas INTEGER,
    viviendas_clase_a REAL,  -- %
    viviendas_clase_b REAL,
    viviendas_clase_c REAL,
    viviendas_clase_d REAL,
    viviendas_clase_e REAL,
    viviendas_clase_f REAL,
    viviendas_clase_g REAL,
    prima_energetica_ab REAL,  -- % premium A/B vs resto
    edad_promedio_edificios INTEGER,
    estado_conservacion_bueno REAL,  -- %
    datasetid TEXT,
    source TEXT,
    etlloadedat TEXT,
    FOREIGN KEY(barrioid) REFERENCES dimbarrios(barrioid),
    UNIQUE(barrioid, anio, datasetid, source)
);

-- 8. Tabla de Variables Financieras
CREATE TABLE fact_financiera (
    id INTEGER PRIMARY KEY,
    barrioid INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    mes INTEGER,
    euribor_12m REAL,  -- %
    tipos_hipotecarios REAL,
    ratio_ltv REAL,  -- Loan to Value promedio
    hipotecas_nuevas INTEGER,
    importe_medio_hipoteca REAL,  -- €
    datasetid TEXT,
    source TEXT,
    etlloadedat TEXT,
    FOREIGN KEY(barrioid) REFERENCES dimbarrios(barrioid),
    UNIQUE(barrioid, anio, COALESCE(mes, 0), datasetid, source)
);
```

### 3.2 Nuevas Tablas de Dimensión (2)

```sql
-- Dimensión: Métricas espaciales de barrios
CREATE TABLE dim_barrios_metricas (
    barrio_metrica_id INTEGER PRIMARY KEY,
    barrioid INTEGER NOT NULL UNIQUE,
    distancia_plaza_catalunya_km REAL,  -- km
    tiempo_metro_plaza_catalunya_min INTEGER,  -- minutos
    estaciones_metro INTEGER,
    estaciones_bus INTEGER,
    frecuencia_transporte_publico REAL,  -- minutos
    numero_equipamientos INTEGER,
    cobertura_servicios REAL,  -- % población a < 500m
    densidad_urbana REAL,  -- hab/km²
    superficie_zona_verde_m2 REAL,
    m2_zona_verde_per_capita REAL,
    indice_fragmentacion REAL,
    fecha_actualizacion TEXT,
    FOREIGN KEY(barrioid) REFERENCES dimbarrios(barrioid)
);

-- Dimensión: Indicadores ambientales
CREATE TABLE dim_barrios_ambiente (
    barrio_ambiente_id INTEGER PRIMARY KEY,
    barrioid INTEGER NOT NULL UNIQUE,
    indice_calidad_aire REAL,  -- ICA
    no2_medio_ug_m3 REAL,
    pm10_medio_ug_m3 REAL,
    pm25_medio_ug_m3 REAL,
    dias_aire_malo INTEGER,  -- por año
    nivel_ruido_diurno_db REAL,
    nivel_ruido_nocturno_db REAL,
    area_verde_m2 REAL,
    parques_jardines INTEGER,
    distancia_parque_medio_m REAL,
    contaminacion_lumnica REAL,
    fecha_actualizacion TEXT,
    FOREIGN KEY(barrioid) REFERENCES dimbarrios(barrioid)
);
```

### 3.3 Cambios a Tablas Existentes

```sql
-- Expandir fact_renta con datos históricos
ALTER TABLE fact_renta ADD COLUMN renta_percentil25 REAL;
ALTER TABLE fact_renta ADD COLUMN renta_percentil75 REAL;
ALTER TABLE fact_renta ADD COLUMN renta_per_capita_anual REAL;
ALTER TABLE fact_renta ADD COLUMN ratio_precio_renta REAL;  -- Derivado

-- Expandir fact_precios con métricas adicionales
ALTER TABLE fact_precios ADD COLUMN numero_transacciones INTEGER;
ALTER TABLE fact_precios ADD COLUMN porcentaje_extranjeros REAL;
ALTER TABLE fact_precios ADD COLUMN dias_medio_mercado INTEGER;
ALTER TABLE fact_precios ADD COLUMN ratio_oferta_venta REAL;

-- Expandir dimbarrios con información espacial
ALTER TABLE dimbarrios ADD COLUMN superficie_km2 REAL;
ALTER TABLE dimbarrios ADD COLUMN centroide_lon REAL;
ALTER TABLE dimbarrios ADD COLUMN centroide_lat REAL;
ALTER TABLE dimbarrios ADD COLUMN poligonos_vecinos TEXT;  -- JSON array
```

---

## 4. Arquitectura de Extractores ETL {#arquitectura-extractores}

### 4.1 Estructura de Módulo de Extractores

```python
# src/extraction/README.md

Estructura de extractores por categoría:

├── base.py                          # BaseExtractor clase padre
├── demographic/
│   ├── __init__.py
│   ├── hogares_extractor.py         # Composición de hogares
│   └── movilidad_extractor.py       # Flujos poblacionales
├── economic/
│   ├── __init__.py
│   ├── desempleo_extractor.py       # Tasas de paro SEPE
│   ├── salario_extractor.py         # Salarios EPA/INE
│   └── educacion_extractor.py       # Nivel educativo
├── supply/
│   ├── __init__.py
│   ├── visados_extractor.py         # Visados obra
│   └── stock_extractor.py           # Stock vivienda
├── location/
│   ├── __init__.py
│   ├── centralidad_extractor.py     # Distancia a centro
│   ├── accesibilidad_extractor.py   # Transporte público
│   └── equipamientos_extractor.py   # Servicios urbanos
├── tourism/
│   ├── __init__.py
│   ├── hut_extractor.py             # Viviendas turísticas
│   ├── airbnb_extractor.py          # Inside Airbnb data
│   └── turismo_extractor.py         # Turismo oficial
├── regulation/
│   ├── __init__.py
│   ├── control_alquiler_extractor.py # Zonas tensionadas
│   ├── vivienda_publica_extractor.py # Stock público
│   └── ley_vivienda_extractor.py     # Regulación
├── efficiency/
│   ├── __init__.py
│   ├── energetica_extractor.py       # Eficiencia EPC
│   └── conservacion_extractor.py     # Estado edificios
└── financial/
    ├── __init__.py
    ├── euribor_extractor.py          # BCE datos
    └── hipotecas_extractor.py        # Hipotecas BE
```

### 4.2 Extractores Prioritarios (Fase 1)

Orden de implementación recomendado (por impacto y disponibilidad de datos):

1. **DesempleoExtractor** (Semana 1) - Alto impacto, fuente clara
2. **EducacionExtractor** (Semana 1) - Alto impacto, datos Portal Dades
3. **HUTExtractor** (Semana 2) - Alto impacto, datos Ajuntament
4. **AirbnbExtractor** (Semana 2) - Alto impacto, API gratuita
5. **VisadosExtractor** (Semana 3) - Medio impacto, requiere web scraping
6. **ControlAlquilerExtractor** (Semana 3) - Medio impacto, validar regulación
7. **CentralidadExtractor** (Semana 4) - Bajo impacto, cálculo geoespacial
8. **AccesibilidadExtractor** (Semana 4) - Bajo impacto, datos TMB/OSM

---

## 5. Tablas Nuevas Propuestas {#tablas-nuevas}

### 5.1 Tabla: fact_socioeconomic

**Propósito:** Concentrar indicadores socioeconómicos clave (desempleo, salarios, educación)

**Cobertura temporal:** 2015-2025
**Granularidad:** Barrio × Año × Indicador
**Registros esperados:** ~2,000-3,000

**Campos críticos:**
- `tasa_desempleo`: Porcentaje de población activa en paro
- `numero_parados`: Absolutos para cálculos derivados
- `salario_medio`: Para ratio precio/salario
- `nivel_educativo`: Categorizado (Primaria/Sec/Univ)

**Extractor primario:** `DesempleoExtractor`, `SalarioExtractor`, `EducacionExtractor`

---

### 5.2 Tabla: fact_turismo

**Propósito:** Capturar dinámicas de vivienda turística y presión sobre residentes

**Cobertura temporal:** 2014-2025
**Granularidad:** Barrio × Año × Mes (opcional)
**Registros esperados:** ~3,000-4,000

**Campos críticos:**
- `huts_registradas`: Viviendas uso turístico oficiales
- `airbnb_listadas`: De InsideAirbnb
- `ocupacion_media`: Tasa de ocupación anual
- `turistas_anuales`: Volumen de visitantes

**Extractores primarios:** `HUTExtractor`, `AirbnbExtractor`, `TurismoExtractor`

---

### 5.3 Tabla: fact_regulacion

**Propósito:** Rastrear cambios regulatorios que afectan mercado

**Cobertura temporal:** 2015-2025
**Granularidad:** Barrio × Año
**Registros esperados:** ~500

**Campos críticos:**
- `zona_tensionada`: Boolean, control de alquileres
- `suelo_protegido_m2`: Reserva para vivienda protegida
- `stock_vivienda_pública`: Número de unidades públicas
- `impacto_ley_vivienda`: Texto descriptivo post-marzo 2024

**Extractores primarios:** `ControlAlquilerExtractor`, `ViviendaPublicaExtractor`, `LeyViviedaExtractor`

---

## 6. Plan de Implementación {#plan-implementacion}

### 6.1 Cronograma de 12 Semanas

**FASE 1: Infraestructura (Semanas 1-2)**
- [ ] Crear nuevas tablas en database.db
- [ ] Actualizar schema.sql
- [ ] Crear migraciones reversibles
- [ ] Validar integridad referencial

**FASE 2: Extractores Críticos (Semanas 3-6)**
- [ ] DesempleoExtractor (SEPE Open Data)
- [ ] EducacionExtractor (Portal Dades)
- [ ] HUTExtractor (Ajuntament API)
- [ ] AirbnbExtractor (InsideAirbnb)
- [ ] Pruebas unitarias para cada extractor

**FASE 3: Extractores Complementarios (Semanas 7-10)**
- [ ] VisadosExtractor (Scraping web)
- [ ] ControlAlquilerExtractor (Generalitat)
- [ ] CentralidadExtractor (GeoPandas)
- [ ] AccesibilidadExtractor (GTFS/OSM)
- [ ] EficienciaEnergeticaExtractor (Portal Dades)

**FASE 4: Integración y Validación (Semanas 11-12)**
- [ ] Integrar todos los extractores en pipeline ETL
- [ ] Validación de calidad multivariante
- [ ] Pruebas de rendimiento
- [ ] Documentación completada
- [ ] Dashboard actualizado con nuevas métricas

### 6.2 Estimación de Esfuerzo

| Componente | Horas | Recurso | Complejidad |
|-----------|-------|---------|-------------|
| Nuevas tablas DB | 8 | DBA/Dev | Baja |
| 8 Extractores | 320 | Dev x4 | Media-Alta |
| Procesamiento ETL | 40 | Dev | Media |
| Validación calidad | 24 | QA | Media |
| Documentación | 20 | Tech Writer | Baja |
| **Total** | **412h** | - | - |

**Calendario:** 4 desarrolladores × 12 semanas = 1,920h disponibles → **Estimado: 3 meses a tiempo parcial**

---

## 7. Detalle de Extractores por Variable {#detalle-extractores}

### 7.1 DESEMPLEADOR EXTRACTOR

**Fuente:** SEPE (Servicio Público de Empleo Estatal)  
**API:** https://www.sepe.es/HomeSepe/que-es-el-sepe/estadisticas  
**Datos:** Paro registrado por territorio, mensual

```python
# src/extraction/economic/desempleo_extractor.py

from src.extraction.base import BaseExtractor
import pandas as pd
import requests

class DesempleoExtractor(BaseExtractor):
    """
    Extrae tasas de desempleo registrado desde SEPE.
    
    Cobertura: 2008-2025 (mensual)
    Granularidad: Barrio/Distrito (requiere mapeo)
    Métrica: Número de parados, tasa %
    """
    
    SOURCE = 'sepe'
    RATE_LIMIT_DELAY = 1.0  # segundos entre peticiones
    
    def extract_unemployment_by_territory(self, year_start: int, year_end: int):
        """
        Descarga datos de paro registrado por territorio y mes.
        
        Args:
            year_start: Año inicial (2008+)
            year_end: Año final (actual)
        
        Returns:
            Tupla[pd.DataFrame, Dict]: DataFrame con desempleo y metadatos
        """
        
        data_frames = []
        
        for year in range(year_start, year_end + 1):
            try:
                # SEPE publica datos agregados a nivel provincial/municipal
                # Requiere scraping o acceso a API interna
                
                url = f"https://www.sepe.es/api/estadisticas/paro/{year}"
                
                response = self._make_request(
                    url=url,
                    method='GET',
                    headers={'User-Agent': 'BarcelonaHousingAnalyzer/2.0'}
                )
                
                df = pd.read_json(response)
                
                # Normalizar nombres de campos
                df = df.rename(columns={
                    'territorio': 'territorio_original',
                    'parados': 'numero_parados',
                    'tasa': 'tasa_desempleo'
                })
                
                # Mapear territorios a barrioid
                df = self._map_territories_to_barrios(df, 'territorio_original')
                
                # Filtrar solo Barcelona
                df = df[df['barrioid'].notna()]
                
                data_frames.append(df)
                
                self.logger.info(f"Descargados {len(df)} registros desempleo {year}")
                
            except Exception as e:
                self.logger.error(f"Error extrayendo {year}: {str(e)}")
                continue
        
        if not data_frames:
            return None, {'success': False, 'error': 'No data extracted'}
        
        df_combined = pd.concat(data_frames, ignore_index=True)
        
        # Guardar raw data
        self.save_raw_data(df_combined, 'sepe_desempleo_raw.csv')
        
        return df_combined, {
            'source': self.SOURCE,
            'years_extracted': list(range(year_start, year_end + 1)),
            'total_records': len(df_combined),
            'barrios_covered': df_combined['barrioid'].nunique(),
            'success': True
        }
    
    def _map_territories_to_barrios(self, df: pd.DataFrame, territory_col: str) -> pd.DataFrame:
        """Mapea territorios SEPE a barrios de Barcelona."""
        # Implementar mapeo de territorios provinciales a barrios
        # Requiere tabla de referencia: territorio -> barrioid
        pass
```

### 7.2 EDUCACIÓN EXTRACTOR

**Fuente:** Open Data BCN  
**Dataset:** `nivell-destudis` (Nivel educativo por barrio)  
**API:** CKAN API

```python
# src/extraction/economic/educacion_extractor.py

from src.extraction.base import BaseExtractor
from src.extraction.opendatabcn import OpenDataBCNExtractor

class EducacionExtractor(OpenDataBCNExtractor):
    """
    Extrae nivel educativo de población desde Open Data BCN.
    
    Cobertura: 2015-2025 (anual)
    Granularidad: Barrio
    Categorías: Sin estudios, Primaria, ESO, Bachillerato, FP, Universidad
    """
    
    DATASET_ID = 'hd7u1b68qj'  # Cambiar por ID real
    SOURCE = 'open_data_bcn'
    
    def extract_education_level(self, year_start: int = 2015, year_end: int = 2025):
        """
        Descarga distribución de nivel educativo por barrio.
        
        Returns:
            Tupla[pd.DataFrame, Dict]
        """
        
        df = self._query_dataset(
            dataset_id=self.DATASET_ID,
            year_range=(year_start, year_end),
            filters={'territorio_type': 'barrio'}
        )
        
        # Normalizar columnas
        df = df.rename(columns={
            'codi_barri': 'barrioid',
            'nom_barri': 'barrio_nombre',
            'nivell_educatiu': 'nivel_educativo',
            'nombre_habitants': 'poblacion'
        })
        
        # Categorizar nivel educativo
        df['nivel_educativo'] = df['nivel_educativo'].map({
            'Sense estudis': 'Sin_estudios',
            'Primària': 'Primaria',
            'ESO': 'ESO',
            'Batxillerat': 'Bachillerato',
            'FP': 'Formacion_profesional',
            'Universitat': 'Universitario'
        })
        
        # Calcular porcentajes
        df['porcentaje'] = df.groupby(['barrioid', 'anio'])['poblacion'].transform(
            lambda x: (x / x.sum()) * 100
        )
        
        self.save_raw_data(df, 'educacion_raw.csv')
        
        return df, {
            'source': self.SOURCE,
            'years': list(range(year_start, year_end + 1)),
            'records': len(df),
            'levels': df['nivel_educativo'].unique().tolist()
        }
```

### 7.3 HUT EXTRACTOR

**Fuente:** Portal Dades / Ajuntament Barcelona  
**Dataset:** `habitatges-us-turistic` (Viviendas de uso turístico)  
**Actualización:** Semanal/Mensual

```python
# src/extraction/tourism/hut_extractor.py

from src.extraction.base import BaseExtractor
import pandas as pd
import geopandas as gpd

class HUTExtractor(BaseExtractor):
    """
    Extrae registro de Habitatges d'ús Turístic (HUT).
    
    Cobertura: 2016-2025 (actualización cuasicontinua)
    Granularidad: Punto geográfico (necesita agregación a barrio)
    Métrica: Número de HUTs registradas, estado, antigüedad
    """
    
    SOURCE = 'ajuntament_barcelona'
    API_BASE = 'https://portaldades.ajuntament.barcelona.cat'
    
    def extract_huts_by_neighborhood(self, date_as_of: str = None):
        """
        Obtiene HUTs agregadas por barrio.
        
        Args:
            date_as_of: Fecha snapshot (YYYY-MM-DD) o None para última disponible
        
        Returns:
            Tupla[pd.DataFrame, Dict]
        """
        
        # Obtener geometrías de barrios para agregación espacial
        barrios_geo = self._load_barrio_geometries()
        
        # Descarga puntos HUT con coordenadas
        huts_points = self._query_hut_points(date_as_of)
        
        # Convertir a GeoDataFrame
        gdf_huts = gpd.GeoDataFrame(
            huts_points,
            geometry=gpd.points_from_xy(huts_points.lon, huts_points.lat)
        )
        
        # Aggregate by barrio using spatial join
        huts_by_barrio = gpd.sjoin(
            gdf_huts,
            barrios_geo,
            how='left',
            predicate='within'
        )
        
        # Agrupación
        df_huts = huts_by_barrio.groupby(['barrioid', 'anio']).agg({
            'hut_id': 'count',  # Total HUTs
            'estado_registro': lambda x: (x == 'Activa').sum(),  # Operativas
            'fecha_alta': 'min',  # Más antigua
            'plazas': 'sum'
        }).reset_index()
        
        df_huts.columns = ['barrioid', 'anio', 'huts_registradas', 
                          'huts_operativas', 'fecha_mas_antigua', 'plazas_totales']
        
        self.save_raw_data(df_huts, 'hut_raw.csv')
        
        return df_huts, {
            'source': self.SOURCE,
            'date_snapshot': date_as_of,
            'total_huts_barcelona': len(gdf_huts),
            'barrios_with_huts': df_huts[df_huts['huts_registradas'] > 0].shape[0],
            'success': True
        }
```

### 7.4 AIRBNB EXTRACTOR

**Fuente:** Inside Airbnb API (datos públicos)  
**URL:** http://insideairbnb.com/  
**Datos:** Listados activos, ocupación, reviews

```python
# src/extraction/tourism/airbnb_extractor.py

from src.extraction.base import BaseExtractor
import pandas as pd
import geopandas as gpd

class AirbnbExtractor(BaseExtractor):
    """
    Extrae datos de Airbnb desde Inside Airbnb.
    
    Cobertura: 2015-2025 (snapshots mensuales/trimestrales)
    Granularidad: Listado individual -> agregación a barrio
    Métricas: Número listados, ocupación, precio
    """
    
    SOURCE = 'inside_airbnb'
    API_BASE = 'http://insideairbnb.com/get-data'
    
    def extract_airbnb_snapshot(self, year: int, month: int):
        """
        Descarga snapshot Airbnb para Barcelona en fecha específica.
        
        Args:
            year: Año (2015+)
            month: Mes (1-12)
        
        Returns:
            Tupla[pd.DataFrame, Dict]
        """
        
        # Construir URL del snapshot
        url = f"{self.API_BASE}/Barcelona/listings/{year}-{month:02d}/data/listings.csv.gz"
        
        try:
            # Descargar y decomprimir
            df_listings = pd.read_csv(url, compression='gzip')
            
            # Geometry spatial join
            barrios_geo = self._load_barrio_geometries()
            gdf_listings = gpd.GeoDataFrame(
                df_listings,
                geometry=gpd.points_from_xy(df_listings.longitude, df_listings.latitude)
            )
            
            # Spatial join a barrios
            gdf_listings = gpd.sjoin(gdf_listings, barrios_geo, how='left')
            
            # Aggregate to barrio level
            df_agg = gdf_listings.groupby('barrioid').agg({
                'id': 'count',  # Total listados
                'has_availability': lambda x: (x).sum(),  # Disponibles
                'availability_365': 'mean',  # Ocupación media
                'price': 'median',  # Precio mediano
                'reviews_per_month': 'mean'
            }).reset_index()
            
            df_agg.columns = [
                'barrioid', 'airbnb_listadas', 'airbnb_disponibles',
                'ocupacion_media_pct', 'precio_mediano', 'reviews_por_mes'
            ]
            
            df_agg['anio'] = year
            df_agg['mes'] = month
            
            self.save_raw_data(df_agg, f'airbnb_{year}_{month:02d}_raw.csv')
            
            return df_agg, {
                'source': self.SOURCE,
                'snapshot_date': f"{year}-{month:02d}",
                'total_listings': len(df_listings),
                'barrios_covered': df_agg['barrioid'].nunique(),
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Error descargando Airbnb {year}-{month}: {str(e)}")
            return None, {'success': False, 'error': str(e)}
```

---

## Referencias de Implementación

Cada extractor debe heredar de `BaseExtractor` y seguir el patrón:

1. **Inicialización:** Configurar rate limiting, autenticación
2. **Extracción:** Descargar desde fuente (API/CSV/Web)
3. **Transformación:** Normalizar columnas, mapear territorios
4. **Validación:** Verificar completitud, rangos, consistencia
5. **Almacenamiento:** Guardar raw + metadatos en data/raw
6. **Retorno:** Tupla (DataFrame, metadatos)

---

## Próximos Pasos

1. **Semana 1:** Crear tablas en database.db
2. **Semana 2:** Implementar DesempleoExtractor + EducacionExtractor
3. **Semana 3:** Implementar HUTExtractor + AirbnbExtractor
4. **Semana 4-6:** Extractores complementarios
5. **Semana 7-12:** Integración, validación, documentación

**Inversión Total:** ~412 horas / ~3 meses a tiempo parcial (4 devs)
**ROI:** +33 variables capturadas, +250% capacidad analítica

