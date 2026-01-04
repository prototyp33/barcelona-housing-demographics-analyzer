# Fuentes de Datos - Vivienda Pública Barcelona

## Resumen

Este documento cataloga las fuentes de datos oficiales para indicadores de vivienda pública en Barcelona y Cataluña, organizadas por categoría y prioridad de integración.

---

## 📊 Categorías de Datos

### 1. DEMOGRAFÍA Y HOGARES

#### 1.1 Población por edad y sexo

- **Fuente**: IDESCAT
- **URL**: https://www.idescat.cat/pub/?id=pmh&n=1180&lang=es
- **Cobertura**: Barcelona, Cataluña
- **Formato**: Web/Descargable
- **Prioridad**: 🔴 Alta (ya integrado parcialmente)

#### 1.2 Población por lugar de nacimiento

- **Fuente**: IDESCAT
- **URL**: https://www.idescat.cat/pub/?id=pmh&n=674
- **Formato**: Web/Descargable
- **Prioridad**: 🟡 Media

#### 1.3 Hogares por tipos de núcleo

- **Fuente**: IDESCAT - Censo
- **URL**: https://www.idescat.cat/pub/?id=censph&n=300&t=200100
- **Formato**: Web/API
- **Prioridad**: 🟢 Baja

#### 1.4 Hogares por tamaño medio

- **Fuente**: IDESCAT - Censo
- **URL**: https://www.idescat.cat/pub/?id=censph&n=450
- **Formato**: Web/API
- **Prioridad**: 🟡 Media

---

### 2. RÉGIMEN DE TENENCIA Y MOVILIDAD

#### 2.1 Hogares por régimen de tenencia

- **Fuente**: Observatori Habitatge Barcelona (OHB)
- **URLs**:
  - Power BI: https://app.powerbi.com/view?r=eyJrIjoiZmQ3ZTRlOTYtNTI0NS00N2QzLWJkOTktOTAwY2MwNjQ3ZmUyIiwidCI6IjQ5NzQzMTcyLTY4ZTgtNGI5Yy1iNTdlLWU5ZTAzMTY4NzYxZCIsImMiOjl9
  - Excel: https://www.ohb.cat/wp-content/uploads/2023/04/1020_Llars_tinenca.xlsx
- **Cobertura**: AMB, Barcelona
- **Prioridad**: 🔴 Alta (crítico para análisis de tenencia)

#### 2.2 Tasa de autocontención residencial

- **Fuente**: OHB
- **URLs**:
  - Power BI: https://app.powerbi.com/view?r=eyJrIjoiMDU5NTc4NjEtNjNiOC00ZGYzLWJlNzYtNmZkN2ZmNTg0OWFiIiwidCI6IjQ5NzQzMTcyLTY4ZTgtNGI5Yy1iNTdlLWU5ZTAzMTY4NzYxZCIsImMiOjl9
  - Excel: https://www.ohb.cat/wp-content/uploads/2023/04/1010_Taxa_autocontencio.xlsx
- **Prioridad**: 🟡 Media

#### 2.3 Tasa de emancipación domiciliar

- **Fuente**: Generalitat - Observatori Joventut
- **URL**: https://dretssocials.gencat.cat/ca/ambits_tematics/joventut/observatori_catala_de_la_joventut/estadistiques/sistema_d_indicadors_sobre_la_joventut_a_catalunya/
- **Prioridad**: 🟡 Media

---

### 3. STOCK DE VIVIENDAS

#### 3.1 Viviendas principales y no principales

- **Fuente**: IDESCAT - Censo
- **URL**: https://www.idescat.cat/pub/?id=censph&n=30&t=202100
- **Prioridad**: 🔴 Alta

#### 3.2 Viviendas por tamaño del propietario

