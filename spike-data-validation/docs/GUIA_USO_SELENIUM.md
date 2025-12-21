# Guía de Uso: Scraping Idealista con Selenium

**Script**: `spike-data-validation/scripts/fase2/scrape_idealista_selenium.py`  
**Fecha**: 2025-01-19

---

## 📋 Requisitos Previos

### 1. Instalar Dependencias

```bash
# Instalar desde requirements.txt
pip install -r requirements.txt

# O instalar manualmente
pip install selenium beautifulsoup4 webdriver-manager pandas
```

### 2. Instalar Geckodriver (Firefox)

El script usa `webdriver-manager` que lo instala automáticamente, pero si prefieres instalarlo manualmente:

**macOS:**
```bash
brew install geckodriver
```

**Linux:**
```bash
# Descargar de: https://github.com/mozilla/geckodriver/releases
# Extraer y añadir al PATH
```

**Windows:**
- Descargar de: https://github.com/mozilla/geckodriver/releases
- Extraer `geckodriver.exe` y añadir al PATH

---

## 🚀 Uso Básico

### Ejemplo 1: Uso Mínimo (3 páginas, modo headless)

```bash
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py
```

**Salida por defecto:**
- `spike-data-validation/data/processed/fase2/idealista_gracia_selenium.csv`

### Ejemplo 2: Especificar Número de Páginas

```bash
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py --max-pages 5
```

### Ejemplo 3: Modo Visible con Resolución Manual de CAPTCHA

```bash
# IMPORTANTE: Usar --no-cache para forzar peticiones reales y abrir el navegador
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py \
    --max-pages 2 \
    --no-headless \
    --no-cache
```

**⚠️ Nota Importante**: Si no usas `--no-cache`, el script usará HTML cacheado (de ejecuciones anteriores) y **no abrirá el navegador**. Usa `--no-cache` para forzar peticiones reales.

**Características:**
- ✅ Navegador visible (puedes ver qué está pasando)
- ✅ **Espera automática para resolver CAPTCHA manualmente**
- ✅ El script detecta cuando resuelves el CAPTCHA y continúa automáticamente
- ✅ Timeout máximo: 5 minutos por CAPTCHA

**Cómo funciona:**
1. El script detecta CAPTCHA
2. Muestra mensaje: "🔒 CAPTCHA DETECTADO - Por favor, resuelve el CAPTCHA en el navegador visible"
3. **Tú resuelves el CAPTCHA en el navegador**
4. El script detecta automáticamente cuando el contenido se carga
5. Continúa con el scraping

**Útil para:**
- Resolver CAPTCHAs manualmente cuando aparecen
- Ver qué está haciendo el navegador
- Detectar problemas de bloqueo
- Verificar que los selectores funcionan

### Ejemplo 4: Sin Cache (forzar descarga fresca)

```bash
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py --max-pages 3 --no-cache
```

**Nota:** Por defecto, el script guarda HTML en cache para evitar peticiones innecesarias.

### Ejemplo 5: Reiniciar Driver entre Páginas (más seguro, más lento)

```bash
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py --max-pages 3 --restart-driver
```

**Ventaja:** Menos detectable (simula sesiones independientes)  
**Desventaja:** Más lento (cierra y reabre el navegador entre páginas)

### Ejemplo 6: Especificar Archivo de Salida

```bash
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py \
    --max-pages 5 \
    --output data/custom_output.csv
```

---

## 📊 Opciones Disponibles

| Opción | Descripción | Por Defecto |
|--------|-------------|-------------|
| `--max-pages N` | Número máximo de páginas a scrapear | `3` |
| `--no-headless` | Ejecutar con navegador visible | `False` (headless) |
| `--no-cache` | No usar cache HTML | `False` (usa cache) |
| `--restart-driver` | Reiniciar driver entre páginas | `False` |
| `--output PATH` | Ruta del archivo CSV de salida | `idealista_gracia_selenium.csv` |

---

## 📁 Estructura de Datos Extraídos

El script extrae las siguientes columnas:

| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| `precio` | Precio en euros (int) | `950` |
| `habitaciones` | Número de habitaciones | `2` |
| `superficie_m2` | Superficie en m² (float) | `45.0` |
| `localidad` | Dirección/localidad | `"calle de Antonio López, Comillas"` |
| `descripcion` | Descripción del anuncio | `"Piso REFORMADO de 45m2..."` |
| `link` | URL completa del anuncio | `"https://www.idealista.com/inmueble/107189787/"` |
| `detalles` | Detalles adicionales | `"Bajo interior con ascensor"` |
| `page` | Número de página | `1` |

---

## ⚙️ Configuración Avanzada

### Cambiar URL Base

Editar línea 51 en `scrape_idealista_selenium.py`:

```python
BASE_URL = "https://www.idealista.com/venta-viviendas/barcelona/gracia/"
```

**Ejemplos de URLs válidas:**
- Venta: `https://www.idealista.com/venta-viviendas/barcelona/gracia/`
- Alquiler: `https://www.idealista.com/alquiler-viviendas/barcelona/gracia/`
- Con filtros: Copiar URL después de aplicar filtros manualmente en el navegador

