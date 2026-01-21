# Plan de Implementación: Dashboard Streamlit v3.0 (Intelligence & Social Impact)

Este documento detalla el plan para integrar los análisis avanzados de series temporales y gentrificación en el dashboard de Streamlit.

## 1. Visión General

El objetivo es transformar el dashboard de una herramienta puramente descriptiva a una plataforma **predictiva y de impacto social**, permitiendo a los stakeholders no solo ver el pasado, sino anticipar tendencias y entender los riesgos territoriales.

---

## 2. Fase 1: Inteligencia Predictiva (Foretell View)

Integración de los resultados del análisis de series temporales (`03_time_series_analysis.ipynb`).

### Características:

- **Forecast 2026-2027**: Gráfico interactivo con bandas de confianza para la evolución del precio de venta.
- **Índice de Volatilidad**: Mapa de calor indicando qué distritos son más "nerviosos" (ej. Sant Martí) vs cuáles son estables (ej. Eixample).
- **Resiliencia Post-COVID**: KPIs que muestran la velocidad de recuperación de cada distrito tras el shock de 2020.

### Implementación:

- Crear `src/app/views/intelligence.py`.
- Cargar datos desde `notebooks/exports/predicciones_precios_2026_2027.csv`.

---

## 3. Fase 2: Monitor de Gentrificación e Impacto Social

Integración del análisis de gentrificación (`04_gentrification_analysis.ipynb`).

### Características:

- **Gentrification Risk Map**: Mapa coroplético ponderando:
  - Incremento de precios de oferta (2012-2024).
  - Densidad de licencias turísticas (Airbnb).
  - Variación en el nivel de renta (sustitución poblacional).
- **Cluster de Vulnerabilidad**: Identificación de barrios con "alto riesgo de desplazamiento" (Renta estable + Precios disparados).

### Implementación:

- Crear `src/app/views/social_impact.py`.
- Usar `notebooks/exports/analisis_gentrificacion_barcelona.csv`.

---

## 4. Fase 3: Simulador de Inversión Avanzado

Evolución de la pestaña actual de Inversión.

### Características:

- **Calculadora de ROI Dinámica**: Permite al usuario proyectar su retorno no solo con la renta actual, sino con la **predicción de plusvalía** del modelo ARIMA.
- **Alertas Predictivas**: Notificaciones sobre barrios que están por entrar en una fase de "pico" de crecimiento según el ciclo histórico.

---

## 5. Fase 4: Refactorización y UX

- **Menú de Navegación**: Agrupar vistas en categorías (Descriptivo, Predictivo, Social).
- **Performance**: Implementar `@st.cache_data` para las consultas pesadas de consolidación de datos.
- **Diseño**: Actualizar `styles.py` para incluir micro-animaciones en los nuevos KPIs de riesgo.

---

## 6. Próximos Notebooks Sugeridos (Antes de Dashboard)

Para completar la visión 3.0, se recomienda:

1. `06_public_housing_analysis.ipynb`: Impacto de la vivienda pública en los precios de mercado.
2. `07_neighborhood_amenities.ipynb`: Relación entre servicios (hospitales, parques, colegios) y el precio m2.

---

## Cronograma Estimado

- **Día 1**: Integración de Time Series (Vistas y Datos).
- **Día 2**: Integración de Gentrificación y Mapas de Riesgo.
- **Día 3**: Pulido de UI y Pruebas de Calidad.
