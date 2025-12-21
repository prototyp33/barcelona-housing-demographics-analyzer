# Guía de Extracción - Idealista para Comet AI

**Objetivo**: Extraer listado de propiedades inmobiliarias de Idealista (página de resultados).

**Sitio**: https://www.idealista.com/venta-viviendas/barcelona/gracia/

---

## 📋 Campos a Extraer

### **1. Precio** 🔴 CRÍTICO
- **Selector CSS**: `span.item-price.h2-simulated` o `span.item-price`
- **Descripción**: Texto grande en negrita con el precio (ej: "950€/mes" o "250.000€")
- **Limpieza**: 
  - Remover símbolo "€" y texto después (ej: "/mes", "/año")
  - Remover puntos de miles (ej: "250.000" → "250000")
  - Remover comas decimales
  - Convertir a número entero
- **Ejemplo**: "950€/mes" → `950` o "250.000€" → `250000`

### **2. Superficie (m²)** 🔴 CRÍTICO
- **Selector CSS**: `div.item-detail-char > span.item-detail` (segundo span)
- **Descripción**: Texto que contiene "m²" (ej: "45 m²", "80 m²")
- **Limpieza**:
  - Extraer solo el número (puede tener decimales con coma o punto)
  - Convertir coma a punto si es necesario
  - Convertir a float
- **Ejemplo**: "45 m²" → `45.0` o "80,5 m²" → `80.5`

### **3. Habitaciones** 🟡 IMPORTANTE
- **Selector CSS**: `div.item-detail-char > span.item-detail` (primer span)
- **Descripción**: Texto que contiene "hab." o número de habitaciones (ej: "2 hab.", "3 hab.")
- **Limpieza**:
  - Extraer solo el número
  - Convertir a entero
- **Ejemplo**: "2 hab." → `2`

### **4. Baños** 🟡 IMPORTANTE
- **Selector CSS**: `div.item-detail-char > span.item-detail` (puede estar en diferentes posiciones)
- **Descripción**: Texto que contiene "baño" o "baños" (ej: "1 baño", "2 baños")
- **Limpieza**:
  - Extraer solo el número
  - Convertir a entero
- **Ejemplo**: "1 baño" → `1` o "2 baños" → `2`
- **Nota**: Puede no estar presente, usar `null` si no existe

### **5. Localidad/Dirección** 🔴 CRÍTICO
- **Selector CSS**: `a.item-link` (atributo `title`)
- **Descripción**: Dirección completa de la propiedad en el atributo `title` del link
- **Limpieza**:
  - Extraer del atributo `title` (NO del texto del link)
  - Remover prefijos como "Piso en " o "Casa en "
  - Tomar primeras 2 partes separadas por coma
- **Ejemplo**: `title="Piso en calle de Antonio López, Comillas, Madrid"` → `"calle de Antonio López, Comillas"`

### **6. Link** 🟡 IMPORTANTE
- **Selector CSS**: `a.item-link` (atributo `href`)
- **Descripción**: URL completa del anuncio
- **Limpieza**:
  - Si el href es relativo (empieza con "/"), agregar "https://www.idealista.com"
  - Si ya es absoluto, usar tal cual
- **Ejemplo**: "/inmueble/107189787/" → `"https://www.idealista.com/inmueble/107189787/"`

### **7. Descripción** 🟢 OPCIONAL
- **Selector CSS**: `div.item-description > p.ellipsis` o `div.item-description > p`
- **Descripción**: Texto descriptivo del anuncio (puede estar truncado con "...")
- **Limpieza**:
  - Extraer texto completo
  - Mantener tal cual (puede tener saltos de línea)
- **Ejemplo**: "Piso REFORMADO de 45m2 que consta de 2 habitaciones..."

### **8. Detalles Adicionales** 🟢 OPCIONAL
- **Selector CSS**: `div.item-detail-char > span.item-detail` (tercer span o posteriores)
- **Descripción**: Información adicional como "Bajo interior con ascensor", "Planta 4ª exterior", etc.
- **Limpieza**:
  - Extraer texto completo
  - Puede ser múltiples spans, unirlos con espacio
