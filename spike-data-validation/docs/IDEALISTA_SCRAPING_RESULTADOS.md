# Resultados: Scraping Idealista (BeautifulSoup)

**Fecha**: 2025-12-19  
**Issue**: #202 - Fase 2  
**Método probado**: BeautifulSoup + requests

---

## ❌ Resultado: Bloqueado (HTTP 403)

### **Pruebas Realizadas**

1. **Test con nuestro script** (`--test-mode`):
   ```
   Error HTTP 403 en página 1
   Total propiedades extraídas: 0
   ```

2. **Test con 5 páginas**:
   ```
   Error HTTP 403 en todas las páginas (1-5)
   Total propiedades extraídas: 0
   ```

3. **Test con código exacto del artículo Octoparse**:
   ```
   Madrid (ejemplo del artículo): HTTP 403 ❌
   Gràcia (nuestro objetivo): HTTP 403 ❌
   ```
   
   **Conclusión**: Incluso el código exacto del artículo falla, confirmando que Idealista ha reforzado su protección desde que se escribió el artículo.

### **Análisis del Error**

**HTTP 403 Forbidden** significa que Idealista está:
- ✅ Detectando peticiones automatizadas
- ✅ Bloqueando activamente el acceso
- ✅ Usando protección anti-bot más agresiva de lo esperado

**Causa probable**:
- Cloudflare o similar detectando patrones de requests
- Headers insuficientes para pasar validación
- IP puede estar en lista negra (si se intentó antes con Playwright)

---

## 🔍 Comparación de Métodos Probados

| Método | Estado | Error | Conclusión |
|--------|--------|-------|------------|
| **Playwright** | ❌ Bloqueado | Cloudflare detection | Navegador detectado como bot |
| **BeautifulSoup** | ❌ Bloqueado | HTTP 403 | Requests simples también bloqueados |
| **Selenium + Firefox** | ❌ Bloqueado | "Uso indebido detectado" | Incluso navegador real es detectado |
| **API Oficial** | ⏳ No probado | Requiere credenciales | Única opción viable restante |

---

## 💡 Conclusión

**Idealista tiene protección anti-bot muy agresiva** que bloquea:
- ✅ Navegadores automatizados (Playwright)
- ✅ Requests HTTP simples (BeautifulSoup)
- ✅ Navegadores reales automatizados (Selenium + Firefox)
- ✅ Incluso con headers realistas y delays

**Implicación**: El artículo de Octoparse está **desactualizado**. El código exacto del artículo también falla con HTTP 403, confirmando que Idealista ha reforzado significativamente su protección anti-bot desde que se escribió el artículo.

---

## 🎯 Opciones Restantes

### **Opción 1: API Oficial** ✅ **ÚNICA OPCIÓN VIABLE**

**Estado**: ⏳ Requiere credenciales

**Ventajas**:
- ✅ No hay bloqueos (es la API oficial)
- ✅ Datos estructurados
- ✅ Legal y permitido

**Limitaciones** (según artículo):
- ⚠️ "Suele dar muchos errores de respuesta"
- ⚠️ "Es muy limitado"
- ⚠️ Límite: 150 calls/mes

**Acción**: Obtener credenciales en https://developers.idealista.com/

---

### **Opción 2: Proxies Rotativos** (Complejo)

**Requisitos**:
- Servicio de proxies rotativos
- Manejo de sesiones
- Más complejidad técnica

**Costo**: Servicios de proxies pueden ser costosos

**Recomendación**: No viable para un spike de validación

---

### **Opción 3: Servicios de Scraping Gestionados** (Costoso)

**Ejemplos**:
- ScraperAPI
- Bright Data
- Apify

**Costo**: Generalmente de pago

**Recomendación**: No viable para un spike de validación

---

### **Opción 4: Continuar con Datos Mock** (Pragmático)

**Estado actual**:
- ✅ Pipeline técnico validado
- ✅ Scripts funcionan correctamente
- ✅ Modelo entrenado (aunque con bajo rendimiento esperado)

**Ventajas**:
- ✅ Spike puede completarse sin bloqueos
- ✅ Validación técnica del pipeline
- ✅ Listo para datos reales cuando estén disponibles

**Limitación**:
- ⚠️ Resultados no representativos del mercado real

---

## 📋 Recomendación Final

### **Para el Spike (Validación Técnica)**

**Opción recomendada**: **Continuar con datos mock** y documentar que:
1. ✅ Pipeline técnico está validado y funciona
2. ✅ Scripts están listos para datos reales
3. ⚠️ Idealista bloquea scraping (Playwright y BeautifulSoup)
4. ⏳ API oficial requiere credenciales (puede tener errores según artículo)

**Justificación**:
- El objetivo del spike es **validar viabilidad técnica**, no optimizar métricas
- Los datos mock permiten validar todo el pipeline
- Cuando lleguen credenciales API, se puede re-entrenar con datos reales

---

### **Para Producción**

**Opción recomendada**: **API Oficial de Idealista**

**Pasos**:
1. Obtener credenciales API
2. Implementar manejo robusto de errores (según artículo, "suele dar muchos errores")
3. Implementar retry logic
4. Validar que funciona mejor que mock

---

## 🔄 Próximos Pasos

### **Inmediato**

1. ✅ Documentar que scraping no es viable (este documento)
2. ✅ Actualizar estrategia en `RESUMEN_ESTADO_FASE2.md`
3. ⏳ Decidir: ¿Continuar con mock o esperar API?

### **Si se Obtienen Credenciales API**

1. ⏳ Probar `extract_idealista_api_gracia.py`
2. ⏳ Manejar errores según artículo ("suele dar muchos errores")
3. ⏳ Re-entrenar modelo con datos reales
4. ⏳ Comparar mock vs real

---

## 📝 Notas Técnicas

### **Por qué HTTP 403**

Idealista probablemente usa:
- Cloudflare u otro WAF (Web Application Firewall)
- Detección de patrones de requests
- Rate limiting agresivo
- Validación de headers/cookies

**Solución requerida** (si se quiere scraping):
- Rotación de proxies
- Manejo de cookies/sesiones
- Headers más sofisticados
- Delays más largos
- Posiblemente resolver CAPTCHAs

**Complejidad**: Alta, no viable para spike

---

## 🔗 Referencias

- Script probado: `spike-data-validation/scripts/fase2/scrape_idealista_beautifulsoup.py`
- Artículo original: https://www.octoparse.es/blog/como-extraer-los-datos-de-idealista-con-web-scraping
- Nota: El artículo puede estar desactualizado o Idealista ha reforzado protección

---

**Última actualización**: 2025-12-19

