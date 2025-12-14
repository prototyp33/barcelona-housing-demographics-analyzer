# Guía Manual: Agregar Issues al Proyecto GitHub

**Fecha:** Diciembre 2025  
**Propósito:** Instrucciones para agregar issues manualmente si el script falla

---

## 📋 Issues a Agregar

### Epics Fase 2-4
- **#194:** [EPIC PLACEHOLDER] Fase 2: Critical Extractors
- **#195:** [EPIC PLACEHOLDER] Fase 3: Complementary Extractors
- **#196:** [EPIC PLACEHOLDER] Fase 4: Integration & Production

### Spike Issues
- **#198:** [SPIKE] Data Validation & Model Feasibility (Epic)
- **#199:** [SPIKE-EQUIPO-A] Validar acceso Portal de Dades
- **#200:** [SPIKE-EQUIPO-A] Validar acceso INE API
- **#201:** [SPIKE-EQUIPO-A] Validar acceso Catastro
- **#204:** [SPIKE-EQUIPO-A] Diseñar schema PostgreSQL v2.0
- **#205:** [SPIKE-EQUIPO-A] Linking barrio_id cross-source
- **#206:** [SPIKE-EQUIPO-A] Validation framework
- **#207:** [SPIKE-EQUIPO-A] Data quality assessment
- **#208:** [SPIKE-EQUIPO-B] Implementar hedonic pricing model
- **#209:** [SPIKE-EQUIPO-B] Evaluar viabilidad Difference-in-Differences

**Total:** 13 issues (3 epics + 10 spike issues)

---

## 🔧 Método 1: Via GitHub Projects UI (Recomendado)

### Pasos

1. **Ir al Proyecto:**
   - URL: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/projects/1
   - O: GitHub → Projects → "Barcelona Housing - Roadmap"

2. **Agregar Issues:**
   - Click en **"Add item"** (botón en la parte superior)
   - En el campo de búsqueda, escribir el número de issue (ej: `#194`)
   - Seleccionar la issue de la lista
   - Repetir para todas las issues

3. **Verificar:**
   - Las issues deberían aparecer en el proyecto
   - Verificar que todas están agregadas

**Tiempo estimado:** 5-10 minutos

---

## 🔧 Método 2: Via GitHub CLI (Si funciona)

### Comando Individual

```bash
# Para cada issue
gh project item-add 1 --owner prototyp33 \
  --url "https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/194"
```

### Script Batch

```bash
# Epics
for i in 194 195 196; do
  gh project item-add 1 --owner prototyp33 \
    --url "https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/$i"
done

# Spike Issues
for i in 198 199 200 201 204 205 206 207 208 209; do
  gh project item-add 1 --owner prototyp33 \
    --url "https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/$i"
done
```

**Tiempo estimado:** 2-3 minutos (si funciona)

---

## 🔧 Método 3: Via GitHub API (Avanzado)

Si los métodos anteriores fallan, usar la API directamente:

```bash
# Obtener project ID
PROJECT_ID=$(gh api graphql -f query='
  query {
    organization(login: "prototyp33") {
      projectV2(number: 1) {
        id
      }
    }
  }
' --jq '.data.organization.projectV2.id')

# Agregar issue (ejemplo para #194)
gh api graphql -f query="
  mutation {
    addProjectV2ItemById(input: {
      projectId: \"$PROJECT_ID\"
      contentId: \"$(gh api repos/prototyp33/barcelona-housing-demographics-analyzer/issues/194 --jq '.node_id')\"
    }) {
      item {
        id
      }
    }
  }
"
```

**Tiempo estimado:** 10-15 minutos (requiere conocimiento de GraphQL)

---

## ✅ Verificación

Después de agregar todas las issues:

1. **Verificar en el Proyecto:**
   - Ir a: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/projects/1
   - Contar que hay 13 issues agregadas

2. **Verificar Custom Fields:**
   - Cada issue debería tener custom fields configurados
   - Ver: `docs/CUSTOM_FIELDS_SUMMARY.md` para valores

---

## 🆘 Troubleshooting

### Problema: "Item already exists"
- **Solución:** La issue ya está en el proyecto. Continuar con la siguiente.

### Problema: "Permission denied"
- **Solución:** Verificar permisos del proyecto. Puede requerir permisos de admin.

### Problema: "Project not found"
- **Solución:** Verificar que el proyecto número 1 existe y es accesible.

### Problema: Script se cuelga
- **Solución:** Usar Método 1 (UI manual) que es más confiable.

---

## 📊 Checklist

- [ ] Epic #194 agregado
- [ ] Epic #195 agregado
- [ ] Epic #196 agregado
- [ ] Spike Epic #198 agregado
- [ ] Spike Issues #199-#209 agregadas (10 issues)
- [ ] Total: 13 issues en el proyecto
- [ ] Custom fields configurados (ver siguiente paso)

---

**Última actualización:** Diciembre 2025