- **Ejemplo**: "Bajo interior con ascensor" o "Planta 4ª exterior sin ascensor"

---

## 🎯 Estructura del Contenedor

**Contenedor Principal**: 
- **Selector CSS**: `article.item` (preferido) o `div.item-info-container`
- **Nota**: Cada propiedad está en un `<article class="item">` separado

**Estructura HTML típica**:
```html
<article class="item">
  <div class="item-info-container">
    <a class="item-link" href="/inmueble/..." title="Piso en...">
      Título
    </a>
    <span class="item-price h2-simulated">950<span class="txt-big">€/mes</span></span>
    <div class="item-detail-char">
      <span class="item-detail">2 hab.</span>
      <span class="item-detail">45 m²</span>
      <span class="item-detail">Bajo interior con ascensor</span>
    </div>
    <div class="item-description">
      <p class="ellipsis">Descripción...</p>
    </div>
  </div>
</article>
```

---

## ⚠️ Reglas de Exclusión

1. **Anuncios Patrocinados**: 
   - Ignorar si contienen `class="adv"` o `class="noHover"` o texto "Publicidad"
   - Selector: `article.adv` o `article.noHover`

2. **Anuncios sin Precio**:
   - Si no se encuentra `span.item-price`, omitir la propiedad completa

3. **Anuncios sin Superficie**:
   - Si no se encuentra superficie en m², usar `null` pero no omitir la propiedad

4. **Duplicados**:
   - Si el mismo `link` aparece múltiples veces, solo extraer una vez

---

## 📊 Formato de Salida Esperado

**JSON Array** con un objeto por propiedad:

```json
[
  {
    "precio": 950,
    "superficie_m2": 45.0,
    "habitaciones": 2,
    "banos": 1,
    "localidad": "calle de Antonio López, Comillas",
    "link": "https://www.idealista.com/inmueble/107189787/",
    "descripcion": "Piso REFORMADO de 45m2 que consta de 2 habitaciones...",
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

**Notas**:
- Si un campo no existe, usar `null` (no omitir el campo)
- `precio` debe ser número entero (sin decimales)
- `superficie_m2` debe ser número float (puede tener decimales)
- `habitaciones` y `banos` deben ser números enteros o `null`
- `localidad`, `link`, `descripcion`, `detalles` deben ser strings o `null`

---

## 🔍 Selectores CSS Resumen

| Campo | Selector Principal | Selector Fallback |
|-------|-------------------|-------------------|
| **Contenedor** | `article.item` | `div.item-info-container` |
| **Precio** | `span.item-price.h2-simulated` | `span.item-price` |
| **Superficie** | `div.item-detail-char > span.item-detail:nth-child(2)` | `span.item-detail` (buscar el que contiene "m²") |
| **Habitaciones** | `div.item-detail-char > span.item-detail:nth-child(1)` | `span.item-detail` (buscar el que contiene "hab.") |
| **Baños** | `div.item-detail-char > span.item-detail` (buscar "baño") | Buscar en todos los spans |
| **Localidad** | `a.item-link[title]` | `a.item-link` (texto) |
| **Link** | `a.item-link[href]` | - |
| **Descripción** | `div.item-description > p.ellipsis` | `div.item-description > p` |
| **Detalles** | `div.item-detail-char > span.item-detail:nth-child(3+)` | Todos los spans después del segundo |

---

## ✅ Validaciones

**Antes de incluir una propiedad**:
- ✅ Debe tener `precio` (no null)
- ✅ Debe tener `link` (no null)
- ✅ No debe ser anuncio patrocinado (`article.adv`)

**Campos opcionales** (pueden ser null):
- `superficie_m2`
- `habitaciones`
- `banos`
- `descripcion`
- `detalles`

---

**Última actualización**: 2025-12-20  
**Basado en**: Estructura HTML real de Idealista (diciembre 2025)

