# Prompt para Comet AI - Extracción Idealista

## 📋 Prompt Principal

```
Rol: Actúa como un experto en Ingeniería de Datos y Automatización Web (Web Scraping).

Contexto: Estoy navegando en la pestaña actual de Idealista (página de resultados de búsqueda de propiedades) y necesito extraer información estructurada de todas las propiedades listadas en esta página.

He adjuntado un documento ("La Guía") que contiene las especificaciones técnicas, selectores CSS y reglas de extracción de los datos que necesito.

Instrucciones:

1. Analiza la Guía Adjunta:
   - Revisa el documento adjunto para entender qué campos específicos necesito extraer
   - Identifica los selectores CSS proporcionados para cada campo
   - Comprende las reglas de limpieza y transformación de datos
   - Nota las reglas de exclusión (anuncios patrocinados, sin precio, etc.)

2. Analiza el DOM de la Pestaña Actual:
   - Escanea el código HTML y la estructura visual de la página de Idealista que tengo abierta
   - Identifica todos los contenedores de propiedades (`article.item` o `div.item-info-container`)
   - Verifica que la estructura HTML coincida con la descrita en la guía

3. Mapeo y Extracción:
   - Para cada propiedad encontrada en la página:
     a. Localiza el contenedor principal (`article.item`)
     b. Extrae cada campo según los selectores CSS de la guía
     c. Aplica las reglas de limpieza especificadas (remover símbolos, convertir tipos, etc.)
     d. Valida que no sea un anuncio patrocinado (excluir si lo es)
     e. Valida que tenga precio (excluir si no lo tiene)
   - Si un campo no existe en una propiedad específica, usa `null` pero no detengas la extracción

4. Formato de Salida:
   - Devuélveme los datos extraídos en un bloque de código formato JSON
   - Un array JSON con un objeto por cada propiedad extraída
   - Estructura exacta según el ejemplo de la guía

Estructura esperada del JSON:

```json
[
  {
    "precio": 950,
    "superficie_m2": 45.0,
    "habitaciones": 2,
    "banos": 1,
    "localidad": "calle de Antonio López, Comillas",
    "link": "https://www.idealista.com/inmueble/107189787/",
    "descripcion": "Piso REFORMADO de 45m2...",
    "detalles": "Bajo interior con ascensor"
  }
]
```

Notas Importantes:
- Si encuentras algún elemento de la guía que no existe en esta página específica, déjalo como `null`, pero no te detengas
- Aplica TODAS las reglas de limpieza especificadas en la guía (remover símbolos €, puntos de miles, convertir tipos, etc.)
- Excluye anuncios patrocinados (`article.adv` o `article.noHover`)
- Solo incluye propiedades que tengan precio válido
- Si el link es relativo (empieza con "/"), conviértelo a absoluto agregando "https://www.idealista.com"
- Extrae la localidad del atributo `title` del link, NO del texto visible
```

---

## 📄 Documento a Adjuntar

Adjunta el archivo: `COMET_AI_GUIA_EXTRACCION.md`

Este documento contiene:
- Selectores CSS específicos para cada campo
- Reglas de limpieza y transformación
- Estructura HTML esperada
- Reglas de exclusión
- Ejemplos de formato de salida

---

## 🎯 Cómo Usar

1. **Abre Comet AI** en tu navegador
2. **Navega a Idealista**: https://www.idealista.com/venta-viviendas/barcelona/gracia/
3. **Adjunta la Guía**: Sube el archivo `COMET_AI_GUIA_EXTRACCION.md`
4. **Copia y pega el prompt**: Usa el prompt principal de arriba
5. **Ejecuta**: Comet AI analizará la página y extraerá los datos

---

## ✅ Validación del Resultado

**Verifica que el JSON tenga**:
- ✅ Array con múltiples objetos (una propiedad por objeto)
- ✅ Campo `precio` como número entero (sin decimales)
- ✅ Campo `superficie_m2` como número float (puede tener decimales)
- ✅ Campo `link` como URL absoluta (empieza con "https://")
- ✅ Campo `localidad` sin prefijos como "Piso en " o "Casa en "
- ✅ Sin anuncios patrocinados incluidos
- ✅ Campos opcionales pueden ser `null` si no existen

**Ejemplo de salida válida**:
```json
[
  {
    "precio": 950,
    "superficie_m2": 45.0,
    "habitaciones": 2,
    "banos": 1,
    "localidad": "calle de Antonio López, Comillas",
    "link": "https://www.idealista.com/inmueble/107189787/",
    "descripcion": "Piso REFORMADO de 45m2...",
    "detalles": "Bajo interior con ascensor"
  },
  {
    "precio": 250000,
    "superficie_m2": 80.5,
    "habitaciones": 3,
    "banos": 2,
    "localidad": "calle Amador Valdés, Ventas",
    "link": "https://www.idealista.com/inmueble/107139428/",
    "descripcion": "Vivienda reformada de 50m2...",
    "detalles": "Bajo exterior sin ascensor"
  }
]
```

---

## 🔧 Troubleshooting

**Si Comet AI no encuentra propiedades**:
- Verifica que estés en una página de resultados (no en detalle de propiedad)
- Verifica que la página haya cargado completamente
- Revisa si hay CAPTCHA o bloqueo (puede que necesites resolverlo primero)

**Si faltan campos**:
- Verifica que los selectores CSS de la guía coincidan con la estructura HTML actual
- Algunos campos pueden no existir en todas las propiedades (usar `null`)

**Si los datos están mal formateados**:
- Verifica que se apliquen las reglas de limpieza (remover símbolos €, puntos, etc.)
- Verifica que los tipos sean correctos (números, no strings)

---

**Última actualización**: 2025-12-20

