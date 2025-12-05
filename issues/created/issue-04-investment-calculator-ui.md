---
title: [FEAT-02] Investment Calculator - UI Streamlit
labels: ["sprint-1", "priority-high", "type-feature", "area-ui", "effort-m"]
milestone: "Quick Wins Foundation"
assignees: ["prototyp33"]
---

## 🎯 Contexto

**Feature ID:** #2 del análisis comparativo  
**Sprint:** Sprint 1 (Semanas 1-4)  
**Milestone:** Quick Wins Foundation  
**Esfuerzo estimado:** 6 horas  
**Fecha límite:** 2025-12-18  

**Dependencias:**
- #3: [FEAT-02] Investment Calculator - Core Logic (debe estar completado)

**Bloqueadores:**
- Ninguno conocido (si #3 está listo)

**Documentación relacionada:**
- 📄 [Feature Doc](docs/features/feature-02-calculator.md)
- 📄 [Streamlit Docs](https://docs.streamlit.io/)

---

## 📝 Descripción

Crear interfaz interactiva en Streamlit para el simulador de inversión inmobiliaria. La UI debe ser intuitiva, responsive, y mostrar todas las métricas calculadas por el core logic.

**Valor de Negocio:**
Permite a usuarios no técnicos usar la calculadora sin necesidad de código. Feature clave para demo del portfolio.

**User Story:**
> Como usuario, quiero introducir datos de una propiedad y ver inmediatamente si es una buena inversión, sin necesidad de entender fórmulas financieras.

---

## 🔧 Componentes Técnicos

### Archivos a crear:

- [ ] `src/app/pages/investment_simulator.py` - Página principal Streamlit
- [ ] `src/app/components/investment_widgets.py` - Componentes reutilizables (opcional)
- [ ] Tests de UI (opcional, validación manual)

### Estructura de la UI

```python
# src/app/pages/investment_simulator.py

import streamlit as st
import plotly.graph_objects as go
from src.analytics.investment_calculator import (
    InvestmentInputs,
    calcular_metricas_inversion,
    generar_escenarios
)

def main():
    st.set_page_config(
        page_title="Calculadora de Inversión",
        page_icon="🏠",
        layout="wide"
    )
    
    st.title("🏠 Calculadora de Viabilidad de Inversión")
    st.markdown("Evalúa la rentabilidad de inversiones inmobiliarias en Barcelona")
    
    # Sidebar con inputs
    with st.sidebar:
        st.header("📊 Parámetros de Inversión")
        
        # Inputs básicos
        barrio_id = st.selectbox(
            "📍 Barrio",
            options=get_barrios_list(),  # Función helper
            format_func=lambda x: f"{x['nombre']} ({x['codi_barri']})"
        )
        
        precio_compra = st.number_input(
            "💶 Precio de Compra (€)",
            min_value=50000,
            max_value=5000000,
            value=250000,
            step=10000
        )
        
        metros_cuadrados = st.number_input(
            "📐 Metros Cuadrados",
            min_value=20,
            max_value=500,
            value=80,
            step=5
        )
        
        alquiler_mensual = st.number_input(
            "🏷️ Alquiler Mensual Esperado (€)",
            min_value=300,
            max_value=5000,
            value=1200,
            step=50
        )
        
        # Sección avanzada (expandible)
        with st.expander("⚙️ Opciones Avanzadas"):
            gastos_comunidad = st.number_input(
                "Gastos de Comunidad (€/mes)",
                min_value=0,
                value=100,
                step=10
            )
            
            ibi_anual = st.number_input(
                "IBI Anual (€)",
                min_value=0,
                value=500,
                step=50
            )
            
            porcentaje_financiacion = st.slider(
                "Porcentaje de Financiación (%)",
                min_value=0,
                max_value=100,
                value=80,
                step=5
            )
            
            tipo_interes = st.number_input(
                "Tipo de Interés Anual (%)",
                min_value=0.0,
                max_value=10.0,
                value=3.5,
                step=0.1
            )
            
            plazo_hipoteca = st.number_input(
                "Plazo Hipoteca (años)",
                min_value=5,
                max_value=40,
                value=25,
                step=5
            )
    
    # Crear inputs object
    inputs = InvestmentInputs(
        precio_compra=precio_compra,
        metros_cuadrados=metros_cuadrados,
        barrio_id=barrio_id['codi_barri'],
        alquiler_mensual=alquiler_mensual,
        gastos_comunidad=gastos_comunidad,
        ibi_anual=ibi_anual,
        porcentaje_financiacion=porcentaje_financiacion,
        tipo_interes=tipo_interes,
        plazo_hipoteca=plazo_hipoteca
    )
    
    # Calcular métricas
    metrics = calcular_metricas_inversion(inputs)
    escenarios = generar_escenarios(inputs)
    
    # Layout principal: 2 columnas
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("💰 Métricas Principales")
        
        # KPIs en métricas
        kpi1, kpi2 = st.columns(2)
        with kpi1:
            st.metric("Rentabilidad Bruta", f"{metrics.rentabilidad_bruta:.2f}%")
            st.metric("Cash Flow Mensual", f"{metrics.cash_flow_mensual:.0f}€")
        with kpi2:
            st.metric("Rentabilidad Neta", f"{metrics.rentabilidad_neta:.2f}%")
            st.metric("Payback", f"{metrics.payback_years:.1f} años")
        
        # Tabla de costes iniciales
        st.subheader("💸 Costes Iniciales")
        # ... tabla con ITP, notaría, etc.
    
    with col2:
        st.header("📈 Análisis de Escenarios")
        
        # Comparativa de 3 escenarios
        escenarios_data = {
            "Pesimista": escenarios["pesimista"],
            "Base": escenarios["base"],
            "Optimista": escenarios["optimista"]
        }
        # ... visualización de escenarios
    
    # Gráfico de cash flow
    st.header("📊 Proyección de Cash Flow")
    fig = create_cash_flow_chart(inputs, metrics)
    st.plotly_chart(fig, use_container_width=True)

def create_cash_flow_chart(inputs, metrics):
    """Crea gráfico de cash flow acumulado."""
    # Implementar con Plotly
    pass

def get_barrios_list():
    """Obtiene lista de barrios desde la base de datos."""
    # Implementar query a SQLite
    pass
```

### Componentes UI Requeridos

1. **Formulario de Inputs**
   - Sidebar con todos los parámetros
   - Validación en tiempo real
   - Valores por defecto razonables

2. **Métricas Principales**
   - 4 KPIs principales (Rentabilidad Bruta/Neta, Cash Flow, Payback)
   - Formato visual atractivo

3. **Tabla de Costes**
   - Desglose de costes iniciales (ITP, notaría, registro, gestoría)
   - Total destacado

4. **Análisis de Escenarios**
   - Comparativa visual de 3 escenarios
   - Tabla o gráfico comparativo

5. **Gráfico de Cash Flow**
   - Proyección a 10 años
   - Cash flow acumulado
   - Interactivo con Plotly

---

## ✅ Criterios de Aceptación

- [ ] Formulario de inputs funcional con validación
- [ ] Métricas actualizadas en tiempo real al cambiar inputs
- [ ] Gráfico interactivo de cash flow (Plotly)
- [ ] Comparativa de 3 escenarios visible
- [ ] Responsive en mobile/tablet (Streamlit auto)
- [ ] Integración con datos de barrios (precio medio, tendencia)
- [ ] UI visualmente atractiva y profesional
- [ ] Sin errores en consola del navegador

---

## 🧪 Plan de Testing

### Testing Manual

1. **Test de Inputs:**
   - Probar valores extremos (sin financiación, 100% financiación)
   - Probar valores inválidos (debe mostrar error)
   - Verificar que métricas se actualizan al cambiar inputs

2. **Test de Visualización:**
   - Verificar que gráficos se renderizan correctamente
   - Verificar que escenarios se muestran correctamente
   - Verificar responsive en diferentes tamaños de pantalla

3. **Test de Integración:**
   - Verificar que datos de barrios se cargan correctamente
   - Verificar que cálculos coinciden con core logic

### Comandos para Ejecutar

```bash
# Ejecutar Streamlit localmente
streamlit run src/app/pages/investment_simulator.py

# Verificar que no hay errores
# Abrir http://localhost:8501
```

---

## 📊 Métricas de Éxito

| KPI | Target | Medición |
|-----|--------|----------|
| **Tiempo de carga** | < 2 segundos | Medición manual |
| **Responsive** | Funciona en mobile | Test manual |
| **UX satisfacción** | > 4/5 | Feedback interno |

---

## 🚧 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Performance con muchos cálculos | Baja | Medio | Caching de resultados |
| UI no responsive | Baja | Bajo | Streamlit es responsive por defecto |
| Integración con DB lenta | Media | Medio | Lazy loading de datos de barrios |

---

## 📚 Referencias

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly for Streamlit](https://plotly.com/python/streamlit/)
- [Feature Doc](docs/features/feature-02-calculator.md)

---

## 🔗 Issues Relacionadas

- #3: [FEAT-02] Investment Calculator - Core Logic (dependencia)
- #5: [FEAT-02] Investment Calculator - Tests

---

## 📝 Notas de Implementación

### Orden de Implementación

1. **Paso 1:** Crear estructura básica de la página
   - Layout con sidebar y contenido principal
   - Inputs básicos (precio, m², alquiler)

2. **Paso 2:** Integrar core logic
   - Importar funciones de `investment_calculator.py`
   - Calcular métricas al cambiar inputs

3. **Paso 3:** Añadir visualizaciones
   - KPIs con `st.metric()`
   - Gráfico de cash flow con Plotly

4. **Paso 4:** Añadir escenarios
   - Comparativa de 3 escenarios
   - Visualización atractiva

5. **Paso 5:** Integrar datos de barrios
   - Selector de barrios desde DB
   - Mostrar precio medio del barrio

6. **Paso 6:** Polish y testing
   - Validación de inputs
   - Mensajes de error claros
   - Testing manual completo

---

**Creado:** 2025-12-03  
**Última actualización:** 2025-12-03

