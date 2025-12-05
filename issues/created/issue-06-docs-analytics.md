---
title: [DOCS] Documentar módulo analytics y decisiones técnicas
labels: ["sprint-1", "priority-medium", "type-docs", "area-analytics", "effort-s"]
milestone: "Quick Wins Foundation"
assignees: ["prototyp33"]
---

## 🎯 Contexto

**Sprint:** Sprint 1 (Semanas 1-4)  
**Milestone:** Quick Wins Foundation  
**Esfuerzo estimado:** 2 horas  
**Fecha límite:** 2025-12-22  

**Dependencias:**
- #3: [FEAT-02] Investment Calculator - Core Logic (debe estar completado)
- #4: [FEAT-02] Investment Calculator - UI Streamlit (debe estar completado)

**Bloqueadores:**
- Ninguno conocido

**Documentación relacionada:**
- 📄 [Feature Doc](docs/features/feature-02-calculator.md)
- 📄 [Architecture Docs](docs/architecture/)

---

## 📝 Descripción

Crear documentación técnica completa del módulo `analytics` incluyendo decisiones técnicas, fórmulas usadas, y ejemplos de uso. Esta documentación será referencia para futuras features y para el portfolio.

**Valor de Negocio:**
Documentación profesional demuestra conocimiento técnico y facilita mantenimiento futuro. Esencial para showcase del proyecto.

**User Story:**
> Como desarrollador futuro (o yo mismo en 6 meses), necesito documentación clara del módulo analytics para entender decisiones técnicas y reutilizar código.

---

## 🔧 Componentes Técnicos

### Archivos a crear/modificar:

- [ ] Actualizar `docs/features/feature-02-calculator.md` (ya existe, completar)
- [ ] Crear `docs/architecture/analytics_module.md` - Documentación del módulo
- [ ] Añadir screenshots de UI en `docs/screenshots/calculator/`
- [ ] Actualizar `README.md` con referencia a calculadora

### Contenido Requerido

#### 1. `docs/features/feature-02-calculator.md` (Actualizar)

Añadir secciones faltantes:
- [ ] Screenshots de UI con anotaciones
- [ ] Ejemplos de uso con datos reales
- [ ] Troubleshooting común
- [ ] Performance considerations

#### 2. `docs/architecture/analytics_module.md` (Nuevo)

```markdown
# Módulo Analytics - Arquitectura

## Visión General

El módulo `src/analytics/` contiene toda la lógica de negocio para cálculos
y análisis de datos inmobiliarios.

## Estructura

```
src/analytics/
├── __init__.py
├── investment_calculator.py  # Calculadora de inversión
├── financial_metrics.py       # Funciones auxiliares financieras
└── segmentation.py           # Clustering (Sprint 2)
```

## Decisiones Técnicas

### Por qué numpy-financial?

- **Precisión:** Más preciso que fórmulas manuales
- **Estándar:** Librería estándar para cálculos financieros
- **Mantenibilidad:** Menos código custom = menos bugs

### Por qué dataclasses?

- **Type safety:** Type hints integrados
- **Inmutabilidad:** Puede usar `frozen=True` si necesario
- **Legibilidad:** Código más claro que dicts

### Fórmulas Fiscales

#### ITP (Impuesto de Transmisiones Patrimoniales)
- **Cataluña:** 10% para vivienda usada
- **Nueva construcción:** 10% (AJD en lugar de ITP)
- **Fuente:** [ATC Generalitat](https://atc.gencat.cat/)

#### Notaría y Registro
- **Notaría:** 0.5% (mínimo 500€)
- **Registro:** 0.3% (mínimo 300€)
- **Fuente:** Tarifas oficiales

## Convenciones

### Naming
- Funciones: `calcular_*` para cálculos
- Clases: `*Inputs`, `*Metrics` para dataclasses
- Constantes: `UPPER_CASE`

### Type Hints
- Siempre usar type hints
- Usar `Optional[T]` para valores que pueden ser None
- Usar `Dict[str, T]` para diccionarios tipados

### Docstrings
- Formato Google-style
- Incluir Args, Returns, Raises
- Ejemplos cuando sea útil

## Ejemplos de Uso

### Ejemplo 1: Cálculo Básico

```python
from src.analytics.investment_calculator import (
    InvestmentInputs,
    calcular_metricas_inversion
)

