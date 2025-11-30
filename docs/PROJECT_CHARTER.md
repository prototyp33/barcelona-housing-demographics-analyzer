## 🏗️ Project Charter & Developer Profile

### 1. Perfil del Desarrollador: "The AI-Augmented Engineer"

Este proyecto es ejecutado por un único desarrollador actuando como un "equipo virtual" gracias al uso intensivo de herramientas de IA Generativa.

- **Rol:** Lead Data Engineer & Analyst (Solo-preneur).
- **Stack de Productividad:** Cursor (IDE), Perplexity (Investigación), Gemini (Arquitectura).
- **Capacidad Operativa:** ~8-15 horas/semana (fines de semana/tardes).
- **Enfoque Técnico:** Desarrollo rápido de prototipos (MVP), Clean Code y automatización mediante CI/CD.

### 2. Visión del Proyecto (Goal)

- **Objetivo Principal (Portfolio):** Demostrar competencia técnica avanzada en la construcción de pipelines ETL end-to-end, ingeniería de datos y visualización analítica, priorizando la calidad del código sobre la complejidad de la infraestructura.
- **Objetivo de Producto (MVP):** Crear un **"Mapa de Rentabilidad (Yield)"** para Barcelona que democratice información financiera compleja (cruce de precios de oferta vs. alquiler real) habitualmente reservada a inversores institucionales.

### 3. Restricciones (Constraints)

Estas limitaciones definen las decisiones de arquitectura:

- **Presupuesto Cero (Bootstrap):** El proyecto debe operar sin costes recurrentes de infraestructura o licencias de datos.
  - *Consecuencia:* No se utilizan APIs de pago (Registradores, Idealista API comercial).
- **Infraestructura Híbrida:**
  - *Computación Pesada (ETL/Scraping):* Ejecución local.
  - *Repositorio/CI:* GitHub Free Tier.
  - *Presentación:* Streamlit Community Cloud (Hosting gratuito).
- **Acceso a Datos:** Limitado a fuentes de datos abiertos (Open Data BCN, Incasòl) y técnicas de *web scraping* ético para datos de mercado en tiempo real.

### 4. Suposiciones (Assumptions)

- **Proxy de Mercado:** Asumimos que los datos de fianzas del Incasòl representan fielmente el "precio real de cierre" del alquiler, sirviendo como verdad terreno frente a los precios de oferta.
- **Viabilidad del Scraping:** Se asume posible la extracción de muestras estadísticas de precios de venta (agregados por barrio) mediante Playwright sin incurrir en bloqueos permanentes, respetando una frecuencia de actualización baja (mensual).
- **Estabilidad de Fuentes:** Asumimos que la estructura de los portales de datos abiertos (Open Data BCN) se mantendrá estable durante el ciclo de desarrollo del Q1 2026.

### 5. Definición de Éxito (KPIs)

- **Técnico:** Pipeline ETL automatizado que ingesta, limpia y carga datos de 3 fuentes dispares (CSV oficial, scraping, GeoJSON) sin intervención manual de limpieza.
- **Producto:** Despliegue de un dashboard público donde un usuario pueda ver el % de rentabilidad bruta (Yield) de cualquier barrio de Barcelona en menos de 3 clics.

---

### ¿Cómo usar esto?

Añade este documento al `README.md` o enlázalo desde la sección de introducción para dar contexto a reclutadores o colaboradores. Explica claramente las decisiones sobre SQLite, scraping y priorización de fuentes gratuitas dentro del marco de un desarrollador aumentado por IA.

