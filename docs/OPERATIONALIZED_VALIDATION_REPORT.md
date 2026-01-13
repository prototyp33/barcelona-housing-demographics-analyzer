# 📑 Reporte de Validación Operacionalizada de Cambios Extremos

**Fecha**: 2026-01-13

Este reporte integra lógica cualitativa de mercado para distinguir entre tendencias reales y artefactos de muestra, "codificando" el conocimiento experto en el proceso de validación.

## 📊 Resumen de Casos

| Barrio | Año | Cambio | Interpretación | Confianza |
|--------|-----|--------|----------------|-----------|
| la Marina del Prat Vermell | 2015 | +135.0% | VALID_GENTRIFICATION_TRANSITION | HIGH |
| Vallvidrera | 2016 | +117.6% | LIKELY_SAMPLE_COMPOSITION_ARTIFACT | LOW |
| Torre Baró | 2019 | +174.7% | LIKELY_SAMPLE_COMPOSITION_ARTIFACT | LOW |

---

### 📍 la Marina del Prat Vermell (2015)

- **Diagnóstico**: `VALID_GENTRIFICATION_TRANSITION`
- **Cambio**: +135.0% (611€ → 1436€)
- **Muestra**: n=5 (2014) | n=3 (2015)
- **Flags Detectados**: `BELOW_LOGIC_THRESHOLD_(1200)` (2014) / `LOW_N_SAMPLE` (2015)
- **Factor de Riesgo**: `GENTRIFICATION`
- **Notas Contextuales**: Refleja la transición de zona industrial a vivienda habitable. El precio de 611€ en 2014 es característico de suelo/industrial, no de vivienda terminada. El salto a 1436€ marca el inicio de la habitabilidad real del barrio.

### 📍 Vallvidrera (2016)

- **Diagnóstico**: `LIKELY_SAMPLE_COMPOSITION_ARTIFACT`
- **Cambio**: +117.6% (1731€ → 3767€)
- **Muestra**: n=3 (2015) | n=5 (2016)
- **Flags Detectados**: `LOW_N_SAMPLE`, `BELOW_LOGIC_THRESHOLD_(2500)` (2015) / `NONE` (2016)
- **Factor de Riesgo**: `SUBZONE_MIX`
- **Notas Contextuales**: Mezcla de zona noble de Vallvidrera y zona rural de Les Planes. El precio de 1731€ en 2015 es excesivamente bajo para Vallvidrera noble, sugiriendo que la muestra de ese año se centró en Les Planes o casas a reformar.

### 📍 Torre Baró (2019)

- **Diagnóstico**: `LIKELY_SAMPLE_COMPOSITION_ARTIFACT`
- **Cambio**: +174.7% (753€ → 2070€)
- **Muestra**: n=4 (2018) | n=4 (2019)
- **Flags Detectados**: `LOW_N_SAMPLE`, `BELOW_LOGIC_THRESHOLD_(800)` (2018) / `LOW_N_SAMPLE`, `ABOVE_LOGIC_THRESHOLD_(2200)` (2019)
- **Factor de Riesgo**: `NEW_BUILD_BIAS`
- **Notas Contextuales**: Barrio periférico con impacto significativo de obra nueva/VPO. El precio de 2070€ en 2019 supera incluso los precios actuales del barrio (2024), lo que confirma que se trata de una anomalía puntual por entrega de nuevas promociones que no representa la tendencia general.

## 🧠 Lógica de Validación Aplicada (Codificada en el Script)

1. **LOW_N_SAMPLE**: Activada cuando N < 5. Indica que estamos midiendo edificios específicos, no la tendencia general del mercado del barrio.
2. **LOGIC_THRESHOLD**: Activada cuando los precios escapan de los rangos históricos razonables definidos por el conocimiento del mercado de Barcelona.
3. **NEW_BUILD_ARTIFACT**: Específica para barrios periféricos como Torre Baró, donde una entrega de Obra Nueva o VPO distorsiona el promedio anual debido al bajo volumen de transacciones de segunda mano.
4. **GENTRIFICATION_TRANSITION**: Regla especial que valida saltos extremos en zonas de transformación urbana masiva como Marina del Prat Vermell.

## 🚀 Próximos Pasos Técnicos

- **Implementar Mediana Obligatoria**: En el pipeline ETL, forzar el uso de la mediana para cualquier barrio/año con `LOW_N_SAMPLE` activo.
- **Visualización de Flags**: Añadir estos flags de validación a la tabla maestra para que Looker Studio pueda mostrar advertencias visuales en los puntos de datos sospechosos.
- **Filtro de Obra Nueva**: Investigar la posibilidad de separar registros de Obra Nueva en la fuente de datos para evitar el `NEW_BUILD_BIAS`.
