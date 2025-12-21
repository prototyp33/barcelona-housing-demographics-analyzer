# Guía: Documentación y GitHub - Spike Data Validation

**Objetivo**: Cómo mantener sincronizada la documentación local con GitHub Issues/Projects

---

## 📚 Estructura de Documentación

### Documentos Principales

1. **`docs/CATASTRO_MASIVO_STATUS.md`** ⭐
   - Estado detallado de la consulta masiva Catastro
   - Actualizar cuando cambie el estado (envío, recepción, parseo)
   - **Cuándo actualizar**: Cada vez que haya un cambio de estado

2. **`docs/ISSUE_202_FASE2_PLAN.md`**
   - Plan completo de Fase 2 (Issue #202)
   - Actualizar secciones de "Estado" cuando se complete una tarea
   - **Cuándo actualizar**: Al completar cada tarea principal

3. **`docs/README.md`**
   - Resumen ejecutivo del spike completo
   - Actualizar sección "Estado del Spike" y "Próximos Pasos"
   - **Cuándo actualizar**: Al completar issues o hitos importantes

4. **`docs/GITHUB_UPDATE_SNIPPETS.md`**
   - Snippets listos para copiar/pegar en GitHub
   - **Cuándo usar**: Cada vez que quieras actualizar GitHub

---

## 🔄 Flujo de Trabajo Recomendado

### Paso 1: Trabajo Local
1. Realizar cambios técnicos (scripts, datos, etc.)
2. Actualizar documentación local (`docs/*.md`)
3. Commit cambios: `git add docs/ && git commit -m "docs: update Catastro masivo status"`

### Paso 2: Actualizar GitHub
1. Abrir Issue #202 (o el issue relevante)
2. Usar snippet de `GITHUB_UPDATE_SNIPPETS.md`
3. Copiar/pegar el snippet apropiado como comentario
4. Opcional: Actualizar cuerpo del issue si es un hito importante

### Paso 3: Project Board (si aplica)
1. Mover tarjeta de "In Progress" a "Done" (si se completó)
2. Actualizar checklist en la tarjeta
3. Añadir comentario con link a documentación actualizada

---

## 📋 Checklist de Actualización

### Cuando Envías XML a Sede Electrónica
- [ ] Actualizar `docs/CATASTRO_MASIVO_STATUS.md` (sección "Envío")
- [ ] Actualizar `docs/ISSUE_202_FASE2_PLAN.md` (Tarea 1: estado)
- [ ] Actualizar `docs/README.md` (Issue #202: estado)
- [ ] Añadir comentario en Issue #202 usando `GITHUB_UPDATE_SNIPPETS.md`
- [ ] Commit cambios: `git add docs/ && git commit -m "docs: Catastro masivo XML enviado"`
- [ ] Push: `git push origin main`

### Cuando Recibes XML de Salida
- [ ] Actualizar `docs/CATASTRO_MASIVO_STATUS.md` (sección "XML recibido")
- [ ] Añadir comentario en Issue #202: "XML recibido, procediendo con parseo"
- [ ] Actualizar Project Board: mover a siguiente tarea

### Cuando Implementas Parser
- [ ] Actualizar `docs/ISSUE_202_FASE2_PLAN.md` (Tarea 2: completada)
- [ ] Actualizar `docs/CATASTRO_MASIVO_STATUS.md` (sección "Parser")
- [ ] Añadir comentario en Issue #202 con métricas de parseo
- [ ] Commit: `git add scripts/fase2/parse_catastro_xml.py docs/ && git commit -m "feat: implement Catastro XML parser"`

### Cuando Completas Fase 2
- [ ] Actualizar `docs/README.md` (Issue #202: completado)
- [ ] Actualizar `docs/ISSUE_202_FASE2_PLAN.md` (todos los estados)
- [ ] Cerrar Issue #202 con resumen final
- [ ] Mover tarjeta en Project Board a "Done"

---

## 🎯 Buenas Prácticas

### 1. Mantener Documentación Actualizada
- **Siempre** actualizar docs locales antes de commit
- **Siempre** incluir link a docs en comentarios de GitHub
- **Nunca** dejar docs desactualizados más de 1 día

### 2. Comentarios en GitHub
- Usar snippets de `GITHUB_UPDATE_SNIPPETS.md` para consistencia
- Incluir fecha en cada update
- Referenciar archivos de documentación con paths relativos

### 3. Commits
- Prefijo: `docs:` para cambios solo de documentación
- Prefijo: `feat:` para nuevas funcionalidades + docs
- Mensaje claro: qué se actualizó y por qué

### 4. Project Board
- Mover tarjetas cuando cambie el estado real
- Actualizar checklist cuando se complete un subtask
- Añadir comentarios con links a docs relevantes

---

## 📝 Ejemplo de Flujo Completo

### Escenario: Acabas de enviar XML a Sede

**1. Actualizar docs locales**:
```bash
# Editar docs/CATASTRO_MASIVO_STATUS.md
# Editar docs/ISSUE_202_FASE2_PLAN.md
# Editar docs/README.md
```

**2. Commit**:
```bash
git add docs/
git commit -m "docs: update Catastro masivo status - XML enviado (ECLTI250200147801.XML)"
git push origin main
```

**3. Actualizar GitHub**:
- Abrir Issue #202
- Copiar snippet "Opción 1" de `GITHUB_UPDATE_SNIPPETS.md`
- Pegar como comentario
- Opcional: Actualizar Project Board

**4. Resultado**:
- ✅ Docs locales actualizados
- ✅ GitHub Issue actualizado
- ✅ Project Board sincronizado
- ✅ Historial claro para futuras referencias

---

## 🔗 Links Útiles

- **Issue #202**: [Link al issue en GitHub]
- **Project Board**: [Link al project board]
- **Documentación local**: `spike-data-validation/docs/`
- **Snippets**: `spike-data-validation/docs/GITHUB_UPDATE_SNIPPETS.md`

---

## ❓ Preguntas Frecuentes

**Q: ¿Debo actualizar GitHub cada vez que cambio algo local?**  
A: No necesariamente. Actualiza GitHub cuando:
- Hay un cambio de estado importante (envío, recepción, completado)
- Completas una tarea del plan
- Quieres mantener al equipo informado

**Q: ¿Qué pasa si olvido actualizar GitHub?**  
A: No es crítico, pero intenta actualizar al menos una vez por día de trabajo activo. La documentación local siempre debe estar actualizada.

**Q: ¿Debo cerrar el issue cuando completo Fase 2?**  
A: Sí, pero solo cuando Fase 2 esté completamente terminada (parser + filtrado + modelo entrenado + evaluación). Hasta entonces, mantén el issue abierto.

---

**Última actualización**: 2025-12-19