- **Fuente**: OHB
- **URLs**:
  - Power BI: https://app.powerbi.com/view?r=eyJrIjoiY2ZiNTUyODMtN2RjMy00ZmYzLWI5Y2EtYWU4YzhkMDFmYTM5IiwidCI6IjQ5NzQzMTcyLTY4ZTgtNGI5Yy1iNTdlLWU5ZTAzMTY4NzYxZCIsImMiOjl9
  - Excel: https://www.ohb.cat/wp-content/uploads/2023/04/2010_Habitatges_grandaria_propietari2-1.xlsx
- **Cobertura**: Barcelona
- **Prioridad**: 🔴 Alta (concentración de propiedad)

#### 3.3 Viviendas por tipo de propietario

- **Fuente**: OHB
- **URLs**:
  - Power BI: https://app.powerbi.com/view?r=eyJrIjoiOTM2MTI3NGMtYWE1Zi00YzVkLTlmMDQtZWVmZTFjYTIwZTk4IiwidCI6IjQ5NzQzMTcyLTY4ZTgtNGI5Yy1iNTdlLWU5ZTAzMTY4NzYxZCIsImMiOjl9
  - Excel: https://www.ohb.cat/wp-content/uploads/2023/04/2020_Habitatges_tipus_propietari2.xlsx
- **Cobertura**: Barcelona
- **Prioridad**: 🔴 Alta

#### 3.4 Edificios residenciales

- **Fuente**: OHB
- **URLs**:
  - Power BI: https://app.powerbi.com/view?r=eyJrIjoiZDIzNDUwZTMtOTgyNi00NTU1LWE3NDQtYTY5Zjc0MzNkNmE5IiwidCI6IjQ5NzQzMTcyLTY4ZTgtNGI5Yy1iNTdlLWU5ZTAzMTY4NzYxZCIsImMiOjl9
  - Excel: https://www.ohb.cat/wp-content/uploads/2024/11/2030_Edificis_residencials2.xlsx
- **Cobertura**: Barcelona
- **Prioridad**: 🟡 Media

---

### 4. MERCADO DE ALQUILER

#### 4.1 Viviendas de alquiler por tamaño del propietario

- **Fuente**: OHB
- **URLs**:
  - Power BI: https://app.powerbi.com/view?r=eyJrIjoiN2EyYjI3YTgtZTQ0Yi00NGViLTllZWEtMTQ2ZjM0ZjBmYjY0IiwidCI6IjQ5NzQzMTcyLTY4ZTgtNGI5Yy1iNTdlLWU5ZTAzMTY4NzYxZCIsImMiOjl9
  - Excel: https://www.ohb.cat/wp-content/uploads/2023/04/2050_Habitatges_lloguer_grandaria_propietari2.xlsx
- **Cobertura**: Demarcación BCN, AMB, Barcelona
- **Prioridad**: 🔴 Alta (concentración en alquiler)

#### 4.2 Viviendas de alquiler por tipo de propietario

- **Fuente**: OHB
- **URLs**:
  - Power BI: https://app.powerbi.com/view?r=eyJrIjoiMDk4YjkxMWItNzI5Yi00ODgwLTllMWQtMzlkM2E0YWFmNzExIiwidCI6IjQ5NzQzMTcyLTY4ZTgtNGI5Yy1iNTdlLWU5ZTAzMTY4NzYxZCIsImMiOjl9
  - Excel: https://www.ohb.cat/wp-content/uploads/2023/04/2060_Habitatges_lloguer_tipus_propietari2.xlsx
- **Cobertura**: Demarcación BCN, AMB, Barcelona
- **Prioridad**: 🔴 Alta

---

### 5. CONSTRUCCIÓN Y OBRA NUEVA

#### 5.1 Viviendas iniciadas (obra nueva)

- **Fuente**: Generalitat - Departament d'Habitatge
- **URL**: https://habitatge.gencat.cat/ca/dades/indicadors_estadistiques/estadistiques_de_construccio_i_mercat_immobiliari/construccio_dhabitatges/
- **Prioridad**: 🟡 Media

#### 5.2 Viviendas terminadas (obra nueva)

