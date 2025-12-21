# Alternativa: Selenium con Firefox para Idealista

**Fecha**: 2025-12-19  
**Issue**: #202 - Fase 2  
**Referencia**: 
- Video: https://www.youtube.com/watch?v=I6Q4B4CSPtU
- Repositorio: https://github.com/JuanPMC/comprar_casa

---

## 🎯 Nueva Alternativa: Selenium + Firefox

Según el video tutorial, el autor **sustituye `requests` por Selenium con Firefox** hacia el final del tutorial porque:

> "Esto hace que la petición sea mucho más realista y eficaz para evitar bloqueos"

**Diferencia clave vs Playwright**:
- Selenium usa drivers de navegadores reales (Firefox, Chrome)
- Puede ser más difícil de detectar que Playwright
- El video específicamente recomienda Firefox

---

## 🔧 Implementación

### **Script Creado**: `scrape_idealista_selenium.py`

**Características**:
- ✅ Usa Selenium con Firefox
- ✅ Opciones para evitar detección:
  - `dom.webdriver.enabled = False`
  - `useAutomationExtension = False`
  - User-Agent realista
- ✅ Delays aleatorios entre requests
- ✅ Espera explícita de elementos (WebDriverWait)
- ✅ Manejo de errores robusto

### **Estructura HTML según Video**

El video menciona usar:
- `item-info-container`: Contenedor principal
- `item-detail`: Detalles (habitaciones, m²)
- `item-price`: Precio
- `item-link`: URL del anuncio

---

## 📋 Próximos Pasos

### **Paso 1: Instalar Selenium**

```bash
pip install selenium
```

**Nota**: También necesitas `geckodriver` para Firefox:
- macOS: `brew install geckodriver`
- Linux: Descargar de https://github.com/mozilla/geckodriver/releases
- Windows: Descargar y añadir al PATH

### **Paso 2: Probar Script**

```bash
# Modo headless (recomendado)
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py --max-pages 2

# Modo visible (para debugging)
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py --max-pages 2 --no-headless
```

### **Paso 3: Comparar Resultados**

Comparar con métodos anteriores:
- Playwright: ❌ Bloqueado
- BeautifulSoup: ❌ HTTP 403
- Selenium: ⏳ Por probar

---

## ⚠️ Consideraciones

### **Ventajas de Selenium**

1. ✅ Navegador real (más difícil de detectar)
2. ✅ Ejecuta JavaScript completo
3. ✅ Puede manejar contenido dinámico
4. ✅ Video específicamente lo recomienda

### **Desventajas**

1. ⚠️ Más lento que requests/BeautifulSoup
2. ⚠️ Requiere geckodriver instalado
3. ⚠️ Puede seguir siendo bloqueado si Idealista detecta automatización

---

## 🔍 Diferencias vs Playwright

| Aspecto | Playwright | Selenium |
|---------|------------|----------|
| **Driver** | Propio (Chromium) | Navegador real (Firefox) |
| **Detección** | Más fácil de detectar | Más difícil (navegador real) |
| **Velocidad** | Rápido | Más lento |
| **Instalación** | `pip install playwright` | `pip install selenium` + geckodriver |
| **Recomendación video** | No mencionado | ✅ Recomendado |

---

## 📝 Notas del Video

**Puntos clave**:
1. **Generar URLs dinámicamente** para recorrer páginas
2. **Usar BeautifulSoup** para parsear HTML (aunque con Selenium también se puede usar)
3. **Delays aleatorios** entre peticiones
4. **Headers realistas** (aunque con Selenium el navegador ya los proporciona)
5. **Selenium con Firefox** es más efectivo que requests

---

## 🚀 Ejecución

### **Requisitos Previos**

```bash
# Instalar Selenium
pip install selenium

# Instalar geckodriver (macOS)
brew install geckodriver

# O descargar manualmente:
# https://github.com/mozilla/geckodriver/releases
```

### **Ejecutar Script**

```bash
# Test con 1 página
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py --max-pages 1

# Extracción completa (3 páginas)
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py --max-pages 3
```

---

## 📊 Resultados Esperados

Si funciona, deberíamos obtener:
- ✅ Propiedades extraídas (sin HTTP 403)
- ✅ Datos: precio, superficie, habitaciones, dirección
- ✅ CSV guardado: `idealista_gracia_selenium.csv`

Si falla:
- ❌ Puede seguir siendo bloqueado (Cloudflare u otro)
- ❌ Puede necesitar ajustes en selectores CSS
- ❌ Puede necesitar más delays o configuración

---

## 🔗 Referencias

- **Video tutorial**: https://www.youtube.com/watch?v=I6Q4B4CSPtU
- **Repositorio GitHub**: https://github.com/JuanPMC/comprar_casa
- **Script creado**: `spike-data-validation/scripts/fase2/scrape_idealista_selenium.py`

---

**Última actualización**: 2025-12-19

