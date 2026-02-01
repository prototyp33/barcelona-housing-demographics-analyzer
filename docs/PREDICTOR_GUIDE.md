# 🔮 Guía de Interpretación: Predictor de Precios v2.1

Esta guía explica cómo utilizar y entender los resultados del **Predictor Inteligente de Precios**, una herramienta diseñada para cuantificar el impacto de los factores socioeconómicos y la presión turística en el mercado inmobiliario de Barcelona.

## 1. ¿Qué es el Valor Predicho?

El valor predicho representa el **"precio teórico de equilibrio"** que el modelo estadístico (Ridge Regression) asigna a un barrio basándose en:

- **Nivel de Renta Familiar**: Capacidad adquisitiva de la zona.
- **Presión Turística**: Volumen de listings de Airbnb.
- **Estructura Demográfica**: % de inmigración, tamaño del hogar, desempleo y edad.

**Importante:** No es una tasación inmobiliaria de un piso concreto. Es una estimación del valor medio del barrio basada puramente en datos agregados.

## 2. El Mapa de Residuales (Detección de Sub/Sobrevaloración)

El mapa de residuales es la herramienta más potente para identificar oportunidades o zonas sobrepreciadas. Muestra la **diferencia entre el precio real de mercado y lo que el modelo predice**.

### 🔵 Zonas Azules (Residuales Negativos)

Indican barrios que son **más baratos de lo que sugiere su nivel de renta y turismo**.

- **Interpretación:** Pueden ser zonas con potencial de revalorización ("gangas estadísticas") o barrios donde existen factores negativos no modelados (ej. problemas de seguridad, degradación del parque edificado o ruido excesivo).
- **Ejemplo Típico:** **El Raval**. Tiene una altísima presión turística y ubicación central, pero su precio real es menor al predicho por el modelo debido a estigmas sociales y conflictos de convivencia.

### 🔴 Zonas Rojas (Residuales Positivos)

Indican barrios que son **más caros de lo que sugiere la estadística básica**.

- **Interpretación:** Estos barrios poseen un **"Premium"** que el modelo no explica. Generalmente se debe a la "marca de barrio", prestigio histórico, calidad constructiva excepcional o abundancia de servicios premium (colegios, comercio de lujo).
- **Ejemplo Típico:** **L'Antiga Esquerra de l'Eixample**. El mercado otorga un valor extra por el estatus y la calidad arquitectónica (Eixample) que va más allá de su renta o densidad de Airbnb.

## 3. El Simulador de Escenarios y Atribución

### Atribución del Valor

El panel de resultados desglosa cuánto del precio final se debe a cada factor:

- **Driver Renta:** El peso económico de los hogares residentes.
- **Driver Turismo:** El "recargo" estimado por la competencia de alquiler turístico de corto plazo.

### Curvas de Sensibilidad

En la pestaña de **Sensibilidad**, puedes ver cómo cambiaría el precio si **solo ajustáramos un factor**.

> _Ejemplo:_ Si en un barrio la renta se mantiene igual pero los listings de Airbnb aumentan de 100 a 500, ¿cuánto subiría el €/m²? La pendiente de la curva te da la respuesta directa.

## 4. Supuestos y Limitaciones Técnicas

Para un uso responsable de la herramienta, se deben tener en cuenta las siguientes limitaciones:

- **Correlación no es Causalidad**: El modelo identifica patrones históricos. Que el aumento de Airbnb esté correlacionado con precios altos no significa que sea la única causa (pueden existir factores ocultos como la inversión extranjera o la gentrificación comercial).
- **Linealidad**: El modelo actual es lineal. Asume que el efecto de un apartamento turístico extra es siempre el mismo, aunque en la práctica el impacto puede ser mucho mayor cuando un barrio llega a su punto de saturación.
- **Calidad de los Datos Históricos**: Los datos de renta y demografía provienen de censos oficiales que a veces tienen desfases de 1-2 años.
- **Factores No Modelados**: Actualmente el modelo **no ve**:
  - Proximidad al transporte público (Metro/Bicing).
  - Niveles de ruido o contaminación.
  - Presencia de colegios internacionales o parques.
  - **Seguridad y Criminalidad**: Estos factores son a menudo la causa de los "residuales negativos" (zonas azules en el mapa).

---

_Nota Metodológica: El modelo actual utiliza una Regresión Ridge con un R² de 0.51, lo que significa que captura el 51% de la lógica que mueve los precios en Barcelona._
