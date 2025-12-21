# Guía Completa: Pipeline Fase 2 (Issue #202)

**Objetivo**: Obtener datos reales del Catastro para Gràcia y prepararlos para el modelo hedónico MICRO.

---

## 📋 Resumen del Flujo

```
XML Sede Electrónica
    ↓
[1] Validar XML recibido
    ↓
[2] Parsear XML → CSV (Barcelona completo)
    ↓
[3] Filtrar para Gràcia (60 edificios)
    ↓
[4] Comparar con datos imputados (Fase 1)
    ↓
catastro_gracia_real.csv (listo para matching Idealista)
```

---

## 🚀 Ejecución Rápida (Todo en Uno)

**Cuando tengas el XML descargado**:

```bash
.venv-spike/bin/python spike-data-validation/scripts/fase2/run_fase2_pipeline.py \
  --xml spike-data-validation/data/raw/catastro_oficial/ECLTI250200147801.XML
```

Este script ejecuta automáticamente todos los pasos en orden.

---

## 📝 Pasos Detallados

### Paso 1: Validar XML Recibido

**Cuándo ejecutar**: Inmediatamente después de descargar el XML desde la Sede.

**Script**: `scripts/fase2/validate_xml_received.py`

**Comando**:
```bash
.venv-spike/bin/python spike-data-validation/scripts/fase2/validate_xml_received.py \
  --xml spike-data-validation/data/raw/catastro_oficial/ECLTI250200147801.XML
```

**Qué verifica**:
- ✅ Archivo existe y es XML válido
- ✅ Tamaño del archivo
- ✅ Tag raíz
- ✅ Número aproximado de inmuebles
- ✅ Tags principales encontrados

**Output**: `data/logs/xml_validation_result.json`

**Si falla**: Revisa que el XML se descargó correctamente y no está corrupto.

---

### Paso 2: Parsear XML → CSV

**Cuándo ejecutar**: Después de validar el XML.

**Script**: `scripts/fase2/parse_catastro_xml.py`

**Comando**:
```bash
.venv-spike/bin/python spike-data-validation/scripts/fase2/parse_catastro_xml.py \
  --xml spike-data-validation/data/raw/catastro_oficial/ECLTI250200147801.XML \
  --out spike-data-validation/data/processed/fase2/catastro_barcelona_parsed.csv \
  --validate
```

**Qué hace**:
- Intenta usar el parser del cliente oficial primero
- Si falla, usa parser heurístico iterativo
- Extrae: `referencia_catastral`, `superficie_m2`, `ano_construccion`, `plantas`, `direccion_normalizada`
- Valida completitud de campos

**Output**: `data/processed/fase2/catastro_barcelona_parsed.csv`

**Opciones útiles**:
- `--limit N`: Limitar a N inmuebles (útil para testing)
- `--validate`: Ejecutar validaciones después del parseo

---

### Paso 3: Filtrar para Gràcia

**Cuándo ejecutar**: Después de parsear el XML.

**Script**: `scripts/filter_gracia_real.py`

**Comando**:
```bash
.venv-spike/bin/python spike-data-validation/scripts/filter_gracia_real.py \
  --input spike-data-validation/data/processed/fase2/catastro_barcelona_parsed.csv \
  --output spike-data-validation/data/processed/catastro_gracia_real.csv
```

**Qué hace**:
- Filtra el CSV de Barcelona usando el seed de Gràcia (`gracia_refs_seed.csv`)
- Coincidencia por `referencia_catastral` (14 caracteres)
- Añade coordenadas/dirección del seed si existen

**Output**: `data/processed/catastro_gracia_real.csv`

**Esperado**: ~60 edificios de Gràcia con datos reales.

---

### Paso 4: Comparar con Datos Imputados (Opcional)

**Cuándo ejecutar**: Después de filtrar para Gràcia.

**Script**: `scripts/compare_imputed_vs_real.py`

**Comando**:
```bash
.venv-spike/bin/python spike-data-validation/scripts/compare_imputed_vs_real.py
```

**Qué hace**:
- Compara `catastro_gracia_imputado.csv` (Fase 1) vs `catastro_gracia_real.csv` (Fase 2)
- Calcula métricas: MAE, RMSE para `superficie_m2` y `ano_construccion`
- Genera reporte en `docs/ANALISIS_IMPUTADO_VS_REAL.md`

**Output**: `docs/ANALISIS_IMPUTADO_VS_REAL.md`

---

## 📊 Archivos Generados

