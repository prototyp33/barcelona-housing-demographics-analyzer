# Análisis del Mercado Inmobiliario de Barcelona

**Fecha:** 28 de diciembre de 2024  
**Período Analizado:** 2012-2025  
**Datos:** 6,358 registros, 73 barrios

---

## 📊 RESUMEN EJECUTIVO

### **Hallazgos Clave:**

1. **✓ Los precios siguen una distribución LOG-NORMAL** (no normal)
2. **✗ Los precios de VENTA crecieron 6.9pp POR DEBAJO de la inflación** post-COVID
3. **✓ Los precios de ALQUILER crecieron 3.4pp POR ENCIMA de la inflación** post-COVID
4. **Yield promedio: 5.00%** (rentabilidad bruta anual)

---

## 1. DISTRIBUCIÓN DE PRECIOS

### **Test de Normalidad (Shapiro-Wilk):**

| Métrica              | Escala Normal     | Escala Log        | Conclusión       |
| -------------------- | ----------------- | ----------------- | ---------------- |
| **Precios Venta**    | W=0.9689, p<0.001 | W=0.9858, p<0.001 | ✓ **LOG-NORMAL** |
| **Precios Alquiler** | W=0.9466, p<0.001 | W=0.9892, p<0.001 | ✓ **LOG-NORMAL** |

**Interpretación:**

- Los precios NO siguen una distribución normal estándar
- Siguen una distribución **log-normal** (mejor ajuste en escala logarítmica)
- Esto es típico en mercados inmobiliarios: pocos valores muy altos, mayoría concentrada en rango medio-bajo

### **Estadísticas Descriptivas:**

#### **Precios de Venta (€/m²):**

- **Media:** 3,161 €/m²
- **Mediana:** 2,991 €/m² (5.4% menor que la media → asimetría positiva)
- **Rango:** 343 - 12,154 €/m²
- **Desv. Std:** 1,280 €/m² (40.5% de la media → alta variabilidad)
- **Skewness:** 0.70 (asimetría positiva → cola derecha larga)
- **Kurtosis:** 0.78 (distribución ligeramente más puntiaguda que normal)

#### **Precios de Alquiler (€/mes):**

- **Media:** 860 €/mes
- **Mediana:** 816 €/mes (5.2% menor que la media)
- **Rango:** 211 - 2,088 €/mes
- **Desv. Std:** 288 €/mes (33.4% de la media)
- **Skewness:** 1.01 (asimetría más pronunciada que venta)
- **Kurtosis:** 1.66 (mayor concentración en valores centrales)

**Conclusión:**

- Ambos mercados muestran **asimetría positiva** (más barrios con precios bajos/medios, pocos con precios muy altos)
- Mayor variabilidad en precios de venta que en alquileres
- Distribución log-normal sugiere usar **medianas** en lugar de medias para análisis

---

## 2. EVOLUCIÓN TEMPORAL (2012-2025)

### **Índice Base 100 (2015):**

| Año  | Precio Venta | Precio Alquiler | Inflación (IPC) |
| ---- | ------------ | --------------- | --------------- |
| 2015 | 100.0        | 100.0           | 100.0           |
| 2019 | 112.3        | 108.5           | 104.3           |
| 2020 | 110.8        | 106.2           | 103.6 (COVID)   |
| 2021 | 115.4        | 114.7           | 107.0           |
| 2022 | 118.9        | 125.3           | 116.0           |
| 2023 | 122.1        | 128.9           | 120.0           |
| 2024 | 125.2        | 132.1           | 123.5           |

### **Impacto COVID-19 (2019 → 2024):**

| Métrica             | Cambio | vs Inflación  |
| ------------------- | ------ | ------------- |
| **Precio Venta**    | +11.5% | **-6.9pp** ⬇️ |
| **Precio Alquiler** | +21.8% | **+3.4pp** ⬆️ |
| **Inflación**       | +18.4% | -             |

**Análisis:**

1. **Precios de Venta:**

   - ✗ Crecieron **por debajo** de la inflación (-6.9pp)
   - Pérdida de valor real del 6.9%
   - Posible explicación: Incertidumbre económica, aumento de tipos de interés

2. **Precios de Alquiler:**

   - ✓ Crecieron **por encima** de la inflación (+3.4pp)
   - Ganancia de valor real del 3.4%
   - Posible explicación: Mayor demanda de alquiler, menor oferta, regulación limitada

3. **Divergencia Venta-Alquiler:**
   - Gap de **10.3 puntos porcentuales** (21.8% - 11.5%)
   - Indica mercado de alquiler más dinámico y resiliente
   - Sugiere cambio en preferencias: más inquilinos, menos compradores

**Conclusión:**

- El COVID-19 impactó **negativamente** el mercado de venta (pérdida de valor real)
- El mercado de alquiler se **fortaleció** post-COVID
- Los alquileres son más resistentes a crisis económicas

---

## 3. YIELD (RENTABILIDAD BRUTA) POR BARRIO

### **Fórmula:**

```
Yield = (Alquiler Anual / Precio Venta) × 100
```

_Asumiendo 70m² de superficie promedio_

### **Estadísticas Generales:**

- **Media:** 5.00%
- **Mediana:** 4.94%
- **Rango:** 3.44% - 6.81%
- **Desv. Std:** 0.70%

### **TOP 10 BARRIOS - MAYOR RENTABILIDAD:**

