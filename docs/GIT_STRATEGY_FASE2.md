# Estrategia Git - Feature Branch fase2-catastro-idealista

**Fecha**: 21 de diciembre de 2025  
**Rama**: `feature/fase2-catastro-idealista`

---

## 📊 Situación Actual

### Estado de la Rama
- ✅ Último commit: `854406e` - Documentación de modelos de predicción
- 📝 Archivos modificados sin commitear: 6
- 📁 Archivos sin trackear: ~60+ (principalmente documentación del spike)

### Contexto
Esta rama contiene el trabajo del spike de validación (Issues #199, #200, #201, #202, #203, #204) que incluye:
- Modelo MACRO v0.2 Optimizado (listo para producción)
- Modelo MICRO v0.1 (no viable, cerrado)
- Investigación completa de coeficientes anómalos
- Documentación extensa del spike

---

## 🎯 Estrategia Recomendada

### Opción A: Commits Organizados por Tipo (RECOMENDADO)

**Ventajas**:
- Historial limpio y fácil de revisar
- PRs más fáciles de entender
- Facilita code review

**Plan**:

#### 1. Commit de Documentación del Spike
```bash
git add spike-data-validation/docs/*.md
git commit -m "docs(spike): añadir documentación completa del spike de validación

- Documentación de Issues #199-#204
- Resultados de modelos MACRO y MICRO
- Guías de scraping y matching
- Análisis de problemas y soluciones"
```

#### 2. Commit de Scripts y Notebooks
```bash
git add spike-data-validation/scripts/fase2/
git add spike-data-validation/notebooks/*.ipynb
git add spike-data-validation/scripts/*.py
git commit -m "feat(spike): scripts y notebooks para modelo MACRO v0.2 y análisis

- Scripts de entrenamiento y enriquecimiento de datos
- Notebooks de EDA y diagnósticos
- Scripts de matching Idealista-Catastro
- Scripts de parsing de Catastro masivo"
```

#### 3. Commit de Cambios en Archivos Principales
```bash
git add CONTRIBUTING.md README.md requirements.txt
git commit -m "chore: actualizar documentación principal y dependencias

- Actualizar README.md con estado del spike
- Actualizar CONTRIBUTING.md
- Actualizar requirements.txt con nuevas dependencias"
```

#### 4. Commit de Estructura del Proyecto (si aplica)
```bash
git add docs/PROJECT_STRUCTURE*.md docs/architecture/
git commit -m "docs: documentación de estructura del proyecto

- Propuesta de reorganización
- Reglas de dependencias
- Estado de implementación"
```

---

### Opción B: Commit Único Grande (NO RECOMENDADO)

**Solo si**:
- Todos los cambios están relacionados
- No necesitas revisión granular
- Es un spike que se mergeará completo

```bash
git add .
git commit -m "feat(spike): completar spike de validación modelos hedónicos

- Modelo MACRO v0.2 Optimizado (R²=0.79)
- Investigación completa de coeficientes
- Documentación extensa
- Scripts y notebooks de análisis

Completa Issues #199, #200, #201, #202, #203, #204"
```

---

## 🔀 Estrategia de PRs

### Opción 1: PR Único (RECOMENDADO para Spike)

**Razón**: El spike es una unidad de trabajo coherente

```bash
# Después de todos los commits
gh pr create \
  --title "feat(spike): Validación modelos hedónicos - MACRO v0.2 Optimizado" \
  --body "Completa el spike de validación de modelos hedónicos para Gràcia.

## Resumen
- ✅ Modelo MACRO v0.2 Optimizado (R²=0.79, RMSE=272€/m²) - LISTO PARA PRODUCCIÓN
- ❌ Modelo MICRO v0.1 - NO VIABLE (curva de demanda no-lineal)
- ✅ Investigación completa de coeficientes anómalos (Fases 1-4)
- ✅ Documentación extensa del spike

## Issues Completados
- #199: Extracción datos Portal Dades
- #200: Datos Catastro (imputados)
- #201: Linking precios y características
- #202: Modelo MICRO (cerrado - no viable)
- #203: Baseline MACRO v0.1
- #204: Diagnósticos OLS

## Archivos Principales
- \`spike-data-validation/scripts/train_macro_v02.py\`
- \`spike-data-validation/notebooks/07_diagnosticos_macro_v02.ipynb\`
- \`spike-data-validation/docs/INVESTIGACION_PLANTAS_RESULTADOS.md\`
- \`docs/PROJECT_STATUS.md\`

## Testing
- [ ] Verificar que notebooks ejecutan sin errores
- [ ] Validar que scripts funcionan correctamente
- [ ] Revisar documentación

Fixes #199, #200, #201, #202, #203, #204" \
  --label "spike,models,ready-for-review"
```

### Opción 2: PRs Separados (Si el PR es muy grande)

1. **PR 1: Documentación**
   - Solo archivos `.md`
   - Fácil de revisar

2. **PR 2: Código y Scripts**
   - Scripts y notebooks
   - Requiere testing

3. **PR 3: Cambios en Archivos Principales**
   - README, CONTRIBUTING, requirements.txt

---

## 📋 Checklist Pre-PR

Antes de crear el PR:

- [ ] Todos los commits tienen mensajes descriptivos
- [ ] Código ejecuta sin errores
- [ ] Notebooks ejecutan de principio a fin
- [ ] Documentación está actualizada
- [ ] No hay archivos temporales o de debug
- [ ] `.gitignore` está actualizado (si es necesario)
- [ ] Branch está sincronizada con `main` (usar `./scripts/git/sync_with_main.sh`)

---

## 🚀 Pasos Recomendados (Ahora)

### Paso 1: Organizar Commits
```bash
# Ver qué archivos son importantes
git status

# Commit 1: Documentación del spike
git add spike-data-validation/docs/*.md
git commit -m "docs(spike): añadir documentación completa del spike"

# Commit 2: Scripts y notebooks
git add spike-data-validation/scripts/ spike-data-validation/notebooks/
git commit -m "feat(spike): scripts y notebooks para análisis de modelos"

# Commit 3: Cambios en archivos principales
git add CONTRIBUTING.md README.md requirements.txt spike-data-validation/docs/README.md
git commit -m "chore: actualizar documentación principal y dependencias"

# Commit 4: Estructura del proyecto (si aplica)
git add docs/PROJECT_STRUCTURE*.md docs/architecture/ docs/STRUCTURE*.md
git commit -m "docs: documentación de estructura del proyecto"
```

### Paso 2: Sincronizar con Main
```bash
./scripts/git/sync_with_main.sh
# O manualmente:
git fetch origin
git rebase origin/main
```

### Paso 3: Push y Crear PR
```bash
git push origin feature/fase2-catastro-idealista

# Crear PR usando gh CLI o GitHub UI
gh pr create --title "feat(spike): Validación modelos hedónicos - MACRO v0.2 Optimizado" \
  --body-file <(cat <<'EOF'
Completa el spike de validación de modelos hedónicos para Gràcia.

## Resumen
- ✅ Modelo MACRO v0.2 Optimizado (R²=0.79, RMSE=272€/m²) - LISTO PARA PRODUCCIÓN
- ❌ Modelo MICRO v0.1 - NO VIABLE (curva de demanda no-lineal)
- ✅ Investigación completa de coeficientes anómalos (Fases 1-4)

## Issues Completados
- #199, #200, #201, #202, #203, #204

Fixes #199, #200, #201, #202, #203, #204
EOF
)
```

---

## ⚠️ Consideraciones

### Archivos que NO deberían commitearse
- Archivos temporales de debug
- Logs grandes
- Datos procesados grandes (ya están en `.gitignore`)
- Archivos de configuración local (`.env`)

### Archivos que SÍ deberían commitearse
- ✅ Documentación (`.md`)
- ✅ Scripts (`.py`)
- ✅ Notebooks (`.ipynb`)
- ✅ Configuración de proyecto (`requirements.txt`, etc.)

---

## 📝 Notas Finales

- **Spike completo**: Este spike es una unidad de trabajo coherente, un PR único tiene sentido
- **Documentación extensa**: Es normal tener muchos archivos `.md` en un spike
- **Revisión**: El PR puede ser grande, pero está bien documentado y organizado

---

**Última actualización**: 2025-12-21

