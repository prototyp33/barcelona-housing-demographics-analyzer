# Feature #02: Calculadora de Viabilidad de Inversión

## 📋 Overview

**Sprint:** 1 (Semanas 1-4)  
**Esfuerzo Estimado:** 15-20 horas  
**Issue:** [FEATURE-02]  
**Estado:** 🔄 Pendiente

### Valor de Negocio

La calculadora de inversión permite a inversores inmobiliarios evaluar rápidamente la viabilidad financiera de adquirir propiedades en cualquier barrio de Barcelona, considerando:

- Precio de compra actual
- Potencial de alquiler
- Impuestos específicos de Cataluña
- Gastos de comunidad y mantenimiento
- Escenarios de financiación

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    INVESTMENT CALCULATOR                         │
├─────────────────────────────────────────────────────────────────┤
│  UI Layer (Streamlit)                                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  src/app/pages/investment_simulator.py                      ││
│  │  - Formulario de inputs                                     ││
│  │  - Visualización de resultados                              ││
│  │  - Gráficos de cash flow                                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  src/analytics/investment_calculator.py                     ││
│  │  - InvestmentInputs (dataclass)                             ││
│  │  - InvestmentMetrics (dataclass)                            ││
│  │  - calcular_metricas_inversion()                            ││
│  │  - generar_escenarios()                                     ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  SQLite Database                                            ││
│  │  - fact_precios (datos históricos)                          ││
│  │  - dim_barrios (info del barrio)                            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Componentes Técnicos

### Archivos a Crear/Modificar

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `src/analytics/investment_calculator.py` | Crear | Lógica de cálculos |
| `src/app/pages/investment_simulator.py` | Crear | Página Streamlit |
| `tests/test_investment_calculator.py` | Crear | Tests unitarios |
| `requirements.txt` | Modificar | Añadir numpy-financial |

### Dependencias

```python
# requirements.txt
numpy-financial>=1.0.0  # Para cálculos de TIR, VAN
```

## 🔧 API Reference

### Dataclasses

```python
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
```

### Funciones Principales

```python
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
    
    Example:
        >>> inputs = InvestmentInputs(
        ...     precio_compra=250000,
        ...     metros_cuadrados=80,
        ...     barrio_id=1,
        ...     alquiler_mensual=1200
        ... )
        >>> metrics = calcular_metricas_inversion(inputs)
        >>> print(f"Rentabilidad: {metrics.rentabilidad_neta:.2f}%")
    """


def generar_escenarios(
    inputs: InvestmentInputs,
    variacion_alquiler: float = 0.10
) -> Dict[str, InvestmentMetrics]:
    """
    Genera 3 escenarios: pesimista, base, optimista.
    
    Args:
        inputs: Parámetros base de la inversión
        variacion_alquiler: % de variación para escenarios
    
    Returns:
        Dict con keys 'pesimista', 'base', 'optimista'
    """
```

## 🎨 UI Components

### Layout de la Página

```
┌────────────────────────────────────────────────────────────────┐
│  🏠 Calculadora de Inversión Inmobiliaria                      │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌─────────────────────────────────┐ │
│  │  INPUTS              │  │  RESULTADOS                     │ │
│  │  ───────────────     │  │  ─────────────────────          │ │
│  │  📍 Barrio [select]  │  │  💰 Rentabilidad Bruta: 5.76%   │ │
│  │  💶 Precio: [input]  │  │  📊 Rentabilidad Neta: 4.12%    │ │
│  │  📐 m²: [input]      │  │  💵 Cash Flow: +320€/mes        │ │
│  │  🏷️ Alquiler: [inp]  │  │  ⏱️ Payback: 8.5 años           │ │
│  │  ───────────────     │  │                                 │ │
│  │  ⚙️ Avanzado ▼       │  │  [Gráfico cash flow 10 años]   │ │
│  │  - Comunidad         │  │                                 │ │
│  │  - IBI               │  │                                 │ │
│  │  - Financiación      │  │                                 │ │
│  └──────────────────────┘  └─────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  📈 ANÁLISIS DE ESCENARIOS                                 ││
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐           ││
│  │  │ Pesimista  │  │    Base    │  │ Optimista  │           ││
│  │  │  TIR: 3.2% │  │  TIR: 4.8% │  │  TIR: 6.1% │           ││
│  │  └────────────┘  └────────────┘  └────────────┘           ││
│  └────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘
```

## ✅ Criterios de Aceptación

- [ ] Formulario de inputs con validación
- [ ] Cálculo correcto de rentabilidad bruta y neta
- [ ] Cálculo de TIR y VAN con numpy-financial
- [ ] Visualización de cash flow proyectado
- [ ] Comparativa de 3 escenarios
- [ ] Datos del barrio mostrados (precio medio, tendencia)
- [ ] Tests unitarios con >80% cobertura
- [ ] Documentación inline completa

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests unitarios
pytest tests/test_investment_calculator.py -v

# Con coverage
pytest tests/test_investment_calculator.py --cov=src/analytics/investment_calculator
```

### Casos de Test

| Test Case | Descripción |
|-----------|-------------|
| `test_rentabilidad_bruta_calculation` | Verifica fórmula básica |
| `test_cash_flow_with_mortgage` | Cash flow con hipoteca |
| `test_scenarios_generation` | 3 escenarios correctos |
| `test_invalid_inputs_raise_error` | Validación de inputs |
| `test_edge_case_zero_mortgage` | Compra sin financiación |

## 📊 Métricas de Éxito

| KPI | Target | Medición |
|-----|--------|----------|
| Tiempo de cálculo | < 500ms | pytest-benchmark |
| Cobertura tests | > 80% | pytest-cov |
| Precisión cálculos | ±0.01% | Validación manual |
| UX satisfacción | > 4/5 | Feedback usuarios |

## 🚀 Future Enhancements

- [ ] Integración con tipos hipotecarios reales (API banco)
- [ ] Exportación de informe PDF
- [ ] Comparativa multi-propiedad
- [ ] Simulación de reformas y su impacto
- [ ] Alertas cuando precio baja en barrio guardado

## 📚 Referencias

- [NumPy Financial Docs](https://numpy.org/numpy-financial/)
- [Fiscalidad inmobiliaria Cataluña](https://atc.gencat.cat/)
- [Calculadora rentabilidad Idealista](https://www.idealista.com/news/finanzas/calculadoras/)

