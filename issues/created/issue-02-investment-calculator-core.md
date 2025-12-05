---
title: [FEAT-02] Investment Calculator - Core Logic
labels: ["sprint-1", "priority-high", "type-feature", "area-analytics", "effort-m", "epic"]
milestone: "Quick Wins Foundation"
assignees: ["prototyp33"]
---

## 🎯 Contexto

**Feature ID:** #2 del análisis comparativo de propuestas  
**Sprint:** Sprint 1 (Semanas 1-4)  
**Milestone:** Quick Wins Foundation  
**Esfuerzo estimado:** 8 horas  
**Fecha límite:** 2025-12-15  

**Dependencias:**
- Ninguna (primer sprint)

**Bloqueadores:**
- Ninguno conocido

**Documentación relacionada:**
- 📄 [Feature Doc](docs/features/feature-02-calculator.md)
- 📄 [Sprint Planning](docs/SPRINT_PLANNING_COMPLETE.md)
- 📄 [Análisis Comparativo](docs/Analisis-Comparativo-de-Propuestas-de-Expansion.pdf)

---

## 📝 Descripción

Implementar la lógica core del calculador de viabilidad de inversión inmobiliaria que considera:

- Costes fiscales españoles (ITP, notaría, registro)
- Cálculo de hipoteca con numpy-financial
- Métricas financieras (VAN, TIR, ROI, Payback)
- Cash flow mensual considerando todos los gastos

**Valor de Negocio:**
Permite a usuarios evaluar rápidamente si una inversión inmobiliaria es viable, considerando la fiscalidad real española. Feature diferenciador para portfolio.

**User Story:**
> Como inversor potencial, quiero calcular el cash flow real y el ROI de una propiedad considerando impuestos españoles, para tomar decisiones informadas.

---

## 🔧 Componentes Técnicos

### Archivos a crear:

- [ ] `src/analytics/investment_calculator.py` - Lógica principal
- [ ] `src/analytics/financial_metrics.py` - Funciones auxiliares
- [ ] `tests/test_investment_calculator.py` - Suite de tests
- [ ] `docs/features/feature-02-calculator.md` - Documentación (ya existe, actualizar)

### Dependencias nuevas:

```python
# requirements.txt
numpy-financial>=1.0.0  # Para cálculos de TIR, VAN, PMT
```

### Estructura de Código

