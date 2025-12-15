## 🎯 Feature del Roadmap

**Feature ID:** `F-217`  
**Sprint Asignado:** `Sprint: Phase 2.1 - Week 4 (Jan 6-9, 2026)`  
**Esfuerzo Estimado:** `6 horas`

### Dependencias

- Depende de: #216 (Research data sources) - **HARD BLOCKER**
- Bloquea: futuros extractors para `fact_educacion` / `fact_calidad_ambiental`
- Relacionada: #218 (Bayesian Networks - consumirá estas tablas)

---

## 📝 Descripción y Valor de Negocio

### Problema que Resuelve

Actualmente `database.db` solo contiene unas pocas tablas fact (demografía, precios, renta, demografía ampliada). Añadir nuevas tablas directamente en producción **sin prototipo validado** implica riesgos:

- **Schema incorrecto:** constraints faltantes → datos corruptos
- **Breaking changes:** cambios de schema después de cargar datos
- **Rollback complejo:** SQLite no soporta `DROP COLUMN` fácilmente

### Valor de Negocio

- **Mitigación de riesgo:** Validar schema en sandbox antes de producción
- **Iteración rápida:** Probar constraints FK/UNIQUE sin afectar ETL
- **Documentación viva:** El script SQL actúa como especificación técnica
- **Onboarding:** Nuevos devs entienden mejor la estructura de datos
- **Compliance:** Prepara el terreno para auditorías (p.ej. GDPR)

### Impacto Esperado

