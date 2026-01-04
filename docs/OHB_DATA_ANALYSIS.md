# Análisis de Fuentes OHB - Resultados de Inspección

## Fecha: 2026-01-04

### Dataset: Régimen de Tenencia (1020_Llars_tinenca.xlsx)

#### Estructura del Archivo

- **Formato**: Excel (.xlsx)
- **Hojas**: 7 hojas (Notes, 16-34 anys, 35-44 anys, 45-54 anys, 55-64 anys, 65 anys i més, Total)
- **Nivel de agregación**: **Metropolitano** (Barcelona ciudad, AMB sin Barcelona, AMB total)
- **⚠️ NO tiene datos por barrio**

#### Columnas (Hoja "Total")

1. `Codi_àmbit` - Código del ámbito (080193 = Barcelona)
2. `Àmbit` - Nombre del ámbito (Barcelona, AMB, AMB sense Barcelona)
3. `Any` - Año (formato: "2016/2017", "2017/2018", etc.)
4. `Propietat totalment pagada(%)` - Propiedad totalmente pagada
5. `Propietat amb pagament pendents(%)` - Propiedad con pagos pendientes
6. `Subtotal propietat(%)` - Total propiedad
7. `Lloguer a preu de mercat(%)` - Alquiler a precio de mercado
8. `Lloguer inferior a preu de mercat(%)` - Alquiler inferior a precio de mercado
9. `Subtotal lloguer(%)` - Total alquiler
10. `Cessió gratuïta(%)` - Cesión gratuita

#### Cobertura Temporal

- **Años disponibles**: 2016/2017 a 2022/2023 (7 años)
- **Última actualización**: 2022/2023

#### Datos de Ejemplo (Barcelona 2022/2023)

```
Propiedad total: ~60%
  - Totalmente pagada: ~40%
  - Con pagos pendientes: ~20%
Alquiler total: ~35%
  - Precio de mercado: ~29%
  - Inferior a mercado: ~6%
Cesión gratuita: ~4%
```

---

## ⚠️ Hallazgo Importante

**Los archivos Excel de OHB contienen datos agregados a nivel metropolitano/ciudad, NO por barrio.**

### Implicaciones

1. **No podemos usar estos datos para `fact_vivienda_publica` por barrio**
2. **Sí podemos usarlos para**:

   - Contexto metropolitano en el dashboard
   - Comparación Barcelona vs AMB
   - Tendencias temporales de tenencia
   - KPIs globales de la ciudad

3. **Para datos por barrio necesitamos**:
   - Portal de Dades BCN (si tienen datasets de tenencia)
   - IDESCAT con desagregación por barrio
   - Censo de vivienda (cada 10 años)

---

## Próximos Pasos Recomendados

### 1. Verificar Portal de Dades BCN

Buscar datasets de:

- Régimen de tenencia por barrio
- Vivienda vacía por barrio
- VPO por barrio

### 2. Explorar IDESCAT API

- Corregir endpoints para obtener datos por barrio
- Verificar disponibilidad de indicadores de vivienda

### 3. Usar datos OHB para contexto

- Crear tabla `fact_vivienda_contexto_metropolitano`
- Mostrar en dashboard como "Contexto Barcelona"
- Comparar barrios vs ciudad

### 4. Priorizar fuentes con granularidad de barrio

- Censo de vivienda (IDESCAT)
- Open Data BCN
- Registros administrativos municipales

---

## Estructura Propuesta Revisada

### Tabla: `fact_vivienda_contexto_metropolitano`

```sql
CREATE TABLE fact_vivienda_contexto_metropolitano (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ambito TEXT NOT NULL,  -- 'Barcelona', 'AMB', 'AMB sense Barcelona'
    anio_inicio INTEGER NOT NULL,
    anio_fin INTEGER NOT NULL,

    -- Régimen de tenencia (%)
    propiedad_total REAL,
    propiedad_pagada REAL,
    propiedad_pendiente REAL,
    alquiler_total REAL,
    alquiler_mercado REAL,
    alquiler_social REAL,
    cesion_gratuita REAL,

    -- Metadatos
    source TEXT,
    etl_loaded_at TEXT,

    UNIQUE(ambito, anio_inicio, anio_fin)
);
```

### Vista para Dashboard

```sql
CREATE VIEW v_contexto_barcelona AS
SELECT
    anio_inicio,
    anio_fin,
    propiedad_total,
    alquiler_total,
    alquiler_social,
    cesion_gratuita
FROM fact_vivienda_contexto_metropolitano
WHERE ambito = 'Barcelona'
ORDER BY anio_inicio DESC;
```

---

## Conclusión

Los datos de OHB son valiosos pero **no tienen la granularidad necesaria** para análisis por barrio. Debemos:

1. ✅ Integrar datos OHB como **contexto metropolitano**
2. 🔍 Buscar fuentes alternativas para **datos por barrio**
3. 📊 Combinar ambos niveles en el dashboard

---

**Actualizado**: 2026-01-04  
**Analista**: Barcelona Housing Demographics Analyzer Team
