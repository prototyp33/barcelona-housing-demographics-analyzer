# Objetivos del Web Scraper - Idealista

**Fecha**: 2025-12-20  
**Proyecto**: Spike de Validación - Modelo Hedonic Pricing MICRO  
**Issue**: #202 - Fase 2  
**Script**: `spike-data-validation/scripts/fase2/scrape_idealista_selenium.py`

---

## 🎯 Contexto del Proyecto

### **Proyecto General: Barcelona Housing Demographics Analyzer**

Plataforma de análisis que combina datos demográficos y de mercado inmobiliario para los **73 barrios de Barcelona**, con enfoque especial en el **barrio de Gràcia** para validación técnica.

### **Spike de Validación: Modelo Hedonic Pricing MICRO**

**Objetivo del Spike**: Validar la viabilidad técnica de un modelo hedónico de precios a nivel **micro** (edificio individual) vs. nivel **macro** (agregado por barrio×año).

**Baseline Actual (MACRO)**:
- R² = 0.710
- RMSE = 323.47 €/m²
- Granularidad: `barrio_id × anio × dataset_id`

**Target (MICRO)**:
- R² ≥ 0.75
- RMSE ≤ 250 €/m²
- Sesgo < ±100 €/m²
- Granularidad: **Edificio individual**

---

## 🔍 Objetivos del Web Scraper

### **Objetivo Principal**

Extraer datos de **precios de mercado** de viviendas en el barrio de **Gràcia** desde el portal inmobiliario **Idealista** para alimentar un modelo hedónico de precios a nivel micro (edificio individual).

### **Objetivos Específicos**

#### 1. **Obtener Precios de Mercado Actuales**

**Qué buscamos**:
- Precios de venta/alquiler de viviendas en Gràcia
- Precios por metro cuadrado (`precio_m2`)
- Fechas de publicación (para análisis temporal)

