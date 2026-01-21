# Notebooks de Análisis - Barcelona Housing Demographics

Este directorio contiene Jupyter Notebooks para el análisis exploratorio de datos (EDA) del proyecto Barcelona Housing Demographics Analyzer.

## 📚 Notebooks Disponibles

### 1. `01_exploratory_data_analysis.ipynb`

**Análisis Exploratorio de Datos Completo**

Contenido:

- ✅ Setup y conexión a base de datos
- ✅ Overview de datos (73 barrios, 10 distritos)
- ✅ Análisis de precios de vivienda (2012-2025)
  - Distribuciones y estadísticas
  - Evolución temporal
  - Top barrios más caros/baratos
  - Análisis por distrito
- ✅ Análisis demográfico
  - Distribución de población
  - Barrios más poblados
- ✅ Análisis de desempleo (2023-2024)
  - Distribución de tasas
  - Barrios con mayor/menor desempleo
- ✅ Presión turística (Airbnb 2011-2025)
  - Evolución temporal
  - Concentración por barrio
- ✅ Análisis de correlaciones
  - Matriz de correlaciones
  - Scatter plots interactivos
- ✅ Conclusiones y recomendaciones

**Visualizaciones**: 15+ gráficos (histogramas, líneas, barras, scatter plots, heatmaps)

---

### 2. `02_geospatial_analysis.ipynb`

**Análisis Geoespacial y Mapas**

Contenido:

- ✅ Setup con GeoPandas y Folium
- ✅ Mapas de precios
  - Mapa de calor estático
  - Mapa interactivo con tooltips
- ✅ Mapas demográficos
  - Densidad poblacional
- ✅ Mapas de desempleo
  - Distribución geográfica de tasas
- ✅ Mapas de presión turística
  - Concentración de Airbnb
- ✅ Análisis de clusters (K-Means)
  - Segmentación de barrios
  - Caracterización de clusters
  - Mapa de clusters

**Visualizaciones**: Mapas estáticos e interactivos, análisis de clustering

---

### 3. `03_time_series_analysis.ipynb` ⭐ NUEVO

**Análisis de Series Temporales y Forecasting**

Contenido:

- ✅ **Análisis de tendencias** (2012-2025)
  - Evolución de precios anuales
  - Tasa de crecimiento anual
  - Línea de tendencia y pendiente
- ✅ **Estacionalidad**
  - Análisis por trimestre
  - Boxplot estacional
  - Evolución trimestral
- ✅ **Puntos de inflexión**
  - Identificación de eventos clave
  - COVID-19, atentados 2017, recuperación post-crisis
  - Análisis de impacto
- ✅ **Análisis por barrio**
  - Evolución de barrios representativos
  - Volatilidad por barrio
  - Coeficiente de variación
- ✅ **Forecasting** (2026-2027)
  - Predicción con regresión lineal
  - Intervalos de confianza 95%
  - Métricas del modelo (R², MAE, RMSE)
- ✅ **Análisis de volatilidad**
  - Volatilidad por distrito
  - Rango de precios
  - Coeficiente de variación
- ✅ **Impacto COVID-19**
  - Comparación pre/durante/post COVID
  - Análisis de recuperación
  - Boxplot comparativo
- ✅ **Resumen ejecutivo**
  - Estadísticas principales
  - Predicciones 2026-2027
  - Insights clave
- ✅ **Exportación de resultados** (CSV)

**Visualizaciones**: 12+ gráficos (líneas, barras, boxplots, forecasting)

**Valor**: Identifica tendencias, predice precios futuros y analiza impacto de eventos históricos

---

### 4. `04_gentrification_analysis.ipynb`

**Análisis de Gentrificación**

Contenido:

- ✅ **Índice de Gentrificación** (0-100)
  - Cambio de precios 2012-2024
  - Presión turística (Airbnb)
  - Tasa de desempleo
  - Clasificación de riesgo (Muy Alto/Alto/Medio/Bajo/Muy Bajo)
- ✅ **Análisis de cambio de precios**
  - Top 15 barrios con mayor incremento
  - Correlación precio inicial vs incremento
- ✅ **Presión turística**
  - Top 10 barrios con más Airbnb
  - Correlación turismo vs precio
- ✅ **Desplazamiento poblacional**
  - Análisis de desempleo como proxy
  - Boxplot por nivel de riesgo
- ✅ **Barrios en riesgo**
  - Identificación de barrios críticos
  - Mapa de riesgo multidimensional
- ✅ **Mapas de gentrificación**
  - Mapa de calor del índice
  - Mapa categórico por nivel de riesgo
  - Etiquetas en barrios críticos
- ✅ **Resumen ejecutivo**
  - Estadísticas generales
  - Top 5 barrios más gentrificados
  - Factores clave y correlaciones
  - Recomendaciones de política pública
- ✅ **Exportación de resultados** (CSV)

**Visualizaciones**: 10+ gráficos + 2 mapas interactivos

**Valor**: Identifica barrios vulnerables, patrones de cambio urbano y genera recomendaciones accionables