- Reducir bugs de integridad referencial en ~90%
- Acelerar desarrollo de extractors (schema ya definido)
- Habilitar análisis avanzados (#218) con datos validados

---

## 🔧 Componentes Técnicos

### Archivos a Crear

```text
scripts/schema/
├── phase2_experimental_tables.sql      # Script DDL principal
├── test_constraints.sql                # Tests de integridad
└── seed_test_data.sql                  # 10 filas mock por tabla

data/processed/
└── database_experimental.db            # SQLite experimental (NO commitear)

docs/database/
└── EXPERIMENTAL_SCHEMA_DESIGN.md       # Decisiones de diseño
```

### Tablas a Diseñar

**1. `fact_educacion`**

- Granularidad: `(barrio_id, anio, source)` → UNIQUE
- Campos: niveles educativos (sin estudios → doctorado)
- Métricas clave: `universitarios_pct` (proxy gentrificación)
- FK: `barrio_id → dim_barrios.barrio_id`

**2. `fact_calidad_ambiental`**

- Granularidad: `(barrio_id, anio, source)` → UNIQUE
- Campos: contaminantes aire (NO₂, PM2.5, PM10), ruido (dB día/noche)
- Metadata: `num_sensores_aire`, `metodo_agregacion`
- FK: `barrio_id → dim_barrios.barrio_id`

### Tecnologías

- SQLite 3.35+
- SQL DDL
- Python `sqlite3` para tests automatizados

---

## ✅ Criterios de Aceptación

### Schema Design

- [ ] **`fact_educacion` creada** con:
  - PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`
  - UNIQUE: `(barrio_id, anio, source)`
  - FK: `FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)`
  - CHECK: `anio BETWEEN 2010 AND 2030`, `universitarios_pct BETWEEN 0 AND 100`
  - Columnas conteo: `sin_estudios`, `primaria_completa`, `secundaria_completa`, `fp_medio`, `fp_superior`, `universitarios`, `doctorado` (INTEGER)
  - Columnas %: `sin_estudios_pct`, `secundaria_completa_pct`, `universitarios_pct` (REAL)
  - Metadata: `poblacion_referencia`, `dataset_id`, `source`, `etl_loaded_at`
  - Índice:
    ```sql
    CREATE INDEX idx_fact_educacion_barrio_anio
    ON fact_educacion(barrio_id, anio);
    ```

- [ ] **`fact_calidad_ambiental` creada** con:
  - PK: `id INTEGER PRIMARY KEY AUTOINCREMENT`
  - UNIQUE: `(barrio_id, anio, source)`
  - FK: `FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)`
  - CHECK: `no2_media >= 0 AND no2_media < 500`, `ruido_dia_db BETWEEN 30 AND 100`
  - Aire: `no2_media`, `pm25_media`, `pm10_media`, `o3_max_8h` (REAL, µg/m³)
  - Ruido: `ruido_dia_db`, `ruido_noche_db`, `superficie_ruido_alto_pct` (REAL)
  - Metadata espacial: `num_sensores_aire`, `metodo_agregacion`, `cobertura_espacial_km2`
  - Metadata estándar: `dataset_id`, `source`, `etl_loaded_at`
  - Índice:
    ```sql
    CREATE INDEX idx_fact_calidad_ambiental_barrio_anio
    ON fact_calidad_ambiental(barrio_id, anio);
    ```

### Validación de Constraints

- [ ] FK Integrity Test PASS (inserción con `barrio_id` inexistente debe fallar)
- [ ] UNIQUE Constraint Test PASS (duplicado `(barrio_id, anio, source)` debe fallar)
- [ ] CHECK Constraint Test PASS (valores fuera de rango fallan correctamente)

### Data Quality

- [ ] Seed data:
  - ≥5 filas en `fact_educacion`
  - ≥5 filas en `fact_calidad_ambiental`
  - Sources variados (`opendatabcn`, `idescat`, `gencat`)
- [ ] Query join ejecuta sin errores y devuelve ≥5 filas:
  ```sql
  SELECT 
    b.barrio_nombre,
    e.anio,
    e.universitarios_pct,
    c.no2_media,
    c.pm25_media,
    c.ruido_dia_db
  FROM dim_barrios b
  LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id
  LEFT JOIN fact_calidad_ambiental c 
    ON b.barrio_id = c.barrio_id AND c.anio = e.anio
  WHERE e.anio = 2023
  ORDER BY e.universitarios_pct DESC
  LIMIT 10;
  ```

### Documentación

- [ ] `docs/database/EXPERIMENTAL_SCHEMA_DESIGN.md` incluye:
  - Justificación de cada campo
  - Decisiones de diseño (por qué UNIQUE en `(barrio_id, anio, source)`)
  - Trade-offs (barrio vs distrito)
  - Data dictionary por tabla
  - Ejemplos de queries típicos

---

## 🧪 Plan de Testing

- Script SQL `scripts/schema/test_constraints.sql` para probar FK/UNIQUE/CHECK.
- Script Python `scripts/schema/test_experimental_schema.py` para:
  - Verificar existencia de tablas/índices.
  - Verificar nº de filas seed.
  - Verificar join educación–ambiental.

---

## 📋 Sub-tareas

### Fase 1: Setup (1h)
- [ ] Copiar DB a `database_experimental.db`.
- [ ] Crear `scripts/schema/` y cabecera de `phase2_experimental_tables.sql`.
- [ ] Ignorar `database_experimental.db` en `.gitignore`.

### Fase 2: Schema `fact_educacion` (2h)
- [ ] Diseñar columnas a partir de findings de #216.
- [ ] Escribir DDL + índice.
- [ ] Crear `seed_test_data.sql` con filas mock.

### Fase 3: Schema `fact_calidad_ambiental` (2h)
- [ ] Diseñar columnas de aire + ruido.
- [ ] Escribir DDL + índice.
- [ ] Ampliar `seed_test_data.sql`.

### Fase 4: Validación (1h)
- [ ] Ejecutar DDL en DB experimental.
- [ ] Insertar seed data.
- [ ] Ejecutar `test_constraints.sql` y `test_experimental_schema.py`.

### Fase 5: Documentación (1h)
- [ ] Redactar `EXPERIMENTAL_SCHEMA_DESIGN.md`.
- [ ] Abrir PR y solicitar code review.

---

## 🏷️ Metadata (Custom Fields sugeridos)

```yaml
Status: 📋 Todo
Priority: 🟡 Medium
Size: M
Estimate: 6
Phase: Infraestructure
Epic: DB
Release: v2.1 Enhancement Analytics
Start Date: 2026-01-06
Target Date: 2026-01-09
Quarter: Q1 2025
Effort (weeks): 0.15
Outcome: "Experimental schema created for fact_educacion and fact_calidad_ambiental with FK constraints validated"
```