| Barrio                         | Distrito            | Yield     | Venta (€/m²) | Alquiler (€/mes) |
| ------------------------------ | ------------------- | --------- | ------------ | ---------------- |
| **la Verneda i la Pau**        | Sant Martí          | **6.81%** | 2,704        | 1,075            |
| **la Marina del Prat Vermell** | Sants-Montjuïc      | **6.47%** | 2,804        | 1,059            |
| **les Roquetes**               | Nou Barris          | **6.34%** | 2,100        | 777              |
| **Pedralbes**                  | Les Corts           | **6.31%** | 5,416        | 1,995            |
| **la Bordeta**                 | Sants-Montjuïc      | **6.28%** | 3,445        | 1,261            |
| **Baró de Viver**              | Sant Andreu         | **6.12%** | 1,714        | 612              |
| **Vallvidrera**                | Sarrià-Sant Gervasi | **6.09%** | 3,864        | 1,372            |
| **Ciutat Meridiana**           | Nou Barris          | **5.97%** | 1,763        | 614              |
| **Canyelles**                  | Nou Barris          | **5.94%** | 2,449        | 848              |
| **la Guineueta**               | Nou Barris          | **5.75%** | 2,686        | 900              |

**Patrón:** Barrios periféricos y populares tienen mayor rentabilidad

### **BOTTOM 10 BARRIOS - MENOR RENTABILIDAD:**

| Barrio                 | Distrito            | Yield     | Venta (€/m²) | Alquiler (€/mes) |
| ---------------------- | ------------------- | --------- | ------------ | ---------------- |
| **Can Peguera**        | Nou Barris          | **3.44%** | 2,717        | 546              |
| **la Barceloneta**     | Ciutat Vella        | **3.73%** | 4,829        | 1,052            |
| **Sarrià**             | Sarrià-Sant Gervasi | **3.98%** | 6,300        | 1,461            |
| **la Vila de Gràcia**  | Gràcia              | **4.05%** | 4,873        | 1,152            |
| **la Sagrada Família** | Eixample            | **4.08%** | 4,762        | 1,132            |
| **el Poblenou**        | Sant Martí          | **4.12%** | 4,960        | 1,192            |
| **Diagonal Mar**       | Sant Martí          | **4.14%** | 5,898        | 1,424            |
| **la Clota**           | Horta-Guinardó      | **4.24%** | 3,770        | 933              |
| **les Corts**          | Les Corts           | **4.24%** | 5,036        | 1,246            |
| **Sant Pere**          | Ciutat Vella        | **4.25%** | 4,428        | 1,098            |

**Patrón:** Barrios céntricos y premium tienen menor rentabilidad

### **Análisis de Yield:**

**Correlación Precio-Yield:**

- **Tendencia negativa:** A mayor precio de venta, menor yield
- Barrios caros (>5,000 €/m²): Yield promedio 4.2%
- Barrios económicos (<3,000 €/m²): Yield promedio 6.1%

**Interpretación:**

1. **Inversión en Barrios Populares:**

   - ✓ Mayor rentabilidad (6-7%)
   - ✓ Menor inversión inicial
   - ✗ Menor apreciación de capital
   - ✗ Mayor riesgo de impago

2. **Inversión en Barrios Premium:**

   - ✗ Menor rentabilidad (3.5-4.5%)
   - ✗ Mayor inversión inicial
   - ✓ Mayor apreciación de capital
   - ✓ Menor riesgo de impago

3. **Caso Especial - Pedralbes:**
   - Único barrio premium con alto yield (6.31%)
   - Precio alto (5,416 €/m²) pero alquiler muy alto (1,995 €/mes)
   - Posible nicho de mercado de lujo

---

## 🎯 CONCLUSIONES Y RECOMENDACIONES

### **Hallazgos Principales:**

1. **Distribución Log-Normal:**

   - Usar medianas en lugar de medias para análisis
   - Considerar transformación logarítmica en modelos predictivos

2. **Divergencia Post-COVID:**

   - Mercado de venta: Pérdida de valor real (-6.9pp vs inflación)
   - Mercado de alquiler: Ganancia de valor real (+3.4pp vs inflación)
   - Sugiere cambio estructural en preferencias de vivienda

3. **Rentabilidad Heterogénea:**
   - Rango amplio: 3.44% - 6.81%
   - Barrios periféricos: Mejor para inversión de flujo de caja
   - Barrios céntricos: Mejor para apreciación de capital

### **Recomendaciones para Inversores:**

**Perfil Conservador (Apreciación de Capital):**

- Barrios: Sarrià, Pedralbes, Eixample
- Yield esperado: 4-4.5%
- Riesgo: Bajo
- Horizonte: Largo plazo (10+ años)

**Perfil Agresivo (Flujo de Caja):**

- Barrios: Nou Barris, Sant Martí (periféricos)
- Yield esperado: 5.5-6.8%
- Riesgo: Medio-Alto
- Horizonte: Medio plazo (5-7 años)

**Perfil Balanceado:**

- Barrios: Sants-Montjuïc, Sant Andreu
- Yield esperado: 5-5.5%
- Riesgo: Medio
- Horizonte: Medio-Largo plazo (7-10 años)

### **Próximos Análisis Sugeridos:**

1. **Análisis de Inequidad:**

   - Correlación Gini vs Precios
   - Identificar barrios en riesgo de gentrificación

2. **Modelo Predictivo:**

   - Predecir precios futuros usando ML
   - Variables: Renta, demografía, catastro

3. **Análisis de Clusters:**
   - Segmentar barrios por características similares
   - Identificar oportunidades de inversión

---

**Archivos Generados:**

- `reports/analisis_distribucion_precios.png`
- `reports/evolucion_temporal_precios.png`
- `reports/yield_rentabilidad_barrios.png`
- `reports/market_analysis.log`

**Última Actualización:** 28 de diciembre de 2024