---

## 🚀 Cómo Usar

### Requisitos

```bash
# Instalar dependencias
pip install jupyter pandas numpy matplotlib seaborn scipy geopandas folium scikit-learn
```

### Ejecutar Notebooks

```bash
# Desde el directorio raíz del proyecto
jupyter notebook notebooks/

# O ejecutar un notebook específico
jupyter notebook notebooks/01_exploratory_data_analysis.ipynb
```

### Desde VS Code

1. Abrir el notebook en VS Code
2. Seleccionar el kernel de Python (myenv)
3. Ejecutar celdas con `Shift + Enter`

---

## 📊 Datos Utilizados

Los notebooks se conectan a la base de datos SQLite:

- **Ubicación**: `data/processed/database.db`
- **Health Score**: 100/100 ✅
- **Total Registros**: 98,604
- **Tablas principales**:
  - `dim_barrios` - 73 barrios con geometrías
  - `fact_precios` - 6,358 registros (2012-2025)
  - `fact_demografia` - 73 registros
  - `fact_desempleo` - 1,752 registros (2023-2024)
  - `fact_presion_turistica` - 2,141 registros (2011-2025)

---

## 🎨 Estilo de Visualización

Los notebooks utilizan:

- **Matplotlib** con estilo `seaborn-v0_8-darkgrid`
- **Seaborn** con paleta `husl`
- **Folium** para mapas interactivos
- **GeoPandas** para análisis geoespacial

Configuración estándar:

```python
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 12
```

---

## 📁 Estructura de Outputs

Los notebooks pueden generar:

```
notebooks/
├── maps/                          # Mapas HTML interactivos
│   ├── mapa_precios_2024.html
│   ├── mapa_desempleo_2024.html
│   └── mapa_turismo_2024.html
└── exports/                       # Datos exportados
    ├── cluster_analysis.csv
    └── correlations.csv
```

---

## 🔍 Hallazgos Principales

### Precios de Vivienda

- **Media**: 3,161€/m² (2024)
- **Rango**: 343€ - 12,154€/m²
- **Crecimiento 2012-2025**: Significativo
- **Barrios más caros**: Pedralbes, Sarrià, Tres Torres
- **Barrios más baratos**: Periféricos (Nou Barris, Sant Andreu)

### Desempleo

- **Tasa media**: 6.27%
- **Rango**: 2.41% - 12.00%
- **Mayor desempleo**: Ciutat Meridiana (11.5%)
- **Menor desempleo**: Pedralbes (2.7%)
- **Correlación negativa** con precio de vivienda

### Presión Turística

- **Distribución**: Altamente sesgada
- **Concentración**: Ciutat Vella (centro histórico)
- **Crecimiento**: Exponencial 2011-2019
- **Correlación positiva** con precio de vivienda

---

## 🎯 Próximos Pasos

Después de ejecutar estos notebooks:

1. ✅ **Datos validados** - Calidad confirmada
2. ✅ **Insights identificados** - Patrones claros
3. ⏳ **Dashboard de Streamlit** - Implementar visualizaciones interactivas
4. ⏳ **Análisis predictivo** - Modelos de ML
5. ⏳ **Reportes automáticos** - Generación de informes

---

## 💡 Tips

### Optimización de Memoria

Si trabajas con datasets grandes:

```python
# Leer solo columnas necesarias
df = pd.read_sql("SELECT col1, col2 FROM table", conn)

# Usar tipos de datos eficientes
df['barrio_id'] = df['barrio_id'].astype('int32')
```

### Exportar Visualizaciones

```python
# Guardar figura
plt.savefig('output.png', dpi=300, bbox_inches='tight')

# Guardar mapa interactivo
m.save('mapa.html')
```

### Debugging

```python
# Ver información del DataFrame
df.info()

# Ver valores únicos
df['columna'].value_counts()

# Detectar nulos
df.isnull().sum()
```

---

## 📖 Referencias

- **Pandas**: https://pandas.pydata.org/docs/
- **Matplotlib**: https://matplotlib.org/stable/contents.html
- **Seaborn**: https://seaborn.pydata.org/
- **GeoPandas**: https://geopandas.org/
- **Folium**: https://python-visualization.github.io/folium/
- **Scikit-learn**: https://scikit-learn.org/

---

## 🤝 Contribuir

Para añadir nuevos notebooks:

1. Seguir la convención de nombres: `XX_nombre_descriptivo.ipynb`
2. Incluir sección de Setup al inicio
3. Documentar cada sección con markdown
4. Añadir conclusiones al final
5. Actualizar este README

---

## 📝 Notas

- Los notebooks están diseñados para ejecutarse en orden
- Requieren conexión a la base de datos SQLite
- Algunos análisis geoespaciales requieren geometrías en `dim_barrios`
- Los datos de desempleo son sintéticos basados en estadísticas reales de 2023

---

**Última actualización**: 2026-01-06  
**Versión**: 1.0.0  
**Autor**: Barcelona Housing Demographics Analyzer Team