inputs = InvestmentInputs(
    precio_compra=250000,
    metros_cuadrados=80,
    barrio_id=1,
    alquiler_mensual=1200
)

metrics = calcular_metricas_inversion(inputs)
print(f"Rentabilidad: {metrics.rentabilidad_neta:.2f}%")
```

### Ejemplo 2: Escenarios

```python
from src.analytics.investment_calculator import generar_escenarios

escenarios = generar_escenarios(inputs, variacion_alquiler=0.15)

for nombre, metricas in escenarios.items():
    print(f"{nombre}: TIR {metricas.tir:.2f}%")
```

## Testing

Ver `tests/test_investment_calculator.py` para ejemplos completos.

## Performance

- Cálculo de métricas: < 10ms
- Generación de escenarios: < 30ms
- No requiere optimización adicional

## Future Enhancements

- [ ] Caching de cálculos repetidos
- [ ] Soporte para múltiples propiedades
- [ ] Integración con APIs de bancos para tipos reales
```

---

## ✅ Criterios de Aceptación

- [ ] `docs/features/feature-02-calculator.md` actualizado con screenshots
- [ ] `docs/architecture/analytics_module.md` creado y completo
- [ ] Screenshots de UI añadidos en `docs/screenshots/calculator/`
- [ ] Ejemplos de código funcionando
- [ ] Referencias a fuentes oficiales (fiscalidad)
- [ ] README.md actualizado con link a calculadora
- [ ] Documentación revisada y sin errores

---

## 🧪 Plan de Testing

### Validación de Documentación

1. **Revisar ortografía y gramática**
   - Usar spell checker
   - Revisar formato markdown

2. **Verificar enlaces**
   - Todos los links funcionan
   - Imágenes se cargan correctamente

3. **Verificar ejemplos de código**
   - Copiar/pegar y ejecutar
   - Verificar que funcionan

4. **Validar screenshots**
   - Resolución adecuada
   - Anotaciones claras

---

## 📊 Métricas de Éxito

| KPI | Target | Medición |
|-----|--------|----------|
| **Completitud** | 100% secciones | Revisión manual |
| **Ejemplos funcionando** | 100% | Ejecución manual |
| **Screenshots** | 3+ screenshots | Conteo manual |

---

## 🚧 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Documentación desactualizada | Media | Medio | Actualizar con cada cambio |
| Screenshots obsoletos | Baja | Bajo | Re-capturar si UI cambia |

---

## 📚 Referencias

- [Google Style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [Markdown Guide](https://www.markdownguide.org/)
- [Feature Doc Template](docs/features/README.md)

---

## 🔗 Issues Relacionadas

- #3: [FEAT-02] Investment Calculator - Core Logic
- #4: [FEAT-02] Investment Calculator - UI Streamlit
- #5: [FEAT-02] Investment Calculator - Tests

---

## 📝 Notas de Implementación

### Orden de Ejecución

1. **Paso 1:** Capturar screenshots de UI
   - Ejecutar Streamlit localmente
   - Capturar diferentes estados (inputs, resultados, escenarios)
   - Añadir anotaciones

2. **Paso 2:** Actualizar feature doc
   - Añadir screenshots
   - Completar secciones faltantes
   - Añadir ejemplos de uso

3. **Paso 3:** Crear architecture doc
   - Documentar decisiones técnicas
   - Añadir ejemplos de código
   - Documentar convenciones

4. **Paso 4:** Actualizar README
   - Añadir sección de calculadora
   - Link a documentación
   - Screenshot destacado

5. **Paso 5:** Revisión final
   - Revisar ortografía
   - Verificar enlaces
   - Validar ejemplos

---

**Creado:** 2025-12-03  
**Última actualización:** 2025-12-03

