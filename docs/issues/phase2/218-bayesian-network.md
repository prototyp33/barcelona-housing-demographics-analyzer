## 🎯 Objetivo
Implementar Bayesian Network (Paper #2) para modelar causalidad precio vivienda Barcelona usando `pgmpy`. **BACKLOG - Solo después validar K-Means #214**.

## 📝 Descripción
Aprender estructura DAG causal para entender drivers de precio: typology → precio, renta → precio, educación → gentrificación → precio.

**Desafío clave:** No hay datos listing-level → **generar datos sintéticos** desde agregados barrio.

## 📦 Dependencias
- **Depends On:** #214 (K-Means - submarkets informan DAG), #216 (fact_educacion - variable causal clave)
- **Feeds Into:** Paper #2, Dashboard causal insights
- **Priority:** 🟢 Low - Fase 2.2+ (Q2 2025)

## ✅ Tareas

### 1. Synthetic Data Generation (8h)
- [ ] Diseñar estrategia bootstrap:
  - Generar n=50 listings/barrio desde distribuciones
  - Preservar correlaciones observadas (precio-renta, precio-educación)
  - Añadir ruido gaussiano realista
- [ ] Implementar `generate_synthetic_listings()`:
  ```
  def generate_synthetic_listings(db_conn, n_per_barrio=50):
      # Extraer aggregates: mean, std por barrio
      # Bootstrap n samples con distribución normal
      # Validar: KS-test vs distribución original
      return synthetic_df  # ~3600 listings (73 barrios × 50)
  ```
- [ ] Validar realismo: comparar distribuciones sintéticas vs reales (si disponibles)

### 2. Structure Learning (6h)
- [ ] Preparar features para DAG:
  - **Endógenas:** `precio_m2_venta`, `precio_alquiler_mes`
  - **Exógenas:** `m2_superficie`, `renta_mediana`, `universitarios_pct`, `distancia_centro_km`
  - **Confounders:** `distrito`, `anio`, `cluster_kmeans` (de #214)
- [ ] Implementar `learn_causal_structure()`:
  ```
  from pgmpy.estimators import HillClimbSearch, BicScore
  
  hc = HillClimbSearch(data)
  best_model = hc.estimate(scoring_method=BicScore(data))
  ```
- [ ] Validar DAG:
  - No ciclos imposibles (ej: precio → renta → precio)
  - Sentido económico (typology → precio es esperado)
  - ≥6 nodos, ≥8 aristas

### 3. Parameter Learning (4h)
- [ ] Maximum Likelihood Estimation para CPDs (Conditional Probability Distributions)
- [ ] Validar parámetros:
  - Signos correctos (renta ↑ → precio ↑)
  - Magnitudes razonables
- [ ] Calcular efectos directos/indirectos:
  ```
  # ¿Cuánto impacta educación en precio?
  # Directo: educación → precio
  # Indirecto: educación → gentrificación → precio
  ```

### 4. Validation (4h)
- [ ] Cross-validation 5-fold:
  - Entrenar DAG en 80% datos
  - Predecir precio en 20% test
  - Métrica: AUC > 0.75, RMSE < 15%
- [ ] Sensitivity analysis:
  - ¿Qué pasa si elimino nodo `universitarios_pct`?
  - ¿Cambia estructura DAG?
- [ ] Bootstrap stability (50 iteraciones):
  - ¿DAG cambia mucho entre samples?
  - Objetivo: ≥80% aristas consistentes

### 5. Visualización y Documentación (4h)
- [ ] Exportar DAG a JSON para viz:
  ```
  dag_json = {
      "nodes": [{"id": "precio", "label": "Precio €/m²"}, ...],
      "edges": [{"source": "renta", "target": "precio", "weight": 0.65}, ...]
  }
  ```
- [ ] Crear visualización D3.js interactiva
- [ ] Redactar report: `docs/analysis/BAYESIAN_CAUSAL_RESULTS.md`
  - Executive summary: variables más influyentes
  - DAG diagram con interpretación
  - Efectos causales cuantificados
  - Limitaciones (datos sintéticos)

## 🎯 Criterios de Aceptación
- ✅ DAG aprendido con ≥6 nodos, ≥8 aristas
- ✅ Validación AUC > 0.75 en price prediction
- ✅ DAG interpretable (no ciclos imposibles)
- ✅ Efectos causales cuantificados (ej: "+10% universitarios → +5% precio")
- ✅ Exportado a JSON para visualización
- ✅ Report con limitaciones documentadas

## 📁 Entregables
```
notebooks/analysis/
  └── 02_bayesian_network_causal.ipynb    # Notebook principal

models/
  └── bayesian_network_v0.pkl             # Modelo serializado

docs/analysis/
  └── BAYESIAN_CAUSAL_RESULTS.md          # Report académico

outputs/visualizations/
  ├── dag_barcelona_housing.json          # DAG para D3.js
  └── dag_interactive.html                # Visualización web
```

## ⏱️ Estimación
**22 horas** (Synthetic 8h + Structure 6h + Parameters 4h + Validation 4h)

## 🔗 Referencias
- **Paper #2:** [Bayesian Networks Barcelona](https://arxiv.org/abs/2506.09539)
- **pgmpy Documentation:** https://pgmpy.org/
- **Pearl Causality:** Book "Causality: Models, Reasoning and Inference"
- **BIC Score:** https://en.wikipedia.org/wiki/Bayesian_information_criterion

## ⚠️ Riesgos
1. **Datos sintéticos no representativos** → Validar con KS-test, ajustar distribuciones
2. **DAG inestable** → Probar múltiples seeds, reportar consenso de aristas
3. **Overfitting** → Usar BIC penalty, validación cruzada rigurosa
4. **Causalidad espuria** → Peer review con economista urbano
5. **Complejidad computacional** → Limitar espacio de búsqueda (whitelist/blacklist aristas)

## 📊 Métricas de Éxito
| Métrica | Target |
|---------|--------|
| DAG nodes | ≥6 |
| DAG edges | ≥8 |
| Validation AUC | >0.75 |
| Bootstrap stability | >80% aristas consistentes |
| Interpretabilidad | Peer review approved |

## 🏷️ Metadata
- **Status:** 📋 Backlog
- **Priority:** 🟢 Low
- **Size:** XL
- **Estimate:** 22h
- **Phase:** Modeling
- **Epic:** AN
- **Release:** v2.2 Dashboard Polish
- **Quarter:** Q2 2025
- **Outcome:** Bayesian Network DAG learned with AUC > 0.75 in price prediction validation
