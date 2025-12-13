# Fase 1: Agregar Issues al Proyecto

**Fecha:** Diciembre 2025  
**Propósito:** Verificar y agregar issues de Fase 1 al GitHub Project

---

## 📋 Issues a Agregar

- Epic #187: [EPIC] Fase 1: Database Infrastructure
- #188: DATA-101 (8 fact tables)
- #189: DATA-102 (2 dimension tables)
- #190: DATA-103 (indexes & constraints)
- #191: DATA-104 (update schema.sql)
- #192: INFRA-101 (test DB on Render)
- #193: DOCS-101 (documentation)

**Total:** 7 issues

---

## 🚀 Script Automatizado

### Ejecutar Script

```bash
./scripts/add_fase1_issues_to_project.sh
```

**Qué hace:**
1. Verifica qué issues ya están en el proyecto
2. Agrega las que faltan
3. Muestra resumen de lo agregado

---

## 📝 Comandos Manuales (Alternativa)

### 1. Verificar Issues en el Proyecto

```bash
gh project item-list 1 --owner prototyp33 --format json | \
  jq -r '.items[] | "#\(.content.number) - \(.content.title)"'
```

### 2. Agregar Issues Individualmente

```bash
# Agregar Epic #187
gh project item-add 1 --owner prototyp33 \
  --url "https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/187"

# Agregar sub-issues #188-#193
for i in {188..193}; do
  gh project item-add 1 --owner prototyp33 \
    --url "https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/$i"
  echo "✅ Issue #$i agregado"
done
```

---

## ✅ Verificación

Después de ejecutar el script, verificar:

1. **En GitHub Projects UI:**
   - Ir a: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/projects/1
   - Verificar que aparecen las 7 issues (#187-#193)

2. **Via CLI:**
   ```bash
   gh project item-list 1 --owner prototyp33 --format json | \
     jq -r '.items[] | select(.content.number >= 187 and .content.number <= 193) | "#\(.content.number) - \(.content.title)"'
   ```

---

## 📋 Próximos Pasos

Después de agregar las issues al proyecto:

1. ✅ Issues agregadas al proyecto
2. ⏭️ Configurar custom fields en GitHub Projects UI
   - Ver: `docs/FASE1_CUSTOM_FIELDS_QUICK_COPY.md`
3. ⏭️ Verificar que aparecen en Roadmap View

---

## 🔗 Referencias

- **Script:** `scripts/add_fase1_issues_to_project.sh`
- **Custom Fields:** `docs/FASE1_CUSTOM_FIELDS_QUICK_COPY.md`
- **Proyecto:** https://github.com/prototyp33/barcelona-housing-demographics-analyzer/projects/1

---

**Última actualización:** Diciembre 2025