### Intermedios
- `data/processed/fase2/catastro_barcelona_parsed.csv` - Barcelona completo parseado
- `data/logs/xml_validation_result.json` - Resultado de validación XML
- `data/logs/masivo_xml_inspection.json` - Inspección detallada (si usas `inspect_catastro_masivo_xml.py`)

### Finales
- `data/processed/catastro_gracia_real.csv` - **Archivo principal para Fase 2**
  - 60 edificios de Gràcia
  - Datos reales del Catastro (superficie, año, plantas)
  - Listo para matching con Idealista

---

## 🔍 Troubleshooting

### Problema: XML no se puede parsear

**Síntomas**: Parser devuelve 0 resultados.

**Soluciones**:
1. Inspeccionar estructura del XML:
   ```bash
   .venv-spike/bin/python spike-data-validation/scripts/inspect_catastro_masivo_xml.py \
     --xml path/al/xml.xml
   ```
2. Verificar que el XML no esté corrupto (abrir en editor de texto)
3. Revisar `data/logs/xml_validation_result.json` para ver qué tags se encontraron

### Problema: Filtrado devuelve 0 edificios

**Síntomas**: `catastro_gracia_real.csv` está vacío o tiene muy pocas filas.

**Soluciones**:
1. Verificar que las referencias catastrales coincidan:
   ```bash
   # Ver referencias en seed
   head spike-data-validation/data/raw/gracia_refs_seed.csv
   
   # Ver referencias en CSV parseado
   head spike-data-validation/data/processed/fase2/catastro_barcelona_parsed.csv
   ```
2. Verificar formato de referencias (14 vs 20 caracteres)
3. Revisar logs del script de filtrado

### Problema: Completitud baja de campos

**Síntomas**: Muchos `null` en `superficie_m2` o `ano_construccion`.

**Esperado**:
- `superficie_m2`: >90% completo
- `ano_construccion`: >80% completo
- `plantas`: >70% completo

**Si está por debajo**:
- Revisar estructura del XML (puede que los tags sean diferentes)
- Ajustar parser heurístico en `parse_catastro_xml.py`

---

## ✅ Checklist de Ejecución

Antes de ejecutar el pipeline completo:

- [ ] XML descargado desde Sede Electrónica
- [ ] XML guardado en `data/raw/catastro_oficial/`
- [ ] Virtual environment activado (`.venv-spike`)
- [ ] Dependencias instaladas (`pandas`, `xml.etree.ElementTree`)

Durante la ejecución:

- [ ] Paso 1 (Validación): ✓ XML válido
- [ ] Paso 2 (Parseo): ✓ CSV generado con >0 filas
- [ ] Paso 3 (Filtrado): ✓ CSV Gràcia con ~60 edificios
- [ ] Paso 4 (Comparación): ✓ Reporte generado (opcional)

Después de ejecutar:

- [ ] Revisar `catastro_gracia_real.csv` manualmente
- [ ] Verificar completitud de campos críticos
- [ ] Documentar cualquier problema encontrado
- [ ] Actualizar Issue #202 con resultados

---

## 📚 Scripts Relacionados

### Scripts Principales
- `fase2/run_fase2_pipeline.py` - Pipeline completo (recomendado)
- `fase2/validate_xml_received.py` - Validación rápida XML
- `fase2/parse_catastro_xml.py` - Parser XML → CSV
- `filter_gracia_real.py` - Filtrado para Gràcia

### Scripts de Utilidad
- `inspect_catastro_masivo_xml.py` - Inspección detallada de estructura XML
- `compare_imputed_vs_real.py` - Comparación Fase 1 vs Fase 2
- `parse_catastro_masivo_output.py` - Parser base (usado por `parse_catastro_xml.py`)

### Scripts de Referencia
- `fase2/download_catastro_massive.py` - Generador XML de entrada
- `catastro_oficial_client.py` - Cliente oficial del Catastro

---

## 🎯 Próximos Pasos (Después del Pipeline)

Una vez completado el pipeline Fase 2:

1. **Matching con Idealista** (`fase2/match_catastro_idealista.py`)
   - Matching por referencia catastral
   - Fuzzy matching por dirección
   - Generar `gracia_micro_matched.csv`

2. **Entrenar Modelo MICRO** (`fase2/train_micro_hedonic.py`)
   - Features: superficie, año, plantas (reales)
   - Target: precio_m2 de Idealista
   - Comparar con baseline MACRO v0.1

3. **Evaluación y Decisión Go/No-Go**
   - R² ≥ 0.75?
   - RMSE ≤ 250 €/m²?
   - ¿Mejora vs baseline MACRO?

---

**Última actualización**: 2025-12-19  
**Issue relacionada**: #202 (Fase 2)

