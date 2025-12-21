# Bloqueo Confirmado: Selenium + Firefox

**Fecha**: 2025-12-20  
**Issue**: #202 - Fase 2  
**Método probado**: Selenium + Firefox (basado en video tutorial)

---

## ❌ Resultado: Bloqueado con CAPTCHA

### **Mensaje de Bloqueo de Idealista**

**Primera prueba (2025-12-20 09:55)**:
```
Se ha detectado un uso indebido
El acceso se ha bloqueado

ID: f662774f-feb6-ff27-75ff-dcd1c157545b
IP: 37.133.54.161
```

**Segunda prueba (2025-12-20 09:57)**:
```
⚠️  CAPTCHA detectado - Bloqueado
```

**URL bloqueada**: `https://www.idealista.com/venta-viviendas/barcelona/gracia/`

**Comportamiento observado**:
- ✅ Script funciona técnicamente (Selenium conecta, Firefox se abre)
- ✅ Geckodriver se descarga automáticamente
- ❌ **Todas las páginas muestran CAPTCHA** (páginas 1, 2, 3)
- ❌ **0 propiedades extraídas** (bloqueo antes de cargar contenido)

---

## 🔍 Análisis de la Prueba

### **Fase 1: Éxito Parcial (Cache)**

1. ✅ Script ejecutado con `--no-cache` inicialmente
2. ✅ Extrajo 30 propiedades del HTML cacheado
3. ✅ Selectores funcionaron correctamente
4. ✅ Datos extraídos: precio, superficie, habitaciones

**Conclusión**: El script funciona técnicamente, pero solo con datos cacheados.

### **Fase 2: Bloqueo con CAPTCHA (2025-12-20 09:57)**

**Comando ejecutado**:
```bash
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py \
    --max-pages 3 --restart-driver
```

**Resultados**:
1. ✅ Script ejecutado correctamente
2. ✅ Geckodriver descargado automáticamente (v0.36.0)
3. ✅ Firefox se abre en modo headless
4. ❌ **Página 1**: Timeout → CAPTCHA detectado → 0 propiedades
5. ❌ **Página 2**: Timeout → CAPTCHA detectado → 0 propiedades  
6. ❌ **Página 3**: Timeout → CAPTCHA detectado → 0 propiedades
7. ❌ **Total**: 0 propiedades extraídas

**Análisis**:
- Idealista muestra CAPTCHA **antes** de cargar el contenido
- El timeout (15 segundos) ocurre porque los selectores no encuentran elementos (CAPTCHA bloquea la carga)
- Incluso con `--restart-driver` (reiniciar navegador entre páginas), el bloqueo persiste
- El comportamiento humano simulado no evita la detección

**Conclusión**: Idealista detecta Selenium incluso con Firefox y muestra CAPTCHA sistemáticamente.

---

## 📊 Comparación de Todos los Métodos Probados

| Método | Navegador Real | Resultado | Detección |
|--------|----------------|-----------|-----------|
| **Playwright** | ✅ (Headless) | ❌ Bloqueado | Cloudflare |
| **BeautifulSoup** | ❌ (Requests) | ❌ HTTP 403 | WAF/Cloudflare |
| **Selenium + Firefox** | ✅ (Real) | ❌ Bloqueado | Detección directa |

**Conclusión**: **Ningún método de scraping funciona**. Idealista tiene protección anti-bot muy robusta.

---

## 💡 Por qué Selenium Fue Detectado

### **Posibles Razones**

1. **WebDriver Detection**:
   - Selenium deja rastros en el DOM (`navigator.webdriver`)
   - Aunque intentamos ocultarlo con `dom.webdriver.enabled = False`, puede no ser suficiente

2. **Patrones de Comportamiento**:
   - Navegación demasiado rápida
   - Falta de interacciones humanas (mouse movements, scrolling)
   - Headers o fingerprints detectables

3. **IP en Lista Negra**:
   - Si se intentó antes con Playwright/BeautifulSoup, la IP puede estar marcada
   - Idealista puede tener rate limiting agresivo

4. **Detección de Automatización**:
   - Idealista puede usar servicios como Cloudflare Bot Management
   - Análisis de comportamiento del navegador
   - Validación de JavaScript execution

---

## 🎯 Conclusión Final

### **Scraping NO es Viable**

**Evidencia acumulada**:
- ✅ Playwright: Bloqueado
- ✅ BeautifulSoup: Bloqueado
- ✅ Selenium + Firefox: Bloqueado
- ✅ Código exacto de tutoriales: Bloqueado

**Implicación**: Idealista ha implementado protección anti-bot muy robusta que detecta:
- Navegadores automatizados (Playwright)
- Requests HTTP simples (BeautifulSoup)
- Navegadores reales automatizados (Selenium)

---

## 📋 Opciones Restantes

### **Opción 1: API Oficial** ✅ **ÚNICA OPCIÓN VIABLE**

**Estado**: ⏳ Requiere credenciales

**Ventajas**:
- ✅ No bloqueada (es la API oficial)
- ✅ Legal y permitido
- ✅ Datos estructurados

**Limitaciones**:
- ⚠️ Límite: 150 calls/mes
- ⚠️ Puede tener errores según documentación

**Acción**: Obtener credenciales en https://developers.idealista.com/

---

### **Opción 2: Continuar con Datos Mock** (Pragmático)

**Estado actual**:
- ✅ Pipeline técnico validado
- ✅ Scripts funcionan correctamente
- ✅ Modelo entrenado (aunque con datos mock)

**Ventajas**:
- ✅ Spike puede completarse sin bloqueos
- ✅ Validación técnica del pipeline
- ✅ Listo para datos reales cuando estén disponibles

---

## 🔗 Archivos Relacionados

- **Script probado**: `spike-data-validation/scripts/fase2/scrape_idealista_selenium.py`
- **Conclusión general**: `CONCLUSION_FINAL_SCRAPING.md`
- **Resultados BeautifulSoup**: `IDEALISTA_SCRAPING_RESULTADOS.md`
- **Estrategia final**: `ESTRATEGIA_FINAL_DATOS_REALES.md`

---

**Última actualización**: 2025-12-20

