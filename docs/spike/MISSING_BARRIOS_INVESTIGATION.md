# Investigación: Barrios Faltantes en Master Table

**Fecha**: 2025-12-14  
**Barrios faltantes**: ID 11 (Poble-sec) y ID 12 (Marina del Prat Vermell)

---

## 🔍 Hallazgos

### 1. Datos en Base de Datos

#### `fact_precios`
- **Barrio 11 (Poble-sec)**: ✅ 71 registros (2015-2024)
  - Fuentes: `portaldades` (mayoría), `opendatabcn_idealista` (2015)
  - Cobertura: Todos los años 2015-2024

- **Barrio 12 (Marina del Prat Vermell)**: ✅ 51 registros (2015-2024)
  - Fuente: `portaldades`
  - Cobertura: Todos los años 2015-2024

#### `fact_renta`
- **Barrio 11**: ✅ 9 registros (2015-2023)
  - Fuentes: `idescat` (2015-2022), `opendatabcn` (2023)
  - Renta mediana: 12,284 - 36,617 €

- **Barrio 12**: ✅ 9 registros (2015-2023)
  - Fuentes: `idescat` (2015-2022), `opendatabcn` (2023)
  - Renta mediana: 12,284 - 34,296 €

### 2. Datos en CSV Raw

#### `official_prices_2015_2024.csv`
- **Barrio 11**: ❌ 0 registros
- **Barrio 12**: ❌ 0 registros

**Conclusión**: Los barrios NO tienen datos en las fuentes oficiales (INCASÒL/Generalitat) usadas para crear el Master Table.

---

## 🔎 Causa Raíz

El Master Table se crea a partir de `official_prices_2015_2024.csv`, que contiene datos de:
- **INCASÒL** (alquiler)
- **Generalitat de Catalunya** (venta)

Estas fuentes oficiales **no incluyen datos** para los barrios 11 y 12 en el período 2015-2024.

Sin embargo, `fact_precios` en la base de datos SÍ tiene datos para estos barrios porque:
- Usa datos de `portaldades` (fuente más amplia)
- Incluye datos de `opendatabcn_idealista`

---

## 📊 Comparación de Fuentes

| Fuente | Barrio 11 | Barrio 12 | Notas |
|--------|-----------|-----------|-------|
| **INCASÒL** | ❌ No disponible | ❌ No disponible | Fuente oficial alquiler |
| **Generalitat** | ❌ No disponible | ❌ No disponible | Fuente oficial venta |
| **Portaldades** | ✅ Disponible | ✅ Disponible | Fuente alternativa |
| **IDESCAT** | ✅ Disponible | ✅ Disponible | Renta familiar |
| **OpenDataBCN Idealista** | ✅ Parcial (2015) | ❌ No disponible | Datos de mercado |

---

## ⚠️ Impacto

### En Master Table
- **Cobertura espacial**: 71/73 barrios (97%)
- **Registros faltantes**: ~40 registros quarterly (2 barrios × ~20 años-quarter)
- **Features afectadas**: Todas (precios, renta, estructurales, affordability)

### En Análisis
- ❌ No se pueden incluir estos barrios en análisis basados en Master Table
- ⚠️ Análisis comparativos pueden tener sesgo si estos barrios son relevantes
- ✅ Datos disponibles en `fact_precios` y `fact_renta` para análisis alternativos

---

## 💡 Posibles Razones

### 1. **Barrios Pequeños o Nuevos**
- Pueden ser barrios con poca actividad inmobiliaria
- Datos oficiales pueden no estar disponibles por volumen insuficiente

### 2. **Cambios Administrativos**
- Pueden haber cambiado de código o nombre durante el período
- Datos históricos pueden estar bajo otro identificador

### 3. **Limitaciones de Fuentes Oficiales**
- INCASÒL y Generalitat pueden tener umbrales mínimos de datos
- Barrios con pocas transacciones pueden quedar excluidos

### 4. **Problemas de Matching**
- Puede haber problemas en el matching de nombres/códigos
- Necesita verificación manual

---

## ✅ Recomendaciones

### Opción 1: Usar Datos de `fact_precios` (Recomendado)
**Estrategia**: Completar Master Table con datos de `fact_precios` para estos barrios

**Ventajas**:
- ✅ Mantiene cobertura completa (73/73 barrios)
- ✅ Datos ya disponibles en DB
- ✅ Consistente con otros barrios

**Desventajas**:
- ⚠️ Fuente diferente (portaldades vs oficial)
- ⚠️ Puede tener granularidad diferente

**Implementación**:
```python
# 1. Extraer datos de fact_precios para barrios 11 y 12
# 2. Convertir a formato quarterly si es necesario
# 3. Interpolar renta desde fact_renta
# 4. Añadir a fact_housing_master
```

### Opción 2: Documentar Limitación
**Estrategia**: Aceptar la limitación y documentarla claramente

**Ventajas**:
- ✅ Mantiene calidad de datos oficiales
- ✅ Transparencia sobre limitaciones

**Desventajas**:
- ❌ Cobertura incompleta
- ❌ Puede afectar análisis

### Opción 3: Investigar Fuentes Alternativas
**Estrategia**: Buscar datos oficiales en otras fuentes

**Acciones**:
1. Verificar Open Data BCN directamente
2. Contactar con INCASÒL/Generalitat
3. Revisar documentación de fuentes

---

## 📝 Próximos Pasos

1. ✅ **Investigación completada**: Causa identificada (falta de datos en fuentes oficiales)
2. **Decidir estrategia**: Opción 1 (completar con fact_precios) vs Opción 2 (documentar)
3. **Si Opción 1**: Crear script para completar Master Table
4. **Validar**: Verificar que datos de fact_precios son comparables
5. **Documentar**: Actualizar documentación con decisión tomada

---

## 🔗 Referencias

- **Master Table**: `data/processed/barcelona_housing_master_table.csv`
- **CSV Raw**: `data/raw/official_prices_2015_2024.csv`
- **Base de datos**: `data/processed/database.db`
- **Tablas relevantes**: `fact_precios`, `fact_renta`, `fact_housing_master`

---

## 📅 Historial

- **2025-12-14**: Investigación completada, causa identificada