- **Fuente**: Generalitat - Departament d'Habitatge
- **URL**: https://habitatge.gencat.cat/ca/dades/indicadors_estadistiques/estadistiques_de_construccio_i_mercat_immobiliari/construccio_dhabitatges/
- **Prioridad**: 🟡 Media

#### 5.3 Licencias de obra menor y mayor (Barcelona)

- **Fuente**: Open Data BCN
- **URL**: https://portaldades.ajuntament.barcelona.cat/ca/estad%C3%ADstiques/mp0mv7kctn
- **Prioridad**: 🟡 Media

#### 5.4 Viviendas de reforma en licencias de obra mayor (Barcelona)

- **Fuente**: Open Data BCN
- **URL**: https://portaldades.ajuntament.barcelona.cat/ca/estad%C3%ADstiques/nf138kwjii
- **Prioridad**: 🟢 Baja

---

### 6. VIVIENDA PROTEGIDA (VPO)

#### 6.1 Demanda de vivienda protegida

- **Fuente**: Generalitat - Departament d'Habitatge
- **URL**: https://habitatge.gencat.cat/ca/dades/indicadors_estadistiques/estadistiques-de-la-politica-dhabitatge-/demanda-dhabitatge-protegit/
- **Prioridad**: 🔴 Alta

#### 6.2 VPO iniciados

- **Fuente**: Generalitat - Departament d'Habitatge
- **URL**: https://habitatge.gencat.cat/ca/dades/indicadors_estadistiques/estadistiques-de-la-politica-dhabitatge-/construccio-dhabitatges-amb-proteccio-oficial-/
- **Prioridad**: 🔴 Alta

#### 6.3 VPO acabados

- **Fuente**: Generalitat - Departament d'Habitatge
- **URL**: https://habitatge.gencat.cat/ca/dades/indicadors_estadistiques/estadistiques-de-la-politica-dhabitatge-/construccio-dhabitatges-amb-proteccio-oficial-/
- **Prioridad**: 🔴 Alta

#### 6.4 Viviendas protegidas con protección vigente

- **Fuente**: Generalitat - Departament d'Habitatge
- **URL**: https://habitatge.gencat.cat/ca/dades/indicadors_estadistiques/estadistiques-de-la-politica-dhabitatge-/habitatges-proteccio-vigent/
- **Prioridad**: 🔴 Alta

---

### 7. ALQUILER SOCIAL Y VIVIENDA VACÍA

#### 7.1 Viviendas alquiladas por bolsas de alquiler social

- **Fuente**: Generalitat - Departament d'Habitatge
- **URL**: https://habitatge.gencat.cat/ca/dades/indicadors_estadistiques/estadistiques-de-la-politica-dhabitatge-/habitatge-de-lloguer-amb-mediacio-social/
- **Prioridad**: 🔴 Alta

#### 7.2 Registro de viviendas vacías y ocupadas sin título

- **Fuente**: Generalitat - Departament d'Habitatge
- **URL**: https://habitatge.gencat.cat/ca/dades/indicadors_estadistiques/estadistiques-de-la-politica-dhabitatge-/Registre-dhabitatges-buits-sense-titol-habilitant/
- **Prioridad**: 🔴 Alta (crítico para políticas públicas)

---

### 8. AYUDAS Y PRESTACIONES

#### 8.1 Ayudas al pago del alquiler

- **Fuente**: Generalitat - Departament d'Habitatge
- **URL**: https://habitatge.gencat.cat/ca/dades/indicadors_estadistiques/estadistiques-de-la-politica-dhabitatge-/ajuts-al-pagament-de-lhabitatge/Ajuts-al-lloguer/
- **Prioridad**: 🟡 Media

#### 8.2 Prestaciones de especial urgencia

- **Fuente**: Generalitat - Departament d'Habitatge
- **URL**: https://habitatge.gencat.cat/ca/dades/indicadors_estadistiques/estadistiques-de-la-politica-dhabitatge-/ajuts-al-pagament-de-lhabitatge/prestacions-despecial-urgencia/
- **Prioridad**: 🟡 Media

---

