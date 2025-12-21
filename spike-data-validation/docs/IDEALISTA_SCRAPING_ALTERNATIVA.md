# Alternativa: Web Scraping Idealista (Sin API)

**Fecha**: 2025-12-19  
**Issue**: #202 - Fase 2  
**Referencia**: [Octoparse - Cómo extraer datos de Idealista](https://www.octoparse.es/blog/como-extraer-los-datos-de-idealista-con-web-scraping)

---

## 🎯 Contexto

Según el artículo de Octoparse, la **API oficial de Idealista suele dar muchos errores y es muy limitada**. Esto explica por qué estamos teniendo dificultades con las credenciales API.

**Alternativa viable**: Web scraping con BeautifulSoup (más simple que Playwright)

---

## ⚖️ Legalidad del Scraping

Según el artículo:

> **Es legal scrapear los datos públicos de Idealista.com**; es perfectamente legal y ético rastrear los datos de Idealista.com de forma lenta y razonable.

**Consideraciones**:
- ✅ Datos públicos son legales de scrapear
- ⚠️ Respetar GDPR al capturar datos personales (nombres, teléfonos)
- ⚠️ Hacer scraping de forma lenta y razonable (evitar bloqueos)
- ⚠️ Cumplir con términos de servicio de Idealista

---

## 🔧 Implementación con BeautifulSoup

### **Ventajas vs Playwright**

| Aspecto | Playwright | BeautifulSoup |
|---------|------------|---------------|
| **Complejidad** | Alta (navegador completo) | Baja (solo parsing HTML) |
| **Detección anti-bot** | Alta (detecta automatización) | Baja (solo requests HTTP) |
| **Velocidad** | Lenta (carga JS completo) | Rápida (solo HTML) |
| **Memoria** | Alta | Baja |
| **Mantenimiento** | Alto (estructura JS cambia) | Medio (estructura HTML cambia) |

### **Código Base (del artículo)**

```python
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd

def scrape_idealista_gracia(max_pages: int = 3) -> pd.DataFrame:
    """
    Scrapea datos de Idealista para Gràcia usando BeautifulSoup.
    
    Args:
        max_pages: Número máximo de páginas a scrapear
        
    Returns:
        DataFrame con propiedades extraídas
    """
    base_url = 'https://www.idealista.com/venta-viviendas/barcelona/gracia/'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    properties = []
    
    for page in range(1, max_pages + 1):
        url = f"{base_url}?pagina={page}"
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar listings (estructura puede variar)
                listings = soup.find_all('article', class_='item')
                
                for listing in listings:
                    try:
                        # Extraer datos (ajustar selectores según estructura real)
                        title_elem = listing.find('a', class_='item-link')
                        price_elem = listing.find('span', class_='item-price')
                        location_elem = listing.find('span', class_='item-detail')
                        
                        if title_elem and price_elem:
                            properties.append({
                                'title': title_elem.get_text(strip=True),
                                'price': price_elem.get_text(strip=True),
                                'location': location_elem.get_text(strip=True) if location_elem else '',
                                'url': title_elem.get('href', '') if title_elem else '',
                            })
                    except Exception as e:
                        logger.warning(f"Error extrayendo listing: {e}")
                        continue
                
                # Delay entre páginas (importante para evitar bloqueos)
                time.sleep(3)  # 3 segundos entre páginas
                
            else:
                logger.warning(f"Error HTTP {response.status_code} en página {page}")
                
        except Exception as e:
            logger.error(f"Error scrapeando página {page}: {e}")
            continue
    
    return pd.DataFrame(properties)
```

---

## 📋 Plan de Implementación

### **Paso 1: Crear Script BeautifulSoup**

**Archivo**: `spike-data-validation/scripts/fase2/scrape_idealista_beautifulsoup.py`

**Características**:
- ✅ Usar `requests` + `BeautifulSoup` (más simple que Playwright)
- ✅ Headers realistas para evitar detección
- ✅ Delays entre requests (3-5 segundos)
- ✅ Manejo de errores robusto
- ✅ Extracción de campos clave: precio, superficie, dirección, URL

### **Paso 2: Probar con Página de Prueba**

```bash
# Test con una sola página
python3 spike-data-validation/scripts/fase2/scrape_idealista_beautifulsoup.py \
  --max-pages 1 \
  --test-mode
```

### **Paso 3: Ajustar Selectores**

- Inspeccionar HTML real de Idealista
- Ajustar selectores CSS según estructura actual
- Validar que se extraen todos los campos necesarios

### **Paso 4: Ejecutar Extracción Completa**

```bash
# Extracción completa (3-5 páginas)
python3 spike-data-validation/scripts/fase2/scrape_idealista_beautifulsoup.py \
  --max-pages 5 \
  --output spike-data-validation/data/processed/fase2/idealista_gracia_scraped.csv
```

---

## ⚠️ Consideraciones Importantes

### **1. Estructura HTML Puede Cambiar**

> **Nota del artículo**: La estructura HTML de la página web puede cambiar, por lo que es posible que tenga que ajustar los parámetros `find` o `find_all` en consecuencia.

**Solución**: 
- Validar selectores antes de ejecución completa
- Usar múltiples selectores como fallback
- Logging detallado para debugging

### **2. Evitar Bloqueos**

**Recomendaciones del artículo**:
- ✅ Delays entre requests (3-5 segundos mínimo)
- ✅ Headers realistas (User-Agent de navegador real)
- ✅ No hacer scraping frecuente o a gran escala
- ✅ Respetar términos de servicio

### **3. Cumplimiento Legal**

- ✅ Solo datos públicos (no datos personales protegidos)
- ✅ Scraping lento y razonable
- ✅ No sobrecargar servidores
- ⚠️ Revisar términos de servicio de Idealista

---

## 🔄 Comparación de Métodos

| Método | Estado | Ventajas | Desventajas |
|--------|--------|----------|-------------|
| **API Oficial** | ⏳ Requiere credenciales | Datos estructurados, oficial | Errores frecuentes, limitado |
| **Playwright** | ❌ Bloqueado (Cloudflare) | JavaScript completo | Detectado como bot, lento |
| **BeautifulSoup** | ✅ **RECOMENDADO** | Simple, rápido, menos detección | HTML puede cambiar |

---

## 🚀 Próximos Pasos

### **Opción A: Implementar BeautifulSoup** (Recomendado)

1. ✅ Crear script `scrape_idealista_beautifulsoup.py`
2. ✅ Probar con página de prueba
3. ✅ Ajustar selectores según HTML real
4. ✅ Ejecutar extracción completa
5. ✅ Matching con Catastro
6. ✅ Re-entrenar modelo

### **Opción B: Continuar con API** (Si llegan credenciales)

1. ⏳ Esperar credenciales API
2. ⏳ Ejecutar `extract_idealista_api_gracia.py`
3. ⏳ Validar que funciona (puede tener errores según artículo)

### **Opción C: Híbrido**

1. ✅ Intentar API primero (si hay credenciales)
2. ✅ Si falla, usar BeautifulSoup como fallback
3. ✅ Combinar resultados si ambos funcionan

---

## 📝 Notas del Artículo

> **Sobre la API**: "Aunque idealista dispone de API para acceder a los datos, suele dar muchos errores de respuesta y es muy limitado."

**Implicación**: Incluso con credenciales, la API puede no ser confiable. BeautifulSoup es una alternativa más robusta.

---

## 🔗 Referencias

- [Artículo Octoparse](https://www.octoparse.es/blog/como-extraer-los-datos-de-idealista-con-web-scraping)
- Script actual: `spike-data-validation/scripts/fase2/scrape_idealista_gracia.py` (Playwright)
- Script API: `spike-data-validation/scripts/fase2/extract_idealista_api_gracia.py`

---

**Última actualización**: 2025-12-19