```python
# src/analytics/investment_calculator.py

from dataclasses import dataclass
from typing import Dict
import numpy_financial as npf

@dataclass
class InvestmentInputs:
    """
    Inputs para el cálculo de inversión inmobiliaria.
    
    Attributes:
        precio_compra: Precio de adquisición en euros
        metros_cuadrados: Superficie útil
        barrio_id: ID del barrio (codi_barri)
        alquiler_mensual: Alquiler esperado mensual
        gastos_comunidad: Gastos de comunidad mensuales
        ibi_anual: Impuesto sobre Bienes Inmuebles anual
        porcentaje_financiacion: % del precio financiado (0-100)
        tipo_interes: TAE del préstamo hipotecario
        plazo_hipoteca: Años de la hipoteca
    """
    precio_compra: float
    metros_cuadrados: float
    barrio_id: int
    alquiler_mensual: float
    gastos_comunidad: float = 100.0
    ibi_anual: float = 500.0
    porcentaje_financiacion: float = 80.0
    tipo_interes: float = 3.5
    plazo_hipoteca: int = 25


@dataclass
class InvestmentMetrics:
    """
    Métricas calculadas de la inversión.
    
    Attributes:
        rentabilidad_bruta: (Alquiler anual / Precio) * 100
        rentabilidad_neta: (Beneficio neto / Precio) * 100
        cash_flow_mensual: Ingresos - Gastos - Hipoteca
        payback_years: Años para recuperar inversión inicial
        roi_5_years: Return on Investment a 5 años
        tir: Tasa Interna de Retorno
        van: Valor Actual Neto
    """
    rentabilidad_bruta: float
    rentabilidad_neta: float
    cash_flow_mensual: float
    payback_years: float
    roi_5_years: float
    tir: float
    van: float


def calcular_gastos_compra(precio_compra: float) -> Dict[str, float]:
    """
    Calcula costes de compra en Cataluña.
    
    Args:
        precio_compra: Precio de adquisición
    
    Returns:
        Dict con ITP, notaría, registro, gestoría, total
    """
    # ITP Cataluña: 10% para vivienda usada
    itp = precio_compra * 0.10
    
    # Notaría: ~0.5% (mínimo 500€)
    notaria = max(precio_compra * 0.005, 500.0)
    
    # Registro: ~0.3% (mínimo 300€)
    registro = max(precio_compra * 0.003, 300.0)
    
    # Gestoría: ~1,000€
    gestoria = 1000.0
    
    total = itp + notaria + registro + gestoria
    
    return {
        "itp": itp,
        "notaria": notaria,
        "registro": registro,
        "gestoria": gestoria,
        "total": total
    }


def calcular_cuota_hipoteca(
    capital: float,
    tipo_interes_anual: float,
    plazo_años: int
) -> float:
    """
    Calcula cuota mensual de hipoteca usando numpy-financial.
    
    Args:
        capital: Capital prestado
        tipo_interes_anual: TAE anual (ej: 3.5 para 3.5%)
        plazo_años: Años de la hipoteca
    
    Returns:
        Cuota mensual en euros
    """
    tipo_mensual = tipo_interes_anual / 100 / 12
    num_pagos = plazo_años * 12
    
    cuota = npf.pmt(tipo_mensual, num_pagos, -capital)
    
    return abs(cuota)


def calcular_metricas_inversion(
    inputs: InvestmentInputs,
    horizonte_años: int = 10
) -> InvestmentMetrics:
    """
    Calcula métricas de inversión inmobiliaria.
    
    Args:
        inputs: Parámetros de la inversión
        horizonte_años: Horizonte temporal para VAN/TIR
    
    Returns:
        InvestmentMetrics con todos los cálculos
    
    Raises:
        ValueError: Si los inputs son inválidos
    """
    # Validación
    if inputs.precio_compra <= 0:
        raise ValueError("precio_compra debe ser positivo")
    if inputs.alquiler_mensual <= 0:
        raise ValueError("alquiler_mensual debe ser positivo")
    
    # Gastos de compra
    gastos_compra = calcular_gastos_compra(inputs.precio_compra)
    inversion_total = inputs.precio_compra + gastos_compra["total"]
    
    # Capital financiado
    capital_financiado = inputs.precio_compra * (inputs.porcentaje_financiacion / 100)
    capital_propio = inputs.precio_compra - capital_financiado
    
    # Cuota hipoteca
    cuota_mensual = 0.0
    if capital_financiado > 0:
        cuota_mensual = calcular_cuota_hipoteca(
            capital_financiado,
            inputs.tipo_interes,
            inputs.plazo_hipoteca
        )
    
    # Ingresos y gastos anuales
    ingresos_anuales = inputs.alquiler_mensual * 12
    gastos_anuales = (
        inputs.gastos_comunidad * 12 +
        inputs.ibi_anual +
        (cuota_mensual * 12 if cuota_mensual > 0 else 0)
    )
    
    # Rentabilidades
    rentabilidad_bruta = (ingresos_anuales / inputs.precio_compra) * 100
    beneficio_neto_anual = ingresos_anuales - gastos_anuales
    rentabilidad_neta = (beneficio_neto_anual / inversion_total) * 100
    
    # Cash flow mensual
    cash_flow_mensual = inputs.alquiler_mensual - inputs.gastos_comunidad - (inputs.ibi_anual / 12) - cuota_mensual
    
    # Payback
    if cash_flow_mensual > 0:
        payback_years = inversion_total / (cash_flow_mensual * 12)
    else:
        payback_years = float('inf')
    
    # ROI a 5 años
    flujos_5_años = [cash_flow_mensual * 12] * 5
    roi_5_years = (sum(flujos_5_años) / inversion_total) * 100
    
    # VAN y TIR
    flujos = [-inversion_total] + [cash_flow_mensual * 12] * horizonte_años
    van = npf.npv(0.03, flujos)  # Tasa descuento 3%
    tir = npf.irr(flujos) * 100 if npf.irr(flujos) else 0.0
    
    return InvestmentMetrics(
        rentabilidad_bruta=rentabilidad_bruta,
        rentabilidad_neta=rentabilidad_neta,
        cash_flow_mensual=cash_flow_mensual,
        payback_years=payback_years,
        roi_5_years=roi_5_years,
        tir=tir,
        van=van
    )


def generar_escenarios(
    inputs: InvestmentInputs,
    variacion_alquiler: float = 0.10
) -> Dict[str, InvestmentMetrics]:
    """
    Genera 3 escenarios: pesimista, base, optimista.
    
    Args:
        inputs: Parámetros base de la inversión
        variacion_alquiler: % de variación para escenarios (default 10%)
    
    Returns:
        Dict con keys 'pesimista', 'base', 'optimista'
    """
    # Escenario base
    base = calcular_metricas_inversion(inputs)
    
    # Escenario pesimista (alquiler -10%)
    inputs_pesimista = InvestmentInputs(
        **{**inputs.__dict__, "alquiler_mensual": inputs.alquiler_mensual * (1 - variacion_alquiler)}
    )
    pesimista = calcular_metricas_inversion(inputs_pesimista)
    
    # Escenario optimista (alquiler +10%)
    inputs_optimista = InvestmentInputs(
        **{**inputs.__dict__, "alquiler_mensual": inputs.alquiler_mensual * (1 + variacion_alquiler)}
    )
    optimista = calcular_metricas_inversion(inputs_optimista)
    
    return {
        "pesimista": pesimista,
        "base": base,
        "optimista": optimista
    }
```

---

## ✅ Criterios de Aceptación

- [ ] Función `calcular_gastos_compra()` implementada con valores correctos para Cataluña
- [ ] Función `calcular_cuota_hipoteca()` usando numpy-financial.pmt()
- [ ] Función `calcular_metricas_inversion()` calcula todas las métricas correctamente
- [ ] Función `generar_escenarios()` retorna 3 escenarios válidos
- [ ] Validación de inputs (precios > 0, porcentajes 0-100, etc.)
- [ ] Manejo de edge cases (sin financiación, cash flow negativo)
- [ ] Tests unitarios con >80% cobertura
- [ ] Docstrings completos en formato Google-style
- [ ] Type hints en todas las funciones

