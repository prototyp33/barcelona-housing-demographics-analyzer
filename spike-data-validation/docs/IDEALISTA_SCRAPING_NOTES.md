# Notas sobre Scraping Idealista

**Fecha**: 2025-12-19  
**Issue**: #202 - Fase 2  
**Estado**: ⚠️ Bloqueo anti-bot detectado

---

## Problema Identificado

Idealista está usando protección Cloudflare que detecta y bloquea automatización:

- **Síntoma**: El script no encuentra propiedades (0 URLs extraídas)
- **Causa**: Cloudflare detecta Playwright y muestra página de verificación
- **Evidencia**: HTML contiene scripts de protección (`data-cfasync`, hash de seguridad)

---

## Soluciones Alternativas

### Opción 1: API Oficial de Idealista ✅ RECOMENDADO

**Ventajas**:
- ✅ No hay bloqueos anti-bot
- ✅ Datos estructurados y limpios
- ✅ Más rápido y confiable

**Limitaciones**:
- ⚠️ Límite: 150 calls/mes (según reglas del proyecto)
- ⚠️ Requiere credenciales API

**Implementación**:
- Usar `src/extraction/idealista.py` (ya existe)
- Configurar `IDEALISTA_API_KEY` y `IDEALISTA_API_SECRET`
- Hacer búsqueda por coordenadas de Gràcia

**Ejemplo**:
```python
from src.extraction.idealista import IdealistaExtractor

extractor = IdealistaExtractor()
df, metadata = extractor.search_properties(
    operation="sale",
    location="Barcelona/Gracia",
    max_items=100
)
```

---

### Opción 2: Scraping Mejorado (Actual)

**Mejoras aplicadas**:
- ✅ Delays más largos (5-8 segundos iniciales)
- ✅ Detección de página Cloudflare
- ✅ Múltiples selectores CSS
- ✅ Stealth mode (ocultar webdriver)

**Limitaciones**:
- ⚠️ Puede seguir siendo bloqueado
- ⚠️ Requiere ajustes manuales frecuentes
- ⚠️ No escalable

**Uso**:
```bash
# Modo debugging (headless=False para ver qué pasa)
python3 spike-data-validation/scripts/fase2/scrape_idealista_gracia.py \
    --max-properties 50 \
    --max-pages 3
```

---

### Opción 3: Datasets Existentes

Si hay datasets de Idealista ya extraídos en el proyecto:
- Buscar en `data/raw/idealista/`
- Usar datos históricos si están disponibles
- Validar que sean de Gràcia y recientes

---

## Recomendación para Spike

**Para validación rápida (spike)**:
1. **Usar API oficial** si hay credenciales disponibles
2. Si no hay API, usar **datos de prueba/simulados** para validar el pipeline
3. Dejar scraping web para producción con mejor infraestructura

**Para producción**:
- Implementar rotación de proxies
- Usar servicios de scraping gestionados
- O negociar acceso API con Idealista

---

## Próximos Pasos

1. ✅ Verificar si hay credenciales API de Idealista disponibles
2. ⏳ Si hay API: Usar `IdealistaExtractor` para obtener datos
3. ⏳ Si no hay API: Considerar datos de prueba para validar matching
4. ⏳ Documentar decisión en Issue #202

---

**Última actualización**: 2025-12-19