### Ajustar Delays

Editar líneas 53-59 en `scrape_idealista_selenium.py`:

```python
# Delays aleatorios entre páginas (segundos)
MIN_DELAY = 2.0
MAX_DELAY = 20.0

# Delays para comportamiento humano
MIN_HUMAN_DELAY = 3.0
MAX_HUMAN_DELAY = 8.0
```

---

## 🔍 Troubleshooting

### Error: "Selenium no está instalado"

```bash
pip install selenium
```

### Error: "geckodriver no encontrado"

El script usa `webdriver-manager` que lo instala automáticamente. Si falla:

```bash
# macOS
brew install geckodriver

# O instalar webdriver-manager
pip install webdriver-manager
```

### Error: "CAPTCHA detectado" / Bloqueado

**Síntomas:**
- El script muestra: "⚠️ CAPTCHA detectado - Bloqueado"
- El navegador muestra un CAPTCHA
- El script no extrae propiedades (0 extraídas)

**Solución Recomendada: Resolver CAPTCHA Manualmente**

```bash
# Ejecutar en modo visible para resolver CAPTCHA
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py \
    --max-pages 3 \
    --no-headless
```

**Proceso:**
1. El script detecta CAPTCHA y muestra mensaje
2. **Tú resuelves el CAPTCHA en el navegador visible**
3. El script detecta automáticamente cuando el contenido se carga
4. Continúa con el scraping

**Nota:** El script espera hasta 5 minutos por cada CAPTCHA. Si no lo resuelves a tiempo, continuará con la siguiente página.

**Otras Soluciones:**

1. **Usar `--restart-driver`** (reiniciar driver entre páginas):
   ```bash
   python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py --restart-driver --no-headless
   ```

2. **Aumentar delays** (editar `MIN_DELAY` y `MAX_DELAY` en el script)

3. **Esperar más tiempo** entre ejecuciones (Idealista puede bloquear IPs temporalmente)

4. **Usar VPN o cambiar IP** si el bloqueo persiste

### Error: "No se encontraron contenedores esperados"

**Causa:** La estructura HTML de Idealista cambió o los selectores CSS necesitan actualización.

**Solución:**
1. Ejecutar con `--no-headless` para ver la página
2. Inspeccionar HTML manualmente en el navegador
3. Ajustar selectores en `extract_property_data_from_html()` (línea 256)

### Error: "Timeout esperando contenido"

**Causa:** La página tarda mucho en cargar o hay problemas de red.

**Soluciones:**
1. Verificar conexión a internet
2. Aumentar timeout en `scrape_page()` (línea 501)
3. Usar `--no-cache` para forzar descarga fresca

---

## 📝 Ejemplos Completos

### Ejemplo Completo: Scraping Conservador

```bash
# Scrapear 2 páginas con todas las precauciones
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py \
    --max-pages 2 \
    --restart-driver \
    --no-headless \
    --output data/idealista_gracia_conservador.csv
```

**Características:**
- ✅ Reinicia driver entre páginas (menos detectable)
- ✅ Navegador visible (para monitorear)
- ✅ Delays aleatorios automáticos (2-20 segundos)
- ✅ Comportamiento humano simulado (scrolling, mouse movements)

### Ejemplo Completo: Scraping Rápido (con cache)

```bash
# Scrapear 5 páginas usando cache
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py \
    --max-pages 5 \
    --output data/idealista_gracia_rapido.csv
```

**Características:**
- ✅ Usa cache HTML (no re-descarga si ya existe)
- ✅ Modo headless (más rápido)
- ✅ Driver persistente (más rápido)

---

## 📊 Verificar Resultados

### Ver CSV Generado

```bash
# Ver primeras líneas
head -20 spike-data-validation/data/processed/fase2/idealista_gracia_selenium.csv

# Contar propiedades
wc -l spike-data-validation/data/processed/fase2/idealista_gracia_selenium.csv
```

### Analizar con Python

```python
import pandas as pd

df = pd.read_csv('spike-data-validation/data/processed/fase2/idealista_gracia_selenium.csv')
print(f"Total propiedades: {len(df)}")
print(f"\nEstadísticas de precios:")
print(df['precio'].describe())
print(f"\nPropiedades por página:")
print(df['page'].value_counts().sort_index())
```

---

## ⚠️ Advertencias Importantes

1. **Respetar Términos de Servicio**: Idealista puede bloquear IPs por scraping excesivo
2. **Delays Recomendados**: No reducir `MIN_DELAY` por debajo de 2 segundos
3. **Uso Responsable**: No scrapear más de 10-20 páginas por sesión
4. **Cache Útil**: Usar cache para desarrollo/testing (evita peticiones innecesarias)

---

## 🔗 Referencias

- **Script**: `spike-data-validation/scripts/fase2/scrape_idealista_selenium.py`
- **Video Tutorial**: https://www.youtube.com/watch?v=I6Q4B4CSPtU
- **Repositorio Referencia**: https://github.com/JuanPMC/comprar_casa
- **Documentación Selenium**: https://www.selenium.dev/documentation/
- **Webdriver Manager**: https://github.com/SergeyPirogov/webdriver_manager

