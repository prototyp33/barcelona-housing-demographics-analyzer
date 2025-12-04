# 📋 Configuración del Project Board

**Guía para configurar y usar el GitHub Project Board**

---

## 🎯 Columnas Recomendadas

```
📋 Backlog
   └─ Issues sin asignar a sprint específico

🚀 Ready (Sprint 2)
   └─ Issues del Sprint 2 listas para trabajar

🔄 In Progress
   └─ Issues en las que se está trabajando actualmente

👀 Review
   └─ Issues con PR abierto esperando revisión

✅ Done
   └─ Issues completadas y cerradas
```

---

## 📝 Pasos para Configurar

### 1. Crear Project Board

1. Ve a: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/projects
2. Click "New project"
3. Selecciona "Board"
4. Nombre: `Barcelona Housing - Sprint Board`
5. Descripción: `Tablero de gestión de sprints y issues`

### 2. Configurar Columnas

Crear estas columnas en orden:

1. **Backlog** (sin límite)
2. **Ready (Sprint 2)** (sin límite)
3. **In Progress** (límite: 3-5 issues)
4. **Review** (sin límite)
5. **Done** (sin límite)

### 3. Añadir Issues al Board

**Opción A: Manualmente**
- Arrastra issues desde la lista de issues al board
- Organiza por milestone o label

**Opción B: Automáticamente**
```bash
# Usar gh CLI para añadir issues al board
# (Requiere Project ID - obtener desde GitHub UI)
```

### 4. Mover Issues del Sprint 2

```bash
# Listar issues del Sprint 2
gh issue list --milestone "Sprint 2 - Calidad de Código" --limit 10

# Mover manualmente al board desde GitHub UI
# O usar el script de priorización:
make prioritize-sprint2
```

---

## 🔄 Flujo de Trabajo

### Al Empezar una Issue

1. Mover issue de "Ready" → "In Progress"
2. Crear branch: `git checkout -b fix/66-print-to-logger`
3. Trabajar en la issue

### Al Crear PR

1. Mover issue de "In Progress" → "Review"
2. Crear PR vinculado a la issue: `Closes #66`
3. Esperar code review

### Al Mergear PR

1. PR mergeado automáticamente cierra la issue
2. Mover issue de "Review" → "Done"
3. Issue se cierra automáticamente

---

## 📊 Métricas del Board

### WIP Limit (Work In Progress)

- **In Progress**: Máximo 3-5 issues
- **Review**: Sin límite (pero revisar frecuentemente)

### Velocity Tracking

- Contar issues movidas a "Done" cada semana
- Objetivo: 5-7 issues/semana

---

## 🛠️ Comandos Útiles

```bash
# Ver issues del Sprint 2
gh issue list --milestone "Sprint 2 - Calidad de Código"

# Priorizar issues del Sprint 2
make prioritize-sprint2

# Analizar estado de issues
make analyze-issues
```

---

## 📈 Mejores Prácticas

1. **Actualizar el board diariamente**
   - Mover issues cuando cambian de estado
   - Cerrar issues completadas

2. **Usar límites WIP**
   - No empezar nueva issue si "In Progress" está lleno
   - Completar antes de empezar nueva

3. **Revisar "Review" frecuentemente**
   - No dejar PRs sin revisar > 24 horas
   - Priorizar PRs de issues críticas

4. **Limpiar "Done" mensualmente**
   - Archivar issues completadas
   - Mantener solo últimas 2-3 semanas

---

**Última actualización:** 2025-12-03

