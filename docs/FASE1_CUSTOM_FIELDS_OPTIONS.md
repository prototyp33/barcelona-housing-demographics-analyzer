# Fase 1: Opciones para Configurar Custom Fields

**Fecha:** Diciembre 2025

---

## 📋 Resumen de Opciones

| Opción | Tiempo | Complejidad | Recomendación |
|--------|--------|-------------|---------------|
| **1. Manual en UI** | 15-20 min | ⭐ Fácil | ✅ **Recomendado** |
| **2. Quick Copy-Paste** | 10-15 min | ⭐ Fácil | ✅ **Más rápido** |
| **3. GraphQL Mutations** | 2+ horas | ⭐⭐⭐ Complejo | ❌ No recomendado |

---

## ✅ OPCIÓN 1: Configuración Manual en UI (Recomendado)

### Pasos

1. Ir a GitHub Projects: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/projects
2. Seleccionar proyecto: "Barcelona Housing - Roadmap"
3. Para cada issue:
   - Abrir el issue en el proyecto
   - Click para abrir panel lateral
   - Configurar cada campo según `docs/FASE1_CUSTOM_FIELDS_REFERENCE.md`

### Tiempo Estimado
- **15-20 minutos** (7 issues × 2-3 min cada una)

### Ventajas
- ✅ Visual y directo
- ✅ Verificación inmediata
- ✅ Sin errores de sintaxis

### Referencia
- `docs/FASE1_CUSTOM_FIELDS_REFERENCE.md` - Tabla completa con todos los valores

---

## ⚡ OPCIÓN 2: Quick Copy-Paste (Más Rápido)

### Pasos

1. Abrir `docs/FASE1_CUSTOM_FIELDS_QUICK_COPY.md`
2. Para cada issue:
   - Copiar la línea de valores
   - Pegar como referencia mientras configuras
   - Configurar campos en UI usando la línea como guía

### Tiempo Estimado
- **10-15 minutos** (copy-paste rápido)

### Ventajas
- ✅ Más rápido que manual puro
- ✅ Formato optimizado para lectura
- ✅ Mismo proceso visual

### Referencia
- `docs/FASE1_CUSTOM_FIELDS_QUICK_COPY.md` - Formato optimizado

---

## ⚠️ OPCIÓN 3: GraphQL Mutations (No Recomendado)

### Pasos

1. Obtener Project ID
2. Obtener Item IDs (uno por issue)
3. Obtener Field IDs (uno por custom field)
4. Generar 84 mutations (7 issues × 12 campos)
5. Ejecutar cada mutation
6. Debug errores

### Tiempo Estimado
- **2+ horas** (debugging incluido)

### Desventajas
- ❌ Muy complejo
- ❌ Requiere múltiples queries para obtener IDs
- ❌ Propenso a errores
- ❌ Diferentes tipos de valores (text, number, date, single_select)
- ❌ No hay soporte completo en GitHub CLI

### Cuándo Usar
- Solo si necesitas automatizar para múltiples proyectos
- Si tienes experiencia con GraphQL
- Si planeas hacer esto frecuentemente

### Referencia
- `scripts/generate_custom_fields_mutations.sh` - Script generador
- `custom_fields_mutations_template.graphql` - Template (si se genera)

---

## 🎯 Recomendación Final

**Usar OPCIÓN 2: Quick Copy-Paste**

1. Abrir `docs/FASE1_CUSTOM_FIELDS_QUICK_COPY.md`
2. Ir a GitHub Projects UI
3. Para cada issue, copiar la línea y configurar campos
4. **Tiempo total: 10-15 minutos**

---

## 📊 Comparación de Tiempo

```
Manual UI:        ████████████████░░░░ 15-20 min
Quick Copy:       ████████████░░░░░░░░ 10-15 min  ⭐ RECOMENDADO
GraphQL:          ████████████████████████████████████████████ 2+ horas
```

---

## 📁 Archivos de Referencia

- **Quick Copy:** `docs/FASE1_CUSTOM_FIELDS_QUICK_COPY.md` ⭐
- **Referencia Detallada:** `docs/FASE1_CUSTOM_FIELDS_REFERENCE.md`
- **Pendientes:** `docs/FASE1_PENDING_CUSTOM_FIELDS.md`
- **CSV Source:** `data/reference/fase1_custom_fields.csv`
- **GraphQL Template:** `scripts/generate_custom_fields_mutations.sh` (si es necesario)

---

**Última actualización:** Diciembre 2025