---

## 🧪 Plan de Testing

### Tests Unitarios

```python
# tests/test_investment_calculator.py

def test_calcular_gastos_compra():
    """Verifica cálculo de gastos de compra en Cataluña."""
    gastos = calcular_gastos_compra(250000)
    assert gastos["itp"] == 25000  # 10%
    assert gastos["total"] > 25000

def test_calcular_cuota_hipoteca():
    """Verifica cálculo de cuota hipoteca."""
    cuota = calcular_cuota_hipoteca(200000, 3.5, 25)
    assert 800 < cuota < 1200  # Rango razonable

def test_calcular_metricas_inversion():
    """Verifica cálculo completo de métricas."""
    inputs = InvestmentInputs(
        precio_compra=250000,
        metros_cuadrados=80,
        barrio_id=1,
        alquiler_mensual=1200
    )
    metrics = calcular_metricas_inversion(inputs)
    assert metrics.rentabilidad_bruta > 0
    assert metrics.cash_flow_mensual is not None

def test_generar_escenarios():
    """Verifica generación de 3 escenarios."""
    inputs = InvestmentInputs(
        precio_compra=250000,
        metros_cuadrados=80,
        barrio_id=1,
        alquiler_mensual=1200
    )
    escenarios = generar_escenarios(inputs)
    assert len(escenarios) == 3
    assert escenarios["pesimista"].rentabilidad_neta < escenarios["base"].rentabilidad_neta
    assert escenarios["optimista"].rentabilidad_neta > escenarios["base"].rentabilidad_neta

def test_invalid_inputs_raise_error():
    """Verifica validación de inputs."""
    with pytest.raises(ValueError):
        inputs = InvestmentInputs(
            precio_compra=-1000,  # Inválido
            metros_cuadrados=80,
            barrio_id=1,
            alquiler_mensual=1200
        )
        calcular_metricas_inversion(inputs)

def test_edge_case_zero_mortgage():
    """Verifica cálculo sin financiación."""
    inputs = InvestmentInputs(
        precio_compra=250000,
        metros_cuadrados=80,
        barrio_id=1,
        alquiler_mensual=1200,
        porcentaje_financiacion=0.0
    )
    metrics = calcular_metricas_inversion(inputs)
    assert metrics.cash_flow_mensual > 0
```

### Ejecutar Tests

```bash
# Tests unitarios
pytest tests/test_investment_calculator.py -v

# Con coverage
pytest tests/test_investment_calculator.py --cov=src/analytics/investment_calculator --cov-report=term-missing

# Target: >80% coverage
```

---

## 📊 Métricas de Éxito

| KPI | Target | Medición |
|-----|--------|----------|
| **Cobertura de tests** | >80% | pytest-cov |
| **Tiempo de cálculo** | < 500ms | pytest-benchmark |
| **Precisión cálculos** | ±0.01% | Validación manual con casos reales |
| **Edge cases cubiertos** | 100% | Tests de casos límite |

---

## 🚧 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Fórmulas fiscales incorrectas | Media | Alto | Validar con casos reales de Barcelona |
| numpy-financial deprecated | Baja | Medio | Verificar versión compatible |
| Performance con muchos cálculos | Baja | Bajo | Optimizar con caching si necesario |

---

## 📚 Referencias

- [NumPy Financial Docs](https://numpy.org/numpy-financial/)
- [Fiscalidad inmobiliaria Cataluña](https://atc.gencat.cat/)
- [Calculadora rentabilidad Idealista](https://www.idealista.com/news/finanzas/calculadoras/)
- [Documentación Feature #02](docs/features/feature-02-calculator.md)

---

## 🔗 Issues Relacionadas

- #86: [FEATURE-02] Calculadora de Viabilidad de Inversión (issue principal)
- #87: [FEATURE-13] Clustering de Barrios (Sprint 1)
- #88: [FEATURE-05] Sistema de Alertas (Sprint 1)

---

## 📝 Notas de Implementación

### Orden de Implementación Recomendado

1. **Paso 1:** Crear dataclasses `InvestmentInputs` y `InvestmentMetrics`
2. **Paso 2:** Implementar `calcular_gastos_compra()` con tests
3. **Paso 3:** Implementar `calcular_cuota_hipoteca()` con tests
4. **Paso 4:** Implementar `calcular_metricas_inversion()` con tests
5. **Paso 5:** Implementar `generar_escenarios()` con tests
6. **Paso 6:** Validación completa y edge cases

### Consideraciones Técnicas

- Usar `numpy-financial` para cálculos financieros (más preciso que fórmulas manuales)
- Validar todos los inputs al inicio de cada función
- Manejar casos especiales (sin financiación, cash flow negativo)
- Documentar fórmulas fiscales en comentarios inline

---

**Creado:** 2025-12-03  
**Última actualización:** 2025-12-03

