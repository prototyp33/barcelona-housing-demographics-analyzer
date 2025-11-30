# 📉 Baseline Report - 2025 Q4

**Fecha de Corte:** Noviembre 2025
**Versión:** v1.0 (Pre-Expansion)

Este documento establece el punto de partida métrico del proyecto antes de iniciar el roadmap de expansión de datos (Q1 2026). Servirá para medir el éxito de las nuevas implementaciones.

---

## 1. Métricas de Inventario de Datos

| Dataset | Registros | Cobertura Temporal | Cobertura Geográfica | Estado |
|---------|-----------|-------------------|----------------------|--------|
| **Precios Vivienda** | 6,358 | 2012 - 2025 (14 años) | 100% Barrios (73/73) | ✅ Saludable |
| **Demografía** | 657 | 2015 - 2023 (9 años) | 100% Barrios | ✅ Saludable |
| **Renta** | 73 | 2022 (1 año) | 100% Barrios | ❌ Crítico (Sin histórico) |
| **Oferta Idealista** | 0 | N/A | 0% | ❌ Sin datos |

### Desglose de Precios
- **Venta:** ~86.4% de los registros.
- **Alquiler:** ~13.6% de los registros (~70 registros/año). ⚠️ **Gap importante**.

---

## 2. KPIs de Negocio (Estado Actual)

### Asequibilidad
- **Índice de Asequibilidad:** No calculable (falta renta histórica).
- **Ratio Precio/Renta (2022):** Calculable solo para un año estático.

### Mercado
- **Yield Bruto (Rentabilidad):** Calculable, pero con baja confianza en alquiler debido a la muestra pequeña.
- **Volumen de Mercado:** Desconocido (sin datos de transacciones).

---

## 3. Infraestructura y Calidad

- **Pipeline ETL:** Funcional, basado en scripts locales.
- **Tests:** Unitarios básicos + Smoke Test de Pipeline implementado.
- **Documentación:** Project Charter y Roadmap definidos.
- **Automatización:** GitHub Actions pendientes de configuración.

---

## 4. Objetivos Q1 2026 (Target)

1. **Renta Histórica:** Obtener serie 2015-2023 (8+ años).
2. **Alquiler:** Aumentar registros a >400/año.
3. **Indicadores Sociales:** Añadir al menos 3 métricas (Paro, Estudios, Hogares).
4. **Dashboard:** Publicar pestaña de "Vulnerabilidad" y "Asequibilidad".

---

*Este reporte se actualizará al finalizar el Q1 2026 para comparar progreso.*

