# Instrucciones para Publicar Comentario en GitHub Issue #202

**Sigue estos pasos para publicar el comentario siguiendo las mejores prácticas:**

---

## 📋 Pre-requisitos

1. ✅ Tener acceso al repositorio en GitHub
2. ✅ Issue #202 debe existir y estar abierta
3. ✅ Tener permisos para comentar en issues

---

## 🚀 Pasos para Publicar

### Paso 1: Preparar el Comentario

1. Abre el archivo: `spike-data-validation/docs/GITHUB_COMMENT_ISSUE_202.md`
2. Copia **todo el contenido** desde la línea que dice `## 🔄 Actualización Estado...` hasta el final
3. **NO copies** las primeras 4 líneas (son instrucciones)

### Paso 2: Acceder a GitHub

1. Ve a: `https://github.com/[TU_ORG]/barcelona-housing-demographics-analyzer/issues/202`
2. O busca "Issue #202" en el repositorio

### Paso 3: Publicar el Comentario

1. Haz scroll hasta el final de los comentarios existentes
2. Haz clic en el campo de texto "Write" (escribir comentario)
3. Pega el contenido copiado
4. **Revisa** que el formato se vea correcto (preview)
5. Haz clic en **"Comment"** (Comentar)

### Paso 4: Verificar Publicación

1. Confirma que el comentario aparece publicado
2. Verifica que los links a archivos funcionan correctamente
3. Verifica que el formato markdown se renderiza bien

---

## ✅ Checklist Pre-Publicación

Antes de publicar, verifica:

- [ ] El comentario incluye la fecha correcta (19/12/2025)
- [ ] Los links a archivos usan rutas relativas correctas
- [ ] Las referencias a issues usan formato `#número`
- [ ] El formato markdown es correcto (emojis, listas, código)
- [ ] No hay información sensible (API keys, tokens, etc.)

---

## 🎯 Mejores Prácticas Aplicadas

El comentario sigue estas mejores prácticas:

### ✅ Estructura Clara
- Encabezados jerárquicos (`##`, `###`)
- Secciones bien definidas (Completado, Pendiente, Documentación)
- Uso consistente de emojis para estados

### ✅ Links Correctos
- Rutas relativas a archivos del repo: `../docs/archivo.md`
- Links a issues: `#202`, `#200`, `#201`
- URLs externas con formato markdown

### ✅ Información Accionable
- Próximos pasos claros y numerados
- Fechas y plazos específicos
- Referencias a scripts y archivos concretos

### ✅ Trazabilidad
- Referencias a issues relacionadas
- Links a documentación completa
- Historial de cambios (problema resuelto)

### ✅ Formato Consistente
- Uso de checkboxes para estados: ✅ ⏳
- Código en bloques con backticks
- Listas ordenadas para pasos secuenciales

---

## 🔄 Actualización Futura

Cuando recibas el XML de salida:

1. **Actualiza el comentario** añadiendo una nueva sección al final:
   ```markdown
   ---
   
   ## 📥 XML Recibido (20/12/2025)
   
   - ✅ XML descargado: `ECLTI250200147801.XML`
   - ✅ Tamaño: [X] bytes
   - ⏳ Próximo: Parsear XML
   ```

2. O crea un **nuevo comentario** con el update (mejor para historial)

---

## 📝 Notas Adicionales

### Si el Issue #202 no existe:
1. Crea el issue primero usando el template apropiado
2. Luego publica el comentario

### Si quieres mencionar a alguien:
Añade `@username` en el comentario para notificar

### Si quieres añadir labels:
Después de publicar, edita el issue y añade labels relevantes:
- `spike`
- `fase-2`
- `catastro`
- `in-progress`

---

## 🆘 Troubleshooting

**Problema**: Los links no funcionan
- **Solución**: Verifica que las rutas relativas sean correctas desde la raíz del repo

**Problema**: El formato markdown no se renderiza
- **Solución**: Verifica que no haya caracteres especiales sin escapar

**Problema**: No puedo comentar en el issue
- **Solución**: Verifica permisos del repositorio o contacta al maintainer

---

**Última actualización**: 2025-12-19

