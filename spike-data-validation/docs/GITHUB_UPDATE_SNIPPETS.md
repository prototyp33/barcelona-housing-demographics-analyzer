# Snippets para Actualizar GitHub - Issue #202 (Fase 2)

**Fecha**: 19 Diciembre 2025  
**Para usar**: Copiar y pegar en comentarios de Issue #202 o actualizar el cuerpo del issue

---

## 📝 Opción 1: Comentario de Actualización de Estado

Usa este snippet para añadir un comentario al Issue #202:

```markdown
## 🔄 Actualización Estado Catastro Masivo (19/12/2025)

### ✅ Completado

**XML de Entrada Generado y Enviado**
- **Fichero sistema**: `ECLTI250200147801.XML`
- **Tamaño**: 2,974 bytes
- **Formato**: `<LISTADATOS>` según Anexo 1 oficial (versión 1.5/1.6)
- **Referencias**: 60 edificios Gràcia (14 caracteres cada una)
- **Fecha envío**: 19/12/2025
- **Sede**: https://www1.sedecatastro.gob.es

**Problema Resuelto**
- ❌ Error inicial: `The 'http://www.catastro.meh.es/:CONSULTA' element is not declared`
- ✅ Solución: Cambio a formato `<LISTADATOS>` según documentación oficial
- 📚 Ver: `docs/XML_VARIANTS_TESTING.md` para detalles del debugging

### ⏳ Pendiente

**Descarga XML de Salida**
- **Plazo estimado**: ≤24 horas desde el envío (según Sede Electrónica)
- **Fecha límite esperada**: 20/12/2025 (antes de medianoche)
- **Acción requerida**: Descargar desde Sede Electrónica cuando esté disponible
- **Guardar en**: `spike-data-validation/data/raw/catastro_oficial/ECLTI250200147801.XML`

**Próximos Pasos** (cuando llegue el XML):
1. Inspeccionar estructura del XML de salida real
2. Implementar/ajustar `fase2/parse_catastro_xml.py`
3. Generar CSV: `catastro_barcelona_parsed.csv`
4. Filtrar para Gràcia con `filter_gracia_real.py`

### 📊 Métricas Esperadas

- **Edificios Gràcia con datos reales**: ~60 (según seed)
- **Completitud esperada**:
  - `superficie_m2`: >90%
  - `ano_construccion`: >80%
  - `plantas`: >70%

### 📚 Documentación

- **Estado completo**: `docs/CATASTRO_MASIVO_STATUS.md`
- **Plan Fase 2**: `docs/ISSUE_202_FASE2_PLAN.md`
- **Debugging XML**: `docs/XML_VARIANTS_TESTING.md`

---

**Scripts relacionados**:
- ✅ `scripts/fase2/download_catastro_massive.py` - Generador XML
- ✅ `scripts/catastro_oficial_client.py` - Cliente oficial
- ⏳ `scripts/fase2/parse_catastro_xml.py` - Parser (pendiente implementación)
```

---

## 📝 Opción 2: Actualizar Cuerpo del Issue #202

Si prefieres actualizar el cuerpo principal del issue, añade esta sección al final:

```markdown
---

## 📋 Estado Actual (19/12/2025)

### Tarea 1: Descarga Masiva Catastro Barcelona ✅ **EN PROGRESO**

- ✅ XML de entrada generado: `consulta_masiva_entrada.xml` (formato `<LISTADATOS>`)
- ✅ Enviado a Sede Electrónica: `ECLTI250200147801.XML` (2,974 bytes)
- ✅ Fecha envío: 19/12/2025
- ⏳ Pendiente: Respuesta de la Sede (plazo ≤24h)

**Próximo paso**: Descargar XML de salida cuando esté disponible → Parsear → Filtrar Gràcia

Ver detalles completos en: `docs/CATASTRO_MASIVO_STATUS.md`
```

---

## 📝 Opción 3: Actualizar Project Board (Checklist)

Si usas un Project Board con checklist, marca estos items:

```markdown
### Tarea 1: Descarga Masiva Catastro Barcelona
- [x] Generar XML de entrada con formato correcto
- [x] Enviar a Sede Electrónica del Catastro
- [ ] Descargar XML de salida (pendiente ≤24h)
- [ ] Verificar estructura del XML recibido

### Tarea 2: Parser XML → CSV
- [ ] Inspeccionar estructura XML de salida real
- [ ] Implementar parser iterativo (`fase2/parse_catastro_xml.py`)
- [ ] Generar CSV: `catastro_barcelona_parsed.csv`
- [ ] Validar completitud de campos

### Tarea 3: Filtrar para Gràcia
- [ ] Ejecutar `filter_gracia_real.py` con datos reales
- [ ] Generar `catastro_gracia_real.csv`
- [ ] Comparar con datos imputados (Fase 1)
```

---

## 📝 Opción 4: Comentario Corto (Quick Update)

Si solo quieres un update rápido:

```markdown
**Update 19/12/2025**: XML de entrada enviado a Sede Electrónica (`ECLTI250200147801.XML`). 
Pendiente respuesta ≤24h. Ver `docs/CATASTRO_MASIVO_STATUS.md` para detalles.
```

---

## 🎯 Recomendación

**Para Issue #202**: Usa **Opción 1** (comentario completo) para mantener un historial claro del progreso.

**Para Project Board**: Usa **Opción 3** (checklist) para tracking visual.

**Para comunicación rápida**: Usa **Opción 4** (comentario corto).

---

**Última actualización**: 2025-12-19

