# Arquitectura de Datos v2.0 - Expansión de Variables

**Fecha:** Diciembre 2025  
**Versión:** 2.0  
**Estado:** Propuesta Ejecutiva

---

## Resumen

Esta propuesta expande la arquitectura de datos actual para capturar **33 variables adicionales** que afectan los precios de vivienda en Barcelona, organizadas en **8 nuevas tablas fact** y **2 nuevas tablas dimension**, manteniendo compatibilidad con el esquema star existente.

**Documentos relacionados:**
- `ARQUITECTURA_DATOS_VARIABLES.md` - Documento técnico completo
- `RESUMEN_EJECUTIVO_ARQUITECTURA.md` - Resumen ejecutivo
- `mapeo_variables_extractores.csv` - Matriz de mapeo completo

---

## Impacto del Proyecto

| Métrica | Actual | Propuesto | Mejora |
|---------|--------|-----------|--------|
| Variables analizables | 12 | 45+ | +375% |
| Tablas fact | 5 | 13 | +160% |
| Tablas dimension | 1 | 3 | +200% |
| Extractores | 6 | 18 | +200% |
| Cobertura temporal | 2015-2025 | 2010-2025 | +5 años |
| Fuentes de datos | 8 | 16+ | +100% |

---

## Nuevas Tablas Propuestas

### Tablas Fact (8 nuevas)

1. **fact_hogares** - Composición de hogares por tamaño
2. **fact_socioeconomic** - Desempleo, salarios, educación
3. **fact_construccion** - Visados, nuevas construcciones
4. **fact_movilidad** - Flujos poblacionales inter-barrios
5. **fact_turismo** - HUTs, Airbnb, ocupación turística
6. **fact_regulacion** - Control alquileres, vivienda pública
7. **fact_eficiencia** - Eficiencia energética, conservación
8. **fact_financiera** - Euribor, tipos hipotecarios

### Tablas Dimension (2 nuevas)

1. **dim_barrios_metricas** - Centralidad, accesibilidad, equipamientos
2. **dim_barrios_ambiente** - Calidad aire, ruido, zonas verdes

---

## Extractores a Implementar (12 nuevos)

### Fase 2: Críticos (Semanas 3-6)
- DesempleoExtractor (SEPE)
- EducacionExtractor (Open Data BCN)
- HUTExtractor (Ajuntament)
- AirbnbExtractor (Inside Airbnb)

### Fase 3: Complementarios (Semanas 7-10)
- VisadosExtractor (Colegio Arquitectos)
- ControlAlquilerExtractor (Generalitat)
- CentralidadExtractor (Cálculo geométrico)
- AccesibilidadExtractor (TMB/GTFS)
- EficienciaEnergeticaExtractor (Portal Dades)
- AmbienteExtractor (Ajuntament)

### Fase 4: Adicionales
- HogaresExtractor
- MovilidadExtractor
- SalarioExtractor
- StockExtractor
- EquipamientosExtractor
- TurismoExtractor
- EuriborExtractor
- HipotecasExtractor

---

## Plan de Implementación

**Duración:** 12 semanas  
**Esfuerzo:** 446 horas  
**Equipo:** 4 developers en paralelo

**Fases:**
1. Infraestructura (Semanas 1-2): 22h
2. Extractores Críticos (Semanas 3-6): 170h
3. Extractores Complementarios (Semanas 7-10): 170h
4. Integración (Semanas 11-12): 84h

---

## Capacidades Analíticas Desbloqueadas

1. Elasticidad precio-demanda multivariable
2. Análisis de gentrificación (5+ indicadores)
3. Análisis regulatorio (control alquileres)
4. Impacto turístico (HUTs/Airbnb vs residencia)
5. Valoración ambiental (eficiencia energética)
6. Proyecciones de precios (15+ variables)
7. Segmentación avanzada de barrios
8. Análisis de asequibilidad residencial
9. Comparaciones temporales (2010-2025)
10. Movilidad poblacional

---

## Referencias

- **Documento Técnico Completo:** `docs/architecture/ARQUITECTURA_DATOS_VARIABLES.md`
- **Resumen Ejecutivo:** `docs/RESUMEN_EJECUTIVO_ARQUITECTURA.md`
- **Mapeo de Variables:** `data/reference/mapeo_variables_extractores.csv`
- **Diagrama Visual:** `docs/architecture/arquitectura_visual.txt`

---

**Última actualización:** Diciembre 2025

