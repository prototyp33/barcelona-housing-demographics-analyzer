# Guía: Configurar API de Idealista

**Fecha**: 2025-12-19  
**Issue**: #202 - Fase 2  
**Referencia**: [Cliente GitHub](https://github.com/yagueto/idealista-api)

---

## Opción 1: Usar Cliente GitHub (Recomendado)

El cliente de GitHub es más simple y directo que nuestro extractor propio.

### Instalación

```bash
pip install git+https://github.com/yagueto/idealista-api.git
```

### Uso

```python
from idealista_api import Idealista, Search

idealista = Idealista(
    api_key=os.getenv("IDEALISTA_API_KEY"),
    api_secret=os.getenv("IDEALISTA_API_SECRET")
)

request = Search(
    "es",
    location_id="0-EU-ES-08-019-001-000",  # Barcelona
    property_type="homes",
    operation="sale",
    max_items=50,
    num_page=1
)

response = idealista.query(request)
```

---

## Opción 2: Usar Extractor Propio

Ya existe en el proyecto: `src/extraction/idealista.py`

```python
from src.extraction.idealista import IdealistaExtractor

extractor = IdealistaExtractor()
df, metadata = extractor.search_properties(
    operation="sale",
    location="8",  # Barcelona location ID
    max_items=50
)
```

---

## Obtener Credenciales API

1. **Registrarse**: https://developers.idealista.com/
2. **Solicitar acceso**: Completar formulario de desarrollador
3. **Recibir credenciales**: API Key y API Secret por email
4. **Configurar variables de entorno**:
   ```bash
   export IDEALISTA_API_KEY=your_key_here
   export IDEALISTA_API_SECRET=your_secret_here
   ```

---

## Limitaciones

- **Límite**: 150 calls/mes (según reglas del proyecto)
- **Máximo por request**: 50 propiedades
- **Paginación**: Necesaria para obtener más resultados

---

## Script de Extracción para Gràcia

Usar el script creado:

```bash
# Con variables de entorno
export IDEALISTA_API_KEY=your_key
export IDEALISTA_API_SECRET=your_secret
python3 spike-data-validation/scripts/fase2/extract_idealista_api_gracia.py

# O con argumentos
python3 spike-data-validation/scripts/fase2/extract_idealista_api_gracia.py \
    --api-key YOUR_KEY \
    --api-secret YOUR_SECRET \
    --max-properties 100
```

---

## Location IDs para Gràcia

Los location IDs específicos de barrios necesitan ser descubiertos usando la API.

**Script de descubrimiento**: `scripts/build_idealista_location_ids.py`

**Barcelona City ID**: `0-EU-ES-08-019-001-000` (usado como fallback)

---

## Próximos Pasos

1. ✅ Script creado: `extract_idealista_api_gracia.py`
2. ⏳ Obtener credenciales API de Idealista
3. ⏳ Ejecutar extracción
4. ⏳ Filtrar resultados para Gràcia
5. ⏳ Matching con datos Catastro

---

**Última actualización**: 2025-12-19

