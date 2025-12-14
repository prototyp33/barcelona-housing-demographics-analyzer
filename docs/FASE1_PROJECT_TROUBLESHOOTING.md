# Fase 1: Troubleshooting - Agregar Issues al Proyecto

**Fecha:** Diciembre 2025

---

## ⚠️ Problema: Error al Agregar Issues

Si el script `add_fase1_issues_to_project.sh` muestra errores, sigue estos pasos:

---

## 🔍 Diagnóstico

### 1. Verificar que el Proyecto Existe

```bash
gh project view 1 --owner prototyp33
```

**Si falla:**
- Verificar el número del proyecto
- Listar proyectos: `gh project list --owner prototyp33`

### 2. Verificar Issues Actuales en el Proyecto

```bash
gh project item-list 1 --owner prototyp33 --format json | \
  jq -r '.items[] | "#\(.content.number) - \(.content.title)"'
```

### 3. Verificar que las Issues Existen

```bash
for i in {187..193}; do
  gh issue view $i --json number,title,state
done
```

---

## ✅ Solución 1: Agregar Manualmente (Recomendado)

Si el script falla, agregar manualmente:

### Opción A: Via GitHub CLI (uno por uno)

```bash
# Epic #187
gh project item-add 1 --owner prototyp33 \
  --url "https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/187"

# Sub-issues #188-#193
for i in {188..193}; do
  gh project item-add 1 --owner prototyp33 \
    --url "https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/$i"
  echo "✅ Issue #$i agregado"
done
```

### Opción B: Via GitHub UI (Más Fácil)

1. Ir a: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/projects/1
2. Click en "Add item" o "+"
3. Buscar cada issue por número (#187, #188, etc.)
4. Agregar al proyecto

**Tiempo:** 2-3 minutos

---

## ✅ Solución 2: Verificar si Ya Están

Si las issues ya están en el proyecto, el error puede ser normal:

```bash
# Verificar si #187 está en el proyecto
gh project item-list 1 --owner prototyp33 --format json | \
  jq -r '.items[] | select(.content.number == 187) | "✅ Issue #187 ya está en el proyecto"'
```

Repetir para #188-#193.

---

## 🔧 Solución 3: Usar GraphQL (Avanzado)

Si GitHub CLI no funciona, usar GraphQL directamente:

```bash
# Obtener Project ID
PROJECT_ID=$(gh api graphql -f query='
  query {
    organization(login: "prototyp33") {
      projectV2(number: 1) {
        id
      }
    }
  }
' | jq -r '.data.organization.projectV2.id')

# Agregar issue #187
gh api graphql -f query="
  mutation {
    addProjectV2ItemById(input: {
      projectId: \"$PROJECT_ID\"
      contentId: \"$(gh api graphql -f query='query { repository(owner: \"prototyp33\", name: \"barcelona-housing-demographics-analyzer\") { issue(number: 187) { id } } }' | jq -r '.data.repository.issue.id')\"
    }) {
      item {
        id
      }
    }
  }
"
```

**⚠️ Complejo:** Requiere obtener IDs de cada issue primero.

---

## 📋 Checklist de Verificación

- [ ] Proyecto #1 existe y es accesible
- [ ] Issues #187-#193 existen
- [ ] Tienes permisos para agregar items al proyecto
- [ ] GitHub CLI está autenticado (`gh auth status`)

---

## 🎯 Recomendación Final

**Si el script falla, usar GitHub UI:**

1. Ir a: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/projects/1
2. Click en "Add item"
3. Buscar y agregar cada issue (#187-#193)
4. **Tiempo:** 2-3 minutos (más rápido que debuggear CLI)

---

## 🔗 Referencias

- **Script:** `scripts/add_fase1_issues_to_project.sh`
- **Project Setup:** `docs/FASE1_PROJECT_SETUP.md`
- **Custom Fields:** `docs/FASE1_CUSTOM_FIELDS_QUICK_COPY.md`

---

**Última actualización:** Diciembre 2025

