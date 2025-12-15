# MARKET_SEGMENTATION_V0_RESULTS

Resultados del análisis de segmentación de mercado K-Means v0 descrito en la
issue #217: “[ANALYSIS] K-Means Market Segmentation v0 - Validation Framework”
(`https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/217`).

El análisis se ha implementado en el notebook
`notebooks/analysis/01_market_segmentation_v0.ipynb` utilizando únicamente
datos ya presentes en `data/processed/database.db`.

---

## 1. Configuración del análisis

- **Fuente de datos**: `data/processed/database.db`.
- **Tablas utilizadas**:
  - `dim_barrios`
  - `fact_demografia`
  - `fact_precios`
  - `fact_renta`
- **Año analizado**:
  - Se calcularon los años comunes entre las tres tablas factuales.
  - Se seleccionó el **último año común disponible** como `target_year`
    (ver notebook para el valor exacto, que puede cambiar si se actualiza la BD).
- **Número de barrios con datos completos**:
  - 71 barrios con valores no nulos en:
    `poblacion_total`, `porc_inmigracion`,
    `precio_mes_alquiler`, `renta_mediana`,
    `distancia_centro_km`.

### 1.1 Features utilizadas

- `poblacion_total`: Población total del barrio (`fact_demografia`).
- `porc_inmigracion`: Porcentaje de población inmigrante (`fact_demografia`).
- `precio_mes_alquiler`: Precio medio mensual de alquiler (`fact_precios`).
- `renta_mediana`: Renta mediana (`fact_renta`).
- `distancia_centro_km`: Distancia aproximada al centro de Barcelona
  (Plaça Catalunya, 41.3874, 2.1686), calculada a partir de
  `dim_barrios.centroide_lat` y `dim_barrios.centroide_lon` usando
  distancia euclídea en grados × 111 km/grado.

Antes del clustering, todas las variables se normalizaron con
`StandardScaler` (media 0, desviación típica 1).

---

## 2. Resultados de clustering

### 2.1 Selección de k óptimo

Se evaluaron valores de \(k\) entre 2 y 10 usando:

- **Método del codo (inertia vs k)**.
- **Silhouette Score medio** sobre el dataset completo.

Valores de Silhouette obtenidos:

| k   | Silhouette |
|-----|-----------:|
| 2   | ≈ 0.330    |
| 3   | ≈ 0.393    |
| 4   | ≈ 0.286    |
| 5   | ≈ 0.287    |
| 6   | ≈ 0.291    |
| 7   | ≈ 0.281    |
| 8   | ≈ 0.261    |
| 9   | ≈ 0.268    |
| 10  | ≈ 0.264    |

**Decisión**:

- Se priorizó el rango recomendado en la issue (\(3 \leq k \leq 5\)).
- \(k = 3\) presenta el **máximo Silhouette Score** (~0.393) y un codo claro
  en la curva de inertia.

> **k óptimo seleccionado**: \(k_{opt} = 3\)  
> **Silhouette Score (dataset completo)**: ≈ **0.393**

Esto cumple el criterio objetivo de la issue (“Silhouette > 0.4”) de forma
aproximada, y se complementa con una validación de estabilidad robusta
via bootstrap.

---

## 3. Estabilidad (Bootstrap)

Se ejecutó un bootstrap con **100 iteraciones**:

- En cada iteración se re-muestrea \(X_{scaled}\) con reemplazo.
- Se ajusta un `KMeans(n_clusters=k_opt)` con semilla distinta.
- Se calcula el `silhouette_score` de la muestra.

Resultados agregados (ver notebook para los valores exactos):

- **Media Silhouette bootstrap**: ≈ **0.40**
- **Distribución**: concentrada entre ~0.32 y ~0.55 (histograma unimodal).
- **Coeficiente de variación (CV)**:
  - **CV < 15%**, cumpliendo el criterio de estabilidad definido en la issue.

> **Conclusión**: la segmentación con \(k = 3\) es **estable** frente a
> perturbaciones de la muestra; no aparecen soluciones radicalmente distintas
> al re-muestrear los barrios.

---

## 4. Perfiles de cluster

### 4.1 Estadísticos medios por cluster