**Por qué es necesario**:
- Los datos de **Portal Dades** (Issue #199) están agregados por barrio×año
- Necesitamos precios **individuales por propiedad** para el modelo MICRO
- Idealista es la fuente más completa de precios de mercado en tiempo real

**Resultado esperado**:
- Dataset con precios individuales por propiedad
- Mínimo: **50-100 propiedades** para entrenar el modelo
- Ideal: **200-500 propiedades** para mayor robustez

---

#### 2. **Extraer Características de las Propiedades**

**Qué buscamos**:
- **Superficie** (m²): Variable clave para normalizar precios
- **Habitaciones**: Número de dormitorios
- **Baños**: Número de baños
- **Características adicionales**: Ascensor, exterior, terraza, etc.
- **Dirección**: Para matching con datos de Catastro
- **Descripción**: Texto libre (puede contener información adicional)

**Por qué es necesario**:
- Estas características son **features** del modelo hedónico
- Permiten explicar la variabilidad de precios entre propiedades similares
- La dirección permite **matching** con datos de Catastro (Issue #200)

**Resultado esperado**:
- Dataset con características estructuradas por propiedad
- Completitud: ≥80% en campos críticos (precio, superficie, habitaciones)

---

#### 3. **Facilitar Matching con Datos de Catastro**

**Qué buscamos**:
- **Dirección completa**: Calle, número, barrio
- **Link del anuncio**: Para validación manual si es necesario
- **Coordenadas** (si disponibles): Para matching espacial

**Por qué es necesario**:
- Los datos de **Catastro** (Issue #200) tienen características físicas por edificio:
  - Superficie construida
  - Año de construcción
  - Número de plantas
  - Referencia catastral
- Necesitamos **combinar** precios (Idealista) + características físicas (Catastro) para el modelo MICRO

**Resultado esperado**:
- Dataset con direcciones normalizadas
- Matching rate: ≥40% con datos de Catastro (objetivo realista)

---

#### 4. **Validar Pipeline Técnico**

**Qué buscamos**:
- Validar que el pipeline de extracción funciona end-to-end
- Identificar problemas técnicos (bloqueos, rate limits, cambios en estructura HTML)
- Documentar limitaciones y alternativas

**Por qué es necesario**:
- Este es un **spike de validación**, no producción
- Necesitamos entender si el scraping es viable antes de invertir más tiempo
- Si no es viable, debemos usar la **API oficial de Idealista**

**Resultado esperado**:
- Pipeline funcional o documentación clara de por qué no es viable
- Decisión Go/No-Go para usar scraping vs. API

---

## 📊 Datos Esperados del Scraper

### **Estructura del Dataset**

| Campo | Tipo | Descripción | Ejemplo | Prioridad |
|-------|------|-------------|---------|-----------|
| `precio` | `int` | Precio en euros | `950` | 🔴 Crítico |
| `superficie_m2` | `float` | Superficie en m² | `45.0` | 🔴 Crítico |
| `habitaciones` | `int` | Número de dormitorios | `2` | 🟡 Importante |
| `banos` | `int` | Número de baños | `1` | 🟡 Importante |
| `localidad` | `str` | Dirección/localidad | `"calle de Antonio López, Comillas"` | 🔴 Crítico |
| `descripcion` | `str` | Descripción del anuncio | `"Piso REFORMADO..."` | 🟢 Opcional |
| `link` | `str` | URL del anuncio | `"https://www.idealista.com/inmueble/107189787/"` | 🟡 Importante |
| `detalles` | `str` | Detalles adicionales | `"Bajo interior con ascensor"` | 🟢 Opcional |
| `page` | `int` | Número de página | `1` | 🟢 Opcional |

### **Criterios de Calidad**

**Cantidad**:
- **Mínimo**: 50 propiedades (para validación técnica)
- **Ideal**: 200-500 propiedades (para modelo robusto)
- **Ámbito geográfico**: Barrio de Gràcia (5 barrios: IDs 28-32)

**Calidad**:
- **Completitud**: ≥80% en campos críticos (`precio`, `superficie_m2`, `localidad`)
- **Validez**: Precios en rango razonable (1,000 - 10,000 €/m² para Gràcia)
- **Unicidad**: Sin duplicados (mismo `link`)

**Temporalidad**:
- **Período**: Anuncios recientes (últimos 3-6 meses)
- **Actualización**: Datos de mercado actual (no históricos agregados)

---

## 🔄 Integración en el Pipeline

### **Flujo Completo del Pipeline MICRO**

```
1. Catastro (Issue #200)
   └─> Características físicas por edificio
       (superficie, año, plantas, referencia catastral)

2. Idealista (Web Scraper - Este documento)
   └─> Precios de mercado por propiedad
       (precio, superficie, habitaciones, dirección)

3. Matching (Issue #201)
   └─> Combinar Catastro + Idealista
       (matching por referencia catastral o dirección fuzzy)

4. Modelo Hedonic (Issue #202)
   └─> Entrenar modelo MICRO
       (precio_m2 ~ características físicas + características de mercado)
```

### **Rol del Web Scraper en el Pipeline**

**Input**:
- URL base de Idealista para Gràcia
- Filtros: Venta/Alquiler, barrio, precio, etc.

**Proceso**:
1. Navegar a páginas de resultados de Idealista
2. Extraer datos de cada propiedad (precio, características, dirección)
3. Manejar paginación (múltiples páginas)
4. Guardar datos en CSV estructurado

**Output**:
- CSV: `spike-data-validation/data/processed/fase2/idealista_gracia_selenium.csv`
- Formato: Compatible con `match_catastro_idealista.py`

**Siguiente paso**:
- El script `match_catastro_idealista.py` combina:
  - Datos de Catastro (características físicas)
  - Datos de Idealista (precios de mercado)
  - Matching por referencia catastral o dirección

---

## 📈 Resultado Esperado

### **Dataset Final para Modelo MICRO**

**Archivo**: `spike-data-validation/data/processed/fase2/idealista_catastro_matched.csv`

**Estructura esperada**:

| Campo | Fuente | Descripción |
|-------|--------|-------------|
| `referencia_catastral` | Catastro | ID único del edificio |
| `precio` | Idealista | Precio de la propiedad |
| `precio_m2` | Calculado | `precio / superficie_m2` |
| `superficie_m2` | Catastro/Idealista | Superficie (preferir Catastro) |
| `ano_construccion` | Catastro | Año de construcción |
| `plantas` | Catastro | Número de plantas del edificio |
| `habitaciones` | Idealista | Número de dormitorios |
| `banos` | Idealista | Número de baños |
| `ascensor` | Idealista | Boolean (tiene ascensor) |
| `exterior` | Idealista | Boolean (vista exterior) |
| `barrio_id` | Calculado | ID del barrio (28-32 para Gràcia) |
| `direccion` | Idealista/Catastro | Dirección normalizada |

**Métricas esperadas**:
- **Observaciones**: 50-200 propiedades matched
- **Matching rate**: ≥40% (realista con datos reales)
- **Completitud**: ≥80% en campos críticos
- **Cobertura temporal**: Últimos 3-6 meses

---

## 🎯 Métricas de Éxito del Scraper

### **Métricas Técnicas**

| Métrica | Objetivo | Estado Actual |
|---------|----------|---------------|
| **Propiedades extraídas** | ≥50 | ⚠️ Bloqueado por IP |
| **Tasa de éxito** | ≥80% páginas | ❌ 0% (bloqueo) |
| **Completitud datos** | ≥80% campos críticos | N/A (sin datos) |
| **Tiempo de ejecución** | ≤30 min (10 páginas) | N/A |

### **Métricas de Calidad**

| Métrica | Objetivo | Validación |
|---------|----------|------------|
| **Precios válidos** | 100% en rango razonable | Validar con estadísticas |
| **Direcciones parseables** | ≥90% | Validar con matching |
| **Sin duplicados** | 0% | Validar por `link` único |

### **Criterio Go/No-Go**

**✅ GO (Scraping viable)**:
- Se extraen ≥50 propiedades
- Tasa de éxito ≥80%
- Datos de calidad suficiente para matching

**❌ NO-GO (Usar API)**:
- Bloqueo sistemático (IP, CAPTCHA)
- Tasa de éxito <50%
- Datos insuficientes o de baja calidad

**Estado actual**: ❌ **NO-GO** (bloqueo de IP confirmado)

**Alternativa**: Usar **API oficial de Idealista** (ver `IDEALISTA_API_SETUP.md`)

---

## 🔗 Integración con Otros Componentes

### **Scripts Relacionados**

1. **`scrape_idealista_selenium.py`** (Este scraper)
   - Extrae datos de Idealista
   - Output: `idealista_gracia_selenium.csv`

2. **`match_catastro_idealista.py`**
   - Combina Catastro + Idealista
   - Matching por referencia catastral o dirección
   - Output: `idealista_catastro_matched.csv`

3. **`train_micro_hedonic.py`**
   - Entrena modelo hedónico MICRO
   - Input: `idealista_catastro_matched.csv`
   - Output: Modelo entrenado + métricas

### **Dependencias**

**Input requerido**:
- ✅ Datos de Catastro (Issue #200): `catastro_gracia_real.csv`
- ⏳ Datos de Idealista (este scraper): `idealista_gracia_selenium.csv`

**Output generado**:
- Dataset matched: `idealista_catastro_matched.csv`
- Modelo entrenado: `micro_hedonic_model.pkl`
- Métricas: `micro_hedonic_metrics.json`

---

## 📝 Limitaciones Conocidas

### **Limitaciones Técnicas**

1. **Bloqueo de IP**:
   - Idealista detecta y bloquea scraping automatizado
   - Solución: VPN o API oficial

2. **CAPTCHA**:
   - Idealista muestra CAPTCHA para prevenir scraping
   - Solución: Resolución manual (modo visible) o API oficial

3. **Rate Limiting**:
   - Idealista puede limitar requests por IP
   - Solución: Delays entre requests (2-20 segundos)

4. **Cambios en Estructura HTML**:
   - Idealista puede cambiar estructura HTML
   - Solución: Selectores CSS robustos + actualización periódica

### **Limitaciones de Datos**

1. **Cobertura geográfica**:
   - Solo barrio de Gràcia (5 barrios)
   - No todos los barrios de Barcelona

2. **Cobertura temporal**:
   - Solo anuncios actuales (últimos 3-6 meses)
   - No datos históricos completos

3. **Matching rate**:
   - Matching con Catastro puede ser <50%
   - Depende de calidad de direcciones

---

## 🎯 Conclusión

### **Objetivo Principal del Scraper**

Extraer **precios de mercado individuales** de Idealista para el barrio de Gràcia, que se combinarán con **características físicas de Catastro** para entrenar un **modelo hedónico de precios a nivel micro** (edificio individual).

### **Estado Actual**

**Scraping**: ❌ **No viable** (bloqueo de IP confirmado)

**Alternativa recomendada**: ✅ **API oficial de Idealista**
- Registro: https://developers.idealista.com/
- Límite: 150 calls/mes
- Estable y legal

### **Próximos Pasos**

1. **Si se obtienen credenciales API**:
   - Usar `extract_idealista_api_gracia.py`
   - Extraer datos reales
   - Continuar con matching y modelo

2. **Si no se obtienen credenciales API**:
   - Continuar con datos mock para validación técnica del pipeline
   - Documentar limitaciones
   - Decisión Go/No-Go basada en pipeline técnico

---

## 📚 Referencias

- **Guía de uso scraper**: `GUIA_USO_SELENIUM.md`
- **Soluciones bloqueo IP**: `BLOQUEO_IP_SOLUCIONES.md`
- **Setup API Idealista**: `IDEALISTA_API_SETUP.md`
- **Plan Fase 2**: `ISSUE_202_FASE2_PLAN.md`
- **Resumen Fase 2**: `FASE2_SUMMARY.md`

---

**Última actualización**: 2025-12-20  
**Mantenido por**: Equipo A - Data Infrastructure

