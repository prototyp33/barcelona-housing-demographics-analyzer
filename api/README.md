# FastAPI Backend - API Documentation

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start API Server

```bash
# Development mode (with auto-reload)
uvicorn api.main:app --reload --port 8000

# Access at http://localhost:8000
```

### Interactive API Documentation

FastAPI automatically generates interactive documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## API Endpoints

### Health Check

- **GET** `/health` - Server health check
  ```bash
  curl http://localhost:8000/health
  # Response: {"status": "ok", "service": "Barcelona Housing API"}
  ```

---

### Barrios (Neighborhoods)

#### Get All Barrios

- **GET** `/api/barrios`
- **Query Parameters**:
  - `include_geometry` (bool, optional): Include GeoJSON geometry (default: false)

```bash
# Without geometry
curl "http://localhost:8000/api/barrios"

# With geometry for mapping
curl "http://localhost:8000/api/barrios?include_geometry=true"
```

#### Get Barrio by ID

- **GET** `/api/barrios/{barrio_id}`

```bash
curl "http://localhost:8000/api/barrios/1"
```

---

### Demographics

#### Get Demographics Data

- **GET** `/api/demographics`
- **Query Parameters**:
  - `barrio_id` (int, optional): Filter by barrio
  - `year` (int, optional): Filter by specific year
  - `year_start` (int, optional): Filter by year range start
  - `year_end` (int, optional): Filter by year range end

```bash
# All demographics
curl "http://localhost:8000/api/demographics"

# Specific barrio and year
curl "http://localhost:8000/api/demographics?barrio_id=1&year=2023"

# Year range
curl "http://localhost:8000/api/demographics?year_start=2020&year_end=2024"
```

#### Get Extended Demographics

- **GET** `/api/demographics/extended`
- **Query Parameters**: Same as above
- **Returns**: Age groups, sex, and nationality breakdowns

```bash
curl "http://localhost:8000/api/demographics/extended?barrio_id=1&year=2023"
```

#### Get Demographic Trends

- **GET** `/api/demographics/trends/{barrio_id}`
- **Query Parameters**:
  - `year_start` (int, optional)
  - `year_end` (int, optional)

```bash
curl "http://localhost:8000/api/demographics/trends/1?year_start=2015&year_end=2024"
```

---

### Housing

#### Get Housing Prices

- **GET** `/api/housing/prices`
- **Query Parameters**:
  - `barrio_id` (int, optional)
  - `year` (int, optional)

```bash
# All prices
curl "http://localhost:8000/api/housing/prices"

# Specific barrio and year
curl "http://localhost:8000/api/housing/prices?barrio_id=1&year=2024"
```

#### Get Rent Data

- **GET** `/api/housing/rent`
- **Query Parameters**:
  - `barrio_id` (int, optional)
  - `year` (int, optional)

```bash
curl "http://localhost:8000/api/housing/rent?year=2022"
```

#### Get Price Trends

- **GET** `/api/housing/prices/trends/{barrio_id}`
- **Query Parameters**:
  - `year_start` (int, optional)
  - `year_end` (int, optional)

```bash
curl "http://localhost:8000/api/housing/prices/trends/1?year_start=2020&year_end=2024"
```

#### Get Gross Yield

- **GET** `/api/housing/yield/{barrio_id}`
- **Query Parameters**:
  - `year` (int, default: 2024)
- **Returns**: Rental yield calculation as percentage

```bash
curl "http://localhost:8000/api/housing/yield/1?year=2024"
```

---

## Response Models

### BarrioResponse

```json
{
  "barrio_id": 1,
  "barrio_nombre": "el Raval",
  "distrito_nombre": "Ciutat Vella",
  "geometry_json": null
}
```

### DemographicsResponse

```json
{
  "barrio_id": 1,
  "anio": 2023,
  "poblacion": 50000,
  "sexo": "H",
  "grupo_edad": "25-44",
  "nacionalidad": "Española"
}
```

### HousingPriceResponse

```json
{
  "barrio_id": 1,
  "anio": 2024,
  "trimestre": 1,
  "precio_venta_m2": 4500.0,
  "precio_alquiler_m2": 18.5,
  "superficie_media": null
}
```

### RentResponse

```json
{
  "barrio_id": 1,
  "anio": 2022,
  "renta_euros": 35000,
  "renta_mediana": 32000,
  "num_secciones": 15
}
```

### YieldResponse

```json
{
  "barrio_id": 1,
  "barrio_nombre": "el Raval",
  "year": 2024,
  "gross_yield_percent": 4.93,
  "precio_venta_m2": 4500.0,
  "precio_alquiler_m2": 18.5,
  "calculation_note": "Based on 70m² apartment average"
}
```

---

## CORS Configuration

The API allows requests from:

- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative React dev server)

For production, update `api/main.py` to include your deployed frontend domain.

---

## Database

The API connects to SQLite database at:

```
data/processed/database.db
```

Ensure this database exists and contains the required tables:

- `dim_barrios`
- `fact_precios`
- `fact_demografia`
- `fact_demografia_ampliada`
- `fact_renta`

Run the ETL pipeline first if the database doesn't exist:

```bash
python scripts/process_and_load.py
```

---

## Development

### Run with Auto-Reload

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Get barrios count
curl -s http://localhost:8000/api/barrios | python -m json.tool | grep barrio_id | wc -l

# Get demographics for 2023
curl -s "http://localhost:8000/api/demographics?year=2023" | python -m json.tool
```

---

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ ./api/
COPY src/ ./src/
COPY data/processed/database.db ./data/processed/
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Server

```bash
# Using Gunicorn with Uvicorn workers
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Successful request
- `404 Not Found`: Resource not found (e.g., barrio ID doesn't exist)
- `422 Unprocessable Entity`: Invalid query parameters
- `500 Internal Server Error`: Server error

All error responses include a `detail` field with explanation.

---

## Next Steps

1. Connect React frontend to API endpoints
2. Add caching (Redis) for frequently accessed data
3. Implement rate limiting
4. Add authentication (JWT) if needed
5. Write pytest unit tests for endpoints
6. Add monitoring (Sentry, Prometheus)