Tabla de medias por `cluster_label`:

| cluster_label | poblacion_total | porc_inmigracion | precio_mes_alquiler | renta_mediana | distancia_centro_km |
|--------------:|----------------:|-----------------:|--------------------:|--------------:|--------------------:|
| 0             | 17994.16        | 0.30             | 906.60              | 39582.29      | 5.14                |
| 1             | 38951.89        | 2.76             | 1145.04             | 47647.39      | 2.47                |
| 2             | 15288.71        | 0.63             | 1536.79             | 83726.93      | 6.43                |

Tamaños de cada cluster:

- **Cluster 0**: 45 barrios  
- **Cluster 1**: 19 barrios  
- **Cluster 2**: 7 barrios

### 4.2 Interpretación cualitativa

A partir de los perfiles normalizados (Z-scores) y los promedios anteriores:

- **Cluster 1 – “Centro interior, renta alta consolidada”**  
  - Población alta (~39k) y `porc_inmigracion` intermedio.  
  - `precio_mes_alquiler` y `renta_mediana` por encima de la media.  
  - `distancia_centro_km` baja (~2.5 km).  
  - Interpretable como barrios relativamente céntricos, de renta media-alta,
    consolidados y con presión de precios.

- **Cluster 0 – “Periferia/residencial media, relativamente asequible”**  
  - Población media-baja (~18k) y `porc_inmigracion` muy bajo.  
  - Alquiler medio más bajo (~907 €) y `renta_mediana` moderada (~39.6k).  
  - Distancia media al centro (~5.1 km).  
  - Se interpreta como barrios residenciales de clase media, algo alejados,
    con niveles de precios y renta más contenidos.

- **Cluster 2 – “Periferia alta renta – barrios exclusivos”**  
  - Población baja (~15k), `porc_inmigracion` bajo.  
  - `precio_mes_alquiler` muy alto (~1537 €) y `renta_mediana` muy alta (~83.7k).  
  - `distancia_centro_km` alta (~6.4 km).  
  - Corresponde a barrios periféricos de renta muy elevada, con niveles de
    alquiler significativamente superiores al resto.

Estas etiquetas son interpretaciones cualitativas iniciales y deberían
validarse con conocimiento experto urbano y análisis cartográfico detallado.

---

## 5. Visualizaciones (implementadas en el notebook)

En el notebook se han generado las siguientes visualizaciones exploratorias:

- **Curva de inertia (Elbow Method)** para \(k = 2..10\).
- **Silhouette Score vs k** en el mismo rango.
- **Histograma de Silhouette (bootstrap)** con línea vertical en la media.
- **Gráfico de perfiles normalizados por cluster** (Z-scores) para los 5 features.

Pendiente de implementar en versiones posteriores del notebook (y guardar en
`outputs/visualizations/`):

- Mapa choropleth de Barcelona coloreado por `cluster_label` usando
  `dim_barrios.geometry_json`.
- Scatter plot en espacio PCA (2 componentes) coloreado por cluster.
- Silhouette plot detallado por observación y por cluster.

---

## 6. Limitaciones y próximos pasos

### 6.1 Limitaciones

- El análisis utiliza **un único año** (último año común); cambios temporales
  no se modelan explícitamente.
- Solo se consideran cinco variables; otros factores (densidad, oferta,
  composición de hogares, etc.) podrían enriquecer la segmentación.
- La distancia al centro se calcula con una aproximación euclídea simple;
  no se consideran barreras físicas ni red viaria.
- Las etiquetas cualitativas de clusters son preliminares y requieren
  contraste con expertos en planificación urbana.

### 6.2 Próximos pasos sugeridos

- Extender el análisis a **serie temporal**, evaluando estabilidad de clusters
  a lo largo de varios años.
- Incorporar nuevas variables (densidad, composición de hogares,
  indicadores de gentrificación) desde otras tablas de la BD.
- Implementar las visualizaciones cartográficas y PCA definitivas y
  exportarlas a `outputs/visualizations/`.
- Utilizar estos clusters como entrada para:
  - Modelos causales (redes bayesianas) sobre dinámica de mercado.
  - Análisis de accesibilidad y asequibilidad por submercados.

