---
title: [FEAT-02] Investment Calculator - Tests Unitarios
labels: ["sprint-1", "priority-high", "type-test", "area-analytics", "effort-s"]
milestone: "Quick Wins Foundation"
assignees: ["prototyp33"]
---

## 🎯 Contexto

**Feature ID:** #2 del análisis comparativo  
**Sprint:** Sprint 1 (Semanas 1-4)  
**Milestone:** Quick Wins Foundation  
**Esfuerzo estimado:** 3 horas  
**Fecha límite:** 2025-12-20  

**Dependencias:**
- #3: [FEAT-02] Investment Calculator - Core Logic (debe estar completado)

**Bloqueadores:**
- Ninguno conocido (si #3 está listo)

**Documentación relacionada:**
- 📄 [Feature Doc](docs/features/feature-02-calculator.md)
- 📄 [Pytest Documentation](https://docs.pytest.org/)

---

## 📝 Descripción

Suite completa de tests unitarios para validar todos los cálculos financieros del calculador de inversión. Los tests deben cubrir casos normales, edge cases, y validación de inputs.

**Valor de Negocio:**
Garantiza que los cálculos financieros son correctos y previene regresiones. Esencial para confianza en la herramienta.

**User Story:**
> Como desarrollador, necesito tests que validen todos los cálculos financieros para asegurar que la calculadora es precisa y confiable.

---

## 🔧 Componentes Técnicos

### Archivos a crear:

- [ ] `tests/test_investment_calculator.py` - Suite de tests principal
- [ ] `tests/fixtures/investment_fixtures.py` - Fixtures reutilizables (opcional)

### Estructura de Tests

```python
# tests/test_investment_calculator.py

import pytest
from src.analytics.investment_calculator import (
    InvestmentInputs,
    InvestmentMetrics,
    calcular_gastos_compra,
    calcular_cuota_hipoteca,
    calcular_metricas_inversion,
    generar_escenarios
)

class TestGastosCompra:
    """Tests para cálculo de gastos de compra."""
    
    def test_itp_cataluna_10_porciento(self):
        """Verifica que ITP es 10% en Cataluña."""
        gastos = calcular_gastos_compra(250000)
        assert gastos["itp"] == 25000.0
    
    def test_notaria_minimo_500(self):
        """Verifica que notaría tiene mínimo 500€."""
        gastos = calcular_gastos_compra(50000)  # 0.5% sería 250€
        assert gastos["notaria"] >= 500.0
    
    def test_registro_minimo_300(self):
        """Verifica que registro tiene mínimo 300€."""
        gastos = calcular_gastos_compra(50000)
        assert gastos["registro"] >= 300.0
    
    def test_total_gastos_compra(self):
        """Verifica que total es suma de todos los gastos."""
        gastos = calcular_gastos_compra(250000)
        total_calculado = gastos["itp"] + gastos["notaria"] + gastos["registro"] + gastos["gestoria"]
        assert abs(gastos["total"] - total_calculado) < 0.01


class TestCuotaHipoteca:
    """Tests para cálculo de cuota hipoteca."""
    
    def test_cuota_hipoteca_standard(self):
        """Verifica cálculo de cuota con parámetros estándar."""
        cuota = calcular_cuota_hipoteca(200000, 3.5, 25)
        # Cuota esperada aproximadamente 1000€/mes
        assert 900 < cuota < 1100
    
    def test_cuota_sin_interes(self):
        """Verifica cálculo con 0% interés."""
        cuota = calcular_cuota_hipoteca(200000, 0.0, 25)
        # Sin interés, cuota = capital / número de pagos
        expected = 200000 / (25 * 12)
        assert abs(cuota - expected) < 0.01
    
    def test_cuota_plazo_corto(self):
        """Verifica que plazo corto aumenta cuota."""
        cuota_25 = calcular_cuota_hipoteca(200000, 3.5, 25)
        cuota_10 = calcular_cuota_hipoteca(200000, 3.5, 10)
        assert cuota_10 > cuota_25


class TestMetricasInversion:
    """Tests para cálculo de métricas de inversión."""
    
    @pytest.fixture
    def inputs_standard(self):
        """Fixture con inputs estándar."""
        return InvestmentInputs(
            precio_compra=250000,
            metros_cuadrados=80,
            barrio_id=1,
            alquiler_mensual=1200,
            gastos_comunidad=100,
            ibi_anual=500,
            porcentaje_financiacion=80.0,
            tipo_interes=3.5,
            plazo_hipoteca=25
        )
    
    def test_rentabilidad_bruta_calculation(self, inputs_standard):
        """Verifica cálculo de rentabilidad bruta."""
        metrics = calcular_metricas_inversion(inputs_standard)
        expected = (inputs_standard.alquiler_mensual * 12 / inputs_standard.precio_compra) * 100
        assert abs(metrics.rentabilidad_bruta - expected) < 0.01
    
    def test_cash_flow_positive(self, inputs_standard):
        """Verifica que cash flow es positivo con inputs razonables."""
        metrics = calcular_metricas_inversion(inputs_standard)
        assert metrics.cash_flow_mensual > 0
    
    def test_cash_flow_negative_high_mortgage(self, inputs_standard):
        """Verifica que cash flow puede ser negativo con hipoteca alta."""
        inputs_high_mortgage = InvestmentInputs(
            **{**inputs_standard.__dict__, "tipo_interes": 10.0}
        )
        metrics = calcular_metricas_inversion(inputs_high_mortgage)
        # Con interés alto, cash flow puede ser negativo
        assert metrics.cash_flow_mensual < 0
    
    def test_payback_calculation(self, inputs_standard):
        """Verifica cálculo de payback."""
        metrics = calcular_metricas_inversion(inputs_standard)
        assert metrics.payback_years > 0
        assert metrics.payback_years < 50  # Razonable
    
    def test_van_tir_consistency(self, inputs_standard):
        """Verifica que VAN y TIR son consistentes."""
        metrics = calcular_metricas_inversion(inputs_standard)
        # Si TIR > tasa descuento, VAN debe ser positivo
        if metrics.tir > 3.0:  # Tasa descuento usada en cálculo
            assert metrics.van > 0


class TestValidacionInputs:
    """Tests para validación de inputs."""
    
    def test_precio_compra_negativo_raise_error(self):
        """Verifica que precio negativo lanza ValueError."""
        inputs = InvestmentInputs(
            precio_compra=-1000,  # Inválido
            metros_cuadrados=80,
            barrio_id=1,
            alquiler_mensual=1200
        )
        with pytest.raises(ValueError, match="precio_compra"):
            calcular_metricas_inversion(inputs)
    
    def test_alquiler_negativo_raise_error(self):
        """Verifica que alquiler negativo lanza ValueError."""
        inputs = InvestmentInputs(
            precio_compra=250000,
            metros_cuadrados=80,
            barrio_id=1,
            alquiler_mensual=-100  # Inválido
        )
        with pytest.raises(ValueError, match="alquiler_mensual"):
            calcular_metricas_inversion(inputs)
    
    def test_porcentaje_financiacion_out_of_range(self):
        """Verifica que porcentaje fuera de rango se maneja correctamente."""
        # Esto debería validarse o normalizarse
        inputs = InvestmentInputs(
            precio_compra=250000,
            metros_cuadrados=80,
            barrio_id=1,
            alquiler_mensual=1200,
            porcentaje_financiacion=150.0  # >100%
        )
        # Debería lanzar error o normalizar a 100%
        # Implementar según diseño


class TestEdgeCases:
    """Tests para casos límite."""
    
    def test_zero_mortgage(self):
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
        # Sin hipoteca, cash flow debe ser mayor
    
    def test_100_percent_mortgage(self):
        """Verifica cálculo con 100% financiación."""
        inputs = InvestmentInputs(
            precio_compra=250000,
            metros_cuadrados=80,
            barrio_id=1,
            alquiler_mensual=1200,
            porcentaje_financiacion=100.0
        )
        metrics = calcular_metricas_inversion(inputs)
        assert metrics.cash_flow_mensual is not None
    
    def test_very_high_rent(self):
        """Verifica cálculo con alquiler muy alto."""
        inputs = InvestmentInputs(
            precio_compra=250000,
            metros_cuadrados=80,
            barrio_id=1,
            alquiler_mensual=5000  # Muy alto
        )
        metrics = calcular_metricas_inversion(inputs)
        assert metrics.rentabilidad_bruta > 20  # Muy rentable


class TestEscenarios:
    """Tests para generación de escenarios."""
    
    @pytest.fixture
    def inputs_base(self):
        return InvestmentInputs(
            precio_compra=250000,
            metros_cuadrados=80,
            barrio_id=1,
            alquiler_mensual=1200
        )
    
    def test_generar_escenarios_retorna_tres(self, inputs_base):
        """Verifica que se generan 3 escenarios."""
        escenarios = generar_escenarios(inputs_base)
        assert len(escenarios) == 3
        assert "pesimista" in escenarios
        assert "base" in escenarios
        assert "optimista" in escenarios
    
    def test_escenarios_orden_correcto(self, inputs_base):
        """Verifica que escenarios están en orden lógico."""
        escenarios = generar_escenarios(inputs_base)
        assert escenarios["pesimista"].rentabilidad_neta < escenarios["base"].rentabilidad_neta
        assert escenarios["optimista"].rentabilidad_neta > escenarios["base"].rentabilidad_neta
    
    def test_escenarios_variacion_correcta(self, inputs_base):
        """Verifica que variación de alquiler es correcta."""
        escenarios = generar_escenarios(inputs_base, variacion_alquiler=0.10)
        # Pesimista: -10%, Optimista: +10%
        # Verificar que diferencias son aproximadamente 10%
        diff_pesimista = (inputs_base.alquiler_mensual - escenarios["pesimista"].rentabilidad_neta) / inputs_base.alquiler_mensual
        # Nota: Esto es una simplificación, ajustar según implementación real
```

---

## ✅ Criterios de Aceptación

- [ ] Tests para `calcular_gastos_compra()` (4+ tests)
- [ ] Tests para `calcular_cuota_hipoteca()` (3+ tests)
- [ ] Tests para `calcular_metricas_inversion()` (5+ tests)
- [ ] Tests para validación de inputs (3+ tests)
- [ ] Tests para edge cases (3+ tests)
- [ ] Tests para `generar_escenarios()` (3+ tests)
- [ ] Cobertura >80% en `investment_calculator.py`
- [ ] Todos los tests pasan en CI
- [ ] Fixtures reutilizables para inputs comunes

---

## 🧪 Plan de Testing

### Ejecutar Tests

```bash
# Tests unitarios
pytest tests/test_investment_calculator.py -v

# Con coverage
pytest tests/test_investment_calculator.py \
  --cov=src/analytics/investment_calculator \
  --cov-report=term-missing \
  --cov-report=html

# Target: >80% coverage
```

### Casos de Test Requeridos

| Test Case | Descripción | Prioridad |
|-----------|-------------|-----------|
| `test_itp_cataluna_10_porciento` | Verifica ITP 10% | 🔴 Alta |
| `test_cuota_hipoteca_standard` | Verifica cálculo cuota | 🔴 Alta |
| `test_rentabilidad_bruta_calculation` | Verifica fórmula básica | 🔴 Alta |
| `test_cash_flow_positive` | Cash flow positivo | 🔴 Alta |
| `test_escenarios_orden_correcto` | 3 escenarios correctos | 🟡 Media |
| `test_invalid_inputs_raise_error` | Validación de inputs | 🟡 Media |
| `test_edge_case_zero_mortgage` | Sin financiación | 🟢 Baja |
| `test_van_tir_consistency` | Consistencia VAN/TIR | 🟢 Baja |

---

## 📊 Métricas de Éxito

| KPI | Target | Medición |
|-----|--------|----------|
| **Cobertura de código** | >80% | pytest-cov |
| **Tests pasando** | 100% | pytest |
| **Tiempo de ejecución** | < 5 segundos | pytest |

---

## 🚧 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Tests flaky | Baja | Medio | Usar valores fijos, mockear dependencias |
| Cobertura insuficiente | Media | Medio | Añadir tests incrementalmente |
| Fórmulas incorrectas | Baja | Alto | Validar con casos reales conocidos |

---

## 📚 Referencias

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Coverage.py](https://coverage.readthedocs.io/)

---

## 🔗 Issues Relacionadas

- #3: [FEAT-02] Investment Calculator - Core Logic (dependencia)
- #4: [FEAT-02] Investment Calculator - UI Streamlit

---

## 📝 Notas de Implementación

### Orden de Implementación

1. **Paso 1:** Crear estructura básica de tests
   - Crear archivo `test_investment_calculator.py`
   - Importar funciones a testear

2. **Paso 2:** Tests de funciones auxiliares
   - `test_calcular_gastos_compra()`
   - `test_calcular_cuota_hipoteca()`

3. **Paso 3:** Tests de función principal
   - `test_calcular_metricas_inversion()`
   - Tests de métricas individuales

4. **Paso 4:** Tests de validación
   - Inputs inválidos
   - Edge cases

5. **Paso 5:** Tests de escenarios
   - Generación de 3 escenarios
   - Orden correcto

6. **Paso 6:** Verificar cobertura
   - Ejecutar con `--cov`
   - Añadir tests para alcanzar >80%

---

**Creado:** 2025-12-03  
**Última actualización:** 2025-12-03

