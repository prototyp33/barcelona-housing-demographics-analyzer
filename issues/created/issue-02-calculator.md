---
title: [FEATURE-02] Calculadora de Viabilidad de Inversión
labels: sprint-1, priority-high, type-feature, area-analytics
milestone: 1
---

## 🎯 Contexto
**Feature ID:** #02
**Sprint:** Sprint 1 (Quick Wins)
**Esfuerzo estimado:** 15-20h

## 📝 Descripción
Herramienta interactiva para evaluar la rentabilidad de inversiones inmobiliarias en Barcelona. Permitirá a los usuarios calcular ROI, Cash Flow y métricas clave considerando la fiscalidad local.

## 🔧 Componentes Técnicos
- [ ] `src/analytics/investment_calculator.py`: Lógica financiera (TIR, VAN, Amortización)
- [ ] `src/app/pages/investment_simulator.py`: Interfaz de usuario en Streamlit
- [ ] `tests/test_investment_calculator.py`: Tests unitarios de fórmulas financieras

## ✅ Criterios de Aceptación
- [ ] Cash flow mensual calculado correctamente
- [ ] Simulación de 3 escenarios (pesimista, base, optimista)
- [ ] Integración de impuestos (ITP, AJD) y gastos de comunidad
- [ ] Visualización gráfica de retorno acumulado a 10 años

