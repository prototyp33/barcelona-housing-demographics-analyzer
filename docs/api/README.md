# 🔌 Documentación de API

Este directorio contiene la documentación de APIs, tanto internas como externas.

## APIs Externas Consumidas

### Open Data BCN (CKAN)
- **Base URL:** `https://opendata-ajuntament.barcelona.cat/data/api/3/`
- **Rate Limit:** 10 req/seg
- **Auth:** No requerida
- **Docs:** [CKAN API Guide](https://docs.ckan.org/en/2.9/api/)

### Portal de Dades
- **Base URL:** `https://portaldades.ajuntament.barcelona.cat/api/`
- **Rate Limit:** Sin límite documentado
- **Auth:** No requerida

### IDESCAT
- **Base URL:** `https://api.idescat.cat/`
- **Rate Limit:** Sin límite documentado
- **Auth:** No requerida
- **Formato:** JSON/XML

### Idealista (via RapidAPI)
- **Rate Limit:** ⚠️ **150 llamadas/mes**
- **Auth:** API Key (RapidAPI)
- **Docs:** [RapidAPI Idealista](https://rapidapi.com/idealista/api/idealista)

## API Interna (Feature #28 - Futuro)

### Endpoints Planificados

```
GET  /api/v1/barrios              # Lista todos los barrios
GET  /api/v1/barrios/{id}         # Detalle de un barrio
GET  /api/v1/barrios/{id}/precios # Histórico de precios
GET  /api/v1/barrios/{id}/demo    # Datos demográficos
GET  /api/v1/prediccion/{id}      # Predicción ML de precios
POST /api/v1/inversion/calcular   # Calculadora de inversión
GET  /api/v1/alertas              # Alertas activas
```

### Autenticación
- API Key via header: `X-API-Key: <key>`
- Rate limit: 100 req/min por key

### Respuesta Estándar

```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "total": 73,
    "page": 1,
    "per_page": 20,
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

### Errores

```json
{
  "status": "error",
  "error": {
    "code": "BARRIO_NOT_FOUND",
    "message": "Barrio con ID 999 no encontrado"
  }
}
```

## Documentación Adicional

- [rest_api_docs.md](rest_api_docs.md) - Documentación completa de la API REST
- [authentication.md](authentication.md) - Guía de autenticación
- [rate_limiting.md](rate_limiting.md) - Políticas de rate limiting

