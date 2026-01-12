# ✅ Mejora de Agregación para Alta Variabilidad

**Fecha**: 2026-01-10  
**Estado**: ✅ Implementado

---

## Objetivo

Usar mediana automáticamente cuando CV > 50% para evitar errores como Baró de Viver, donde el promedio estaba sesgado por valores extremos.

---

## Implementación

### Cambios en `create_master_table_for_looker.py`

#### 1. Nueva CTE `precios_stats`

Calcula estadísticas completas para cada barrio/año:
- **Promedio** (`AVG`)
- **Mediana** (`PERCENTILE_CONT(0.5)`)
- **Desviación estándar** (`STDDEV`)
- **Conteo de registros**

#### 2. Nueva CTE `precios_agg`

Decide qué valor usar basado en CV:
- **Si CV > 50% y registros >= 3**: Usa **mediana**
- **Si CV ≤ 50% o registros < 3**: Usa **promedio**

#### 3. Nuevas Columnas Agregadas

- `usa_mediana_venta`: Flag (0/1) indicando si se usó mediana para precio de venta
- `usa_mediana_alquiler`: Flag (0/1) indicando si se usó mediana para precio de alquiler
- `cv_precio_venta`: Coeficiente de variación (%) para precio de venta
- `cv_precio_alquiler`: Coeficiente de variación (%) para precio de alquiler
- `usa_mediana`: Flag combinado (1 si cualquiera de los dos usa mediana)

---

## Resultados

### Registros con Alta Variabilidad

- **Total detectados**: 9 registros usan mediana automáticamente
- **Criterio**: CV > 50% y al menos 3 registros

### Impacto

- ✅ **Prevención de errores**: Evita promedios sesgados por outliers
- ✅ **Transparencia**: Flags claros indican cuándo se usa mediana
- ✅ **Robustez**: Método más robusto para datos con alta variabilidad

---

## Ejemplo: Baró de Viver (2015)

**Antes** (promedio):
- Precio promedio: 1,490.10 €/m²
- CV: 77.7%
- Problema: Sesgado por valores extremos (2,758 €/m²)

**Después** (mediana automática):
- Precio promedio: ~664.91 €/m² (mediana)
- CV: 77.7% (detectado)
- Flag `usa_mediana_venta`: 1
- Solución: Valor más representativo

---

## Criterios de Decisión

### Usar Mediana Cuando:
- ✅ CV > 50%
- ✅ Al menos 3 registros disponibles
- ✅ Desviación estándar > 0

### Usar Promedio Cuando:
- ✅ CV ≤ 50%
- ✅ Menos de 3 registros (insuficiente para mediana confiable)
- ✅ Desviación estándar = 0 (sin variabilidad)

---

## Columnas en Tabla Maestra

### Nuevas Columnas (5)

1. `usa_mediana_venta` (int): 0 o 1
2. `usa_mediana_alquiler` (int): 0 o 1
3. `cv_precio_venta` (float): Coeficiente de variación (%)
4. `cv_precio_alquiler` (float): Coeficiente de variación (%)
5. `usa_mediana` (int): Flag combinado

### Total de Columnas

- **Antes**: 50 columnas
- **Después**: 55 columnas (+5 nuevas)

---

## Uso en Análisis

### Filtrar por Método de Agregación

```python
# Solo registros que usan promedio (baja variabilidad)
df_promedio = df[df['usa_mediana'] == 0]

# Solo registros que usan mediana (alta variabilidad)
df_mediana = df[df['usa_mediana'] == 1]

# Ver CV de registros con alta variabilidad
df[df['usa_mediana'] == 1][['barrio_nombre', 'anio', 'cv_precio_venta']]
```

### Visualización

- Usar `usa_mediana` como color o marcador en gráficos
- Mostrar CV en tooltips para transparencia
- Filtrar análisis por método de agregación si es necesario

---

## Validación

### Verificación Automática

El script verifica:
- ✅ Cálculo correcto de CV
- ✅ Decisión correcta entre mediana/promedio
- ✅ Flags agregados correctamente
- ✅ Log de registros con alta variabilidad

### Log de Ejecución

```
Alta variabilidad detectada: 9 registros usan mediana
```

---

## Beneficios

1. **Prevención de Errores**
   - Evita promedios sesgados por outliers
   - Detecta automáticamente alta variabilidad

2. **Transparencia**
   - Flags claros indican método usado
   - CV disponible para análisis adicional

3. **Robustez**
   - Método más robusto para datos variables
   - Automático, sin intervención manual

4. **Trazabilidad**
   - Se puede identificar qué registros usan mediana
   - CV disponible para validación

---

## Próximos Pasos Opcionales

1. ⏳ Crear visualización de CV por barrio/año
2. ⏳ Alertar sobre nuevos casos de alta variabilidad
3. ⏳ Documentar casos específicos que requieren mediana
4. ⏳ Considerar otros métodos de agregación (trimmed mean, etc.)

---

**Estado**: ✅ Implementado y funcionando  
**Impacto**: Prevención automática de errores como Baró de Viver