## 🎯 Plan de Integración Recomendado

### Fase 1: Datos Críticos (Prioridad Alta 🔴)

1. **Régimen de tenencia** (OHB Excel)
2. **Tamaño y tipo de propietario** (OHB Excel)
3. **Viviendas de alquiler por propietario** (OHB Excel)
4. **Stock de viviendas** (IDESCAT)
5. **VPO (demanda, iniciados, acabados, vigentes)** (Generalitat)
6. **Vivienda vacía** (Generalitat)
7. **Alquiler social** (Generalitat)

### Fase 2: Datos Complementarios (Prioridad Media 🟡)

1. Hogares por tamaño
2. Tasa de autocontención
3. Tasa de emancipación
4. Construcción (iniciadas/terminadas)
5. Licencias de obra
6. Ayudas al alquiler

### Fase 3: Datos de Contexto (Prioridad Baja 🟢)

1. Población por lugar de nacimiento
2. Hogares por tipos de núcleo
3. Edificios residenciales
4. Viviendas de reforma

---

## 💾 Estructura de Datos Propuesta

### Nueva Tabla: `fact_vivienda_publica`

```sql
CREATE TABLE fact_vivienda_publica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,

    -- Régimen de tenencia
    hogares_propiedad INTEGER,
    hogares_alquiler INTEGER,
    hogares_cesion INTEGER,

    -- Concentración de propiedad
    viviendas_gran_tenedor INTEGER,
    viviendas_pequeno_propietario INTEGER,
    viviendas_persona_fisica INTEGER,
    viviendas_persona_juridica INTEGER,

    -- VPO
    vpo_demanda INTEGER,
    vpo_iniciados INTEGER,
    vpo_acabados INTEGER,
    vpo_proteccion_vigente INTEGER,

    -- Alquiler social
    viviendas_alquiler_social INTEGER,
    viviendas_vacias_registradas INTEGER,

    -- Ayudas
    ayudas_alquiler_concedidas INTEGER,
    prestaciones_urgencia INTEGER,

    -- Metadatos
    source TEXT,
    etl_loaded_at TEXT,

    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id),
    UNIQUE(barrio_id, anio)
);
```

---

## 🔧 Estrategia de Extracción

### Archivos Excel (OHB)

- **Método**: Descarga directa + pandas
- **Frecuencia**: Trimestral
- **Complejidad**: Baja

### IDESCAT

- **Método**: API REST (requiere corrección de endpoints)
- **Frecuencia**: Anual
- **Complejidad**: Media

### Generalitat (habitatge.gencat.cat)

- **Método**: Web scraping + descarga de archivos
- **Frecuencia**: Trimestral/Anual
- **Complejidad**: Media-Alta

### Open Data BCN

- **Método**: API CKAN (ya implementado)
- **Frecuencia**: Mensual
- **Complejidad**: Baja

---

## 📝 Próximos Pasos

1. **Crear extractor para archivos Excel de OHB**

   ```bash
   python -m src.extraction.ohb_extractor --year 2024
   ```

2. **Corregir endpoints IDESCAT**

   - Actualizar `ViviendaPublicaExtractor`
   - Añadir operación correcta (`dades` o `nodes`)

3. **Implementar scraper para Generalitat**

   - Crear `GeneralitatHabitatgeExtractor`
   - Manejar diferentes formatos de descarga

4. **Actualizar schema de base de datos**

   ```bash
   python src/database_setup.py --add-vivienda-publica
   ```

5. **Crear vista agregada**
   ```sql
   CREATE VIEW v_vivienda_publica_summary AS ...
   ```

---

## 📚 Referencias

- **OHB**: https://www.ohb.cat/
- **IDESCAT**: https://www.idescat.cat/
- **Generalitat Habitatge**: https://habitatge.gencat.cat/
- **Open Data BCN**: https://opendata-ajuntament.barcelona.cat/

---

**Última actualización**: 2026-01-04  
**Mantenedor**: Barcelona Housing Demographics Analyzer Team
